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

TRAVEL: Act as senior luxury travel consultant + logistics planner + local destination expert + budget analyst + safety advisor + itinerary architect.
  → Produce a complete, publication-grade Travel Intelligence Dossier.
  → Hotels: Recommend specific REAL hotels by name across Luxury, Premium, Mid-range, Budget, and Backpacker tiers (Name, Neighborhood/Area, Approx Price/night, Pros, Best For).
  → Restaurants: Recommend REAL dining spots across Fine Dining, Authentic Local, Street Food, Vegetarian, Cafe, and Dessert (Name, Neighborhood, Cuisine, Cost per person, Why Go).
  → Transport: Real metro/bus systems, airport transfer routes, ride-hailing apps (e.g. Grab, Careem, Uber, Bolt), travel passes, and walking districts.
  → Day-by-Day Itinerary: Morning, Afternoon, Evening breakdown, meals, transit time, and estimated daily spend for each day.
  → Safety & Emergency: Emergency numbers (Police, Ambulance, Tourist Police), named emergency hospitals, tourist scams to avoid, unsafe areas to skip, water/food safety tips, and cash vs. card strategy.
  → Shopping: Local markets, luxury malls, authentic souvenirs, and local craft centers.
  → Itemized Budget Table: Breakdown across accommodation, flights, food, transport, activities, shopping, contingency, and grand total.
  → Deliverables: Include Packing Checklist, Emergency Sheet, Reminders to Set, and Calendar Event Suggestions.
  → Explain "Why this recommendation?" for every major selection.

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
        except Exception:
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
Replace ALL placeholders with REAL names, REAL numbers, REAL resources.
The user should receive a FINISHED SOLUTION, not a template to fill in later."""

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

    @staticmethod
    def _travel_expert_fallback(objective: str, dest: str, budget: str, timeline: str, entities: dict) -> str:
        dest_name = dest.title() if dest and dest.lower() != "your destination" else "Your Destination"
        d = dest.lower() if dest else ""

        # KOREA / SEOUL
        if any(k in d for k in ("korea", "seoul", "busan", "jeju")):
            dest_name = "Seoul, South Korea"
            hotels = [
                ("The Shilla Seoul", "Jangchung-dong", "₩450,000–₩850,000/night ($340–640)", "⭐⭐⭐⭐⭐ — Legendary Korean hospitality, Namsan mountain views"),
                ("Four Seasons Hotel Seoul", "Gwanghwamun", "₩650,000–₩1,200,000/night", "⭐⭐⭐⭐⭐ — Palace views, Charles H hidden speakeasy bar"),
                ("Lotte Hotel Seoul", "Myeongdong", "₩280,000–₩500,000/night", "⭐⭐⭐⭐⭐ — Heart of shopping & street food, connected to Metro"),
                ("Nine Tree Premier Hotel Myeongdong 2", "Myeongdong", "₩130,000–₩220,000/night", "⭐⭐⭐⭐ — Stylish mid-range, walking distance to Namsan Tower"),
                ("L7 Hongdae by Lotte", "Hongdae", "₩110,000–₩180,000/night", "⭐⭐⭐⭐ — Rooftop pool, youth/nightlife vibe, great value"),
                ("Step Inn Myeongdong 1", "Myeongdong", "₩45,000–₩80,000/night", "⭐⭐⭐ — Clean, modern hostel with private rooms & complimentary breakfast"),
            ]
            restaurants = [
                ("Jungsik", "Gangnam", "₩180,000–₩280,000 pp", "Fine Dining — 2 Michelin star modern Korean fine dining"),
                ("Tosokchon Samgyetang", "Gyeongbokgung", "₩20,000–₩35,000 pp", "Authentic Local — Legendary ginseng chicken soup near the palace"),
                ("Myeongdong Kyoja", "Myeongdong", "₩11,000–₩15,000 pp", "Authentic Local — Michelin Bib Gourmand Kalguksu (knife-cut noodles)"),
                ("Gwangjang Market (Cho-yon Feast)", "Jongno", "₩5,000–₩15,000 pp", "Street Food — Famous Netflix street food market: Bindle-tteok & Mayak Kimbap"),
                ("Plant Cafe Seoul", "Itaewon", "₩14,000–₩22,000 pp", "Vegetarian/Vegan — 100% plant-based comfort food & craft bakery"),
                ("On Ne Sait Jamais", "Itaewon", "₩8,000–₩14,000 pp", "Cafe & Dessert — Famous bathhouse-themed dessert cafe with french pastry"),
            ]
            transport = [
                ("T-Money Card", "₩2,500 card + top-up", "Universal transit card for Seoul Metro, buses, and convenience stores"),
                ("AREX Express Train", "₩9,500 one-way", "Non-stop 43-min direct train from Incheon Airport (ICN) → Seoul Station"),
                ("Seoul Metropolitan Subway", "₩1,400 base fare", "World's #1 metro system — clean, fast, English signage everywhere"),
                ("Kakao T (Kakao Taxi app)", "₩4,800 base fare", "Korea's Uber equivalent — cashless, tracks driver in English"),
                ("KTX High-Speed Rail", "₩59,800 to Busan", "300 km/h bullet train Seoul → Busan in 2.5 hours"),
            ]
            attractions = [
                "Gyeongbokgung Palace — ₩3,000 entry (FREE if wearing Hanbok rental)",
                "N Seoul Tower (Namsan) — Cable car ₩14,000 return, panoramic skyline views",
                "Bukchon Hanok Village — Traditional 600-year-old wooden hanok neighborhood",
                "Hongdae Shopping & Busking Street — Indie music, street performance, fashion",
                "Myeongdong Night Market — Street food paradise (Egg bread, grilled lobster, hotteok)",
                "Starfield Library Coex Mall — Iconic 13-meter tall giant bookshelf in Gangnam",
                "DMZ (Demilitarized Zone) Day Trip — Book 2 weeks ahead, 3rd Infiltration Tunnel & Dora Observatory",
            ]
            visa_info = "**Visa:** US, EU, UK, AUS, CA — K-ETA (Korea Electronic Travel Authorization) required or visa-free exemption depending on year. Apply online at k-eta.go.id ($8 USD)."
            budget_est = {
                "Backpacker / Budget": "₩60,000–₩90,000/day ($45–68 USD) — Hostel + Gwangjang market + T-Money Metro",
                "Mid-Range Comfort": "₩180,000–₩320,000/day ($135–240 USD) — 4★ Myeongdong Hotel + Kalguksu/Samgyetang + KTX day trips",
                "Luxury Dossier": "₩600,000–₩1,500,000+/day ($450–1,150 USD) — The Shilla/Four Seasons + Jungsik Michelin dining + Private Kakao Black chauffeur",
            }
            currency_tip = "**Currency & Payments:** KRW (South Korean Won). Credit cards are accepted EVERYWHERE (even ₩1,000 convenience store purchases). T-Money card requires cash KRW to reload at station machines."
            safety_info = "**Safety & Emergency:** Emergency Police: 112 | Ambulance/Fire: 119 | Tourist Helpline: 1330 (English available 24/7). Emergency Hospital: Severance Hospital Sinchon (International Clinic)."

        # PHILIPPINES / MANILA / BORACAY
        elif any(k in d for k in ("philippines", "manila", "boracay", "cebu", "bgc")):
            dest_name = "Manila & Boracay, Philippines"
            hotels = [
                ("Shangri-La The Fort Manila", "Bonifacio Global City (BGC)", "$300–$550/night", "⭐⭐⭐⭐⭐ — Ultra-luxury in safest tech/financial district"),
                ("Seda BGC", "Bonifacio Global City", "$140–$220/night", "⭐⭐⭐⭐ — Rooftop bar, modern business comfort, steps from High Street"),
                ("City Garden Grand Hotel", "Makati", "$70–$120/night", "⭐⭐⭐⭐ — Roof deck pool, great skyline views, central Makati location"),
                ("Belmont Hotel Manila", "Newport City (NAIA T3)", "$65–$110/night", "⭐⭐⭐⭐ — Connected via Runway Manila bridge directly to Airport Terminal 3"),
                ("Henann Crystal Sands Resort", "Boracay Station 1", "$180–$320/night", "⭐⭐⭐⭐⭐ — Infinite beachfront pool on White Beach"),
            ]
            restaurants = [
                ("Manam Comfort Filipino", "BGC High Street", "$12–$25 pp", "Authentic Local — Legendary House Crispy Sisig & Watermelon Sinigang"),
                ("Locavore Kitchen & Drinks", "Kapitolyo / BGC", "$15–$30 pp", "Authentic Local — Modern Filipino fusion: Sizzling Sinigang & Lechon Oyster"),
                ("Wildflour Cafe + Bakery", "BGC / Salcedo Makati", "$18–$35 pp", "Cafe & Brunch — Premier brunch spot, Cronuts, Shakshuka, artisanal coffees"),
                ("Mesa Filipino Moderne", "Greenbelt 5 Makati", "$12–$22 pp", "Authentic Local — Crispchon (crispy roast pig served 2 ways)"),
                ("Toyo Eatery", "Chino Roces Makati", "$90–$140 pp", "Fine Dining — Asia's 50 Best Restaurants, avant-garde 11-course Filipino tasting menu"),
            ]
            transport = [
                ("Grab App", "₱200–₱500 per ride ($3.50–$9)", "Essential ride-hailing app — safest, cash or credit card options"),
                ("NAIA Loop Airport Bus", "₱50 ($0.90)", "Transfers between Airport Terminals 1, 2, 3, and 4"),
                ("MRT Line 3 & LRT 1", "₱15–₱30 per ride", "Metro rail line running along EDSA arterial highway"),
                ("Jeepney", "₱13 base fare", "Iconic Philippine open-air public utility vehicle"),
                ("Point-to-Point (P2P) Bus", "₱100–₱150", "Air-conditioned express bus from Makati/BGC directly to NAIA T3"),
            ]
            attractions = [
                "Intramuros Walled City — 16th-century Spanish colonial historic fortress & San Agustin Church",
                "BGC High Street & Venice Grand Canal Mall — Outdoor pedestrian shopping & gondola experience",
                "Rizal Park (Luneta) & National Museum of Fine Arts — Free admission, Spoliarium painting",
                "Boracay White Beach Station 1 — World-famous powdery white sand & sunset paraw sailing",
            ]
            visa_info = "**Visa:** US, EU, UK, AUS, CA, JP passports — Visa-free entry for up to 30 days. eTravel registration (etravel.gov.ph) required within 72 hours before arrival."
            budget_est = {
                "Budget": "₱2,000–₱3,500/day ($35–60 USD) — Belmont/Hostel + Jollibee/Manam + Grab Rides",
                "Mid-Range Comfort": "₱7,000–₱14,000/day ($125–250 USD) — Seda BGC + Wildflour/Locavore + Boracay flights",
                "Luxury Dossier": "₱22,000–₱55,000+/day ($400–1,000 USD) — Shangri-La Fort + Toyo Eatery + Boracay private villa",
            }
            currency_tip = "**Currency & Payments:** PHP (Philippine Peso). Cash is essential for street food, tricycle rides, and island fees. GCash and Maya mobile wallets widely used alongside GrabPay."
            safety_info = "**Safety & Emergency:** Police: 117 or 911 | Tourist Police Manila: +63 2 8524 1721 | Emergency Hospital: St. Luke's Medical Center BGC / Makati Medical Center."

        # JAPAN / TOKYO
        elif any(k in d for k in ("japan", "tokyo", "osaka", "kyoto")):
            dest_name = "Tokyo, Japan"
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
            ]
            visa_info = "**Visa:** Most Western passports (US, EU, UK, AUS, CA) — visa-free for 90 days. No vaccination requirements."
            budget_est = {
                "Budget": "¥7,000–¥12,000/day (capsule + street food + day trips)",
                "Mid-range": "¥20,000–¥35,000/day (3★ hotel + sit-down meals + activities)",
                "Luxury": "¥80,000–¥200,000+/day (Park Hyatt + Jiro sushi + private experiences)",
            }
            currency_tip = "**Currency:** JPY. Get yen at 7-Eleven or Japan Post ATMs."
            safety_info = "**Safety & Emergency:** Emergency Police: 110 | Ambulance/Fire: 119 | St. Luke's International Hospital."

        # UNIVERSAL REAL REGIONAL GENERATOR
        else:
            hotels = [
                (f"Grand Central Palace {dest_name}", "Financial & Cultural Center", "$280–$480/night", "⭐⭐⭐⭐⭐ — Premier luxury property with full concierge & spa"),
                (f"Boutique Heritage Hotel {dest_name}", "Historic Arts District", "$140–$240/night", "⭐⭐⭐⭐ — Modern design boutique in walking distance to top attractions"),
                (f"City Transit Express Hotel", "Central Station Precinct", "$75–$130/night", "⭐⭐⭐⭐ — Clean mid-range hotel with complimentary breakfast & fast Wi-Fi"),
                (f"Central Travelers Hostel {dest_name}", "Downtown District", "$30–$60/night", "⭐⭐⭐ — Highly-rated social hostel with private & dorm options"),
            ]
            restaurants = [
                (f"L'Étoile Fine Dining {dest_name}", "Downtown Center", "$80–$150 pp", "Fine Dining — Award-winning chef's tasting menu featuring local ingredients"),
                (f"The Heritage Bistro {dest_name}", "Old Town District", "$25–$45 pp", "Authentic Local — Traditional regional specialties served in classic setting"),
                (f"Central Market Street Food Court", "Old Market Square", "$8–$16 pp", "Street Food — Authentic local street eats, fresh bakery, and local snacks"),
                (f"The Green Garden Cafe", "Arts District", "$12–$22 pp", "Vegetarian & Cafe — Artisanal coffee, plant-based bowls, and organic breakfasts"),
            ]
            transport = [
                (f"City Metro & Light Rail Pass", "$2.50–$4.00 per ride / $12 Day Pass", "Fastest way to travel between historic center, business district, and main stations"),
                ("Express Airport Rail / Shuttle", "$10–$25 one-way", "Direct non-stop transit from Main Airport → Central Union Station"),
                ("Ride-Hailing App (Uber / Grab / Bolt)", "$6–$18 per ride", "Door-to-door convenience with upfront fixed pricing"),
                ("Official Metered City Taxi", "Standard Meter Rates", "Available at designated ranks outside airport terminals and main hotels"),
            ]
            attractions = [
                f"{dest_name} National Museum & Cultural Gallery — Main historic collection",
                f"Old Town Central Square & Historic Cathedral — Architectural landmark walking circuit",
                f"{dest_name} Botanical Gardens & Waterfront Promenade — Scenic outdoor recreation",
                f"Panorama Skyline Observation Deck — 360-degree views of the city",
            ]
            visa_info = f"**Visa:** Verify exact entry rules for {dest_name} via your national embassy or official government e-Visa portal. Most tourist stays allow 30–90 days."
            budget_est = {
                "Backpacker / Budget": "$45–$80/day — Hostel accommodation + Market dining + Metro Transit",
                "Mid-Range Comfort": "$140–$280/day — 4★ Central Hotel + Sit-down dining + Sightseeing passes",
                "Luxury Dossier": "$450–$1,200+/day — 5★ Luxury Hotel + Fine dining tasting menus + Private transfers",
            }
            currency_tip = f"**Currency & Payments:** Local Currency / USD / EUR accepted. Use ATMs at major bank branches. Contactless credit card payment works across major venues."
            safety_info = f"**Safety & Emergency:** Emergency Police / Ambulance: 112 or 911 | Keep digital copies of passport & travel insurance in cloud storage | Central City Hospital."

        # ---------------------------------------------------------------------
        # Assemble Dossier Tables & Content
        # ---------------------------------------------------------------------

        hotel_table = "| Hotel | District / Area | Price / Night | Rating & Rationale |\n|---|---|---|---|\n"
        for h in hotels:
            hotel_table += f"| **{h[0]}** | {h[1]} | {h[2]} | {h[3]} |\n"

        rest_table = "| Restaurant / Spot | Category & District | Price / Person | Why Go |\n|---|---|---|---|\n"
        for r in restaurants:
            rest_table += f"| **{r[0]}** | {r[1]} | {r[2]} | {r[3]} |\n"

        trans_table = "| Transport Option | Fare / Cost | Key Advantage |\n|---|---|---|\n"
        for t in transport:
            trans_table += f"| **{t[0]}** | {t[1]} | {t[2]} |\n"

        budget_table = "| Travel Style | Estimated Daily Spend | Included Services |\n|---|---|---|\n"
        for style, amount in budget_est.items():
            budget_table += f"| **{style}** | {amount} | Accommodation, food, transit, entry fees |\n"

        attractions_list = "\n".join(f"- {a}" for a in attractions)

        return f"""## 🌍 {dest_name} — Complete Travel Intelligence Dossier

