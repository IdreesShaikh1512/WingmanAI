"""Expert Responder — Domain Specialist AI Engine.

This is the core of Wingman's intelligence upgrade.

Instead of generating templates with "Option A", "To be calculated", "Research this",
the ExpertResponder acts as a team of senior domain consultants who deliver
FINAL, COMPLETE, REAL answers.

Every response should feel like:
  "I hired a team of experts."
  Not: "I received a generic AI response."

Domain specialists:
  - Travel:    travel planner + airline consultant + visa advisor + local guide + budget planner
  - Learning:  career coach + curriculum designer + industry mentor
  - Coding:    software architect + DevOps engineer + security consultant
  - Business:  strategy consultant + market analyst + financial modeler
  - Fitness:   certified trainer + nutritionist + physiologist
  - Finance:   financial advisor + investment analyst + tax strategist
  - Career:    executive recruiter + career coach + industry mentor
  - Health:    clinical advisor + wellness coach + diagnostics specialist

PRIMARY RULE:
  - Never generate templates.
  - Never generate placeholders.
  - Never generate "Option A", "Option B", "Research this", "Fill this later".
  - Generate REAL recommendations with REAL names, REAL prices, REAL sources.

Knowledge cutoff caveat:
  - For real-time prices (flights, live stock prices), note the approximate range
    and state that live verification is needed, but still provide the best-known estimate.
"""

from __future__ import annotations

import json
import os

import httpx

from agents.planner_agent import Mission

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_MODEL = "claude-sonnet-4-6"

# ─────────────────────────────────────────────────────────────────────────────
# MASTER EXPERT SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

_EXPERT_SYSTEM_PROMPT = """You are Wingman — an elite AI assistant powered by a team of senior domain experts.

You are competing against:
  OpenAI Operator, Perplexity, Claude, Cursor, Apple Intelligence, Google Gemini.

Every response MUST be expert-level. Do NOT optimize for speed. Optimize for usefulness.

══════════════════════════════════════════════════════════
PRIMARY RULE: REAL CONTENT ONLY. FINAL ANSWERS ONLY.
══════════════════════════════════════════════════════════

FORBIDDEN — Never output:
  ✗ "Option A", "Option B", "Option C"
  ✗ "Placeholder", "To be filled", "Research this"
  ✗ "Insert later", "To be calculated", "Fill this table"
  ✗ "Lorem ipsum", "Sample data"
  ✗ "[destination]", "[company]", "[tool]"
  ✗ Generic step lists with no real content
  ✗ "You should research...", "Consider looking into..."

REQUIRED — Always output:
  ✓ Real hotel names (e.g., Shangri-La The Fort, Park Hyatt Tokyo, The Hoxton)
  ✓ Real restaurant names (e.g., Manam Manila, Nobu London, Noma Copenhagen)
  ✓ Real transport options (e.g., Grab, MRT Line 3, JR Pass, Oyster Card, BTS Skytrain)
  ✓ Real frameworks (e.g., React, FastAPI, Next.js, Django, Spring Boot)
  ✓ Real books (e.g., "Hands-On Machine Learning" by Aurélien Géron, "Clean Code" by Robert C. Martin)
  ✓ Real YouTube channels (e.g., Andrej Karpathy, Fireship, Traversy Media, 3Blue1Brown)
  ✓ Real certifications (e.g., AWS Solutions Architect, Google Data Analytics, CFA Level 1)
  ✓ Real companies (e.g., Stripe, Vercel, Cloudflare, Supabase, Railway)
  ✓ Real universities (e.g., MIT OpenCourseWare, Stanford Online, Coursera, fast.ai)
  ✓ Real attractions (e.g., Senso-ji Temple, Shibuya Crossing, teamLab Borderless)
  ✓ Real salary ranges (e.g., $85,000–$140,000/year for Mid-Level Data Scientist in US)
  ✓ Real price estimates (e.g., ¥15,000–¥25,000/night for mid-range Tokyo hotel)
  ✓ Real timelines (e.g., "Python fundamentals: 6–8 weeks with 2 hours/day")

══════════════════════════════════════════════════════════
DOMAIN EXPERT MODES
══════════════════════════════════════════════════════════

TRAVEL: Act as travel planner + airline consultant + visa advisor + local guide + budget planner.
  → Recommend REAL hotels by name and price tier
  → Recommend REAL restaurants by cuisine and neighborhood
  → Name REAL transit systems, passes, and apps
  → Provide REAL visa requirements by passport nationality
  → Give REAL budget ranges with actual currency

LEARNING / CAREER: Act as career coach + curriculum designer + industry mentor.
  → Provide REAL course names (e.g., "CS50x by Harvard on edX")
  → Provide REAL book titles and authors
  → Provide REAL YouTube channels by name
  → Provide REAL certifications with exam codes and costs
  → Provide REAL weekly roadmaps with hour estimates
  → Provide REAL salary data by role and market

CODING: Act as software architect + senior engineer.
  → Write REAL folder structures with actual file names
  → Write REAL database schemas with actual table/column names
  → Write REAL API endpoints (GET /api/v1/users, POST /api/v1/auth/login, etc.)
  → Recommend REAL libraries (e.g., "Pydantic v2 for validation, SQLAlchemy 2.0 for ORM")
  → Recommend REAL hosting platforms with pricing (e.g., "Railway.app at ~$5/month")

BUSINESS: Act as strategy consultant + market analyst.
  → Name REAL competitors with REAL market positions
  → Provide REAL pricing models with REAL numbers
  → Give REAL unit economics estimates (CAC, LTV, margins)
  → Suggest REAL marketing channels with REAL cost-per-acquisition ranges

FITNESS: Act as certified personal trainer + sports nutritionist.
  → Provide REAL workout programs (e.g., 5/3/1, GZCLP, PPL)
  → Name REAL exercises with sets/reps/rest
  → Provide REAL meal plans with actual macros
  → Recommend REAL supplements with doses (e.g., "Creatine monohydrate: 5g/day")

FINANCE: Act as financial advisor + investment analyst.
  → Recommend REAL brokers (e.g., Fidelity, Interactive Brokers, eToro)
  → Cite REAL average returns (e.g., "S&P 500 historical average: ~10%/year")
  → Provide REAL fee comparisons
  → Give REAL tax-advantaged account types by country

══════════════════════════════════════════════════════════
KNOWLEDGE CAVEAT RULE
══════════════════════════════════════════════════════════
If you cannot know exact real-time information (live prices, today's visa fees):
  ✓ State the approximate known range
  ✓ Explain what needs live verification
  ✓ Never leave a blank or "To be calculated"

Example:
  ✓ "Flight estimate: $400–$650 round trip (varies; use Google Flights to compare today's fares)"
  ✗ "Flight cost: — (To be calculated)"

══════════════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════════════
Use rich markdown:
  - Tables for comparisons, budgets, schedules, roadmaps
  - Numbered lists for step-by-step processes
  - Bullet lists for options and checklists
  - Code blocks for schemas, folder structures, API specs
  - Bold for emphasis on key names and numbers
  - Emojis sparingly for section headers only

Always end with a "✅ Immediate Action" section — the single most important thing to do right now."""


# ─────────────────────────────────────────────────────────────────────────────
# Expert Responder
# ─────────────────────────────────────────────────────────────────────────────

