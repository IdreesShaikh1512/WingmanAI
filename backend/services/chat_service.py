"""Chat Service — Autonomous AI OS Orchestration Pipeline.

Every user message flows through:
  1. MemoryManager.read()           — Load user context for personalization
  2. IntentRouter.classify()        — Classify domain + extract entities
  3. InformationGatekeeper.check()  — Ask follow-up questions if context is missing
  4. PlannerAgent.plan()            — Generate domain-specific Mission structure
  5. ExpertResponder.generate()     — Generate REAL expert-level content (final answers)
  6. _apply_side_effects()          — Create Tasks, Trips, Reminders in DB
  7. NextActionAdvisor.suggest()    — Generate proactive next steps
  8. MemoryManager.write()          — Store new user facts for future sessions
  9. _format_rich_response()        — Assemble the final assistant message

PRIMARY RULE:
  Every response must feel like "I hired a team of experts."
  Not: "I received a generic AI response."

  NO templates. NO placeholders. NO "Option A". NO "To be calculated".
  REAL hotels. REAL frameworks. REAL books. REAL companies. REAL prices.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from agents.artifact_generator import generate_artifacts
from agents.expert_responder import ExpertResponder
from agents.information_gatekeeper import InformationGatekeeper
from agents.intent_router import IntentRouter
from agents.memory_manager import MemoryManager
from agents.next_action_advisor import NextActionAdvisor
from agents.planner_agent import Mission, PlannerAgent
from models.chat import Chat, Message
from repositories.chat_repository import ChatRepository
from repositories.memory_repository import MemoryRepository
from repositories.reminder_repository import ReminderRepository
from repositories.task_repository import TaskRepository
from repositories.trip_repository import TripRepository


class ChatService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        task_repository: TaskRepository,
        trip_repository: TripRepository,
        reminder_repository: ReminderRepository,
        planner_agent: PlannerAgent,
        intent_router: IntentRouter,
        gatekeeper: InformationGatekeeper,
        memory_manager: MemoryManager,
        next_action_advisor: NextActionAdvisor,
    ) -> None:
        self._chat_repository = chat_repository
        self._task_repository = task_repository
        self._trip_repository = trip_repository
        self._reminder_repository = reminder_repository
        self._planner_agent = planner_agent
        self._intent_router = intent_router
        self._gatekeeper = gatekeeper
        self._memory_manager = memory_manager
        self._next_action_advisor = next_action_advisor
        self._expert_responder = ExpertResponder()

    # ------------------------------------------------------------------
    # Chat management
    # ------------------------------------------------------------------

    def start_chat(self, user_id: uuid.UUID) -> Chat:
        return self._chat_repository.create_chat(user_id)

    def list_chats(self, user_id: uuid.UUID) -> list[Chat]:
        return self._chat_repository.list_chats(user_id)

    # ------------------------------------------------------------------
    # Core: send_message — the full orchestration pipeline
    # ------------------------------------------------------------------

    def send_message(self, chat_id: uuid.UUID, user_id: uuid.UUID, content: str) -> Message:
        chat = self._chat_repository.get_chat(chat_id, user_id)
        if chat is None:
            raise ValueError(f"Chat not found: {chat_id}")

        # Persist the user's message
        self._chat_repository.add_message(chat_id, role="user", content=content)

        # ── Step 1: Load memory context for personalization ──────────────
        user_context = self._memory_manager.read(user_id, content, "general")

        # ── Step 2: Classify intent + extract entities ───────────────────
        intent = self._intent_router.classify(
            content,
            user_context={"memory_snippets": user_context.memory_snippets},
        )

        # ── Step 3: Check if we have enough information ──────────────────
        decision = self._gatekeeper.check(intent)

        if decision.needs_clarification:
            clarification_reply = self._format_clarification_reply(decision)
            return self._chat_repository.add_message(
                chat_id,
                role="assistant",
                content=clarification_reply,
                agent_metadata={
                    "type": "clarification",
                    "domain": intent.domain,
                    "missing_fields": intent.missing_fields,
                    "questions": decision.questions,
                },
            )

        # ── Step 4: Load domain-specific memory context ──────────────────
        domain_context = self._memory_manager.read(user_id, content, intent.domain)

        # ── Step 5: Generate domain-specific Mission structure ───────────
        mission = self._planner_agent.plan(intent, domain_context)

        # ── Step 6: Generate REAL expert-level content ───────────────────
        # ExpertResponder acts as a team of senior domain consultants.
        # Produces FINAL ANSWERS with real hotels, real frameworks, real books.
        expert_content = self._expert_responder.generate_expert_response(
            objective=content,
            domain=intent.domain,
            mission_title=mission.mission_title,
            rationale=mission.rationale,
            operations=[
                {
                    "title": op.title,
                    "description": op.description,
                    "artifact_type": op.artifact_type,
                    "why_this": op.why_this,
                }
                for op in mission.operations
            ],
            entities=intent.entities,
            user_context_snippets=domain_context.memory_snippets if domain_context.has_context() else [],
        )

        # ── Step 7: Execute DB side effects ──────────────────────────────
        actions_summary = self._apply_side_effects(user_id, chat_id, content, mission)

        # ── Step 8: Generate next-action suggestions ─────────────────────
        next_actions = self._next_action_advisor.suggest(intent, mission)

        # ── Step 9: Assemble the complete expert response ─────────────────
        assistant_reply = self._format_rich_response(
            mission=mission,
            expert_content=expert_content,
            actions=actions_summary,
            next_actions=next_actions,
            user_context=domain_context,
        )

        # ── Step 10: Persist memory facts from this exchange ─────────────
        self._memory_manager.write(
            user_id=user_id,
            user_message=content,
            assistant_response=assistant_reply[:500],
            domain=intent.domain,
        )

        # ── Step 11: Persist and return the assistant message ─────────────
        return self._chat_repository.add_message(
            chat_id,
            role="assistant",
            content=assistant_reply,
            agent_metadata={
                "type": "mission",
                "domain": intent.domain,
                "domain_label": mission.domain_label,
                "mission_title": mission.mission_title,
                "rationale": mission.rationale,
                "operations": [
                    {
                        "title": op.title,
                        "description": op.description,
                        "artifact_type": op.artifact_type,
                        "why_this": op.why_this,
                        "status": op.status,
                    }
                    for op in mission.operations
                ],
                "next_actions": next_actions,
                "proactive_suggestions": mission.proactive_suggestions,
                "actions": actions_summary,
                "personalized": domain_context.has_context(),
            },
        )

    # ------------------------------------------------------------------
    # Side effects
    # ------------------------------------------------------------------

    def _apply_side_effects(
        self,
        user_id: uuid.UUID,
        chat_id: uuid.UUID,
        objective: str,
        mission: Mission,
    ) -> dict[str, int | str | None]:
        created_tasks_count = 0
        created_trip_name = None
        created_reminder_title = None

        # Create trip record for travel missions
        if mission.domain == "travel":
            destination = objective
            created_trip = self._trip_repository.create(
                user_id=user_id,
                destination=destination,
                start_date=None,
                end_date=None,
                budget=None,
            )
            created_trip_name = created_trip.destination

        # Create reminder for reminder missions
        elif mission.domain == "reminder":
            remind_time = datetime.now(timezone.utc) + timedelta(days=1)
            created_reminder = self._reminder_repository.create(
                user_id=user_id,
                title=objective,
                remind_at=remind_time,
            )
            created_reminder_title = created_reminder.title

        # Create a Task for each operation
        for op in mission.operations:
            self._task_repository.create(
                user_id=user_id,
                title=op.title,
                description=op.description or f"Operation for: {objective}",
                chat_id=chat_id,
            )
            created_tasks_count += 1

        return {
            "tasks_created": created_tasks_count,
            "trip_created": created_trip_name,
            "reminder_created": created_reminder_title,
        }

    # ------------------------------------------------------------------
    # Response formatters
    # ------------------------------------------------------------------

    @staticmethod
    def _format_clarification_reply(decision) -> str:  # type: ignore[no-untyped-def]
        """Format a conversational follow-up question response."""
        lines = [decision.preamble, ""]
        for i, q in enumerate(decision.questions, 1):
            lines.append(f"**{i}.** {q}")
        lines.append("")
        lines.append("*Just answer what you know — I'll build your personalized plan from there.*")
        return "\n".join(lines)

    @staticmethod
    def _format_rich_response(
        mission: Mission,
        expert_content: str,
        actions: dict[str, int | str | None],
        next_actions: list[str],
        user_context,  # type: ignore[no-untyped-def]
    ) -> str:
        """
        Assemble the full expert response.

        Structure:
          1. Domain header + mission title
          2. Expert content (real hotels, real books, real frameworks, real prices)
          3. Proactive tracking suggestions
          4. Execution summary (tasks/trips/reminders created)
        """
        domain_emoji = {
            "travel": "🌍",
            "career": "🚀",
            "learning": "📚",
            "coding": "💻",
            "business": "🏢",
            "fitness": "💪",
            "finance": "💰",
            "health": "🏥",
            "research": "🔬",
            "writing": "✍️",
            "productivity": "⚡",
            "reminder": "🔔",
            "meetings": "📋",
            "shopping": "🛒",
            "documents": "📄",
            "life_planning": "🌟",
            "education": "🎓",
            "relationships": "❤️",
            "entertainment": "🎬",
            "task": "✅",
        }.get(mission.domain, "⚡")

        personalized_note = " *(personalized from your history)*" if user_context.has_context() else ""

        # The expert content is the main body — no templates, no placeholders
        # It already contains domain-specific real content generated by ExpertResponder
        body = expert_content

        # Proactive suggestions
        proactive_section = ""
        if mission.proactive_suggestions:
            suggestions = "\n".join(f"- {s}" for s in mission.proactive_suggestions)
            proactive_section = f"\n\n---\n\n**🔮 Wingman is also proactively tracking:**\n{suggestions}"

        # Execution summary
        summary_parts = []
        if actions.get("tasks_created"):
            summary_parts.append(f"📋 **{actions['tasks_created']} Operations** added to your workspace")
        if actions.get("trip_created"):
            summary_parts.append(f"✈️ **Trip log created**: {actions['trip_created']}")
        if actions.get("reminder_created"):
            summary_parts.append(f"🔔 **Reminder set**: {actions['reminder_created']}")

        summary_section = ""
        if summary_parts:
            summary_section = "\n\n---\n\n" + " · ".join(summary_parts)

        return body + proactive_section + summary_section
