"""Memory Manager.

Reads user memories before planning (personalization context) and writes
new facts extracted from the conversation after execution.

Provides UserContext to the MissionPlanner so every plan is shaped by
what Wingman already knows about this user.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field

import httpx

from repositories.memory_repository import MemoryRepository

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-sonnet-4-6"

_EXTRACTION_SYSTEM_PROMPT = """You are Wingman's Memory Extraction Engine.
Given a user's message and the assistant's response, extract ONLY factual, durable user preferences, constraints, or habits worth remembering for future personalization.

Respond with ONLY a JSON array of strings (no markdown, no prose). Each string is one concise fact.
Examples:
- "User prefers Emirates airline"
- "User studies on weekends only"
- "User has a budget of $3000 for Japan trip"
- "User is a beginner Python programmer"
- "User wants to become a Data Scientist"
- "User works in healthcare industry"

If there are no meaningful facts to extract, return an empty array: []
Extract at most 5 facts per message. Only extract facts the user stated or strongly implied — never infer."""


@dataclass
class UserContext:
    """Structured context from user memory, used by MissionPlanner for personalization."""
    memory_snippets: list[str] = field(default_factory=list)
    preferred_tools: list[str] = field(default_factory=list)
    learning_style: str = ""
    past_domains: list[str] = field(default_factory=list)
    budget_preference: str = ""
    time_preference: str = ""
    raw_memories: list[dict] = field(default_factory=list)

    def has_context(self) -> bool:
        return bool(self.memory_snippets)

    def as_prompt_context(self) -> str:
        """Formats memory as a prompt-insertable context block."""
        if not self.memory_snippets:
            return ""
        lines = "\n".join(f"- {s}" for s in self.memory_snippets[:10])
        return f"Known user context (use this to personalize the plan):\n{lines}"


class MemoryManager:
    """Reads and writes user memories for cross-session personalization."""

    def __init__(self, memory_repository: MemoryRepository) -> None:
        self._repo = memory_repository
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")

    # ------------------------------------------------------------------
    # Read: build UserContext before planning
    # ------------------------------------------------------------------

    def read(self, user_id: uuid.UUID, objective: str, domain: str) -> UserContext:
        """Retrieve relevant user memories and build a UserContext."""
        memories = self._repo.list_for_user(user_id, limit=50)

        if not memories:
            return UserContext()

        # Collect all memory content
        snippets = [m.content for m in memories]

        # Filter to domain-relevant ones first, then general
        domain_relevant = [
            s for s in snippets
            if domain in s.lower() or self._is_general_preference(s)
        ]
        final_snippets = (domain_relevant or snippets)[:15]

        # Parse out known preferences
        context = UserContext(
            memory_snippets=final_snippets,
            raw_memories=[{"content": m.content, "type": m.memory_type} for m in memories],
        )

        for snippet in final_snippets:
            low = snippet.lower()
            if any(kw in low for kw in ("weekend", "morning", "evening", "night")):
                context.time_preference = snippet
            if any(kw in low for kw in ("budget", "$", "price", "cost")):
                context.budget_preference = snippet
            if any(kw in low for kw in ("python", "react", "javascript", "sql", "prefer")):
                context.preferred_tools.append(snippet)

        return context

    # ------------------------------------------------------------------
    # Write: extract and store new facts after execution
    # ------------------------------------------------------------------

    def write(
        self,
        user_id: uuid.UUID,
        user_message: str,
        assistant_response: str,
        domain: str,
    ) -> list[str]:
        """Extract memorable facts from this exchange and persist them."""
        facts = self._extract_facts(user_message, assistant_response)
        for fact in facts:
            self._repo.create(
                user_id=user_id,
                content=fact,
                source="chat",
                memory_type=domain,
            )
        return facts

    def _extract_facts(self, user_message: str, assistant_response: str) -> list[str]:
        """Use LLM if available, otherwise use a simple rule-based extractor."""
        if self._api_key:
            try:
                return self._extract_with_llm(user_message, assistant_response)
            except Exception:
                pass
        return self._extract_with_rules(user_message)

    def _extract_with_llm(self, user_message: str, assistant_response: str) -> list[str]:
        combined = f"USER: {user_message}\n\nASSISTANT: {assistant_response[:500]}"
        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": 300,
                "system": _EXTRACTION_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": combined}],
            },
            timeout=10.0,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"].strip()
        data = json.loads(raw)
        return data if isinstance(data, list) else []

    @staticmethod
    def _extract_with_rules(user_message: str) -> list[str]:
        """Simple rule-based fact extractor."""
        import re
        facts = []
        low = user_message.lower()

        # Budget mentions
        budget_m = re.search(r"(\$[\d,]+|\d+\s*(?:dollars?|usd|k\b))", low)
        if budget_m:
            facts.append(f"User mentioned budget: {budget_m.group(0)}")

        # Airline preference
        airlines = ["emirates", "qatar airways", "etihad", "lufthansa", "air france",
                    "british airways", "singapore airlines", "delta", "united", "american airlines"]
        for airline in airlines:
            if airline in low:
                facts.append(f"User prefers {airline.title()} airline")
                break

        # Time preferences
        if "weekend" in low:
            facts.append("User prefers working/studying on weekends")
        if "morning" in low:
            facts.append("User prefers morning schedule")

        # Tech preferences
        techs = ["python", "javascript", "react", "typescript", "go", "rust", "java"]
        for tech in techs:
            if tech in low:
                facts.append(f"User mentioned {tech.title()} as preferred technology")
                break

        return facts[:5]

    @staticmethod
    def _is_general_preference(snippet: str) -> bool:
        keywords = ["prefer", "like", "always", "usually", "style", "budget",
                    "never", "hate", "love", "favorite", "favourite"]
        return any(kw in snippet.lower() for kw in keywords)
