"""Artifact Generator — Routes to ExpertResponder.

This module now delegates ALL content generation to the ExpertResponder,
which produces REAL, FINAL, expert-level content per domain.

No templates. No placeholders. No "Option A", "Option B", "Research this".
"""

from __future__ import annotations

from agents.planner_agent import Mission


def generate_artifacts(mission: Mission) -> str:
    """
    Legacy entry point kept for backward compatibility.
    Returns a minimal markdown representation of the mission operations.
    The full expert content is now generated in chat_service.py via ExpertResponder.
    """
    sections = []
    for i, op in enumerate(mission.operations, 1):
        icon = _get_domain_icon(mission.domain, i)
        section = (
            f"### {icon} {op.title}\n\n"
            f"> **Why this?** {op.why_this}\n\n"
            f"{op.description}"
        )
        sections.append(section)

    return "\n\n---\n\n".join(sections)


# ---------------------------------------------------------------------------
# Icon helpers
# ---------------------------------------------------------------------------

_DOMAIN_ICONS = {
    "travel": ["🗺️", "🛂", "💰", "✈️", "🏨", "📅", "🚇", "🎒", "🆘", "💳"],
    "career": ["🔍", "🗺️", "📅", "💼", "📄", "🎯", "🔎", "🤝", "📊"],
    "learning": ["🧠", "🗺️", "📅", "📖", "💡", "🛠️", "🎓", "📊"],
    "coding": ["📋", "🏗️", "⚙️", "📁", "🗄️", "🔌", "🔐", "🎨", "🗺️", "🧪", "🚀"],
    "business": ["🔬", "⚖️", "📊", "💎", "💰", "🚀", "📣", "📈", "📋"],
    "fitness": ["📏", "🏋️", "🥗", "🔄", "💤", "📊"],
    "finance": ["💼", "📊", "🏦", "🛡️", "📈", "🔄"],
    "research": ["🎯", "🔍", "📚", "💡", "📄", "📑"],
    "writing": ["🎯", "📝", "🔍", "✍️", "✅", "🚀"],
    "health": ["📋", "👨‍⚕️", "🏃", "💊", "📊"],
    "productivity": ["🔬", "🧠", "🎯", "🏠", "🔄"],
}

_DEFAULT_ICONS = ["⚡", "🎯", "🔧", "✅", "📋", "🚀", "💡", "📊", "🔍", "🎪"]


def _get_domain_icon(domain: str, index: int) -> str:
    icons = _DOMAIN_ICONS.get(domain, _DEFAULT_ICONS)
    return icons[(index - 1) % len(icons)]
