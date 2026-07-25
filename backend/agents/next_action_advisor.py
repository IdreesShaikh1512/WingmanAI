"""Next Action Advisor.

After every successfully completed mission, generates 3 proactive,
domain-aware next-step suggestions that the user should pursue.

These are NOT generic — they are reasoned follow-ups specific to 
the domain and entities in the mission just executed.
"""

from __future__ import annotations

import os
import json

import httpx

from agents.planner_agent import Mission
from agents.intent_router import IntentResult

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-sonnet-4-6"

_ADVISOR_SYSTEM_PROMPT = """You are Wingman's Next Action Advisor.

Given a completed mission, suggest the 3 most logical, high-value follow-up objectives the user should pursue next.

Rules:
- Suggestions must be SPECIFIC to the user's actual domain and entities (not generic)
- Each suggestion should be an actionable objective the user can speak or type
- Think: what does a smart advisor recommend NEXT after completing this plan?

Respond with ONLY a JSON array of 3 strings. No prose, no markdown.
Example: ["Practice 50 SQL queries on a real dataset", "Build your first SQL analytics dashboard", "Learn PostgreSQL advanced features"]"""


class NextActionAdvisor:
    """Generates proactive next-step suggestions after a mission is planned."""

    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")

    def suggest(self, intent: IntentResult, mission: Mission) -> list[str]:
        """Return 3 next-action suggestions."""
        # Mission already has next_actions from pipeline — use those if rich
        if mission.next_actions and len(mission.next_actions) >= 2:
            return mission.next_actions[:3]

        # Otherwise generate via LLM or static fallback
        if self._api_key:
            try:
                return self._suggest_with_llm(intent, mission)
            except Exception:
                pass

        return self._suggest_with_rules(intent, mission)

    def _suggest_with_llm(self, intent: IntentResult, mission: Mission) -> list[str]:
        prompt = (
            f"Completed Mission: {mission.mission_title}\n"
            f"Domain: {mission.domain}\n"
            f"Key Operations: {', '.join(op.title for op in mission.operations[:5])}\n"
            f"Entities: {json.dumps(intent.entities)}"
        )
        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": 200,
                "system": _ADVISOR_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=10.0,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"].strip()
        data = json.loads(raw)
        return data if isinstance(data, list) else []

    @staticmethod
    def _suggest_with_rules(intent: IntentResult, mission: Mission) -> list[str]:
        domain = intent.domain
        subject = intent.entities.get("subject", intent.entities.get("goal", "this topic"))

        domain_suggestions: dict[str, list[str]] = {
            "travel": [
                f"Book your flights and accommodation for {subject}",
                f"Apply for the {subject} visa if required",
                "Set travel insurance and emergency contacts",
            ],
            "career": [
                f"Enroll in the top course from your {subject} roadmap",
                f"Start your first {subject} portfolio project this week",
                f"Connect with 5 {subject} professionals on LinkedIn",
            ],
            "learning": [
                f"Complete your first {subject} practice problem set",
                f"Build your first real project applying {subject}",
                f"Join a {subject} community or study group",
            ],
            "coding": [
                "Set up your project repository and scaffold",
                "Build and test the database schema",
                "Create your first working API endpoint",
            ],
            "business": [
                f"Interview 10 potential customers for {subject}",
                f"Build the landing page for {subject}",
                "Register the business entity and domain name",
            ],
            "fitness": [
                "Complete your baseline fitness assessment",
                "Start Week 1 of your training program today",
                "Meal prep your first week according to the macro plan",
            ],
            "finance": [
                "Open a dedicated savings account for your goal",
                "Set up automatic transfers on payday",
                "Review and cancel unused subscriptions",
            ],
            "research": [
                f"Begin the literature review with 10 key papers on {subject}",
                f"Set up your citation manager for {subject}",
                "Schedule focused 2-hour research blocks this week",
            ],
            "writing": [
                f"Write your detailed outline for {subject} before starting",
                "Set a daily word-count target and stick to it",
                "Find 2-3 beta readers for feedback after your first draft",
            ],
            "productivity": [
                "Run a 3-day time audit starting tomorrow",
                "Block your first deep work session this week",
                "Set up your weekly review ritual for Sunday",
            ],
        }

        return domain_suggestions.get(domain, [
            f"Continue working on {subject} with your next priority task",
            "Review your progress against the plan at the end of this week",
            "Identify and resolve the next biggest blocker",
        ])