class ExpertResponder:
    """Calls Claude with the domain-expert system prompt to generate REAL content."""

    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def has_api_key(self) -> bool:
        return bool(self._api_key)

    def generate_expert_response(
        self,
        objective: str,
        domain: str,
        mission_title: str,
        rationale: str,
        operations: list[dict],
        entities: dict,
        user_context_snippets: list[str] | None = None,
    ) -> str:
        """
        Generate a complete, expert-level response for the given objective.
        Returns formatted markdown string with real content — no templates.
        """
        if not self.has_api_key():
            return self._fallback_expert_response(objective, domain, mission_title, operations, entities)

        try:
            return self._call_llm(
                objective, domain, mission_title, rationale, operations, entities, user_context_snippets or []
            )
        except Exception as e:
            return self._fallback_expert_response(objective, domain, mission_title, operations, entities)

    def _call_llm(
        self,
        objective: str,
        domain: str,
        mission_title: str,
        rationale: str,
        operations: list[dict],
        entities: dict,
        user_context_snippets: list[str],
    ) -> str:
        """Call the Anthropic API with the expert system prompt."""

        ops_text = "\n".join(
            f"  {i+1}. {op['title']}: {op.get('description', '')}"
            for i, op in enumerate(operations)
        )

        user_prompt = f"""User Objective: "{objective}"

Domain: {domain}
Mission Title: {mission_title}
Context from user history: {', '.join(user_context_snippets) if user_context_snippets else 'First-time user, no prior context'}

Extracted details:
{json.dumps(entities, indent=2)}

Planned Operations to execute:
{ops_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are acting as a team of senior domain experts for the "{domain}" domain.

Generate a COMPLETE, EXPERT-LEVEL response for this objective.

This means:
1. Work through every planned operation above
2. For each operation, provide REAL, SPECIFIC, ACTIONABLE content
3. Use the extracted entities (destination, budget, timeline, etc.) to personalize everything
4. Replace ALL placeholders with REAL names, REAL numbers, REAL resources
5. Think like you are delivering a paid consulting engagement

The user should receive a FINISHED SOLUTION, not a template to fill in later.

Format your response in rich markdown with tables, structured lists, and code blocks where appropriate.
Include specific names, prices, links to resources, and concrete recommendations throughout.

Remember:
- Real hotel names, not "Hotel A"
- Real frameworks, not "Framework X"  
- Real certifications with actual costs
- Real salary ranges
- Real timelines with hour estimates
- Real books with authors
- Real YouTube channels
- Real companies and tools

End with a "✅ Take Action Now" section with the 3 most important immediate steps."""

        response = httpx.post(
            _ANTHROPIC_API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": 4096,
                "system": _EXPERT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]

    # ─────────────────────────────────────────────────────────────────────────
    # Rich Fallback — no API key but still better than templates
    # ─────────────────────────────────────────────────────────────────────────

    def _fallback_expert_response(
        self,
        objective: str,
        domain: str,
        mission_title: str,
        operations: list[dict],
        entities: dict,
    ) -> str:
        """
        Domain-specific rich fallback when no API key is configured.
        Still uses real domain knowledge — NOT generic templates.
        """
        dest = entities.get("destination", "")
        subject = entities.get("subject", entities.get("goal", ""))
        budget = entities.get("budget", "")
        timeline = entities.get("timeline", "")

        if domain == "travel":
            return self._travel_expert_fallback(objective, dest, budget, timeline, entities)
        elif domain in ("career", "learning"):
            return self._career_learning_expert_fallback(objective, subject, timeline, entities)
        elif domain == "coding":
            return self._coding_expert_fallback(objective, subject, entities)
        elif domain == "business":
            return self._business_expert_fallback(objective, subject, entities)
        elif domain == "fitness":
            return self._fitness_expert_fallback(objective, entities)
        elif domain == "finance":
            return self._finance_expert_fallback(objective, entities)
        else:
            return self._general_expert_fallback(objective, domain, operations, entities)

    # ─────────────────────────────────────────────────────────────────────────
    # Domain Expert Fallbacks
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _travel_expert_fallback(objective: str, dest: str, budget: str, timeline: str, entities: dict) -> str:
        dest_name = dest.title() if dest else "your destination"
        d = dest.lower() if dest else ""

        # Destination-specific real content
        if "japan" in d or "tokyo" in d:
            hotels = [
                ("Park Hyatt Tokyo", "Shinjuku", "¥60,000–¥120,000/night", "⭐⭐⭐⭐⭐ — Lost in Translation iconic views"),
                ("Andaz Tokyo", "Toranomon Hills", "¥45,000–¥80,000/night", "⭐⭐⭐⭐⭐ — Rooftop bar, Marunouchi access"),
                ("Shinjuku Granbell Hotel", "Shinjuku", "¥18,000–¥30,000/night", "⭐⭐⭐⭐ — Great location, stylish mid-range"),
                ("Dormy Inn Asakusa", "Asakusa", "¥12,000–¥20,000/night", "⭐⭐⭐⭐ — Onsen, budget-friendly, near Senso-ji"),
                ("Capsule by Container", "Shinjuku", "¥4,000–¥7,000/night", "⭐⭐⭐ — Budget capsule with great design"),
            ]
            restaurants = [
                ("Ichiran Ramen", "Shibuya/Shinjuku", "¥900–¥1,500", "Solo ramen booth dining — unmissable"),
                ("Sukiyabashi Jiro", "Ginza", "¥40,000+", "World's most famous sushi — book 2 months ahead"),
                ("Gonpachi Nishi-Azabu", "Nishi-Azabu", "¥3,000–¥6,000", "Kill Bill restaurant, izakaya classics"),
                ("Tsukiji Outer Market", "Tsukiji", "¥800–¥2,000", "Best tuna sashimi breakfast in the world"),
                ("Narisawa", "Minami-Aoyama", "¥30,000+", "#1 restaurant in Japan — innovative Japanese cuisine"),
            ]
            transport = [
                ("IC Card (Suica/Pasmo)", "¥500 deposit + top-up", "Works on ALL Tokyo trains, buses, and convenience stores"),
                ("JR Pass", "~¥50,000 for 14 days", "If visiting Osaka/Kyoto/Hiroshima — saves significant money"),
                ("Tokyo Metro 72h Pass", "¥1,500", "Best for Tokyo-only trips on Metro lines"),
                ("Airport Express (Narita Express)", "¥3,070 one-way", "55 min Narita → Shinjuku, most comfortable"),
                ("Limousine Bus (Haneda)", "¥1,230–¥1,550", "Best option from Haneda to central Tokyo"),
            ]
            attractions = [
                "Senso-ji Temple (Asakusa) — free, best at 6am before crowds",
                "teamLab Borderless/Planets — digital art immersion (book online, ¥3,200)",
                "Shibuya Crossing & Sky — observation deck Shibuya Scramble Square (¥2,000)",
                "Tsukiji Fish Market — outer market for breakfast, free to explore",
                "Akihabara Electric Town — anime, electronics, gaming culture",
                "Shinjuku Golden Gai — 200+ tiny bars, best nightlife dive",
                "Harajuku Takeshita Street — youth fashion, crepe culture",
                "Meiji Shrine — tranquil forest walk in the heart of Tokyo (free)",
                "teamLab Planets Toyosu — walk through digital water (book in advance)",
                "Odaiba — futuristic waterfront, teamLab, digital art, Gundam statue",
            ]
            visa_info = "**Visa:** Most Western passports (US, EU, UK, AUS, CA) — visa-free for 90 days. Others: apply via nearest Japanese embassy, ~2 weeks processing, ~$30–50 fee. No vaccination requirements."
            budget_est = {
                "Budget": "¥7,000–¥12,000/day (capsule + street food + day trips)",
                "Mid-range": "¥20,000–¥35,000/day (3★ hotel + sit-down meals + activities)",
                "Luxury": "¥80,000–¥200,000+/day (Park Hyatt + Jiro sushi + private experiences)",
            }
            currency_tip = "**Currency:** JPY. Japan is still heavily cash-based. Get yen at 7-Eleven or Japan Post ATMs (accept foreign cards). Avoid airport exchange bureaus — worst rates."
        elif "bali" in d or "indonesia" in d:
            hotels = [
                ("COMO Uma Ubud", "Ubud", "$350–$600/night", "⭐⭐⭐⭐⭐ — Jungle views, world-class spa"),
                ("Four Seasons Bali at Sayan", "Ubud", "$700–$1,500/night", "⭐⭐⭐⭐⭐ — Floating above the Ayung River"),
                ("Katamama", "Seminyak", "$400–$700/night", "⭐⭐⭐⭐⭐ — Boutique, Balinese craftsmanship"),
                ("The Layar", "Seminyak", "$500–$900/night villa", "⭐⭐⭐⭐⭐ — Private pool villas"),
                ("Bisma Eight", "Ubud", "$150–$280/night", "⭐⭐⭐⭐ — Valley views, infinity pool, great value"),
                ("Surfers Loft", "Canggu", "$40–$80/night", "⭐⭐⭐⭐ — Best budget surfer hostel in Canggu"),
            ]
            restaurants = [
                ("Locavore", "Ubud", "$80–$120 pp", "Asia's 50 Best — modern Indonesian tasting menu"),
                ("Mozaic", "Ubud", "$100–$150 pp", "French-Indonesian fine dining, garden setting"),
                ("Merah Putih", "Seminyak", "$30–$60 pp", "Contemporary Indonesian cuisine in a stunning space"),
                ("Shelter Cafe", "Canggu", "$8–$15", "Best smoothie bowls + working cafe in Canggu"),
                ("Naughty Nuri's Warung", "Ubud", "$10–$25", "Legendary ribs and cocktails, institution since 1995"),
            ]
            transport = [
                ("GoJek / Grab", "~$2–8 per ride", "Essential app — download before arrival"),
                ("Scooter Rental", "$5–10/day", "Best way to explore — get international driving permit"),
                ("Metered Blue Bird Taxi", "$0.50/km", "Only official metered taxi — insist on meter"),
                ("Private Driver", "$50–80/full day", "Best for Nusa Penida trips or temple circuit days"),
                ("Fast Boat to Nusa Penida", "$25–40 return", "From Sanur port, 45 min — book Maruti Fast Boat"),
            ]
            attractions = [
                "Tegallalang Rice Terraces — sunrise visit ($2 entry fee, avoid midday heat)",
                "Sacred Monkey Forest Ubud — 700+ macaques, $5 entry",
                "Tanah Lot Temple — spectacular at sunset, $4 entry",
                "Mount Batur Sunrise Trek — 4am start, guide required, $35–50",
                "Nusa Penida Day Trip — Kelingking Beach, Angel's Billabong, Crystal Bay",
                "Seminyak Beach — best sunset bars (Potato Head Beach Club, La Plancha)",
                "Uluwatu Temple & Kecak Fire Dance — cliffside temple, $5 + $10 show",
                "Ubud Art Market — local crafts, best in morning before tour groups",
            ]
            visa_info = "**Visa:** Most nationalities (US, EU, UK, AUS) — Visa on Arrival or e-VoA, 30 days ($35 USD), extendable to 60 days. Purchase online at molina.imigrasi.go.id before arrival to skip queues."
            budget_est = {
                "Budget": "$30–60/day (guesthouse + warungs + scooter)",
                "Mid-range": "$100–200/day (boutique villa + restaurants + drivers)",
                "Luxury": "$400–1,500+/day (Four Seasons + fine dining + private experiences)",
            }
            currency_tip = "**Currency:** IDR. Best rates at licensed money changers (PT Central Kuta). Avoid airport. ATMs widely available but charge $3–5 per withdrawal — withdraw larger amounts."
        elif "dubai" in d or "uae" in d:
            hotels = [
                ("Burj Al Arab", "Jumeirah", "from $1,500/night", "⭐⭐⭐⭐⭐⭐ — 7-star icon, butler service"),
                ("Atlantis The Palm", "Palm Jumeirah", "$300–800/night", "⭐⭐⭐⭐⭐ — Waterpark access, celebrity restaurants"),
                ("Address Downtown", "Downtown Dubai", "$200–500/night", "⭐⭐⭐⭐⭐ — Burj Khalifa pool view"),
                ("Rove Downtown", "Downtown Dubai", "$80–150/night", "⭐⭐⭐⭐ — Best value mid-range, great location"),
                ("ibis One Central", "Trade Centre", "$60–100/night", "⭐⭐⭐ — Budget, metro access, solid choice"),
            ]
            restaurants = [
                ("Nobu Dubai", "Atlantic The Palm", "$120–200 pp", "World-class Japanese-Peruvian fusion"),
                ("At.mosphere", "Burj Khalifa Level 122", "$150+ pp", "Highest restaurant in the world"),
                ("Zuma Dubai", "DIFC", "$80–150 pp", "Japanese robata — Dubai's most-booked restaurant"),
                ("Arabian Tea House", "Al Fahidi", "$15–30 pp", "Authentic Emirati cuisine in heritage district"),
                ("Ravi Restaurant", "Satwa", "$5–15 pp", "Best Pakistani curry in Dubai since 1978 — locals only"),
            ]
            transport = [
                ("Dubai Metro (Red/Green Line)", "AED 1.09–7.50/trip", "Best for airport, downtown, marina — Nol card required"),
                ("Careem / Uber", "AED 10–40 per ride", "Both work — Careem is local, often cheaper"),
                ("Dubai Taxi (RTA)", "AED 12 flag fall + meter", "Official taxis — White taxis from airport mandatory"),
                ("Water Bus / Abra", "AED 1–25", "Creek abra for 1 AED — best experience in Old Dubai"),
                ("Car Rental", "AED 100–300/day", "Useful for desert trips — Hertz/Europcar in airports"),
            ]
            attractions = [
                "Burj Khalifa (At the Top observation) — book online, AED 129 (non-peak)",
                "Dubai Mall — 1,200 stores, aquarium, ice rink, Dubai Fountain show (free)",
                "Gold Souk + Spice Souk — Deira, early morning, take abra across Creek",
                "Desert Safari — 4WD dunes, camelback, BBQ dinner (~AED 150–250)",
                "Dubai Frame — architectural landmark, AED 50, great skyline photos",
                "Palm Jumeirah Monorail + The View at The Palm — AED 69 for 360° views",
                "Al Fahidi Historical Neighbourhood — free, Dubai Museum AED 3",
                "Global Village (Oct–May) — 90+ countries, food, culture, AED 20 entry",
            ]
            visa_info = "**Visa:** US, EU, UK, AUS — visa-free for 30–90 days on arrival. Most other nationalities get a free 30-day visa on arrival. Indian passport: apply for UAE tourist visa online ($90), 30 days."
            budget_est = {
                "Budget": "AED 300–500/day ($80–140) — budget hotel + local food + metro",
                "Mid-range": "AED 800–1,500/day ($220–400) — 4★ + restaurants + activities",
                "Luxury": "AED 3,000–10,000+/day ($800–2,700) — 5★+ + fine dining + private tours",
            }
            currency_tip = "**Currency:** AED (pegged to USD at 3.67). Use ATMs from Emirates NBD or ADCB — best rates. Avoid airport forex counters. Contactless payment widely accepted everywhere."
        elif "thailand" in d or "bangkok" in d or "phuket" in d:
            hotels = [
                ("Capella Bangkok", "Charoenkrung", "฿18,000–40,000/night ($500–1,100)", "⭐⭐⭐⭐⭐ — Best new luxury on the Chao Phraya"),
                ("The Peninsula Bangkok", "Charoenkrung", "฿12,000–25,000/night", "⭐⭐⭐⭐⭐ — River views, legendary service"),
                ("SO/ Bangkok", "Sathorn", "฿5,000–10,000/night", "⭐⭐⭐⭐⭐ — Rooftop park, design-forward"),
                ("Lub d Bangkok Silom", "Silom", "฿900–2,500/night", "⭐⭐⭐⭐ — Best design hostel in SEA"),
                ("ibis Bangkok Riverside", "Riverside", "฿1,200–2,000/night", "⭐⭐⭐ — Free hotel ferry, great value"),
            ]
            restaurants = [
                ("Gaggan Anand", "Wireless Road", "฿5,000–7,000 pp", "Asia's #1 restaurant — progressive Indian cuisine, book 2 months ahead"),
                ("Bo.lan", "Sukhumvit", "฿3,000–4,500 pp", "Sustainable Thai fine dining — James Beard Award winner"),
                ("Nahm", "Sathorn", "฿2,500–4,000 pp", "Traditional Royal Thai cuisine — superb curries"),
                ("Thip Samai", "Old City", "฿150–400", "Best Pad Thai in Bangkok since 1966 — queue outside"),
                ("Jay Fai", "Old City", "฿1,000–3,000", "Michelin-starred street food — crab omelette legend"),
            ]
            transport = [
                ("BTS Skytrain", "฿17–59/trip", "Essential for Sukhumvit, Silom corridors — Rabbit Card for savings"),
                ("MRT (Subway)", "฿17–42/trip", "Covers Chatuchak, Chinatown, Lumphini Park"),
                ("Grab", "฿60–200 per ride", "Most reliable — avoid tuk-tuks for long distances"),
                ("Chao Phraya Express Boat", "฿15–40", "Fastest way to visit temples — orange/blue flags"),
                ("Airport Rail Link", "฿45 (express) / ฿15–45 (city)", "25 min Suvarnabhumi → Makkasan, best airport option"),
            ]
            attractions = [
                "Wat Phra Kaew (Grand Palace) — ฿500, Bangkok's most sacred temple complex",
                "Chatuchak Weekend Market — 35 acres, 15,000+ stalls, Saturday-Sunday only",
                "Wat Arun (Temple of Dawn) — ฿100, stunning at sunset across the river",
                "Khao San Road — backpacker hub, night market, pad thai on the street",
                "ICONSIAM — world-class floating market inside a mall, free to enter",
                "Lumpini Park — morning tai chi, weekend run, giant monitor lizards",
                "Damnoen Saduak Floating Market — 1hr from Bangkok, ฿50 longtail boat",
                "Muay Thai at Rajadamnern Stadium — ฿1,000–3,000 ringside, Tuesday/Friday/Sunday",
            ]
            visa_info = "**Visa:** US, EU, UK, AUS — Visa Exemption 30 days on arrival (extendable 30 days at immigration for ฿1,900). Thailand e-Visa available for 60-day tourist. No vaccination requirements."
            budget_est = {
                "Budget": "฿1,000–2,000/day ($28–55) — guesthouse + street food + BTS",
                "Mid-range": "฿4,000–9,000/day ($110–250) — 4★ hotel + restaurants + tours",
                "Luxury": "฿20,000–60,000+/day ($550–1,650) — Capella/Peninsula + fine dining",
            }
            currency_tip = "**Currency:** THB. Best rates at SuperRich exchange booths (orange or green) — significantly better than airport. ATMs charge ฿250 foreign fee; use Kasikorn Bank ATMs."
        else:
            # Generic but still expert-quality
            hotels = [
                (f"Best luxury hotel in {dest_name}", "City Center", "Varies", "⭐⭐⭐⭐⭐ — Research on Booking.com/hotels.com"),
                (f"Best boutique hotel in {dest_name}", "Arts District", "Varies", "⭐⭐⭐⭐ — Check Mr & Mrs Smith curated collection"),
                (f"Best budget hotel in {dest_name}", "Near transit", "Varies", "⭐⭐⭐ — Hostelworld or Booking.com for deals"),
            ]
            restaurants = [
                (f"Fine dining in {dest_name}", "City Center", "$$$$", "Check Michelin Guide or World's 50 Best local edition"),
                (f"Local cuisine restaurants in {dest_name}", "Local neighborhoods", "$$", "Ask locals or use Google Maps 4.5★+ filter"),
            ]
            transport = [
                ("Local metro/subway system", "Cheapest option", "Download transit app for your destination"),
                ("Uber/Grab/local rideshare", "$", "Most convenient door-to-door"),
                ("Official airport taxi", "$$", "Only use licensed, metered services"),
            ]
            attractions = [
                f"Top-rated attractions in {dest_name} — check TripAdvisor Top 25 Things to Do",
                "Skip-The-Line tickets — book via GetYourGuide or Viator",
                "Free walking tours — search 'free walking tour {}'".format(dest_name),
            ]
            visa_info = f"**Visa:** Check exact requirements for {dest_name} at your country's foreign affairs website or iVisa.com"
            budget_est = {
                "Budget": "Estimate varies — search 'budget travel {}'".format(dest_name),
                "Mid-range": "Estimate varies — check Numbeo cost of living data",
                "Luxury": "Estimate varies — contact concierge at luxury hotels",
            }
            currency_tip = f"**Currency:** Check XE.com for current rates. Use ATMs from major banks for best rates in {dest_name}."

        # Build the expert travel response
        hotel_table = "| Hotel | Area | Price/Night | Why |\n|---|---|---|---|\n"
        for h in hotels:
            hotel_table += f"| **{h[0]}** | {h[1]} | {h[2]} | {h[3]} |\n"

        rest_table = "| Restaurant | Area | Price/Person | Specialty |\n|---|---|---|---|\n"
        for r in restaurants:
            rest_table += f"| **{r[0]}** | {r[1]} | {r[2]} | {r[3]} |\n"

        trans_table = "| Transport | Cost | Best For |\n|---|---|---|\n"
        for t in transport:
            trans_table += f"| **{t[0]}** | {t[1]} | {t[2]} |\n"

        budget_table = "| Travel Style | Daily Budget | What's Included |\n|---|---|---|\n"
        for style, amount in budget_est.items():
            budget_table += f"| {style} | {amount} | — |\n"

        attractions_list = "\n".join(f"- {a}" for a in attractions)

        return f"""## 🌍 {dest_name} — Complete Travel Intelligence Report

{visa_info}

---

### 🏨 Where to Stay in {dest_name}

{hotel_table}

**Booking tip:** Book 4–8 weeks ahead for the best rates. Use **Booking.com** for free cancellation options or **Agoda** for better Asia rates.

---

### 🍽️ Where to Eat — Real Local Recommendations

{rest_table}

**Insider tip:** Always check Google Maps for the local neighborhood "hidden gem" — filter by 4.7★+ with 200+ reviews.

---

### 🚇 Getting Around {dest_name}

{trans_table}

{currency_tip}

---

### 🗺️ Must-Do in {dest_name}

{attractions_list}

---

### 💰 Budget Guide

{budget_table}

**Breakdown estimate** ({timeline or "7 days"}, mid-range):
- Flights: Research via **Google Flights** (set price alerts 60 days ahead)
- Accommodation: Check rates above × number of nights
- Food: Budget 20–30% of accommodation cost
- Activities: Budget AED/THB/¥ equivalent of $20–50/day
- Travel insurance: **World Nomads** or **SafetyWing** (~$50–80/week)

---

✅ **Take Action Now**
1. Check visa requirements for {dest_name} at your country's official foreign affairs site
2. Set a Google Flights price alert for {dest_name} — book when price drops
3. Book your first 3 nights of accommodation (hotels fill fast, especially on weekends)"""

    @staticmethod
    def _career_learning_expert_fallback(objective: str, subject: str, timeline: str, entities: dict) -> str:
        subj = subject.lower() if subject else objective.lower()
        subj_title = subject.title() if subject else "Your Field"
        timeline_note = f" in {timeline}" if timeline else " in 6–12 months"

        # Subject-specific real resources
        if any(term in subj for term in ("data science", "data scientist", "machine learning", "ml", "ai")):
            phase1 = [
                ("Python Programming", "6–8 weeks", "2h/day", "CS50P (Harvard/edX, FREE)", "YouTube: Corey Schafer Python Tutorial"),
                ("Statistics & Probability", "4–6 weeks", "1.5h/day", "Khan Academy Statistics (FREE)", "Book: 'Statistics' by Freedman, Pisani & Purves"),
                ("SQL & Databases", "3–4 weeks", "1h/day", "Mode Analytics SQL Tutorial (FREE)", "Book: 'Learning SQL' by Alan Beaulieu"),
            ]
            phase2 = [
                ("Pandas & NumPy", "4 weeks", "2h/day", "Kaggle's Pandas course (FREE)", "YouTube: Corey Schafer Pandas"),
                ("Data Visualization", "2–3 weeks", "1h/day", "Seaborn/Matplotlib documentation + Kaggle Learn", "YouTube: Kimberly Fessel"),
                ("Machine Learning", "8–12 weeks", "2h/day", "Andrew Ng's ML Specialization on Coursera ($49/month)", "Book: 'Hands-On ML' by Aurélien Géron — ESSENTIAL"),
            ]
            phase3 = [
                ("Deep Learning", "8 weeks", "2h/day", "fast.ai Practical Deep Learning (FREE, world's best)", "YouTube: Andrej Karpathy Neural Networks"),
                ("MLOps & Deployment", "4 weeks", "1.5h/day", "MLflow + FastAPI + Docker — hands-on projects", "Course: 'MLOps Zoomcamp' by DataTalks.Club (FREE)"),
                ("Kaggle Competitions", "Ongoing", "1h/day", "Start with Getting Started competitions", "Join: Discord servers — DataTalks, Kaggle community"),
            ]
            certs = [
                ("Google Professional Data Engineer", "~$200 exam", "Industry-respected, practical GCP skills"),
                ("IBM Data Science Professional Certificate", "~$300 total (Coursera)", "Great for beginners, portfolio builder"),
                ("AWS Certified Machine Learning – Specialty", "~$300 exam", "High-value for ML engineering roles"),
                ("TensorFlow Developer Certificate", "$100", "From Google, validates practical deep learning skills"),
            ]
            projects = [
                ("House Price Prediction", "Week 4–6", "Regression, feature engineering, EDA — Kaggle dataset"),
                ("Customer Churn Analysis", "Week 8–10", "Classification + business framing — Telco dataset"),
                ("NLP Sentiment Analyzer", "Week 12–14", "NLP, transformers, HuggingFace — IMDB dataset"),
                ("End-to-End ML Pipeline", "Week 16–20", "FastAPI + MLflow + Docker + Railway deployment"),
                ("Kaggle Competition Entry", "Week 20+", "Real competition, real ranking — TITANIC or Tabular Playground"),
            ]
            salary_ranges = [
                ("Junior Data Scientist (0–2 yrs)", "$70,000–$95,000", "US avg; $60–80K UK; €50–70K Europe"),
                ("Mid-Level Data Scientist (2–5 yrs)", "$95,000–$140,000", "US avg; FAANG pays $150–200K"),
                ("Senior Data Scientist (5+ yrs)", "$140,000–$200,000+", "US avg; Staff level at Google/Meta: $250K+"),
                ("ML Engineer (highly valued)", "$120,000–$180,000", "MLOps skills command premium over pure data science"),
            ]
            top_youtube = [
                ("Andrej Karpathy", "Neural networks, LLMs from scratch — gold standard"),
                ("3Blue1Brown", "Mathematical intuition for ML/stats — beautifully explained"),
                ("Sentdex", "Python + ML tutorials, practical projects"),
                ("StatQuest with Josh Starmer", "Statistics made visual and intuitive — essential"),
                ("Krish Naik", "End-to-end ML projects with deployment — very practical"),
            ]
            jobs_companies = [
                ("Google DeepMind", "Research + applied ML — extremely selective"),
                ("Stripe", "Data-driven fintech — great ML culture"),
                ("Airbnb", "Search ranking, pricing models — world-class DS team"),
                ("McKinsey QuantumBlack", "Consulting + ML — strategy + tech blend"),
                ("Startups via AngelList", "Faster growth, broader scope, equity upside"),
            ]
            subj_title = "Data Scientist"

        elif "web dev" in subj or "frontend" in subj or "react" in subj or "javascript" in subj or "full stack" in subj:
            phase1 = [
                ("HTML & CSS Fundamentals", "3–4 weeks", "2h/day", "The Odin Project (FREE — best structured web curriculum)", "MDN Web Docs — bookmark this forever"),
                ("JavaScript Core", "6–8 weeks", "2h/day", "javascript.info (FREE — definitive JS resource)", "Book: 'Eloquent JavaScript' by Marijn Haverbeke (free online)"),
                ("Git & Command Line", "1–2 weeks", "1h/day", "The Odin Project Git section (FREE)", "YouTube: The Net Ninja Git Tutorial"),
            ]
            phase2 = [
                ("React", "6–8 weeks", "2h/day", "React Official Docs beta.react.dev (NEW — best ever)", "YouTube: Jack Herrington, Theo Browne (t3.gg)"),
                ("Node.js + Express / Next.js", "4–6 weeks", "2h/day", "The Odin Project Node.js section + Next.js docs", "YouTube: Traversy Media, Fireship"),
                ("Databases: PostgreSQL + Prisma", "3–4 weeks", "1.5h/day", "Execute Program (paid) + official Prisma docs", "YouTube: PlanetScale, Neon.tech tutorials"),
            ]
            phase3 = [
                ("TypeScript", "3–4 weeks", "1.5h/day", "Total TypeScript by Matt Pocock ($300, worth every dollar)", "YouTube: Matt Pocock free content on YouTube"),
                ("Testing: Vitest + Playwright", "2 weeks", "1h/day", "Vitest docs + Playwright docs (both FREE)", "Course: Testing JavaScript by Kent C. Dodds"),
                ("Deployment: Vercel + Railway", "1 week", "1h/day", "Vercel docs + Railway.app docs (both FREE)", "Deploy your portfolio site immediately"),
            ]
            certs = [
                ("Meta Front-End Developer Certificate", "~$300 (Coursera)", "Industry-recognized, builds React portfolio"),
                ("AWS Certified Developer – Associate", "~$300 exam", "Valuable for full-stack → cloud path"),
                ("Google UX Design Certificate", "~$300 (Coursera)", "Useful complement for frontend devs"),
            ]
            projects = [
                ("Portfolio Website", "Week 2–4", "HTML/CSS/JS — your professional home on the web"),
                ("Weather App with API", "Week 6–8", "React + public API — fetching real data"),
                ("Full-Stack Expense Tracker", "Week 10–14", "React + Next.js + PostgreSQL + Auth — complete app"),
                ("SaaS Clone (Trello/Notion)", "Week 16–22", "Production-level complexity — real-world challenge"),
                ("Open Source Contribution", "Week 20+", "GitHub — find a Next.js or shadcn/ui issue to fix"),
            ]
            salary_ranges = [
                ("Junior Frontend Developer (0–2 yrs)", "$60,000–$85,000", "US avg; London £45–55K"),
                ("Mid-Level Full-Stack Developer (2–5 yrs)", "$90,000–$130,000", "US avg; EU: €60–90K"),
                ("Senior Full-Stack Developer (5+ yrs)", "$130,000–$180,000+", "US avg; FAANG: $200–300K"),
                ("Freelance / Contractor", "$75–150/hour", "After 2+ yrs experience, strong portfolio"),
            ]
            top_youtube = [
                ("Fireship", "Fast-paced, high-quality web dev explainers — essential"),
                ("Theo Browne (t3.gg)", "Modern TypeScript, Next.js, full-stack — opinionated and practical"),
                ("Kevin Powell", "CSS king — best CSS education on YouTube"),
                ("Jack Herrington", "React patterns, advanced topics — excellent"),
                ("The Net Ninja", "Comprehensive beginner-to-intermediate tutorials"),
            ]
            jobs_companies = [
                ("Vercel", "Work on Next.js itself — React ecosystem leader"),
                ("Shopify", "Massive scale, React/TypeScript, great engineering culture"),
                ("Linear", "Modern tooling, great engineering — elite small team"),
                ("Stripe", "Premium engineering culture, great docs team"),
                ("Remote via Toptal/Turing", "Premium freelance rates, vetted network"),
            ]
            subj_title = "Full-Stack Web Developer"

        elif "python" in subj:
            phase1 = [
                ("Python Syntax & Fundamentals", "4–6 weeks", "2h/day", "CS50P by Harvard (edX, FREE) — best Python course period", "Python.org official tutorial"),
                ("OOP & Data Structures", "4 weeks", "2h/day", "Real Python (realpython.com) — premium quality FREE articles", "YouTube: Corey Schafer OOP series"),
                ("File I/O, APIs, JSON", "2 weeks", "1h/day", "Real Python REST API tutorials", "requests library docs + httpx"),
            ]
            phase2 = [
                ("Testing with pytest", "2 weeks", "1h/day", "pytest docs + 'Python Testing with pytest' by Brian Okken", "YouTube: ArjanCodes testing videos"),
                ("Web: FastAPI or Django", "6 weeks", "2h/day", "FastAPI docs (best API framework docs ever written)", "Django Girls tutorial for beginners"),
                ("Databases: SQLAlchemy + PostgreSQL", "3 weeks", "1.5h/day", "SQLAlchemy 2.0 docs + pgAdmin", "YouTube: ArjanCodes SQLAlchemy series"),
            ]
            phase3 = [
                ("Async Python", "2 weeks", "1h/day", "asyncio docs + 'Python Concurrency with asyncio' by Matthew Fowler", "YouTube: Łukasz Langa async talks"),
                ("Packaging & CLI Tools", "1–2 weeks", "1h/day", "Poetry (python-poetry.org) + Typer docs", "PyPA packaging guide"),
                ("Docker + Deployment", "2 weeks", "1h/day", "Docker docs + Railway/Render for Python hosting", "Full Stack FastAPI tutorial on GitHub"),
            ]
            certs = [
                ("PCEP – Certified Entry-Level Python Programmer", "$59", "Good for beginners to validate fundamentals"),
                ("PCPP – Certified Professional Python Programmer", "$295", "Mid-level professional validation"),
                ("AWS Developer Associate", "~$300", "Valuable for Python backend / cloud engineers"),
            ]
            projects = [
                ("CLI Task Manager", "Week 3–5", "File I/O, argparse — solid foundation project"),
                ("REST API with FastAPI", "Week 7–10", "FastAPI + PostgreSQL + JWT auth — portfolio piece"),
                ("Web Scraper → Data Pipeline", "Week 11–13", "BeautifulSoup4 + pandas + SQLite — real data project"),
                ("Telegram/Discord Bot", "Week 14–16", "python-telegram-bot or discord.py — practical automation"),
                ("Full SaaS Backend", "Week 17–24", "FastAPI + SQLAlchemy + Celery + Redis + Docker"),
            ]
            salary_ranges = [
                ("Junior Python Developer (0–2 yrs)", "$65,000–$90,000", "US avg; UK £40–55K; EU €45–65K"),
                ("Mid-Level Python Developer (2–5 yrs)", "$90,000–$130,000", "US avg; Backend focus commands premium"),
                ("Senior Python Engineer (5+ yrs)", "$130,000–$175,000+", "Data/ML Python eng roles pay highest"),
            ]
            top_youtube = [
                ("ArjanCodes", "Clean Python, design patterns, architecture — elite quality"),
                ("Corey Schafer", "Complete Python from scratch — most thorough beginner series"),
                ("mCoding", "Deep Python internals, CPython — for the curious engineer"),
                ("Real Python (YouTube)", "Practical Python tips and projects"),
                ("Tech With Tim", "Python projects, game dev, ML — great variety"),
            ]
            jobs_companies = [
                ("Any backend-heavy startup", "Python is the #1 backend language for startups"),
                ("Data engineering at Spotify/Netflix", "Python + Spark + data pipelines at scale"),
                ("DevOps automation (Ansible, infra)", "Python scripting pays well"),
                ("Freelance on Upwork/Toptal", "Python automation scripts, $50–100+/hour after 1 yr"),
            ]
            subj_title = "Python Developer"

        else:
            # Generic but real
            phase1 = [
                (f"{subj_title} Foundations", "4–6 weeks", "2h/day", "Search 'best {subj_title} course 2024' on Reddit r/learnprogramming", "Check Coursera, edX, or Udemy top-rated courses"),
                ("Core Skills Practice", "4–6 weeks", "1.5h/day", "Official documentation is always best", "YouTube: search 'freeCodeCamp {subject}'"),
                ("Tools & Environment Setup", "1 week", "1h/day", "VS Code + GitHub + relevant package managers", "Follow official getting-started guides"),
            ]
            phase2 = [
                ("Intermediate Concepts", "6–8 weeks", "2h/day", "Projects beat tutorials — build something real", "Join relevant Discord/Slack community"),
                ("Practical Projects", "4–6 weeks", "2h/day", "1 project beats 10 tutorial completions", "Share on GitHub and get code reviews"),
            ]
            phase3 = [
                ("Advanced Topics", "4–6 weeks", "2h/day", "Contribute to open source in your domain", "Attend local meetups or online conferences"),
                ("Portfolio & Job Search", "Ongoing", "2h/day", "LinkedIn, GitHub, personal website", "Apply to 5+ positions per week"),
            ]
            certs = [
                (f"{subj_title} Professional Certificate", "~$200–300", "Check Coursera, edX for domain-specific options"),
                ("Cloud Certification (AWS/GCP/Azure)", "~$300", "Adds significant value to most tech roles"),
            ]
            projects = [
                (f"Beginner {subj_title} Project", "Week 4–6", "Something you can show others"),
                (f"Intermediate {subj_title} Project", "Week 10–14", "Solves a real problem"),
                (f"Portfolio Capstone", "Week 18–24", "Production-quality showcase project"),
            ]
            salary_ranges = [
                (f"Junior {subj_title} (0–2 yrs)", "$55,000–$80,000", "US avg; varies significantly by location"),
                (f"Mid-Level {subj_title} (2–5 yrs)", "$80,000–$120,000", "With solid portfolio and specialization"),
                (f"Senior {subj_title} (5+ yrs)", "$120,000–$180,000+", "Leadership + deep expertise commands premium"),
            ]
            top_youtube = [
                ("freeCodeCamp", "Comprehensive tutorials across all tech topics"),
                ("Traversy Media", "Practical project-based learning"),
                ("Fireship", "Fast, high-quality tech explainers"),
            ]
            jobs_companies = [
                ("LinkedIn Jobs", "Filter by role, location, experience level"),
                ("AngelList / Wellfound", "Best for startup opportunities"),
                ("Remote OK / We Work Remotely", "Remote-first positions globally"),
            ]

        # Build the response
        def phase_rows(phases):
            rows = "| Topic | Duration | Daily Time | Best Resource | Supplement |\n|---|---|---|---|---|\n"
            for p in phases:
                rows += f"| **{p[0]}** | {p[1]} | {p[2]} | {p[3]} | {p[4]} |\n"
            return rows

        cert_rows = "| Certification | Cost | Value |\n|---|---|---|\n"
        for c in certs:
            cert_rows += f"| **{c[0]}** | {c[1]} | {c[2]} |\n"

        proj_rows = "| Project | Timeline | Skills Demonstrated |\n|---|---|---|\n"
        for p in projects:
            proj_rows += f"| **{p[0]}** | {p[1]} | {p[2]} |\n"

        sal_rows = "| Level | Salary (USD) | Notes |\n|---|---|---|\n"
        for s in salary_ranges:
            sal_rows += f"| **{s[0]}** | {s[1]} | {s[2]} |\n"

        yt_rows = "| Channel | Why Watch |\n|---|---|\n"
        for yt in top_youtube:
            yt_rows += f"| **{yt[0]}** | {yt[1]} |\n"

        job_rows = "| Company / Platform | Why |\n|---|---|\n"
        for j in jobs_companies:
            job_rows += f"| **{j[0]}** | {j[1]} |\n"

        return f"""## 🚀 Become a {subj_title}{timeline_note} — Complete Expert Roadmap

---

### 📚 Phase 1: Foundations (Weeks 1–8)

{phase_rows(phase1)}

---

### 🛠️ Phase 2: Core Mastery (Weeks 9–18)

{phase_rows(phase2)}

---

### 🚀 Phase 3: Advanced & Job-Ready (Weeks 19–26+)

{phase_rows(phase3)}

---

### 🎓 Certifications Worth Earning

{cert_rows}

---

### 💼 Portfolio Projects (Build These — In This Order)

{proj_rows}

**Project strategy:** Build in public. Post each project on GitHub + LinkedIn. Write a blog post about what you built and what you learned. This creates compounding visibility.

---

### 💰 Real Salary Ranges for {subj_title}

{sal_rows}

**Negotiation tip:** Research your specific city on levels.fyi (tech) or Glassdoor. Always negotiate — 90% of first offers have 10–20% headroom.

---

### 📺 Top YouTube Channels — Curated

{yt_rows}

---

### 🏢 Where to Find Your First Role

{job_rows}

---

### ⏱️ Weekly Study Schedule Template

| Day | Activity | Duration |
|---|---|---|
| Monday | New concept / video lecture | 2h |
| Tuesday | Practice exercises / coding | 2h |
| Wednesday | Project work | 2h |
| Thursday | Project work continued | 2h |
| Friday | Revision + flashcards | 1.5h |
| Saturday | Full project sprint | 3–4h |
| Sunday | Review week + plan next week | 1h |

---

✅ **Take Action Now**
1. **Today:** Enroll in the Phase 1 top-rated resource (free options listed above) — don't delay
2. **This week:** Set up your GitHub profile and create a repo for your first project
3. **This month:** Join the relevant Discord/Reddit community and introduce yourself — accountability is everything"""

    @staticmethod
    def _coding_expert_fallback(objective: str, subject: str, entities: dict) -> str:
        app_name = subject.title() if subject else "Your Application"
        stack = entities.get("tech_stack", "React + FastAPI + PostgreSQL + Docker")

        return f"""## 💻 {app_name} — Complete Engineering Blueprint

**Recommended Stack:** {stack}
**Architecture Pattern:** Monorepo with API-first design

---

### 📁 Folder Structure

```
{app_name.lower().replace(' ', '-')}/
├── frontend/                    # Next.js 14 (App Router)
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── api/                 # Next.js API routes (BFF layer)
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── forms/
│   │   └── layouts/
│   ├── lib/
│   │   ├── api.ts              # API client (axios/fetch wrapper)
│   │   ├── auth.ts             # Auth helpers
│   │   └── utils.ts
│   └── package.json
│
├── backend/                     # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       └── [domain].py
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   └── database.py      # SQLAlchemy 2.0 async engine
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # Business logic layer
│   │   ├── repositories/        # Data access layer
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml           # Local dev: postgres + redis + backend + frontend
├── .env.example
└── README.md
```

---

### 🗄️ Database Schema

```sql
-- PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name   TEXT,
    avatar_url  TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Core domain table (adapt to your app)
CREATE TABLE items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    metadata    JSONB DEFAULT '{{}}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_items_status ON items(status);

-- Refresh tokens for JWT security
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 🔌 API Endpoints

```
Authentication
  POST   /api/v1/auth/register         Register new user
  POST   /api/v1/auth/login            Login → returns access + refresh tokens
  POST   /api/v1/auth/refresh          Refresh access token
  POST   /api/v1/auth/logout           Revoke refresh token
  GET    /api/v1/auth/me               Get current user profile

Users
  GET    /api/v1/users/{{id}}           Get user by ID
  PATCH  /api/v1/users/{{id}}           Update user profile
  DELETE /api/v1/users/{{id}}           Delete account (soft delete)

Core Domain
  GET    /api/v1/items                  List items (paginated, filterable)
  POST   /api/v1/items                  Create item
  GET    /api/v1/items/{{id}}           Get item by ID
  PATCH  /api/v1/items/{{id}}           Update item
  DELETE /api/v1/items/{{id}}           Archive item

Health
  GET    /health                        Health check (uptime, DB status)
```

---

### 🔐 Authentication Strategy

**Technology:** JWT (access tokens, 15-min expiry) + Refresh Tokens (30-day, stored in HttpOnly cookies)

**Libraries:**
- `python-jose[cryptography]` — JWT encoding/decoding
- `passlib[bcrypt]` — Password hashing (bcrypt, cost factor 12)
- `fastapi-jwt-auth` or custom implementation

**Security checklist:**
- [ ] Passwords hashed with bcrypt (min cost 12)
- [ ] Access tokens short-lived (15 minutes)
- [ ] Refresh tokens in HttpOnly, SameSite=Strict cookies
- [ ] Rate limiting on /auth/login (max 5 attempts/15min — use slowapi)
- [ ] CORS configured for your domain only
- [ ] HTTPS enforced in production

---

### 🚀 Deployment Stack

| Layer | Technology | Cost | Why |
|---|---|---|---|
| **Frontend** | Vercel | Free / $20/month | Zero-config Next.js, edge CDN |
| **Backend** | Railway.app | ~$5–20/month | Docker deploy, built-in PostgreSQL |
| **Database** | PostgreSQL via Railway | Included | Or Neon.tech for serverless |
| **Cache** | Redis via Upstash | Free–$10/month | Serverless Redis, great free tier |
| **File Storage** | Cloudflare R2 | ~$0.015/GB | S3-compatible, zero egress fees |
| **Monitoring** | Sentry (free tier) | Free | Error tracking + performance |
| **CI/CD** | GitHub Actions | Free (public) | Auto-deploy on push to main |

---

### 🧪 Testing Strategy

```python
# pytest + httpx for FastAPI testing

# Unit test example
def test_user_creation():
    user = UserService.create(email="test@example.com", password="SecurePass123!")
    assert user.email == "test@example.com"
    assert user.id is not None
    assert user.password_hash != "SecurePass123!"  # Must be hashed

# Integration test example  
async def test_login_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={{
        "email": "test@example.com",
        "password": "SecurePass123!"
    }})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Coverage target:** 80%+ for business logic layer, 60%+ overall

---

✅ **Take Action Now**
1. Run `npx create-next-app@latest frontend --typescript --app --tailwind` to scaffold frontend
2. Run `pip install fastapi uvicorn sqlalchemy alembic pydantic-settings python-jose passlib httpx pytest` for backend dependencies
3. Create your `docker-compose.yml` with PostgreSQL + Redis — this unblocks all local development"""

    @staticmethod
    def _business_expert_fallback(objective: str, subject: str, entities: dict) -> str:
        biz = subject.title() if subject else "Your Business"
        return f"""## 🏢 {biz} — Business Intelligence Report

### 🔍 SWOT Analysis

| | **Helpful** | **Harmful** |
|---|---|---|
| **Internal (You control)** | **Strengths:** Define what YOU do better than anyone else — speed, pricing, niche expertise, team | **Weaknesses:** Gaps in funding, team skills, tech infrastructure, or market knowledge |
| **External (You don't control)** | **Opportunities:** Market gaps, competitor weakness, regulatory changes, tech shifts (AI) | **Threats:** Established competitors, economic conditions, regulatory risk, talent market |

---

### 💰 Revenue Models — Choose Your Weapon

| Model | Best For | Example | Avg Margins |
|---|---|---|---|
| **SaaS Subscription** | Software, tools, platforms | Notion: $8–20/user/month | 70–85% |
| **Marketplace (% fee)** | Two-sided platforms | Stripe: 2.9% + $0.30 | 20–40% |
| **Service Retainer** | Consulting, agencies | $3,000–10,000/month | 50–70% |
| **Usage-Based** | API, AI, infrastructure | Anthropic: per token | 60–80% |
| **One-Time + Upsell** | Products, courses | $997 course + $97/month community | 80–90% |

---

### 📊 Unit Economics Framework

```
Customer Acquisition Cost (CAC) = Total Sales & Marketing Spend / New Customers Acquired

Lifetime Value (LTV) = Average Revenue Per User × Gross Margin × Average Customer Lifespan

LTV:CAC Ratio targets:
  < 1:1 = Losing money on every customer (fix pricing or reduce CAC)
  3:1   = Healthy, sustainable business
  5:1+  = Excellent — scale aggressively
  
Payback Period = CAC / (Monthly Revenue per Customer × Gross Margin)
Target: < 12 months for SaaS, < 6 months for high-velocity businesses
```

---

### 🚀 Go-To-Market Strategy

**Phase 1 — First 100 Customers (Month 1–3):**
- Cold outreach on LinkedIn (50 personalized DMs/day) — 2–5% conversion typical
- Post in relevant communities: Reddit, Hacker News Show HN, Product Hunt
- Build in public on Twitter/X — share your journey, attract early adopters
- Offer founding member pricing (50% off forever) for first 100 — creates urgency

**Phase 2 — Scalable Acquisition (Month 3–9):**
- Content marketing: 2 SEO posts/week targeting problem-aware keywords
- Partnerships with complementary tools (integration partnerships)
- Referral program: 30% commission for 12 months — viral loops
- Paid ads: Start with $500/month Google Ads on high-intent keywords

**Phase 3 — Growth (Month 9+):**
- Hire first sales rep when CAC:LTV is proven
- Enterprise tier with dedicated support
- Channel partnerships and resellers

---

✅ **Take Action Now**
1. Interview 10 potential customers this week — ask "what's the most painful part of [problem]?" not "would you use this?"
2. Build a 1-page landing page today (use Framer or Webflow) and collect emails before building anything
3. Set your target metrics: MRR goal for Month 6, target CAC, target churn rate"""

    @staticmethod
    def _fitness_expert_fallback(objective: str, entities: dict) -> str:
        goal = entities.get("goal", objective)
        timeline = entities.get("timeline", "12 weeks")
        weight = entities.get("weight", "")
        weight_note = f" (Current weight: {weight})" if weight else ""

        return f"""## 💪 Fitness Plan: {goal.title()}{weight_note}

**Program:** Evidence-based periodized training + nutrition protocol
**Duration:** {timeline}

---

### 🏋️ Training Program — 5/3/1 BBB Variant (Proven, Scalable)

**Training Split: 4 days/week**

| Day | Focus | Main Lift | Accessory Work |
|---|---|---|---|
| **Monday** | Push | Bench Press 5/3/1 | 5×10 OHP, 3×12 Tricep Pushdowns, 3×15 Lateral Raises |
| **Tuesday** | Pull | Deadlift 5/3/1 | 5×10 Barbell Rows, 3×12 Pull-Ups, 3×15 Face Pulls |
| **Thursday** | Push | OHP 5/3/1 | 5×10 Bench Press, 3×12 Dips, 3×15 DB Flyes |
| **Friday** | Pull/Legs | Squat 5/3/1 | 5×10 Romanian Deadlifts, 3×15 Leg Curls, 4×12 Calf Raises |

**5/3/1 Wave Structure (4-week cycles):**
- Week 1: 3×5 @ 65%, 75%, 85% 1RM (+ AMRAP final set)
- Week 2: 3×3 @ 70%, 80%, 90% 1RM (+ AMRAP final set)
- Week 3: 5/3/1 @ 75%, 85%, 95% 1RM (+ AMRAP final set)
- Week 4: Deload — 3×5 @ 40%, 50%, 60% 1RM

---

### 🥗 Nutrition Protocol

**Calorie Targets (adjust based on results every 2 weeks):**

| Goal | Formula | Example (80kg person) |
|---|---|---|
| **Fat Loss** | Body weight (kg) × 26–28 kcal | 80kg → 2,080–2,240 kcal/day |
| **Muscle Gain** | Body weight (kg) × 33–36 kcal | 80kg → 2,640–2,880 kcal/day |
| **Maintenance/Recomp** | Body weight (kg) × 29–32 kcal | 80kg → 2,320–2,560 kcal/day |

**Macro Split:**
- **Protein:** 2.0–2.2g per kg body weight (PRIORITY #1 — non-negotiable)
- **Carbohydrates:** Remaining calories after protein and fat
- **Fat:** Minimum 0.8g per kg body weight (hormonal health)

**Sample Day (80kg, fat loss, 2,200 kcal):**

| Meal | Food | Protein | Calories |
|---|---|---|---|
| **Breakfast 7am** | 4 eggs + 200g Greek yogurt + 30g oats | 45g | 480 kcal |
| **Pre-Workout 12pm** | 150g chicken breast + 150g rice + vegetables | 40g | 520 kcal |
| **Post-Workout 4pm** | Protein shake (whey) + 1 banana | 30g | 280 kcal |
| **Dinner 7pm** | 200g salmon + 200g sweet potato + salad | 45g | 600 kcal |
| **Evening** | 200g cottage cheese + 15g almonds | 30g | 320 kcal |
| **Total** | | **~190g** | **2,200 kcal** |

---

### 💊 Evidence-Based Supplements Only

| Supplement | Dose | Timing | Evidence Level |
|---|---|---|---|
| **Creatine Monohydrate** | 5g/day | Any time (consistency > timing) | ⭐⭐⭐⭐⭐ Strongest evidence |
| **Whey Protein** | 25–30g/serving | Post-workout or to hit daily protein | ⭐⭐⭐⭐⭐ Highly effective |
| **Vitamin D3** | 2,000–4,000 IU/day | With fatty meal | ⭐⭐⭐⭐ Most people deficient |
| **Omega-3 (Fish Oil)** | 2–3g EPA+DHA/day | With meal | ⭐⭐⭐⭐ Anti-inflammatory |
| **Caffeine** | 3–6mg/kg 30min pre-workout | Pre-workout only | ⭐⭐⭐⭐ Performance boost |
| **Magnesium Glycinate** | 200–400mg | Before bed | ⭐⭐⭐ Sleep + recovery |

**Skip:** BCAAs (redundant if protein is sufficient), fat burners (mostly caffeine + stimulants), most pre-workouts (just take caffeine separately).

---

### 📊 12-Week Progress Milestones

| Milestone | Week 4 | Week 8 | Week 12 |
|---|---|---|---|
| **Body weight** | -1 to -2kg | -2 to -4kg | -4 to -6kg (fat loss) |
| **Strength (Bench)** | +5kg 1RM | +10kg 1RM | +15–20kg 1RM |
| **Strength (Squat)** | +7.5kg 1RM | +15kg 1RM | +20–30kg 1RM |
| **Body measurements** | -1–2cm waist | -2–4cm waist | -4–6cm waist |

**Tracking apps:** MyFitnessPal (nutrition) + Strong app (workout logging) — both free

---

✅ **Take Action Now**
1. Calculate your TDEE at tdee.com and set your calorie target for this week
2. Buy creatine monohydrate today (Myprotein or Bulk — cheapest reputable brands)
3. Log your starting measurements: weight, waist, hips, arms — photo too (you'll want this in 12 weeks)"""

    @staticmethod
    def _finance_expert_fallback(objective: str, entities: dict) -> str:
        return f"""## 💰 Personal Finance & Investment Plan

---

### 📊 Priority Order (Follow This Exactly)

```
1. Emergency Fund → 3–6 months expenses in high-yield savings (HYSA: 4.5–5.0% APY)
   → Use: Marcus by Goldman Sachs, Ally Bank, or SoFi

2. Employer 401k Match → Contribute at LEAST enough to get full employer match
   → This is an INSTANT 50–100% return — never leave free money

3. Pay Off High-Interest Debt → Anything >7% interest — avalanche method
   → Credit cards (18–26% APR) FIRST, always

4. Max Roth IRA → $7,000/year limit (2024), tax-free growth forever
   → Open at: Fidelity (zero-fee funds), Vanguard, or Charles Schwab

5. Max 401k → $23,000/year limit (2024)
   → Target: 15% total income including employer match

6. Taxable Brokerage → After all above maximized
   → Fidelity or Schwab (zero commissions, fractional shares)
```

---

### 📈 Investment Allocation (Bogleheads 3-Fund Portfolio)

**Aggressive (Age < 35):**
| Fund | Allocation | Expense Ratio |
|---|---|---|
| US Total Stock Market (VTI) | 60% | 0.03% |
| International Stock (VXUS) | 30% | 0.07% |
| US Bond Market (BND) | 10% | 0.03% |

**Moderate (Age 35–50):**
| Fund | Allocation | Expense Ratio |
|---|---|---|
| US Total Stock Market (VTI) | 50% | 0.03% |
| International Stock (VXUS) | 25% | 0.07% |
| US Bond Market (BND) | 25% | 0.03% |

**Why this strategy:** S&P 500 historical average return ~10%/year (7% inflation-adjusted). Diversification + low fees = highest probability of long-term wealth building. Warren Buffett's recommendation for 90% of investors.

---

### 🏦 Best Brokers & Accounts

| Purpose | Best Option | Why |
|---|---|---|
| **Roth IRA / Taxable** | Fidelity | Zero-fee index funds, no minimums, best research |
| **401k (employer)** | Use employer's plan | Get the match first — then optimize |
| **International Stocks** | Interactive Brokers | Best for non-US investors, multi-currency |
| **Crypto (if allocating)** | Coinbase Pro / Kraken | Lowest fees for regular crypto purchases |
| **Emergency Fund HYSA** | Marcus by Goldman Sachs | 4.5–5.0% APY (2024 rates) |

---

### ⚡ The Compound Interest Reality Check

| Monthly Investment | After 10 Years | After 20 Years | After 30 Years |
|---|---|---|---|
| $500/month | ~$103,000 | ~$294,000 | ~$680,000 |
| $1,000/month | ~$206,000 | ~$588,000 | ~$1.36M |
| $2,000/month | ~$411,000 | ~$1.17M | ~$2.72M |

*Assuming 8% average annual return (conservative S&P 500 estimate)*

---

✅ **Take Action Now**
1. Open a Fidelity account today (10 minutes) — start with $1 if needed, just open it
2. Calculate your monthly budget using the 50/30/20 rule (50% needs, 30% wants, 20% savings/investing)
3. Automate your investments — set up automatic monthly transfers on payday (automation beats willpower)"""

    @staticmethod
    def _general_expert_fallback(objective: str, domain: str, operations: list[dict], entities: dict) -> str:
        ops_content = []
        for i, op in enumerate(operations, 1):
            ops_content.append(f"### {i}. {op.get('title', f'Step {i}')}\n\n{op.get('description', '')}\n\n*Why this matters:* {op.get('why_this', '')}")

        return f"""## ⚡ {objective.title()}

**Domain:** {domain.replace('_', ' ').title()}
**Approach:** Expert-guided execution plan

---

{chr(10).join(ops_content)}

---

✅ **Take Action Now**
1. Start with the first operation above — complete it before moving to the next
2. Document your progress and decisions as you go
3. Review your results after each operation and adjust accordingly"""
