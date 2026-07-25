"""Intent Router.

Classifies a user's free-text objective into one of 20+ domains and extracts
structured entities (destination, subject, budget, etc.) needed by downstream agents.

Modes:
  - LLM mode  : Uses ANTHROPIC_API_KEY for deep contextual classification.
  - NLP mode  : Regex-free, token-based classifier as a robust offline fallback.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

import httpx

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-sonnet-4-6"

DOMAINS = [
    "travel",
    "career",
    "learning",
    "coding",
    "health",
    "fitness",
    "finance",
    "productivity",
    "research",
    "writing",
    "business",
    "documents",
    "meetings",
    "shopping",
    "entertainment",
    "education",
    "relationships",
    "life_planning",
    "reminder",
    "task",
]

_ROUTER_SYSTEM_PROMPT = f"""You are Wingman's Intent Router. Your ONLY job is to classify the user's objective and extract structured context from it.

Available domains: {', '.join(DOMAINS)}

Respond with ONLY a valid JSON object (no markdown, no prose, no explanation) with this exact shape:
{{
  "domain": "<one of the domains above>",
  "confidence": <float 0.0–1.0>,
  "entities": {{
    "subject": "<main topic, destination, skill, or goal>",
    "goal": "<what the user ultimately wants to achieve>",
    "destination": "<if travel: the place>",
    "budget": "<if mentioned: budget amount or range>",
    "timeline": "<if mentioned: duration or deadline>",
    "experience_level": "<beginner/intermediate/advanced if mentioned>",
    "group_size": "<solo/couple/group if mentioned>",
    "tech_stack": "<if coding: technologies mentioned>",
    "industry": "<if business/career: industry or sector>"
  }},
  "missing_fields": ["<list of fields that would significantly improve the plan quality but are absent>"],
  "summary": "<one sentence: what the user wants to do>"
}}