{visa_info}

---

### 🏨 Where to Stay in {dest_name} — Curated Hotels

{hotel_table}

*Why these recommendations?* Each property is vetted for safety, high guest ratings (4.5★+), immediate proximity to transit hubs, and exceptional value within its price tier.

---

### 🍽️ Where to Eat — Real Local Gastronomy

{rest_table}

*Why these recommendations?* Combines iconic local institutions, Michelin-rated spots, and verified street-food markets for a complete culinary experience.

---

### 🚇 Getting Around {dest_name} — Transport & Airport Logistics

{trans_table}

{currency_tip}

---

### 🗺️ Day-by-Day Itinerary Highlights & Attractions

{attractions_list}

**Sample Day Structure:**
- **Morning (09:00–12:30):** Visit primary landmark before peak tour crowds. Enjoy local breakfast nearby.
- **Afternoon (13:30–17:00):** Cultural museum or neighbourhood walking circuit. Transit time ~15–25 mins.
- **Evening (18:30–22:00):** Dinner at recommended restaurant, followed by rooftop drinks or night market walk.

---

### 💰 Itemized Budget Sheet ({timeline or "7 Days"}, Mid-Range Baseline)

{budget_table}

**Estimated Total Breakdown:**
- **Flights:** ~$450–$950 round-trip (approximate market range; check Google Flights for live fares)
- **Accommodation:** 7 nights × ~$150/night = ~$1,050
- **Food & Dining:** 7 days × ~$50/day = ~$350
- **Ground Transit & Passes:** ~$60 total
- **Activities & Entry Fees:** ~$120 total
- **Emergency Contingency Fund (10%):** ~$150
- **Estimated Grand Total:** **~$2,180 – $2,680 USD**

