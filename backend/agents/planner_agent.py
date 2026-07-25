"""Planner Agent — Domain Mission Pipelines.

Takes a classified IntentResult + UserContext and produces a Mission:
a rich, domain-specific execution plan with named Operations,
each with a title, description, artifact type, and a 'why this?' rationale.

NO generic templates. Every domain has its own unique pipeline.
NO two objectives produce the same structure.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import httpx

from agents.intent_router import IntentResult
from agents.memory_manager import UserContext

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-sonnet-4-6"

_MISSION_SYSTEM_PROMPT = """You are Wingman's Mission Planner — an autonomous AI operating system.

Your job: given a classified user objective with extracted entities and user memory context,
produce a UNIQUE, domain-specific mission plan. Never use generic step names.

Respond with ONLY a valid JSON object (no markdown, no prose):
{
  "mission_title": "<compelling title for this specific objective>",
  "domain_label": "<human-friendly domain name>",
  "rationale": "<1-2 sentences: why THIS specific plan structure was chosen for THIS specific user>",
  "operations": [
    {
      "title": "<specific, actionable operation title>",
      "description": "<2-3 sentences of exactly what this operation involves and how to execute it>",
      "artifact_type": "<roadmap|checklist|budget_sheet|schedule|architecture|schema|swot|document|tracker|comparison|guide|none>",
      "why_this": "<1 sentence: why this specific operation is critical for THIS objective>"
    }
  ],
  "next_actions": [
    "<3 specific, logical follow-up objectives the user should pursue after this one>"
  ],
  "proactive_suggestions": [
    "<2-3 things Wingman should automatically create/track alongside this mission>"
  ]
}

Rules:
- Operations: 6-12, never fewer than 6
- Every operation title must be specific to the user's actual subject/destination/goal
- Use user's memory context to personalize descriptions (preferred tools, budget, timeline)
- Proactive suggestions = things the user didn't ask for but will obviously need
- next_actions = what the user should do AFTER completing this mission"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Operation:
    title: str
    description: str
    artifact_type: str  # roadmap | checklist | budget_sheet | schedule | architecture | etc.
    why_this: str
    status: str = "pending"


@dataclass
class Mission:
    mission_title: str
    domain: str
    domain_label: str
    rationale: str
    operations: list[Operation] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    proactive_suggestions: list[str] = field(default_factory=list)
    # Backward-compat: flat step list for side-effect executor
    steps: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.steps:
            self.steps = [op.title for op in self.operations]

    # Keep the old .intent attribute for backward compat with trip/reminder side effects
    @property
    def intent(self) -> str:
        return self.domain


# ---------------------------------------------------------------------------
# Planner Agent
# ---------------------------------------------------------------------------