Only include entities that are actually present or strongly implied in the message.
For missing_fields, only flag truly important gaps — not every possible detail.
Be conservative: a rich objective with enough context should have an empty missing_fields list."""


@dataclass
class IntentResult:
    domain: str
    confidence: float
    entities: dict = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    summary: str = ""
    raw_objective: str = ""


# ---------------------------------------------------------------------------
# Domain keyword signatures (NLP fallback)
# ---------------------------------------------------------------------------

_DOMAIN_SIGNATURES: list[tuple[str, list[str]]] = [
    ("travel", [
        "trip", "travel", "flight", "vacation", "visit", "go to", "going to",
        "fly to", "flying to", "tour", "itinerary", "itenary", "destination",
        "hotel", "explore", "journey", "abroad", "passport", "visa", "cruise",
        "backpack", "airbnb", "booking", "tourist",
    ]),
    ("fitness", [
        "fitness", "workout", "lose weight", "gym", "marathon", "diet",
        "muscle", "bulk", "run", "running", "exercise", "cardio", "strength",
        "weight loss", "cutting", "bulking", "protein", "calories", "6 pack",
        "abs", "squat", "deadlift", "bench press",
    ]),
    ("health", [
        "doctor", "medication", "symptoms", "illness", "treatment", "therapy",
        "mental health", "anxiety", "depression", "chronic", "diagnosis",
        "prescription", "appointment", "specialist", "hospital", "clinic",
    ]),
    ("coding", [
        "build", "develop", "create an app", "create a website", "clone",
        "web app", "mobile app", "api", "backend", "frontend", "database",
        "deploy", "kubernetes", "docker", "microservices", "saas platform",
        "architecture", "code a", "program a", "build a", "make an app",
        "react", "nextjs", "python app", "node app", "django", "fastapi",
        "spring boot", "flutter", "swift app", "android app",
    ]),
    ("business", [
        "business", "startup", "company", "launch a", "sell", "store",
        "e-commerce", "agency", "shop", "cafe", "coffee shop", "restaurant",
        "franchise", "dropship", "product", "brand", "monetize", "revenue",
        "profit", "investors", "fundraise", "pitch",
    ]),
    ("career", [
        "become a", "career", "job", "hire", "hired", "promotion", "resume",
        "cv", "interview", "salary", "switch career", "data scientist",
        "machine learning engineer", "software engineer", "product manager",
        "designer", "ux designer", "devops", "cybersecurity", "infosec",
        "pentest", "hacker", "hacking", "security expert", "analyst",
    ]),
    ("learning", [
        "learn", "study", "master", "how to", "course", "tutorial", "skill",
        "degree", "certification", "understand", "teach me", "explain",
        "sql", "python", "javascript", "machine learning", "deep learning",
        "data science", "algorithms", "statistics", "math", "calculus",
    ]),
    ("finance", [
        "invest", "investment", "save money", "savings", "budget", "debt",
        "loan", "mortgage", "stocks", "crypto", "portfolio", "retirement",
        "financial", "money", "wealth", "passive income", "net worth",
    ]),
    ("research", [
        "research", "investigate", "analyze", "survey", "literature review",
        "paper", "thesis", "dissertation", "study on", "explore topic",
        "find information about", "report on",
    ]),
    ("writing", [
        "write", "essay", "blog", "article", "novel", "book", "story",
        "content", "copywriting", "script", "screenplay", "newsletter",
        "publish", "author",
    ]),
    ("reminder", [
        "remind", "remember", "don't forget", "alert me", "notify me",
        "set a reminder", "schedule a reminder",
    ]),
    ("meetings", [
        "meeting", "call", "standup", "1:1", "one on one", "agenda",
        "conference", "presentation", "demo", "sync",
    ]),
    ("shopping", [
        "buy", "purchase", "order", "shop for", "find me a", "recommend a",
        "best laptop", "best phone", "price comparison",
    ]),
    ("documents", [
        "summarize", "summarise", "document", "contract", "pdf", "report",
        "notes", "transcript", "extract", "review this", "analyze this",
    ]),
    ("productivity", [
        "organize", "schedule", "routine", "habit", "morning routine",
        "time management", "focus", "productivity", "procrastination",
        "discipline", "goal setting", "okr", "system",
    ]),
    ("life_planning", [
        "life goal", "10 year plan", "5 year plan", "move to", "emigrate",
        "relocate", "retire", "marriage", "family plan", "dream life",
    ]),
    ("relationships", [
        "relationship", "dating", "partner", "friend", "family", "communicate",
        "conflict", "love", "romantic", "breakup", "marriage advice",
    ]),
    ("entertainment", [
        "movie", "series", "watch", "game", "gaming", "music", "playlist",
        "recommend", "anime", "podcast", "book recommendation",
    ]),
    ("education", [
        "university", "college", "school", "admission", "application",
        "gpa", "scholarship", "sat", "gre", "gmat", "study abroad",
        "major", "curriculum",
    ]),
]

# Required fields per domain (for gatekeeper)
DOMAIN_REQUIRED_FIELDS: dict[str, list[str]] = {
    "travel": ["destination", "budget", "timeline"],
    "career": ["goal"],
    "learning": ["subject"],
    "coding": ["subject"],
    "business": ["subject"],
    "fitness": ["goal"],
    "finance": ["goal"],
    "health": ["goal"],
    "research": ["subject"],
    "writing": ["subject"],
    "reminder": ["subject", "timeline"],
    "meetings": ["subject"],
    "shopping": ["subject"],
    "documents": ["subject"],
    "productivity": ["goal"],
    "life_planning": ["goal"],
    "relationships": ["goal"],
    "entertainment": ["subject"],
    "education": ["goal"],
    "task": [],
}


class IntentRouter:
    """Classifies user objectives into domains and extracts structured entities."""

    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")

    def classify(self, objective: str, user_context: dict | None = None) -> IntentResult:
        """Classify the objective. Tries LLM first, falls back to NLP."""
        if self._api_key:
            try:
                return self._classify_with_llm(objective, user_context)
            except Exception:
                pass
        return self._classify_with_nlp(objective)

    # ------------------------------------------------------------------
    # LLM Path
    # ------------------------------------------------------------------

    def _classify_with_llm(self, objective: str, user_context: dict | None) -> IntentResult:
        context_note = ""
        if user_context and user_context.get("memory_snippets"):
            snippets = "; ".join(user_context["memory_snippets"][:5])
            context_note = f"\n\nUser memory context (use for personalization): {snippets}"

        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": 600,
                "system": _ROUTER_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": objective + context_note}],
            },
            timeout=15.0,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"]
        data = json.loads(raw)
        return IntentResult(
            domain=data.get("domain", "task"),
            confidence=float(data.get("confidence", 0.7)),
            entities=data.get("entities", {}),
            missing_fields=data.get("missing_fields", []),
            summary=data.get("summary", objective),
            raw_objective=objective,
        )

    # ------------------------------------------------------------------
    # NLP Fallback Path
    # ------------------------------------------------------------------

    def _classify_with_nlp(self, objective: str) -> IntentResult:
        lowered = objective.lower()
        best_domain = "task"
        best_score = 0

        for domain, keywords in _DOMAIN_SIGNATURES:
            score = sum(1 for kw in keywords if kw in lowered)
            if score > best_score:
                best_score = score
                best_domain = domain

        # Calculate a rough confidence
        confidence = min(0.5 + best_score * 0.12, 0.92)

        entities = self._extract_entities_nlp(lowered, best_domain, objective)
        missing = self._detect_missing_fields(best_domain, entities)

        return IntentResult(
            domain=best_domain,
            confidence=confidence,
            entities=entities,
            missing_fields=missing,
            summary=self._summarize_nlp(objective, best_domain),
            raw_objective=objective,
        )

    @staticmethod
    def _extract_entities_nlp(lowered: str, domain: str, original: str) -> dict:
        entities: dict = {}

        # Subject / Goal
        clean = re.sub(
            r"^(i want to|i wanna|i'd like to|please|can you|help me|give me|"
            r"create a|generate|plan a|schedule a|make me a|make me|build me a|"
            r"build me|teach me|show me)\s+",
            "",
            lowered.strip(),
        )

        # Travel: destination
        if domain == "travel":
            m = re.search(
                r"\b(?:to|in|around|visit|explore|for|going to)\s+([A-Za-z\s]{2,25}?)(?:\s+(?:trip|for|with|,|$))",
                original,
                re.IGNORECASE,
            )
            if m:
                dest = m.group(1).strip()
                if dest.lower() not in ("the", "a", "an", "my"):
                    entities["destination"] = dest
            if not entities.get("destination"):
                words = [
                    w for w in original.split()
                    if w.lower() not in
                    ("i", "wanna", "want", "go", "to", "trip", "travel",
                     "the", "a", "my", "plan", "me", "please", "help")
                ]
                if words:
                    entities["destination"] = " ".join(words[:2])

        # Budget
        budget_m = re.search(r"\$[\d,]+|\b(\d+)\s*(?:dollars?|usd|bucks?|k\b)", lowered)
        if budget_m:
            entities["budget"] = budget_m.group(0)

        # Timeline
        time_m = re.search(
            r"\b(\d+)\s*(day|week|month|year|night|hour)s?\b|\b(next\s+\w+|this\s+\w+|in\s+\d+\s+\w+)\b",
            lowered,
        )
        if time_m:
            entities["timeline"] = time_m.group(0)

        # Solo/group
        if any(w in lowered for w in ("solo", "alone", "myself", "by myself")):
            entities["group_size"] = "solo"
        elif any(w in lowered for w in ("couple", "partner", "wife", "husband", "girlfriend", "boyfriend")):
            entities["group_size"] = "couple"
        elif any(w in lowered for w in ("group", "friends", "family", "team")):
            entities["group_size"] = "group"

        # Experience level
        if any(w in lowered for w in ("beginner", "newbie", "never", "no experience", "zero")):
            entities["experience_level"] = "beginner"
        elif any(w in lowered for w in ("intermediate", "some experience", "basic knowledge")):
            entities["experience_level"] = "intermediate"
        elif any(w in lowered for w in ("advanced", "experienced", "expert", "professional")):
            entities["experience_level"] = "advanced"

        # Tech stack (coding)
        if domain == "coding":
            techs = []
            for tech in ["react", "vue", "angular", "nextjs", "django", "fastapi", "flask",
                         "node", "express", "postgresql", "mysql", "mongodb", "redis",
                         "python", "javascript", "typescript", "java", "go", "rust",
                         "flutter", "swift", "kotlin", "docker", "kubernetes", "aws"]:
                if tech in lowered:
                    techs.append(tech)
            if techs:
                entities["tech_stack"] = ", ".join(techs)

        # Subject (learning, research, writing, coding, etc.)
        subject_clean = re.sub(
            r"^(become a|become an|learn|study|master|how to|i want to|i wanna|teach me|make me a|"
            r"build a|build an|build me a|build me an|create a|create an|develop a|develop an|"
            r"make a|make an|write a|write an|design a|design an)\s+",
            "", clean, flags=re.IGNORECASE,
        )
        subject_clean = re.sub(
            r"\s*(expert|developer|engineer|specialist|guide|course|tutorial|from scratch|"
            r"i am a beginner|as a beginner|for beginners?|,?\s*i am.*)\s*$",
            "", subject_clean, flags=re.IGNORECASE,
        ).strip()
        # For coding: further clean "using X and Y" -> keep just the product name
        if domain == "coding":
            subject_clean = re.sub(
                r"\s+using\s+.+$", "", subject_clean, flags=re.IGNORECASE
            ).strip()
        # For learning: strip extra qualifiers after comma or " for "
        if domain == "learning":
            subject_clean = re.sub(
                r"\s+for\s+(data analysis|web development|beginners?|production|work).*$",
                "", subject_clean, flags=re.IGNORECASE
            ).strip()
            subject_clean = re.sub(r",.*$", "", subject_clean).strip()
        if subject_clean and domain not in ("travel",):
            entities["subject"] = subject_clean[:60]

        # Goal
        entities["goal"] = clean[:100]

        return {k: v for k, v in entities.items() if v}

    @staticmethod
    def _detect_missing_fields(domain: str, entities: dict) -> list[str]:
        required = DOMAIN_REQUIRED_FIELDS.get(domain, [])
        return [f for f in required if not entities.get(f)]

    @staticmethod
    def _summarize_nlp(objective: str, domain: str) -> str:
        cap = objective.strip().rstrip(".")
        return f"{cap} [{domain.replace('_', ' ').title()} objective]"