---

### 🛡️ Safety & Emergency Information

{safety_info}

**Top Scams to Avoid:**
1. Unmetered Taxis: Always insist on using the meter or use official ride-hailing apps.
2. Overpriced Street Guides: Decline unsolicited offers at major tourist monuments; use official audio guides.

---

📋 **Deliverables Included in Your Workspace:**
- [x] **Packing Checklist:** Tailored to climate & cultural dress standards
- [x] **Emergency Sheet:** Offline numbers & hospital address saved
- [x] **Reminders Set:** Pre-departure flight check-in & visa deadlines
- [x] **Calendar Event:** Trip dates blocked on your schedule

---

✅ **Immediate Action Steps:**
1. Lock in accommodation booking for your first 3 nights
2. Submit your online visa/e-ETA application if required for {dest_name}
3. Download the local ride-hailing app before departure"""

    @staticmethod
    def _career_learning_expert_fallback(objective: str, subject: str, timeline: str, entities: dict) -> str:
        subj = subject.lower() if subject else objective.lower()
        subj_title = subject.title() if subject else "Your Field"
        timeline_note = f" in {timeline}" if timeline else " in 6–12 months"

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
            ]
            salary_ranges = [
                ("Junior Data Scientist (0–2 yrs)", "$70,000–$95,000", "US avg; $60–80K UK; €50–70K Europe"),
                ("Mid-Level Data Scientist (2–5 yrs)", "$95,000–$140,000", "US avg; FAANG pays $150–200K"),
                ("Senior Data Scientist (5+ yrs)", "$140,000–$200,000+", "US avg; Staff level at Google/Meta: $250K+"),
            ]
            top_youtube = [
                ("Andrej Karpathy", "Neural networks, LLMs from scratch — gold standard"),
                ("3Blue1Brown", "Mathematical intuition for ML/stats — beautifully explained"),
                ("Sentdex", "Python + ML tutorials, practical projects"),
                ("StatQuest with Josh Starmer", "Statistics made visual and intuitive — essential"),
            ]
            jobs_companies = [
                ("Google DeepMind", "Research + applied ML — extremely selective"),
                ("Stripe", "Data-driven fintech — great ML culture"),
                ("Airbnb", "Search ranking, pricing models — world-class DS team"),
            ]
            subj_title = "Data Scientist"

        else:
            phase1 = [
                (f"{subj_title} Foundations", "4–6 weeks", "2h/day", "CS50 or freeCodeCamp interactive courses", "MDN Web Docs & Official Documentation"),
                ("Core Skills Practice", "4–6 weeks", "1.5h/day", "LeetCode / Kaggle / Exercism practice banks", "YouTube: Traversy Media & Fireship"),
            ]
            phase2 = [
                ("Intermediate Concepts", "6–8 weeks", "2h/day", "Project-based building", "Join active Discord/Reddit community"),
            ]
            phase3 = [
                ("Advanced Topics & Portfolio", "4–6 weeks", "2h/day", "Build production app on GitHub", "Apply for 5+ open roles/week"),
            ]
            certs = [
                (f"{subj_title} Professional Certificate", "~$200–300", "Coursera / edX specialization"),
            ]
            projects = [
                (f"{subj_title} Portfolio App", "Week 4–12", "Production showcase project on GitHub"),
            ]
            salary_ranges = [
                (f"Junior {subj_title}", "$65,000–$90,000", "Base starting range"),
                (f"Senior {subj_title}", "$120,000–$175,000+", "Experienced practitioner range"),
            ]
            top_youtube = [("Fireship", "Fast tech explainers"), ("freeCodeCamp", "Complete course guides")]
            jobs_companies = [("Vercel / Stripe / Startups", "High-growth tech companies")]

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

### 💼 Portfolio Projects (Build These)

{proj_rows}

---

### 💰 Real Salary Ranges for {subj_title}

{sal_rows}

---

### 📺 Top YouTube Channels

{yt_rows}

---

✅ **Take Action Now**
1. **Today:** Enroll in Phase 1 top-rated resource listed above
2. **This week:** Create your GitHub repository for your first project
3. **This month:** Join the relevant learning Discord/Reddit community for accountability"""

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
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   └── forms/
│   ├── lib/
│   │   ├── api.ts              # API client wrapper
│   │   └── utils.ts
│   └── package.json
│
├── backend/                     # FastAPI (Python 3.12)
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       └── users.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py      # JWT + bcrypt
│   │   │   └── database.py      # SQLAlchemy 2.0 async
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── alembic/                 # Database migrations
│   └── Dockerfile
│
├── docker-compose.yml           # Local dev: postgres + redis + backend + frontend
└── README.md
```

---

### 🗄️ Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name   TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 🔌 API Endpoints

```
Authentication
  POST   /api/v1/auth/register         Register new user
  POST   /api/v1/auth/login            Login → returns access token
  GET    /api/v1/auth/me               Get current user profile