class PlannerAgent:
    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")

    def plan(self, intent: IntentResult, user_context: UserContext | None = None) -> Mission:
        ctx = user_context or UserContext()
        if self._api_key:
            try:
                return self._plan_with_llm(intent, ctx)
            except Exception:
                pass
        return self._plan_with_pipelines(intent, ctx)

    # ------------------------------------------------------------------
    # LLM Path — deep contextual planning
    # ------------------------------------------------------------------

    def _plan_with_llm(self, intent: IntentResult, ctx: UserContext) -> Mission:
        user_prompt = (
            f"Objective: {intent.raw_objective}\n"
            f"Domain: {intent.domain}\n"
            f"Entities: {json.dumps(intent.entities)}\n"
            f"Summary: {intent.summary}\n"
        )
        if ctx.has_context():
            user_prompt += f"\n{ctx.as_prompt_context()}"

        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": 2000,
                "system": _MISSION_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        raw = response.json()["content"][0]["text"]
        data = json.loads(raw)

        operations = [
            Operation(
                title=op["title"],
                description=op.get("description", ""),
                artifact_type=op.get("artifact_type", "none"),
                why_this=op.get("why_this", ""),
            )
            for op in data.get("operations", [])
        ]

        return Mission(
            mission_title=data.get("mission_title", intent.raw_objective),
            domain=intent.domain,
            domain_label=data.get("domain_label", intent.domain.replace("_", " ").title()),
            rationale=data.get("rationale", ""),
            operations=operations,
            next_actions=data.get("next_actions", []),
            proactive_suggestions=data.get("proactive_suggestions", []),
        )

    # ------------------------------------------------------------------
    # Pipeline Path — rich NLP-driven domain pipelines (no LLM needed)
    # ------------------------------------------------------------------

    def _plan_with_pipelines(self, intent: IntentResult, ctx: UserContext) -> Mission:
        domain = intent.domain
        entities = intent.entities
        e = entities  # shorthand

        dispatch = {
            "travel": self._travel_pipeline,
            "career": self._career_pipeline,
            "learning": self._learning_pipeline,
            "coding": self._coding_pipeline,
            "business": self._business_pipeline,
            "fitness": self._fitness_pipeline,
            "finance": self._finance_pipeline,
            "research": self._research_pipeline,
            "writing": self._writing_pipeline,
            "health": self._health_pipeline,
            "productivity": self._productivity_pipeline,
            "reminder": self._reminder_pipeline,
            "meetings": self._meetings_pipeline,
            "shopping": self._shopping_pipeline,
            "documents": self._documents_pipeline,
            "life_planning": self._life_planning_pipeline,
            "education": self._education_pipeline,
            "relationships": self._relationships_pipeline,
            "entertainment": self._entertainment_pipeline,
        }

        pipeline_fn = dispatch.get(domain, self._task_pipeline)
        return pipeline_fn(intent, ctx)

    # ------------------------------------------------------------------
    # TRAVEL
    # ------------------------------------------------------------------
    @staticmethod
    def _travel_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        dest = intent.entities.get("destination", "your destination").title()
        budget = intent.entities.get("budget", "")
        timeline = intent.entities.get("timeline", "")
        group = intent.entities.get("group_size", "")
        budget_note = f" (Budget: {budget})" if budget else ""
        group_note = f" — {group} travel" if group else ""
        time_note = f" for {timeline}" if timeline else ""

        # Memory personalization
        airline_pref = ""
        for snippet in ctx.memory_snippets:
            if "airline" in snippet.lower() or "prefer" in snippet.lower():
                airline_pref = f" Note: {snippet}"
                break

        ops = [
            Operation(
                title=f"{dest} Destination Intelligence",
                description=(
                    f"Deep-dive into {dest}: top neighborhoods, must-see landmarks, hidden gems, cultural norms, "
                    f"safety ratings, and travel advisories. Identify the best time zones and areas to base yourself{time_note}."
                ),
                artifact_type="guide",
                why_this=f"Knowing {dest} before you arrive prevents wasted days on poor decisions.",
            ),
            Operation(
                title=f"Visa & Entry Requirements for {dest}",
                description=(
                    f"Verify current visa requirements, processing times, costs, and documentation needed for {dest}. "
                    f"Check health/vaccination requirements, customs limits, and any travel insurance mandates."
                ),
                artifact_type="checklist",
                why_this="Visa issues can derail an entire trip — this must be resolved first.",
            ),
            Operation(
                title=f"Budget Optimization Plan{budget_note}",
                description=(
                    f"Build an itemized budget breakdown for {dest}: flights, accommodation, food, transport, activities, "
                    f"emergency fund, and shopping. Identify where to save vs. splurge{group_note}."
                ),
                artifact_type="budget_sheet",
                why_this="A clear budget prevents overspending and removes decision fatigue on the ground.",
            ),
            Operation(
                title=f"Flight Strategy & Booking{airline_pref}",
                description=(
                    f"Compare flight options to {dest}: best routes, layover considerations, price-alert strategy, "
                    f"luggage policies, and seat selection tips. Evaluate round-trip vs. open-jaw options."
                ),
                artifact_type="comparison",
                why_this="Flights are the highest-leverage variable — the right booking strategy saves hundreds.",
            ),
            Operation(
                title=f"Accommodation Selection for {dest}",
                description=(
                    f"Rank accommodation options in {dest} by location, price, and amenities: hotels, Airbnb, hostels, "
                    f"and boutique stays. Identify the best neighborhoods for your travel style{group_note}."
                ),
                artifact_type="comparison",
                why_this="Where you stay shapes every other experience — centrally located base = more efficient days.",
            ),
            Operation(
                title=f"Day-by-Day Itinerary for {dest}",
                description=(
                    f"Create a detailed day-by-day itinerary optimized for geography (cluster nearby attractions). "
                    f"Include opening hours, ticket pre-booking requirements, travel times between sites, and meal suggestions."
                ),
                artifact_type="schedule",
                why_this="An optimized itinerary eliminates wasted transit time and ensures you see what matters most.",
            ),
            Operation(
                title=f"{dest} Transportation Master Plan",
                description=(
                    f"Map out all ground transport options in {dest}: metro, bus, taxi, rental car, bike share, ferries. "
                    f"Evaluate transit passes vs. pay-per-ride economics."
                ),
                artifact_type="guide",
                why_this="Getting around efficiently is the #1 time-saver for any trip.",
            ),
            Operation(
                title=f"Smart Packing List for {dest}",
                description=(
                    f"Generate a categorized packing list tailored to {dest}'s climate{time_note}, cultural dress codes, "
                    f"planned activities, and airline baggage limits."
                ),
                artifact_type="checklist",
                why_this="Over-packing or forgetting essentials are the two most common trip disruptions.",
            ),
            Operation(
                title="Emergency Contacts & Safety Toolkit",
                description=(
                    f"Compile: local emergency numbers in {dest}, nearest embassy/consulate, travel insurance policy details, "
                    f"critical app downloads (offline maps, translation), and backup payment methods."
                ),
                artifact_type="document",
                why_this="Having this ready before departure means no panic if something goes wrong.",
            ),
            Operation(
                title="Expense Tracker & Currency Setup",
                description=(
                    f"Set up an expense tracking system for the trip. Research local currency, best exchange methods, "
                    f"no-foreign-fee credit cards, and ATM strategy in {dest}."
                ),
                artifact_type="tracker",
                why_this="Tracking spend in real-time prevents budget blowout and reveals where to cut.",
            ),
        ]

        return Mission(
            mission_title=f"{dest} Travel Intelligence{group_note}",
            domain="travel",
            domain_label="Travel",
            rationale=(
                f"This plan covers every dimension of your {dest} trip{time_note} — "
                f"from entry requirements to on-the-ground logistics — so nothing is left to chance."
            ),
            operations=ops,
            next_actions=[
                f"Book flights to {dest} and lock in accommodation",
                f"Apply for {dest} visa if required",
                "Set up travel insurance and emergency contacts",
            ],
            proactive_suggestions=[
                f"Set a currency exchange rate alert for {dest}'s local currency",
                "Create a pre-departure countdown checklist with deadline reminders",
                "Download offline maps and translation app for your destination",
            ],
        )

    # ------------------------------------------------------------------
    # CAREER
    # ------------------------------------------------------------------
    @staticmethod
    def _career_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your target career")
        level = intent.entities.get("experience_level", "beginner")
        timeline = intent.entities.get("timeline", "6-12 months")
        industry = intent.entities.get("industry", "")
        industry_note = f" in {industry}" if industry else ""

        # Extract job title from goal
        job_title = goal.replace("become a ", "").replace("become an ", "").title()

        ops = [
            Operation(
                title=f"{job_title} Skill Gap Assessment",
                description=(
                    f"Audit your current skills vs. the complete skill set required for a {job_title}{industry_note}. "
                    f"Map hard skills (technical), soft skills, domain knowledge, and tooling proficiency gaps."
                ),
                artifact_type="tracker",
                why_this="You can't build a roadmap without knowing your starting coordinates.",
            ),
            Operation(
                title=f"Personalized {job_title} Learning Roadmap",
                description=(
                    f"Design a phased, week-by-week learning roadmap covering all required competencies for {job_title}. "
                    f"Curate top courses, books, YouTube channels, and certifications — ranked by ROI for your current level ({level})."
                ),
                artifact_type="roadmap",
                why_this="A sequenced roadmap prevents the 'tutorial hell' trap and ensures progressive skill building.",
            ),
            Operation(
                title=f"Weekly {job_title} Study & Practice Calendar",
                description=(
                    f"Build a realistic weekly calendar that fits your existing schedule. "
                    f"Block dedicated learning sessions, project time, and review days across {timeline}."
                ),
                artifact_type="schedule",
                why_this="Consistency beats intensity — a scheduled habit produces results that binge-studying never does.",
            ),
            Operation(
                title=f"Hands-On {job_title} Project Portfolio",
                description=(
                    f"Design 3-5 progressively complex real-world projects that demonstrate {job_title} skills. "
                    f"Each project should solve a real problem and be publishable on GitHub or a portfolio site."
                ),
                artifact_type="roadmap",
                why_this="Projects are what get you hired — a portfolio speaks louder than any certificate.",
            ),
            Operation(
                title=f"Professional {job_title} Resume & LinkedIn",
                description=(
                    f"Draft a targeted resume and LinkedIn profile optimized for {job_title} roles{industry_note}. "
                    f"Include ATS-friendly keywords, quantified achievements, and skills section."
                ),
                artifact_type="document",
                why_this="Even the best candidate loses opportunities to a poorly crafted resume.",
            ),
            Operation(
                title=f"{job_title} Interview Preparation System",
                description=(
                    f"Build a systematic interview prep plan: common technical questions, system design (if applicable), "
                    f"behavioral STAR-method answers, and mock interview practice schedule."
                ),
                artifact_type="guide",
                why_this="Interview performance is a separate skill from the job itself — it needs dedicated practice.",
            ),
            Operation(
                title=f"Strategic {job_title} Job Search Campaign",
                description=(
                    f"Map out a targeted job search strategy: target company list{industry_note}, job board priorities, "
                    f"recruiter outreach scripts, and application tracking system."
                ),
                artifact_type="tracker",
                why_this="A structured search is 3x more effective than spray-and-pray applications.",
            ),
            Operation(
                title=f"{job_title} Network Building Plan",
                description=(
                    f"Identify and engage 10-20 {job_title}s and hiring managers in your target industry. "
                    f"Script LinkedIn outreach messages, find relevant communities (Discord, Slack, LinkedIn groups)."
                ),
                artifact_type="guide",
                why_this="80% of jobs are filled through networks — relationships accelerate timelines dramatically.",
            ),
            Operation(
                title="Progress Tracking & Milestone System",
                description=(
                    "Create a weekly self-assessment system with defined milestones. Track skill progress, "
                    "applications sent, interviews completed, and portfolio projects shipped."
                ),
                artifact_type="tracker",
                why_this="Tracking creates accountability and reveals what's working vs. what needs adjustment.",
            ),
        ]

        return Mission(
            mission_title=f"Become a {job_title}{industry_note} — Career Transformation",
            domain="career",
            domain_label="Career",
            rationale=(
                f"This plan takes you from your current level ({level}) to {job_title}{industry_note} "
                f"over {timeline} through a sequenced skill-build, portfolio development, and job search strategy."
            ),
            operations=ops,
            next_actions=[
                f"Complete the {job_title} skill gap assessment this week",
                f"Enroll in the top-ranked {job_title} course from the roadmap",
                "Start your first portfolio project within 2 weeks",
            ],
            proactive_suggestions=[
                f"Set a weekly progress check-in reminder every Sunday",
                f"Create a job application tracker spreadsheet",
                f"Follow 5 {job_title}s on LinkedIn for industry insights",
            ],
        )

    # ------------------------------------------------------------------
    # LEARNING
    # ------------------------------------------------------------------
    @staticmethod
    def _learning_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", intent.entities.get("goal", "your topic")).title()
        level = intent.entities.get("experience_level", "beginner")
        timeline = intent.entities.get("timeline", "")
        goal = intent.entities.get("goal", "")
        time_note = f" in {timeline}" if timeline else ""
        goal_note = f" for {goal}" if goal and goal != intent.entities.get("subject") else ""

        ops = [
            Operation(
                title=f"{subject} Prerequisite & Skill Assessment",
                description=(
                    f"Identify exactly what you already know about {subject} and what prerequisites you're missing. "
                    f"Take a diagnostic quiz or self-assessment to calibrate your true starting point."
                ),
                artifact_type="tracker",
                why_this=f"Starting at the wrong level wastes weeks — this ensures you begin exactly where you should.",
            ),
            Operation(
                title=f"Curated {subject} Learning Roadmap",
                description=(
                    f"Build a phase-by-phase learning roadmap from {level} to proficiency in {subject}. "
                    f"Rank the top 3-5 resources (courses, books, docs) by quality and learning efficiency."
                ),
                artifact_type="roadmap",
                why_this=f"The right resources — in the right order — cut learning time by 60%.",
            ),
            Operation(
                title=f"Daily {subject} Study Plan{time_note}",
                description=(
                    f"Design a realistic daily/weekly study schedule for {subject}, broken into focused 25-50 minute blocks. "
                    f"Include active recall sessions, spaced repetition, and weekly review days."
                ),
                artifact_type="schedule",
                why_this="Distributed practice with spaced repetition retains 4x more than massed studying.",
            ),
            Operation(
                title=f"Core {subject} Concepts Breakdown",
                description=(
                    f"Map all critical {subject} concepts from foundational to advanced. "
                    f"Create a dependency graph: what must be understood before what."
                ),
                artifact_type="guide",
                why_this="Understanding concept dependencies prevents confusion when advanced topics reference basics.",
            ),
            Operation(
                title=f"{subject} Practice Problem Bank",
                description=(
                    f"Curate 50-100 practice problems and exercises for {subject}, categorized by difficulty and topic. "
                    f"Include sources: LeetCode, Kaggle, official docs exercises, textbook problems."
                ),
                artifact_type="guide",
                why_this="Active problem-solving builds skill faster than any passive content consumption.",
            ),
            Operation(
                title=f"{subject} Real-World Project Plan",
                description=(
                    f"Design 2-3 real projects that apply {subject} to actual problems{goal_note}. "
                    f"Projects should progressively increase in complexity and be portfolio-worthy."
                ),
                artifact_type="roadmap",
                why_this="Building real things cements understanding in ways that tutorials can never achieve.",
            ),
            Operation(
                title=f"{subject} Interview & Assessment Preparation",
                description=(
                    f"Compile the top {subject} interview questions, certification exam topics, or assessment criteria. "
                    f"Build a targeted review schedule for the final 2 weeks before any test or interview."
                ),
                artifact_type="guide",
                why_this="Knowing how mastery is evaluated helps you study what actually matters.",
            ),
            Operation(
                title="Weekly Progress Review System",
                description=(
                    f"Establish a Sunday review ritual: what did you cover this week in {subject}, "
                    f"what's stuck, what needs revision, and what's the plan for next week."
                ),
                artifact_type="tracker",
                why_this="Weekly reflection is the most powerful meta-learning tool — most learners skip it.",
            ),
        ]

        return Mission(
            mission_title=f"Master {subject}{time_note}{goal_note}",
            domain="learning",
            domain_label="Learning",
            rationale=(
                f"This system takes you from {level} to {subject} proficiency{time_note} "
                f"through curated resources, structured practice, and real projects — not random YouTube videos."
            ),
            operations=ops,
            next_actions=[
                f"Complete the {subject} skill assessment today",
                f"Enroll in the #1 ranked course from your {subject} roadmap",
                f"Start your first {subject} practice problem set this week",
            ],
            proactive_suggestions=[
                "Set a daily study reminder at your preferred time",
                "Create a Notion or Obsidian knowledge base to capture your notes",
                f"Join a {subject} community (Discord, Reddit, forum) for peer support",
            ],
        )

    # ------------------------------------------------------------------
    # CODING / BUILD
    # ------------------------------------------------------------------
    @staticmethod
    def _coding_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your application").title()
        stack = intent.entities.get("tech_stack", "")
        level = intent.entities.get("experience_level", "intermediate")
        stack_note = f" using {stack}" if stack else ""

        # Recommend a stack if none specified
        stack_rec = stack if stack else "React + FastAPI + PostgreSQL"

        ops = [
            Operation(
                title=f"{subject} — Product Requirements Document",
                description=(
                    f"Define the full scope of {subject}: core features, user stories, non-functional requirements, "
                    f"and MVP vs. post-MVP feature split. List what is explicitly out of scope."
                ),
                artifact_type="document",
                why_this="Undefined scope is the #1 cause of project failure — this locks in what you're building.",
            ),
            Operation(
                title=f"System Architecture Design for {subject}",
                description=(
                    f"Design the high-level architecture for {subject}: frontend, backend, database, caching, "
                    f"third-party APIs, and deployment infrastructure. Create a component diagram."
                ),
                artifact_type="architecture",
                why_this="Architecture decisions made early are expensive to reverse later — getting this right saves weeks.",
            ),
            Operation(
                title=f"Tech Stack Decision: {stack_rec}",
                description=(
                    f"Evaluate and finalize the tech stack for {subject}: framework choices, database selection, "
                    f"authentication library, hosting platform, and CI/CD tooling. Justify each choice."
                ),
                artifact_type="document",
                why_this="The right stack matches your skill level, scalability needs, and deployment constraints.",
            ),
            Operation(
                title=f"Folder Structure & Project Scaffold",
                description=(
                    f"Define the folder structure, naming conventions, and code organization for {subject}. "
                    f"Set up the project scaffold, package manager, linting, and formatting tools."
                ),
                artifact_type="guide",
                why_this="A clean structure from day one prevents the chaotic spaghetti that kills most side projects.",
            ),
            Operation(
                title=f"Database Schema Design for {subject}",
                description=(
                    f"Design the full relational/document database schema for {subject}: entities, relationships, "
                    f"indexes, and constraints. Include an ER diagram."
                ),
                artifact_type="schema",
                why_this="Schema mistakes are the hardest to fix later — designing this upfront prevents painful migrations.",
            ),
            Operation(
                title=f"API Design & Endpoint Specification",
                description=(
                    f"Define all REST (or GraphQL) endpoints for {subject}: routes, request/response shapes, "
                    f"authentication requirements, and error codes. Write the OpenAPI spec."
                ),
                artifact_type="document",
                why_this="API contracts let frontend and backend work in parallel without blocking each other.",
            ),
            Operation(
                title=f"Authentication & Authorization System",
                description=(
                    f"Design the auth flow for {subject}: registration, login, JWT/session management, "
                    f"role-based access control, and password reset. Choose an auth library or service."
                ),
                artifact_type="guide",
                why_this="Auth is the most security-critical component — retrofitting it later is dangerous.",
            ),
            Operation(
                title=f"UI/UX Design & Component Plan",
                description=(
                    f"Sketch the key screens and user flows for {subject}. Define the component library, "
                    f"design system (colors, typography, spacing), and responsive layout strategy."
                ),
                artifact_type="guide",
                why_this="A clear UI plan prevents endless redesigns mid-development.",
            ),
            Operation(
                title=f"Development Roadmap & Sprint Plan for {subject}",
                description=(
                    f"Break {subject} into 2-week development sprints, ordered by dependency. "
                    f"Define the MVP milestone and which features ship in each sprint."
                ),
                artifact_type="roadmap",
                why_this="Shipping in iterations keeps momentum and reveals integration issues early.",
            ),
            Operation(
                title=f"Testing Strategy for {subject}",
                description=(
                    f"Define the testing pyramid for {subject}: unit tests, integration tests, and E2E tests. "
                    f"Choose testing frameworks and set a coverage target."
                ),
                artifact_type="guide",
                why_this="A tested codebase is a maintainable codebase — skipping this creates technical debt.",
            ),
            Operation(
                title=f"Deployment & DevOps Plan for {subject}",
                description=(
                    f"Design the deployment pipeline for {subject}: hosting platform selection, CI/CD pipeline, "
                    f"environment management (dev/staging/prod), monitoring, and rollback strategy."
                ),
                artifact_type="guide",
                why_this="Deployment strategy determines how fast you can ship improvements and recover from failures.",
            ),
        ]

        return Mission(
            mission_title=f"Build {subject}{stack_note} — Complete Blueprint",
            domain="coding",
            domain_label="Software Development",
            rationale=(
                f"This blueprint covers every technical decision needed to build {subject} from zero to deployed — "
                f"architecture, schema, API, auth, UI, and testing strategy."
            ),
            operations=ops,
            next_actions=[
                f"Write the Product Requirements Document for {subject}",
                f"Set up the project scaffold and repository",
                "Build the database schema and run first migration",
            ],
            proactive_suggestions=[
                "Set up a GitHub repository with branch protection rules",
                "Create a project board (GitHub Projects or Linear) for sprint tracking",
                f"Register a domain name for {subject} if it will be public-facing",
            ],
        )

    # ------------------------------------------------------------------
    # BUSINESS
    # ------------------------------------------------------------------
    @staticmethod
    def _business_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        biz = intent.entities.get("subject", "your business").title()
        budget = intent.entities.get("budget", "")
        industry = intent.entities.get("industry", "")
        budget_note = f" (Budget: {budget})" if budget else ""
        industry_note = f" in the {industry} industry" if industry else ""

        ops = [
            Operation(
                title=f"{biz} — Market Research & Opportunity Analysis",
                description=(
                    f"Analyze the total addressable market for {biz}{industry_note}. "
                    f"Identify target customer segments, pain points, willingness to pay, and market size estimates."
                ),
                artifact_type="document",
                why_this="Validating market demand before building prevents the #1 startup failure: building what nobody wants.",
            ),
            Operation(
                title=f"Competitor Landscape Analysis for {biz}",
                description=(
                    f"Map the top 5-10 competitors to {biz}: their pricing, features, weaknesses, and customer reviews. "
                    f"Identify your differentiation angle and positioning gap."
                ),
                artifact_type="comparison",
                why_this="You can only win if you know exactly where existing solutions fall short.",
            ),
            Operation(
                title=f"SWOT Analysis — {biz}",
                description=(
                    f"Conduct a structured SWOT analysis for {biz}: Strengths, Weaknesses, Opportunities, Threats. "
                    f"Translate findings into concrete strategic decisions."
                ),
                artifact_type="swot",
                why_this="A SWOT analysis reveals whether to proceed, pivot, or abandon the concept before spending money.",
            ),
            Operation(
                title=f"Value Proposition & Brand Positioning",
                description=(
                    f"Craft the core value proposition for {biz} in one sentence. "
                    f"Define the brand voice, name, visual identity direction, and tagline."
                ),
                artifact_type="document",
                why_this="Unclear positioning is invisible in a crowded market — this is your signal in the noise.",
            ),
            Operation(
                title=f"Revenue Model & Pricing Strategy for {biz}",
                description=(
                    f"Design the revenue model for {biz}: subscription, one-time, freemium, marketplace, or service. "
                    f"Calculate unit economics: CAC, LTV, gross margin targets."
                ),
                artifact_type="budget_sheet",
                why_this="A business without a viable revenue model is a hobby, not a business.",
            ),
            Operation(
                title=f"MVP Feature Set & Launch Plan{budget_note}",
                description=(
                    f"Define the minimum viable product for {biz}: the fewest features needed to test core value. "
                    f"Create a 90-day build-and-launch timeline."
                ),
                artifact_type="roadmap",
                why_this="An MVP gets real feedback in weeks instead of spending 12 months building the wrong thing.",
            ),
            Operation(
                title=f"Go-to-Market Strategy for {biz}",
                description=(
                    f"Design the launch marketing strategy for {biz}: channels (content, paid, partnerships, cold outreach), "
                    f"first 100 customer acquisition plan, and messaging."
                ),
                artifact_type="guide",
                why_this="Product without distribution is invisible — a GTM strategy is how you get your first customers.",
            ),
            Operation(
                title=f"Financial Model & 12-Month Projections",
                description=(
                    f"Build a 12-month financial model for {biz}: revenue scenarios, fixed/variable costs, "
                    f"break-even analysis, and cash flow projection."
                ),
                artifact_type="budget_sheet",
                why_this="Financial modeling reveals when the business becomes viable and how much runway you need.",
            ),
            Operation(
                title=f"Pitch Deck Outline for {biz}",
                description=(
                    f"Structure a 10-slide investor pitch deck for {biz}: Problem, Solution, Market, Product, "
                    f"Business Model, Traction, Team, Competition, Financials, Ask."
                ),
                artifact_type="document",
                why_this="Even if you're not raising, building a pitch deck forces you to articulate your business clearly.",
            ),
        ]

        return Mission(
            mission_title=f"Launch {biz}{industry_note} — Business Blueprint",
            domain="business",
            domain_label="Business",
            rationale=(
                f"This blueprint validates, defines, and launches {biz}{industry_note} "
                f"through market research, revenue modeling, and a structured go-to-market strategy."
            ),
            operations=ops,
            next_actions=[
                f"Interview 10 potential customers to validate the {biz} concept",
                f"Build the MVP for {biz} in 30 days",
                "Launch a landing page to capture early interest",
            ],
            proactive_suggestions=[
                f"Register the business entity and domain name for {biz}",
                "Set up a simple CRM to track early prospects",
                "Create a waitlist to build pre-launch demand",
            ],
        )

    # ------------------------------------------------------------------
    # FITNESS
    # ------------------------------------------------------------------
    @staticmethod
    def _fitness_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your fitness goal").capitalize()
        timeline = intent.entities.get("timeline", "12 weeks")
        level = intent.entities.get("experience_level", "beginner")

        ops = [
            Operation(
                title="Baseline Assessment & Target Milestones",
                description=(
                    f"Measure current baselines: weight, body fat %, key lifts (if applicable), resting heart rate, "
                    f"and cardiovascular fitness. Set weekly milestones toward: {goal}."
                ),
                artifact_type="tracker",
                why_this="You can't optimize what you don't measure — baselines make progress visible.",
            ),
            Operation(
                title=f"Custom Training Program for: {goal}",
                description=(
                    f"Design a {timeline} progressive training program calibrated for a {level} targeting '{goal}'. "
                    f"Include weekly schedule, sets/reps, rest periods, and progression model."
                ),
                artifact_type="schedule",
                why_this="Generic workouts produce generic results — a program designed for your goal accelerates progress.",
            ),
            Operation(
                title="Nutrition & Macro Plan",
                description=(
                    f"Calculate your TDEE and set daily caloric targets for '{goal}'. "
                    f"Define macro splits (protein/carbs/fats), meal timing strategy, and high-performance food list."
                ),
                artifact_type="guide",
                why_this="Nutrition is 70% of any body composition result — training without it is building on sand.",
            ),
            Operation(
                title="Habit Stacking & Lifestyle Integration",
                description=(
                    "Design the behavioral system around your training: sleep protocol (7-9 hours), "
                    "hydration targets, stress management, and how to integrate workouts into your daily schedule."
                ),
                artifact_type="schedule",
                why_this="Sustainable fitness is built on habits, not motivation — this is the system that keeps you consistent.",
            ),
            Operation(
                title="Recovery & Injury Prevention Protocol",
                description=(
                    "Define weekly active recovery sessions, mobility work, deload weeks, and injury prevention exercises. "
                    "Include sleep optimization and stress monitoring checkpoints."
                ),
                artifact_type="guide",
                why_this="Recovery is when the body actually adapts — skipping it leads to plateaus and injuries.",
            ),
            Operation(
                title="Weekly Progress Tracking System",
                description=(
                    f"Set up a weekly measurement protocol: weight (same day/time), photos, key lift PRs, "
                    f"and a subjective energy/sleep rating. Trigger plan adjustments at 4-week intervals."
                ),
                artifact_type="tracker",
                why_this="Weekly tracking creates the feedback loop that lets you adjust before momentum stalls.",
            ),
        ]

        return Mission(
            mission_title=f"{goal} — {timeline} Transformation Plan",
            domain="fitness",
            domain_label="Fitness",
            rationale=(
                f"This plan combines progressive training, precision nutrition, and habit design "
                f"to achieve '{goal}' in {timeline} for a {level}-level athlete."
            ),
            operations=ops,
            next_actions=[
                "Complete your baseline assessment this week",
                "Start Week 1 of your training program",
                "Meal prep for the first week according to your macro plan",
            ],
            proactive_suggestions=[
                "Set a daily workout reminder at your preferred training time",
                "Log your first baseline metrics today",
                "Download a calorie tracking app (MyFitnessPal, Cronometer)",
            ],
        )

    # ------------------------------------------------------------------
    # FINANCE
    # ------------------------------------------------------------------
    @staticmethod
    def _finance_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your financial goal").capitalize()
        budget = intent.entities.get("budget", "")
        timeline = intent.entities.get("timeline", "12 months")

        ops = [
            Operation(
                title="Net Worth & Financial Snapshot",
                description=(
                    "Calculate current net worth: assets (cash, investments, property) minus liabilities (debt, loans). "
                    "Create a complete financial baseline before making any decisions."
                ),
                artifact_type="tracker",
                why_this="Every financial plan starts with an honest snapshot — you can't navigate without knowing where you are.",
            ),
            Operation(
                title=f"Goal-Aligned Budget Design — {goal}",
                description=(
                    f"Build a zero-based budget designed specifically to accelerate: {goal}. "
                    f"Categorize all income and expenses. Identify and eliminate at least 3 spending leaks."
                ),
                artifact_type="budget_sheet",
                why_this="A budget built around your goal funds it automatically — willpower isn't required.",
            ),
            Operation(
                title=f"Debt Elimination Strategy (if applicable)",
                description=(
                    "Inventory all debts by interest rate. Apply the Avalanche method (highest interest first) "
                    "or Snowball method (smallest balance first) based on your psychology."
                ),
                artifact_type="roadmap",
                why_this="High-interest debt compounds against you — eliminating it is the highest guaranteed return.",
            ),
            Operation(
                title=f"Savings & Emergency Fund Plan",
                description=(
                    f"Calculate your 3-6 month emergency fund target. "
                    f"Design an automatic savings system using separate accounts and transfer triggers."
                ),
                artifact_type="guide",
                why_this="An emergency fund prevents debt spirals — it's the foundation every other financial goal sits on.",
            ),
            Operation(
                title=f"Investment Roadmap — {timeline}",
                description=(
                    f"Design an investment strategy aligned with '{goal}': asset allocation, account types (ISA, 401k, brokerage), "
                    f"index fund selection, and contribution schedule."
                ),
                artifact_type="roadmap",
                why_this="Compound interest requires time — starting even small amounts now matters enormously.",
            ),
            Operation(
                title="Monthly Financial Review System",
                description=(
                    "Set up a monthly financial review ritual: review budget actuals vs. plan, net worth update, "
                    "investment performance check, and next-month adjustments."
                ),
                artifact_type="tracker",
                why_this="Monthly reviews catch drift before it becomes derailment — this is the discipline mechanism.",
            ),
        ]

        return Mission(
            mission_title=f"{goal} — Financial Roadmap",
            domain="finance",
            domain_label="Finance",
            rationale=(
                f"This plan builds a complete financial system around '{goal}' over {timeline} — "
                f"from baseline clarity through budgeting, debt strategy, savings, and investing."
            ),
            operations=ops,
            next_actions=[
                "Calculate your complete net worth this weekend",
                "Open a dedicated savings account for your goal",
                "Set up automatic transfers on payday",
            ],
            proactive_suggestions=[
                "Set a monthly financial review reminder on the 1st of each month",
                "Download a budgeting app (YNAB, Copilot, or spreadsheet template)",
                "Check your credit score if debt paydown is part of your goal",
            ],
        )

    # ------------------------------------------------------------------
    # RESEARCH
    # ------------------------------------------------------------------
    @staticmethod
    def _research_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your topic").title()
        goal = intent.entities.get("goal", "")
        goal_note = f" for {goal}" if goal else ""

        ops = [
            Operation(
                title=f"Research Scope & Question Framing — {subject}",
                description=(
                    f"Define the precise research question(s) for {subject}. "
                    f"Establish scope boundaries, key terms, and what 'done' looks like{goal_note}."
                ),
                artifact_type="document",
                why_this="Unscoped research wanders forever — a clear question makes every search decision obvious.",
            ),
            Operation(
                title=f"Source Strategy & Database Selection",
                description=(
                    f"Identify the top primary and secondary sources for {subject}: academic databases (Google Scholar, JSTOR), "
                    f"industry reports, expert interviews, and grey literature."
                ),
                artifact_type="guide",
                why_this="Source quality determines research quality — finding the right databases cuts search time in half.",
            ),
            Operation(
                title=f"Literature Review & Knowledge Mapping",
                description=(
                    f"Systematically review existing literature on {subject}. Map key themes, debates, and gaps. "
                    f"Build a synthesis matrix organizing findings by theme."
                ),
                artifact_type="document",
                why_this="Understanding what's already known prevents reinventing the wheel and reveals where new insight is needed.",
            ),
            Operation(
                title=f"Key Findings Synthesis for {subject}",
                description=(
                    f"Distill all research into 5-10 core findings with evidence citations. "
                    f"Identify conflicting evidence, consensus views, and open questions."
                ),
                artifact_type="document",
                why_this="Raw research without synthesis is just data — this turns it into actionable knowledge.",
            ),
            Operation(
                title=f"Research Report / Summary Document",
                description=(
                    f"Write the final structured output for {subject}: executive summary, methodology, findings, "
                    f"analysis, conclusions, and recommendations."
                ),
                artifact_type="document",
                why_this="A well-structured output ensures your research is actually used, not forgotten.",
            ),
            Operation(
                title="Bibliography & Citation Management",
                description=(
                    f"Organize all sources for {subject} in a citation manager (Zotero, Mendeley, or manual). "
                    f"Format citations in the required style (APA, MLA, Chicago, etc.)."
                ),
                artifact_type="document",
                why_this="Proper citations are non-negotiable for credibility and avoiding plagiarism.",
            ),
        ]

        return Mission(
            mission_title=f"Research: {subject}{goal_note}",
            domain="research",
            domain_label="Research",
            rationale=(
                f"This systematic research plan takes {subject} from undefined question "
                f"to a structured, evidence-backed output{goal_note}."
            ),
            operations=ops,
            next_actions=[
                f"Define your {subject} research question in writing",
                "Identify your top 5 source databases",
                "Begin literature review with 10 key papers",
            ],
            proactive_suggestions=[
                "Set up a citation manager (Zotero is free)",
                "Create a research notes folder with a consistent naming system",
                "Schedule 2-hour focused research blocks",
            ],
        )

    # ------------------------------------------------------------------
    # WRITING
    # ------------------------------------------------------------------
    @staticmethod
    def _writing_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your piece").title()
        goal = intent.entities.get("goal", "")
        timeline = intent.entities.get("timeline", "")

        ops = [
            Operation(
                title=f"Topic Clarity & Audience Analysis — {subject}",
                description=(
                    f"Define exactly what you're writing about in {subject}: the precise angle, target reader profile, "
                    f"their pain points, and what transformation the piece delivers."
                ),
                artifact_type="document",
                why_this="Writing for everyone means writing for no one — audience clarity makes every sentence decision easier.",
            ),
            Operation(
                title=f"Structural Outline for {subject}",
                description=(
                    f"Build a detailed hierarchical outline for {subject}: main sections, sub-points, supporting evidence, "
                    f"and transitions. Think architecture before bricklaying."
                ),
                artifact_type="document",
                why_this="An outline is a map — without it, writers get lost and produce meandering, hard-to-edit drafts.",
            ),
            Operation(
                title=f"Research & Evidence Gathering for {subject}",
                description=(
                    f"Collect all facts, statistics, quotes, case studies, and examples needed for {subject}. "
                    f"Organize by section to make drafting fast."
                ),
                artifact_type="guide",
                why_this="Evidence-gathering before writing prevents flow-breaking research interruptions mid-draft.",
            ),
            Operation(
                title=f"First Draft — {subject}",
                description=(
                    f"Write the complete first draft of {subject} without self-editing. "
                    f"Aim for clarity over perfection — the goal is a complete rough canvas to refine."
                ),
                artifact_type="document",
                why_this="A bad first draft beats a perfect empty page — drafting and editing are different cognitive modes.",
            ),
            Operation(
                title=f"Revision & Style Refinement",
                description=(
                    f"Revise {subject} for structure, argument flow, clarity, and concision. "
                    f"Apply a style guide (AP, Chicago, etc.) and eliminate weak phrases, passive voice, and filler."
                ),
                artifact_type="checklist",
                why_this="Great writing is rewriting — first drafts are raw material, revisions are the actual craft.",
            ),
            Operation(
                title=f"Publishing & Distribution Plan for {subject}",
                description=(
                    f"Define where and how {subject} will be published/delivered: platform selection, "
                    f"SEO/visibility strategy, promotion plan, and feedback collection."
                ),
                artifact_type="guide",
                why_this="Writing without distribution is a tree falling in an empty forest.",
            ),
        ]

        return Mission(
            mission_title=f"Write: {subject}",
            domain="writing",
            domain_label="Writing",
            rationale=(
                f"This plan takes {subject} from concept to published piece "
                f"through structured outlining, evidence gathering, drafting, and revision."
            ),
            operations=ops,
            next_actions=[
                f"Complete the audience analysis for {subject} today",
                "Write your detailed outline before starting the draft",
                "Set a daily word-count target",
            ],
            proactive_suggestions=[
                "Block 2-hour distraction-free writing sessions in your calendar",
                "Set a deadline for your first draft",
                "Find 2-3 beta readers for feedback after your first revision",
            ],
        )

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------
    @staticmethod
    def _health_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your health concern").capitalize()

        ops = [
            Operation(
                title=f"Health Goal Clarification & Symptom Log — {goal}",
                description=(
                    f"Document your current health status related to '{goal}': symptoms, duration, severity, "
                    f"triggers, and what you've already tried. Create a structured health log."
                ),
                artifact_type="document",
                why_this="Clear documentation leads to faster, more accurate medical consultations.",
            ),
            Operation(
                title="Specialist & Resource Identification",
                description=(
                    f"Identify the right type of medical specialist or health professional for '{goal}'. "
                    f"Find top-rated practitioners in your area and understand the referral pathway."
                ),
                artifact_type="guide",
                why_this="Seeing the right specialist first saves months of being redirected through the wrong channels.",
            ),
            Operation(
                title="Lifestyle Factor Analysis",
                description=(
                    f"Audit lifestyle factors impacting '{goal}': sleep quality, stress levels, nutrition, "
                    f"exercise habits, and environmental factors. Identify quick wins."
                ),
                artifact_type="tracker",
                why_this="Lifestyle is often the highest-leverage health variable — many conditions are diet and sleep problems in disguise.",
            ),
            Operation(
                title="Treatment / Wellness Plan Outline",
                description=(
                    f"Structure a wellness plan for '{goal}': medical interventions, lifestyle modifications, "
                    f"supplementation (evidence-based only), and monitoring protocol."
                ),
                artifact_type="guide",
                why_this="A structured plan ensures all relevant levers are pulled systematically rather than randomly.",
            ),
            Operation(
                title="Progress Monitoring & Follow-up Schedule",
                description=(
                    f"Set up a tracking system for '{goal}': weekly metrics to log, follow-up appointment schedule, "
                    f"and threshold triggers for when to escalate care."
                ),
                artifact_type="tracker",
                why_this="Health improvements are gradual — systematic tracking reveals what's working before subjective feelings do.",
            ),
        ]

        return Mission(
            mission_title=f"Health Plan: {goal}",
            domain="health",
            domain_label="Health",
            rationale=(
                f"This plan provides a structured approach to '{goal}' — from documentation and specialist selection "
                f"through lifestyle optimization and ongoing monitoring."
            ),
            operations=ops,
            next_actions=[
                "Book an appointment with the identified specialist",
                "Start your daily health log today",
                "Audit your sleep and nutrition habits this week",
            ],
            proactive_suggestions=[
                "Set a medication/supplement reminder if applicable",
                "Log baseline metrics before making any changes",
                "Share your health log with your doctor at your next appointment",
            ],
        )

    # ------------------------------------------------------------------
    # PRODUCTIVITY
    # ------------------------------------------------------------------
    @staticmethod
    def _productivity_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your productivity goal").capitalize()

        ops = [
            Operation(
                title=f"Productivity Audit — Current State",
                description=(
                    f"Track and analyze how you currently spend your time over 3 days for '{goal}'. "
                    f"Identify your biggest time sinks, energy peaks, and recurring interruptions."
                ),
                artifact_type="tracker",
                why_this="You can't optimize a system you haven't measured — the audit reveals the real bottlenecks.",
            ),
            Operation(
                title="Deep Work System Design",
                description=(
                    "Design a deep work schedule: identify your peak cognitive hours, block distraction-free work sessions, "
                    "set communication boundaries, and create a distraction elimination protocol."
                ),
                artifact_type="schedule",
                why_this="Deep work produces 4x the output of shallow work — designing a system for it is the highest-leverage move.",
            ),
            Operation(
                title=f"Goal-Aligned Task Prioritization for '{goal}'",
                description=(
                    f"Implement a prioritization system (Eisenhower Matrix, MoSCoW, or weekly OKRs) for '{goal}'. "
                    f"Define your top 3 Most Important Tasks (MITs) for each day."
                ),
                artifact_type="guide",
                why_this="Doing the wrong things efficiently is still failure — prioritization ensures effort goes where it matters.",
            ),
            Operation(
                title="Environment Design & Tool Optimization",
                description=(
                    "Redesign your physical and digital workspace to minimize friction: tool consolidation, "
                    "notification pruning, workspace setup, and single-source-of-truth task management."
                ),
                artifact_type="checklist",
                why_this="Environment design is the most underrated productivity lever — your context shapes your behavior automatically.",
            ),
            Operation(
                title="Weekly Review & Planning Ritual",
                description=(
                    "Create a structured Weekly Review ritual (45-60 min every Sunday): "
                    "review last week, capture open loops, plan next week's priorities, and update your system."
                ),
                artifact_type="schedule",
                why_this="The weekly review is the engine of any GTD-style system — without it, everything collapses within 2 weeks.",
            ),
        ]

        return Mission(
            mission_title=f"Productivity System: {goal}",
            domain="productivity",
            domain_label="Productivity",
            rationale=(
                f"This plan builds a complete productivity system around '{goal}' — "
                f"from time audit through deep work scheduling and weekly review rituals."
            ),
            operations=ops,
            next_actions=[
                "Run a 3-day time audit starting tomorrow",
                "Block your first deep work session this week",
                "Set up your weekly review ritual for Sunday",
            ],
            proactive_suggestions=[
                "Install a time-tracking app (Toggl, Clockify) for the audit",
                "Set 'Do Not Disturb' schedule on your phone during deep work hours",
                "Create a morning startup routine that primes deep work",
            ],
        )

    # ------------------------------------------------------------------
    # REMINDER
    # ------------------------------------------------------------------
    @staticmethod
    def _reminder_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your reminder").capitalize()
        timeline = intent.entities.get("timeline", "")

        ops = [
            Operation(
                title=f"Reminder: {subject}",
                description=(
                    f"Set a precise reminder for '{subject}'{(' at ' + timeline) if timeline else ''}. "
                    f"Configure notification type, snooze behavior, and any attached notes or context."
                ),
                artifact_type="none",
                why_this="Capturing this now ensures it doesn't fall through the cracks.",
            ),
            Operation(
                title="Attach Context & Notes",
                description=(
                    f"Add any relevant links, documents, contacts, or preparation notes to the reminder for '{subject}' "
                    f"so when it fires, you have everything you need immediately."
                ),
                artifact_type="document",
                why_this="A reminder with no context requires you to reconstruct what you meant — attached notes eliminate that friction.",
            ),
            Operation(
                title="Recurring & Escalation Setup",
                description=(
                    f"Determine if '{subject}' should recur (daily, weekly, monthly) or is one-time. "
                    f"Set an escalation: if snoozed 3 times, increase notification priority."
                ),
                artifact_type="none",
                why_this="Recurring reminders for habits or regular tasks should be set once and maintained automatically.",
            ),
        ]

        return Mission(
            mission_title=f"Reminder: {subject}",
            domain="reminder",
            domain_label="Reminder",
            rationale=f"Smart reminder configured for '{subject}' with context and escalation.",
            operations=ops,
            next_actions=[
                f"Mark '{subject}' as done when completed",
                "Check if this should become a recurring habit",
            ],
            proactive_suggestions=[
                "Add prep steps as sub-tasks if this requires preparation",
            ],
        )

    # ------------------------------------------------------------------
    # MEETINGS
    # ------------------------------------------------------------------
    @staticmethod
    def _meetings_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your meeting").capitalize()

        ops = [
            Operation(
                title=f"Meeting Agenda for: {subject}",
                description=(
                    f"Draft a structured agenda for '{subject}': objectives, topics in order, time allocations per topic, "
                    f"and decisions needed. Share 24 hours in advance."
                ),
                artifact_type="document",
                why_this="A clear agenda reduces meeting time by 40% and ensures the right outcomes are reached.",
            ),
            Operation(
                title="Pre-Meeting Prep Checklist",
                description=(
                    f"Compile everything needed before '{subject}': materials to review, data to pull, "
                    f"open questions to resolve, and actions from the last meeting."
                ),
                artifact_type="checklist",
                why_this="Prepared participants make meetings 3x more productive.",
            ),
            Operation(
                title="Meeting Notes & Action Items Template",
                description=(
                    f"Set up a meeting notes template for '{subject}': attendees, key discussions, decisions made, "
                    f"action items with owners and deadlines."
                ),
                artifact_type="document",
                why_this="Documented action items with owners are the only outputs that actually move things forward.",
            ),
        ]

        return Mission(
            mission_title=f"Meeting: {subject}",
            domain="meetings",
            domain_label="Meetings",
            rationale=f"Complete meeting preparation and follow-up system for '{subject}'.",
            operations=ops,
            next_actions=["Send the agenda to participants", "Schedule a follow-up to review action items"],
            proactive_suggestions=["Set a reminder to review action items 48 hours after the meeting"],
        )

    # ------------------------------------------------------------------
    # SHOPPING
    # ------------------------------------------------------------------
    @staticmethod
    def _shopping_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "your purchase").capitalize()
        budget = intent.entities.get("budget", "")
        budget_note = f" (Budget: {budget})" if budget else ""

        ops = [
            Operation(
                title=f"Requirements Definition — {subject}",
                description=(
                    f"Define exactly what you need from '{subject}': must-have features, nice-to-haves, and deal-breakers. "
                    f"Clarify intended use case and frequency of use."
                ),
                artifact_type="document",
                why_this="Defining requirements prevents buyer's remorse from shiny features you'll never use.",
            ),
            Operation(
                title=f"Market Research & Option Comparison{budget_note}",
                description=(
                    f"Research the top 5 options for '{subject}' across price points. "
                    f"Compare by specs, reviews, reliability, and value for money."
                ),
                artifact_type="comparison",
                why_this="A structured comparison removes emotion from the decision and surfaces the objectively best option.",
            ),
            Operation(
                title="Best Deal & Timing Strategy",
                description=(
                    f"Identify where to buy '{subject}' at the best price: price history tracking, "
                    f"upcoming sale events, and cashback/reward maximization."
                ),
                artifact_type="guide",
                why_this="Buying at the wrong time or place can cost 20-40% more for identical items.",
            ),
        ]

        return Mission(
            mission_title=f"Smart Buy: {subject}",
            domain="shopping",
            domain_label="Shopping",
            rationale=f"Structured research and comparison for purchasing '{subject}'{budget_note}.",
            operations=ops,
            next_actions=[f"Finalize your top pick for {subject}", "Set a price alert if not buying immediately"],
            proactive_suggestions=["Check return policy before purchasing", "Compare extended warranty options"],
        )

    # ------------------------------------------------------------------
    # DOCUMENTS
    # ------------------------------------------------------------------
    @staticmethod
    def _documents_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "the document").capitalize()

        ops = [
            Operation(
                title=f"Document Summary — {subject}",
                description=(
                    f"Extract and summarize the key points from '{subject}': main thesis, supporting arguments, "
                    f"and conclusions. Produce a concise executive summary."
                ),
                artifact_type="document",
                why_this="A clear summary saves re-reading time and makes the document's value immediately accessible.",
            ),
            Operation(
                title="Entity & Data Extraction",
                description=(
                    f"Extract all key entities from '{subject}': people, organizations, dates, dollar amounts, "
                    f"commitments, and deadlines."
                ),
                artifact_type="document",
                why_this="Structured extraction makes the document searchable and actionable rather than a black box.",
            ),
            Operation(
                title="Action Items & Follow-up Tasks",
                description=(
                    f"Identify all action items, commitments, and follow-ups required from '{subject}'. "
                    f"Assign owners and deadlines where determinable."
                ),
                artifact_type="checklist",
                why_this="Documents only create value when the actions they require are captured and executed.",
            ),
        ]

        return Mission(
            mission_title=f"Document Analysis: {subject}",
            domain="documents",
            domain_label="Documents",
            rationale=f"Complete structured analysis and action extraction from '{subject}'.",
            operations=ops,
            next_actions=["Execute the action items from the document", "File the document in the correct location"],
            proactive_suggestions=["Set reminders for any deadlines found in the document"],
        )

    # ------------------------------------------------------------------
    # LIFE PLANNING
    # ------------------------------------------------------------------
    @staticmethod
    def _life_planning_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your life goal").capitalize()
        timeline = intent.entities.get("timeline", "5 years")

        ops = [
            Operation(
                title=f"Vision Clarification — {goal}",
                description=(
                    f"Write a vivid, specific description of '{goal}' as if already achieved. "
                    f"Define what success looks, feels, and sounds like in concrete terms."
                ),
                artifact_type="document",
                why_this="Vague goals produce vague results — specificity is the difference between a dream and a plan.",
            ),
            Operation(
                title=f"{timeline} Milestone Roadmap",
                description=(
                    f"Back-calculate from '{goal}' to today: what milestones must be hit at 1 year, 2 years, "
                    f"3 years, and {timeline}? Define each milestone in measurable terms."
                ),
                artifact_type="roadmap",
                why_this="Milestones turn a distant goal into a series of achievable near-term steps.",
            ),
            Operation(
                title="Obstacle & Risk Analysis",
                description=(
                    f"Identify the top 5 obstacles that could prevent '{goal}': financial, social, skill gaps, "
                    f"and external risks. Design pre-committed responses for each."
                ),
                artifact_type="document",
                why_this="Pre-mortem thinking prevents obstacles from becoming full stops rather than speed bumps.",
            ),
            Operation(
                title="Resource & Support System Mapping",
                description=(
                    f"Map all resources needed for '{goal}': financial capital, knowledge, mentors, community, "
                    f"and tools. Identify the first resource to acquire."
                ),
                artifact_type="guide",
                why_this="Goals achieved without support systems are fragile — identifying your resources makes execution durable.",
            ),
            Operation(
                title="Quarterly Review & Adaptation System",
                description=(
                    f"Design a quarterly review ritual for '{goal}': assess progress, update milestones, "
                    f"celebrate wins, and recalibrate the plan based on what you've learned."
                ),
                artifact_type="schedule",
                why_this="Life plans need regular recalibration — the plan that doesn't adapt gets abandoned.",
            ),
        ]

        return Mission(
            mission_title=f"{goal} — {timeline} Life Plan",
            domain="life_planning",
            domain_label="Life Planning",
            rationale=(
                f"This plan builds a complete, milestone-driven roadmap for '{goal}' over {timeline} "
                f"with obstacle pre-emption and a quarterly adaptation system."
            ),
            operations=ops,
            next_actions=[
                "Write your vision statement for this goal",
                "Identify your 1-year milestone",
                "Schedule your first quarterly review",
            ],
            proactive_suggestions=[
                "Find a mentor or accountability partner for this goal",
                "Read one book on this life domain for perspective",
                "Block time in your calendar for quarterly reviews",
            ],
        )

    # ------------------------------------------------------------------
    # EDUCATION
    # ------------------------------------------------------------------
    @staticmethod
    def _education_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your educational goal").capitalize()
        timeline = intent.entities.get("timeline", "")

        ops = [
            Operation(
                title=f"Program & Institution Research — {goal}",
                description=(
                    f"Research the top programs/institutions for '{goal}': rankings, admission rates, "
                    f"curriculum quality, alumni outcomes, and cost."
                ),
                artifact_type="comparison",
                why_this="Choosing the right program is the single most impactful decision in your educational journey.",
            ),
            Operation(
                title="Admission Requirements Analysis",
                description=(
                    f"List all requirements for target programs: GPA, test scores (SAT/GRE/GMAT), "
                    f"letters of recommendation, statement of purpose, and portfolio."
                ),
                artifact_type="checklist",
                why_this="Missing one requirement eliminates your application — this ensures nothing is overlooked.",
            ),
            Operation(
                title="Application Timeline & Deadline Tracker",
                description=(
                    f"Create a master timeline for '{goal}' applications: test registration dates, "
                    f"recommendation letter requests, essay drafts, and submission deadlines."
                ),
                artifact_type="schedule",
                why_this="Application processes have interdependent deadlines — a master timeline prevents catastrophic misses.",
            ),
            Operation(
                title="Test Preparation Plan",
                description=(
                    f"Design a preparation plan for required tests (GRE/GMAT/SAT/IELTS): "
                    f"diagnostic test, study schedule, practice test cadence, and target score timeline."
                ),
                artifact_type="schedule",
                why_this="Test scores are often the most controllable admission variable — a preparation plan maximizes them.",
            ),
            Operation(
                title="Statement of Purpose & Application Essay Strategy",
                description=(
                    f"Develop a compelling narrative for '{goal}': your story, why this program, "
                    f"your vision for what you'll do with the degree."
                ),
                artifact_type="document",
                why_this="The SOP is your one chance to be human — programs reject numbers but accept compelling stories.",
            ),
        ]

        return Mission(
            mission_title=f"Education Plan: {goal}",
            domain="education",
            domain_label="Education",
            rationale=f"Complete admission strategy for '{goal}' — from program research through application submission.",
            operations=ops,
            next_actions=[
                "Shortlist 5 target programs",
                "Register for required standardized tests",
                "Request letters of recommendation early",
            ],
            proactive_suggestions=[
                "Set application deadline reminders for each program",
                "Contact current students at target programs for insider insights",
                "Start a financial aid and scholarship search",
            ],
        )

    # ------------------------------------------------------------------
    # RELATIONSHIPS
    # ------------------------------------------------------------------
    @staticmethod
    def _relationships_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", "your relationship goal").capitalize()

        ops = [
            Operation(
                title=f"Situation Assessment — {goal}",
                description=(
                    f"Clearly define the current situation and the specific challenge related to '{goal}'. "
                    f"Write down both perspectives (yours and the other party's) objectively."
                ),
                artifact_type="document",
                why_this="Clarity about the actual problem prevents solving the wrong thing.",
            ),
            Operation(
                title="Communication Strategy",
                description=(
                    f"Design a communication approach for '{goal}': how to open the conversation, "
                    f"active listening techniques, and how to express needs without blame."
                ),
                artifact_type="guide",
                why_this="How something is said is as important as what is said — effective communication changes outcomes.",
            ),
            Operation(
                title="Action Plan & Commitments",
                description=(
                    f"Define specific, concrete actions you can take unilaterally to improve '{goal}'. "
                    f"Set check-in milestones to evaluate progress."
                ),
                artifact_type="guide",
                why_this="Vague intentions produce no change — specific commitments do.",
            ),
        ]

        return Mission(
            mission_title=f"Relationship Plan: {goal}",
            domain="relationships",
            domain_label="Relationships",
            rationale=f"Structured approach to navigating '{goal}' with clarity and intentional action.",
            operations=ops,
            next_actions=["Take one concrete action toward your relationship goal this week"],
            proactive_suggestions=["Consider speaking with a counselor or therapist if the challenge is significant"],
        )

    # ------------------------------------------------------------------
    # ENTERTAINMENT
    # ------------------------------------------------------------------
    @staticmethod
    def _entertainment_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        subject = intent.entities.get("subject", "entertainment").capitalize()

        ops = [
            Operation(
                title=f"Personalized {subject} Recommendations",
                description=(
                    f"Curate the top 10 {subject} options based on your stated preferences: "
                    f"genre, mood, platform availability, and quality metrics."
                ),
                artifact_type="guide",
                why_this="Personalized curation saves hours of scrolling through suboptimal options.",
            ),
            Operation(
                title=f"Ranked {subject} Watchlist / Playlist",
                description=(
                    f"Build a prioritized list of {subject} content ordered by relevance to your taste. "
                    f"Include key details: runtime, platform, why it matches your preferences."
                ),
                artifact_type="guide",
                why_this="A pre-built list eliminates decision fatigue at the moment you want to relax.",
            ),
        ]

        return Mission(
            mission_title=f"Entertainment: {subject}",
            domain="entertainment",
            domain_label="Entertainment",
            rationale=f"Personalized {subject} curation based on your preferences.",
            operations=ops,
            next_actions=[f"Pick your first item from the {subject} list tonight"],
            proactive_suggestions=[f"Set a regular '{subject} time' block in your weekly schedule"],
        )

    # ------------------------------------------------------------------
    # GENERIC TASK (fallback)
    # ------------------------------------------------------------------
    @staticmethod
    def _task_pipeline(intent: IntentResult, ctx: UserContext) -> Mission:
        goal = intent.entities.get("goal", intent.raw_objective).capitalize()

        ops = [
            Operation(
                title=f"Scope & Requirements — {goal}",
                description=(
                    f"Define the precise deliverables, success criteria, constraints, and resources needed for: '{goal}'."
                ),
                artifact_type="document",
                why_this="Clear scope prevents scope creep and ensures everyone has the same definition of done.",
            ),
            Operation(
                title=f"Resource & Tool Identification",
                description=(
                    f"Identify all tools, people, information, and resources needed to complete '{goal}'. "
                    f"Resolve any blockers or dependencies upfront."
                ),
                artifact_type="checklist",
                why_this="Starting without the right resources wastes the time you spend discovering gaps mid-execution.",
            ),
            Operation(
                title=f"Execution Plan & Timeline",
                description=(
                    f"Break '{goal}' into concrete, ordered sub-tasks with estimated time per task and a completion date."
                ),
                artifact_type="schedule",
                why_this="A sequenced task list prevents decision-making overhead during execution.",
            ),
            Operation(
                title=f"Quality Review & Completion Criteria",
                description=(
                    f"Define what 'done' looks like for '{goal}': quality checks, acceptance criteria, "
                    f"and any review or approval required."
                ),
                artifact_type="checklist",
                why_this="Without completion criteria, tasks hover perpetually at '90% done'.",
            ),
        ]

        return Mission(
            mission_title=f"Mission: {goal}",
            domain="task",
            domain_label="Task",
            rationale=f"Structured execution plan for '{goal}' with clear scope and completion criteria.",
            operations=ops,
            next_actions=[f"Start with the scope definition for '{goal}'"],
            proactive_suggestions=["Set a target completion date and create a reminder"],
        )
