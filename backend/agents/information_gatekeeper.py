"""Information Gatekeeper.

Decides whether Wingman has enough context to produce a high-quality,
personalized mission plan — or whether it should first ask intelligent
follow-up questions.

Never guesses. Never generates a generic plan when key information is absent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agents.intent_router import IntentResult

# ---------------------------------------------------------------------------
# Domain-specific question templates
# Each entry: (missing_field_key, question_to_ask)
# ---------------------------------------------------------------------------

_DOMAIN_QUESTIONS: dict[str, dict[str, str]] = {
    "travel": {
        "destination": "🗺️ Where exactly are you planning to travel? (City, country, or region)",
        "budget": "💰 What's your approximate budget for this trip? (e.g. $1,500, $5,000)",
        "timeline": "📅 When are you planning to go, and for how long? (e.g. 10 days in October)",
        "group_size": "👥 Will you be travelling solo, as a couple, or with a group?",
        "travel_style": "🏨 Are you looking for luxury, mid-range, or budget travel experiences?",
    },
    "career": {
        "goal": "🎯 What specific career are you targeting? (e.g. Data Scientist, Product Manager, DevOps Engineer)",
        "experience_level": "📊 What is your current experience level? (e.g. complete beginner, 2 years in a related field)",
        "timeline": "⏱️ What's your target timeline to achieve this career switch? (e.g. 6 months, 1 year)",
        "industry": "🏢 Do you have a specific industry in mind? (e.g. fintech, healthcare, gaming)",
    },
    "learning": {
        "subject": "📚 What exactly do you want to learn? (Be specific — e.g. 'SQL for data analysis' vs just 'databases')",
        "experience_level": "🧠 What is your current level with this topic? (Complete beginner, some basics, intermediate?)",
        "timeline": "⏰ How much time can you dedicate per day/week, and by when do you want to achieve proficiency?",
        "goal": "🎯 What do you want to DO with this skill once you've learned it? (Job, project, hobby?)",
    },
    "coding": {
        "subject": "💻 What exactly do you want to build? (Describe the product/app in one sentence)",
        "tech_stack": "⚙️ Do you have a preferred tech stack, or should I recommend one based on your goal?",
        "experience_level": "🧑‍💻 What is your current coding experience level?",
        "timeline": "📆 Do you have a deadline or launch target date?",
    },
    "business": {
        "subject": "🏢 What type of business do you want to start? (Describe the product/service and target customer)",
        "budget": "💵 What startup budget do you have available?",
        "timeline": "📅 What is your target launch timeline?",
        "industry": "🌐 Which industry or market are you entering?",
    },
    "fitness": {
        "goal": "🏋️ What is your specific fitness goal? (e.g. lose 10kg, run a 5K, build muscle, improve endurance)",
        "timeline": "📅 What is your target timeline or event date?",
        "experience_level": "💪 What is your current fitness level? (Sedentary, lightly active, regularly training?)",
    },
    "finance": {
        "goal": "💰 What is your specific financial goal? (e.g. save $20k, pay off debt, invest for retirement)",
        "timeline": "⏱️ What is your target timeline for this goal?",
        "budget": "📊 What is your approximate monthly income and current savings? (Helps me create a realistic plan)",
    },
    "research": {
        "subject": "🔍 What specific topic do you want to research?",
        "goal": "📄 What will the research be used for? (Academic paper, business report, personal knowledge?)",
    },
    "writing": {
        "subject": "✍️ What do you want to write? (Topic, genre, or format)",
        "goal": "🎯 Who is the target audience and what is the purpose?",
        "timeline": "📅 Do you have a deadline or target word count?",
    },
    "reminder": {
        "subject": "🔔 What exactly do you want to be reminded about?",
        "timeline": "⏰ When should the reminder trigger? (Date and time, or a relative time like 'tomorrow at 9am')",
    },
    "health": {
        "goal": "🏥 What health goal or concern would you like help with?",
    },
    "meetings": {
        "subject": "📋 What is the meeting about and who are the participants?",
    },
    "shopping": {
        "subject": "🛒 What exactly are you looking to buy? (Include any preferences or constraints)",
        "budget": "💳 What is your budget for this purchase?",
    },
    "education": {
        "goal": "🎓 What educational goal are you working toward? (Degree, certification, admission?)",
        "timeline": "📅 What is your target date or application deadline?",
    },
    "productivity": {
        "goal": "⚡ What specific productivity challenge or goal are you tackling?",
    },
    "life_planning": {
        "goal": "🌟 What major life goal are you planning toward?",
        "timeline": "📅 What is your target timeline?",
    },
    "documents": {
        "subject": "📄 What document or content would you like me to analyze or summarize?",
    },
    "entertainment": {
        "subject": "🎬 What type of entertainment are you looking for? (Genre, mood, platform preferences?)",
    },
    "relationships": {
        "goal": "❤️ What relationship challenge or goal would you like help with?",
    },
}

# Domains that are "low-context" — they can execute with minimal info
_LOW_CONTEXT_DOMAINS = {"reminder", "task", "shopping", "entertainment", "meetings"}

# Maximum missing fields before we ask (per domain strictness)
_MAX_MISSING_BEFORE_ASKING: dict[str, int] = {
    "travel": 1,       # Even 1 missing critical field → ask
    "career": 1,
    "coding": 1,
    "business": 1,
    "learning": 1,
    "finance": 1,
    "fitness": 1,
    "reminder": 1,
    "research": 1,
    "writing": 1,
    "health": 2,
    "productivity": 2,
    "life_planning": 1,
    "education": 1,
    "documents": 2,
    "meetings": 2,
    "shopping": 2,
    "entertainment": 3,
    "relationships": 2,
    "task": 99,        # Always executes
}


@dataclass
class GatekeeperDecision:
    needs_clarification: bool
    questions: list[str] = field(default_factory=list)
    # A personalized preamble explaining WHY we're asking
    preamble: str = ""


class InformationGatekeeper:
    """
    Determines whether the current objective has enough context for Wingman
    to produce a high-quality, personalized mission plan.

    If not, it returns targeted follow-up questions instead of a generic plan.
    """

    def check(self, intent: IntentResult) -> GatekeeperDecision:
        domain = intent.domain
        missing = intent.missing_fields

        # Domains that always execute immediately
        if domain == "task":
            return GatekeeperDecision(needs_clarification=False)

        # Get the threshold for this domain
        threshold = _MAX_MISSING_BEFORE_ASKING.get(domain, 1)

        if len(missing) < threshold:
            return GatekeeperDecision(needs_clarification=False)

        # Build targeted questions from missing fields
        questions = self._build_questions(domain, missing, intent.entities)

        if not questions:
            return GatekeeperDecision(needs_clarification=False)

        preamble = self._build_preamble(domain, intent.summary)
        return GatekeeperDecision(
            needs_clarification=True,
            questions=questions,
            preamble=preamble,
        )

    @staticmethod
    def _build_questions(domain: str, missing_fields: list[str], entities: dict) -> list[str]:
        domain_qs = _DOMAIN_QUESTIONS.get(domain, {})
        questions = []
        for field_key in missing_fields:
            q = domain_qs.get(field_key)
            if q:
                questions.append(q)
        # Limit to 4 questions max to avoid overwhelming the user
        return questions[:4]

    @staticmethod
    def _build_preamble(domain: str, summary: str) -> str:
        domain_label = domain.replace("_", " ").title()
        preambles = {
            "travel": "I'd love to build you a complete travel intelligence package — but to make it genuinely useful (not generic), I need a few details:",
            "career": "I'll design a complete career transformation roadmap for you. To make it truly personalized rather than a generic template, I need to understand your starting point:",
            "learning": "I'll create a custom learning system for you — not a generic course list. To personalize it properly, help me with a few quick questions:",
            "coding": "I'll architect the full technical blueprint for your project. To design the right stack and structure, I need to understand the scope:",
            "business": "I'll build you a complete business launch strategy. To make it market-specific and actionable (not a template), I need some context:",
            "fitness": "I'll create a fully personalized training and nutrition plan. To calibrate it to your body and goals, I need a bit more information:",
            "finance": "I'll design a personalized financial roadmap. To build a realistic plan (not a generic savings tip list), I need your specific numbers:",
            "reminder": "I'll set up a smart reminder for you. Just need these details:",
            "research": "I'll design a complete research strategy for you. To scope it properly, I need a few details:",
            "writing": "I'll build a complete writing plan — outline, structure, and workflow. To make it audience-specific, I need to know:",
        }
        return preambles.get(
            domain,
            f"I want to build you the best possible **{domain_label}** plan — personalized, not templated. To do that right, I need a few quick answers:"
        )