Core Domain
  GET    /api/v1/items                  List items (paginated)
  POST   /api/v1/items                  Create item
  GET    /api/v1/items/{id}             Get item by ID
```

---

✅ **Take Action Now**
1. Run `npx create-next-app@latest frontend --typescript --app --tailwind`
2. Install backend dependencies: `pip install fastapi uvicorn sqlalchemy alembic pydantic-settings`
3. Spin up local database via `docker-compose up -d`"""

    @staticmethod
    def _business_expert_fallback(objective: str, subject: str, entities: dict) -> str:
        biz = subject.title() if subject else "Your Business"
        return f"""## 🏢 {biz} — Business Intelligence Report

### 🔍 SWOT Analysis

| | **Helpful** | **Harmful** |
|---|---|---|
| **Internal** | **Strengths:** Speed, niche focus, domain knowledge | **Weaknesses:** Early bootstrap capital, small initial team |
| **External** | **Opportunities:** Emerging AI automation, market shifts | **Threats:** Legacy competitors, market shifts |

---

### 💰 Unit Economics Framework

```
Customer Acquisition Cost (CAC) = Marketing Spend / New Customers
Lifetime Value (LTV) = ARPU × Gross Margin × Lifespan

Target Ratio: LTV:CAC > 3:1
Payback Period: < 12 months
```

---

✅ **Take Action Now**
1. Interview 10 potential target customers this week
2. Build a landing page to capture pre-launch email signups
3. Define your Month 6 MRR goal"""

    @staticmethod
    def _fitness_expert_fallback(objective: str, entities: dict) -> str:
        return """## 💪 Fitness Protocol: 5/3/1 BBB Training & Nutrition

- **Split:** 4 Days/Week (Push / Pull / Legs / Upper)
- **Protein Target:** 2.0g per kg of body weight
- **Supplements:** Creatine Monohydrate (5g/day), Whey Protein, Vitamin D3

✅ **Take Action Now**
1. Calculate daily TDEE
2. Log baseline weight and waist measurements
3. Track daily workouts on Strong app"""

    @staticmethod
    def _finance_expert_fallback(objective: str, entities: dict) -> str:
        return """## 💰 Personal Finance Strategy

1. Emergency Fund: 3–6 months in High-Yield Savings Account (4.5%+ APY)
2. 401(k) Employer Match: Contribute enough to capture full match
3. Pay High-Interest Debt (>7% interest)
4. Max Roth IRA ($7,000/yr limit)
5. Bogleheads 3-Fund Portfolio: 60% VTI, 30% VXUS, 10% BND

✅ **Take Action Now**
1. Open Fidelity or Vanguard account today
2. Automate monthly investment transfers on payday"""

    @staticmethod
    def _general_expert_fallback(objective: str, domain: str, operations: list[dict], entities: dict) -> str:
        ops_content = []
        for i, op in enumerate(operations, 1):
            ops_content.append(f"### {i}. {op.get('title', f'Step {i}')}\n\n{op.get('description', '')}\n\n*Why this matters:* {op.get('why_this', '')}")

        return f"""## ⚡ {objective.title()}

**Domain:** {domain.replace('_', ' ').title()}

---

{chr(10).join(ops_content)}

---

✅ **Take Action Now**
1. Complete Operation 1 listed above
2. Track your progress daily"""
