"""Artifact Generator.

Takes a Mission and produces rich, formatted markdown content for each Operation.
These artifacts are embedded directly in the assistant's response — not just text, 
but actual structured deliverables: roadmaps as tables, checklists as bullet lists,
budget sheets as financial tables, etc.
"""

from __future__ import annotations

from agents.planner_agent import Mission, Operation


def generate_artifacts(mission: Mission) -> str:
    """
    Produce a complete formatted markdown string rendering all mission operations
    with their artifact content. This is the primary output the user sees.
    """
    sections = []

    for i, op in enumerate(mission.operations, 1):
        section = _render_operation(i, op, mission.domain)
        sections.append(section)

    return "\n\n".join(sections)


def _render_operation(index: int, op: Operation, domain: str) -> str:
    """Render one operation with its artifact content."""
    icon = _get_domain_icon(domain, index)
    header = f"### {icon} {op.title}"
    rationale = f"> **Why this?** {op.why_this}"

    artifact_content = _render_artifact(op)

    parts = [header, rationale]
    if op.description:
        parts.append(f"\n{op.description}")
    if artifact_content:
        parts.append(artifact_content)

    return "\n".join(parts)


def _render_artifact(op: Operation) -> str:
    """Render the artifact content block based on artifact type."""
    artifact_type = op.artifact_type.lower()
    title = op.title

    renderers = {
        "checklist": _render_checklist,
        "budget_sheet": _render_budget_sheet,
        "schedule": _render_schedule,
        "roadmap": _render_roadmap,
        "comparison": _render_comparison,
        "tracker": _render_tracker,
        "swot": _render_swot,
        "architecture": _render_architecture,
        "schema": _render_schema,
        "document": _render_document,
        "guide": _render_guide,
    }

    renderer = renderers.get(artifact_type)
    if renderer:
        return renderer(title)
    return ""


# ---------------------------------------------------------------------------
# Artifact Renderers
# ---------------------------------------------------------------------------

def _render_checklist(title: str) -> str:
    return f"""
**📋 {title} Checklist**
- [ ] Research and verify requirements
- [ ] Gather necessary documentation
- [ ] Complete primary action item
- [ ] Secondary action item
- [ ] Review and confirm completion
- [ ] Archive / file completed items"""


def _render_budget_sheet(title: str) -> str:
    return f"""
**💰 {title}**

| Category | Estimated Cost | Notes |
|---|---|---|
| Primary Expense | — | To be calculated |
| Secondary Expense | — | To be calculated |
| Contingency (10%) | — | Emergency buffer |
| **Total Estimated** | **—** | — |

*Fill in actual amounts as you research each category.*"""


def _render_schedule(title: str) -> str:
    return f"""
**📅 {title}**

| Time Block | Activity | Duration | Notes |
|---|---|---|---|
| Week 1 | Foundation & Setup | — | Core prerequisites |
| Week 2 | Primary Activities | — | Main execution phase |
| Week 3 | Deep Work | — | Intensive focus phase |
| Week 4 | Review & Adjust | — | Mid-point calibration |
| Ongoing | Maintain & Iterate | — | Sustain progress |

*Adjust timeline based on your availability and pace.*"""


def _render_roadmap(title: str) -> str:
    return f"""
**🗺️ {title} Roadmap**

| Phase | Milestone | Timeline | Key Deliverable |
|---|---|---|---|
| Phase 1 | Foundation | Week 1–2 | Core setup complete |
| Phase 2 | Development | Week 3–6 | First working version |
| Phase 3 | Refinement | Week 7–10 | Polished output |
| Phase 4 | Launch / Apply | Week 11–12 | Goal achieved |

*Adapt phases to match your specific target timeline.*"""


def _render_comparison(title: str) -> str:
    return f"""
**⚖️ {title} Comparison**

| Option | Pros | Cons | Price | Rating |
|---|---|---|---|---|
| Option A | — | — | — | ⭐⭐⭐⭐⭐ |
| Option B | — | — | — | ⭐⭐⭐⭐ |
| Option C | — | — | — | ⭐⭐⭐ |

*Research and fill in specifics for your requirements.*"""


def _render_tracker(title: str) -> str:
    return f"""
**📊 {title} Tracker**

| Metric | Baseline | Week 4 Target | Week 8 Target | Final Target |
|---|---|---|---|---|
| Primary KPI | — | — | — | — |
| Secondary KPI | — | — | — | — |
| Progress % | 0% | 25% | 60% | 100% |

*Update weekly to maintain accountability and visibility.*"""


def _render_swot(title: str) -> str:
    return f"""
**🔍 SWOT Analysis — {title}**

| | **Helpful** | **Harmful** |
|---|---|---|
| **Internal** | **Strengths:** Unique advantages you have | **Weaknesses:** Areas to improve |
| **External** | **Opportunities:** Market gaps to exploit | **Threats:** Risks to mitigate |

*Complete each quadrant with 3-5 specific, honest points.*"""


def _render_architecture(title: str) -> str:
    return f"""
**🏗️ Architecture — {title}**

```
┌─────────────────────────────────────────┐
│            CLIENT LAYER                  │
│         (Web / Mobile / API)            │
└────────────────┬────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────────┐
│           API GATEWAY / BFF             │
│        (Authentication, Routing)        │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│            SERVICE LAYER                │
│     (Business Logic / Domain Services)  │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│             DATA LAYER                  │
│       (Database / Cache / Storage)      │
└─────────────────────────────────────────┘
```

*Refine this diagram based on your specific tech stack choices.*"""


def _render_schema(title: str) -> str:
    return f"""
**🗄️ Schema — {title}**

```sql
-- Core entities (adapt field names to your domain)
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    email       TEXT UNIQUE NOT NULL
);

CREATE TABLE [main_entity] (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Add domain-specific fields here
    status      TEXT NOT NULL DEFAULT 'active'
);
```

*Design your full schema based on the identified entities and relationships.*"""


def _render_document(title: str) -> str:
    return f"""
**📄 {title}**

*This document will be populated as you complete the operation.*

**Key Points to Cover:**
- Executive Summary
- Detailed Analysis / Content
- Key Findings / Decisions
- Action Items & Next Steps
- References & Resources"""


def _render_guide(title: str) -> str:
    return f"""
**📖 {title} — Action Guide**

**Step 1:** Research and gather information
**Step 2:** Evaluate options against your requirements
**Step 3:** Make a decision and document your reasoning
**Step 4:** Execute the action plan
**Step 5:** Verify completion against success criteria"""


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
