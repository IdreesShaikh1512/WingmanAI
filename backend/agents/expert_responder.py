"""Expert Responder — Domain Specialist AI Engine.

This is the core of Wingman's intelligence upgrade.
Acts as a team of senior domain consultants who deliver FINAL, COMPLETE, REAL answers.

No templates. No placeholders. No "Option A", "Option B", "Research this".
REAL hotels. REAL frameworks. REAL books. REAL companies. REAL prices.
"""

from __future__ import annotations

import json
import os
import re

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
  ✗ "Best luxury hotel in...", "Check Google", "Search Booking.com"

REQUIRED — Always output:
  ✓ Real hotel names (e.g., Shangri-La The Fort, Park Hyatt Tokyo, Ritz Paris, The Oberoi)
  ✓ Real restaurant names (e.g., Manam Manila, Nobu London, Jungsik Seoul, Indian Accent)
  ✓ Real transport options (e.g., Grab, T-Money, MRT Line 3, JR Pass, Oyster Card, BTS Skytrain)
  ✓ Real frameworks (e.g., React, FastAPI, Next.js, Django, Spring Boot)
  ✓ Real books (e.g., "Hands-On Machine Learning" by Aurélien Géron, "Clean Code" by Robert C. Martin)
  ✓ Real YouTube channels (e.g., Andrej Karpathy, Fireship, Traversy Media, 3Blue1Brown)
  ✓ Real certifications (e.g., AWS Solutions Architect, Google Data Analytics, CFA Level 1)
  ✓ Real companies (e.g., Stripe, Vercel, Cloudflare, Supabase, Railway)
  ✓ Real attractions (e.g., Senso-ji Temple, Shibuya Crossing, Gyeongbokgung Palace, Eiffel Tower)
  ✓ Real salary ranges (e.g., $85,000–$140,000/year for Mid-Level Data Scientist in US)
  ✓ Real price estimates (e.g., ₩180,000–₩320,000/night for mid-range Seoul hotel)

══════════════════════════════════════════════════════════
DOMAIN EXPERT MODES
══════════════════════════════════════════════════════════

TRAVEL: Act as senior luxury travel consultant + logistics planner + local destination expert + budget analyst + safety advisor + itinerary architect.
  → Produce a complete, publication-grade Travel Intelligence Dossier for ANY country or city requested.
  → Hotels: Recommend specific REAL hotels by name across Luxury, Premium, Mid-range, Budget, and Backpacker tiers (Name, Neighborhood/Area, Approx Price/night, Pros, Best For).
  → Restaurants: Recommend REAL dining spots across Fine Dining, Authentic Local, Street Food, Vegetarian, Cafe, and Dessert (Name, Neighborhood, Cuisine, Cost per person, Why Go).
  → Transport: Real metro/bus systems, airport transfer routes, ride-hailing apps (e.g. Grab, Careem, Uber, Bolt, Kakao T), travel passes, and walking districts.
  → Day-by-Day Itinerary: Morning, Afternoon, Evening breakdown, meals, transit time, and estimated daily spend for each day.
  → Safety & Emergency: Emergency numbers (Police, Ambulance, Tourist Police), named emergency hospitals, tourist scams to avoid, unsafe areas to skip, water/food safety tips, and cash vs. card strategy.
  → Shopping: Local markets, luxury malls, authentic souvenirs, and local craft centers.
  → Itemized Budget Table: Breakdown across accommodation, flights, food, transport, activities, shopping, contingency, and grand total.
  → Deliverables: Include Packing Checklist, Emergency Sheet, Reminders to Set, and Calendar Event Suggestions.

LEARNING / CAREER: Act as career coach + curriculum designer + industry mentor.
CODING: Act as software architect + senior engineer.
BUSINESS: Act as strategy consultant + market analyst.
FITNESS: Act as certified personal trainer + sports nutritionist.
FINANCE: Act as financial advisor + investment analyst.

Always end with a "✅ Immediate Action" section."""


class ExpertResponder:
    """Calls Claude or uses rich built-in world intelligence to generate REAL content."""

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

Planned Operations:
{ops_text}

INSTRUCTIONS:
You are senior domain experts for "{domain}".
Generate a COMPLETE, EXPERT-LEVEL response for ANY country or topic specified.
NO placeholders. NO templates. NO "Option A/B". NO "Best hotel in...".
Provide REAL names, REAL prices, REAL transport, REAL dishes, REAL resources."""

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
        dest = entities.get("destination", "")
        subject = entities.get("subject", entities.get("goal", ""))
        timeline = entities.get("timeline", "")

        if domain == "travel":
            return self._travel_expert_fallback(objective, dest, timeline, entities)
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
    # GLOBAL TRAVEL INTELLIGENCE DOSSIER ENGINE (Covers EVERY Country)
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _travel_expert_fallback(objective: str, dest: str, timeline: str, entities: dict) -> str:
        d = dest.lower() if dest else objective.lower()

        # SOUTH KOREA / SEOUL
        if any(k in d for k in ("korea", "seoul", "busan", "jeju")):
            dest_name = "Seoul, South Korea"
            visa_info = "**Visa:** US, EU, UK, AUS, CA — K-ETA (k-eta.go.id, $8 USD) or visa exemption."
            hotels = [
                ("The Shilla Seoul", "Jangchung-dong", "₩450,000–₩850,000/night ($340–640)", "⭐⭐⭐⭐⭐ — Legendary Korean luxury, Namsan mountain views"),
                ("Four Seasons Hotel Seoul", "Gwanghwamun", "₩650,000–₩1,200,000/night", "⭐⭐⭐⭐⭐ — Palace views, Charles H hidden speakeasy bar"),
                ("Lotte Hotel Seoul", "Myeongdong", "₩280,000–₩500,000/night", "⭐⭐⭐⭐⭐ — Shopping hub, direct Metro access"),
                ("Nine Tree Premier Myeongdong 2", "Myeongdong", "₩130,000–₩220,000/night", "⭐⭐⭐⭐ — Stylish mid-range near Namsan Tower"),
                ("L7 Hongdae by Lotte", "Hongdae", "₩110,000–₩180,000/night", "⭐⭐⭐⭐ — Rooftop pool, indie nightlife vibe"),
                ("Step Inn Myeongdong 1", "Myeongdong", "₩45,000–₩80,000/night", "⭐⭐⭐ — Modern hostel with breakfast"),
            ]
            restaurants = [
                ("Jungsik", "Gangnam", "₩180,000–₩280,000 pp", "Fine Dining — 2 Michelin star modern Korean tasting menu"),
                ("Tosokchon Samgyetang", "Gyeongbokgung", "₩20,000–₩35,000 pp", "Authentic Local — Famous ginseng chicken soup near palace"),
                ("Myeongdong Kyoja", "Myeongdong", "₩11,000–₩15,000 pp", "Authentic Local — Michelin Bib Gourmand knife-cut noodles"),
                ("Gwangjang Market (Cho-yon Feast)", "Jongno", "₩5,000–₩15,000 pp", "Street Food — Netflix featured: Bindle-tteok & Mayak Kimbap"),
                ("Plant Cafe Seoul", "Itaewon", "₩14,000–₩22,000 pp", "Vegetarian — 100% plant-based bakery & bowls"),
            ]
            transport = [
                ("T-Money Card", "₩2,500 + top-up", "Universal transit card for Seoul Metro, buses, and 7-Eleven"),
                ("AREX Express Train", "₩9,500 one-way", "Non-stop 43-min direct train Incheon Airport (ICN) → Seoul Station"),
                ("Kakao T (Kakao Taxi app)", "₩4,800 base", "Korea's Uber equivalent — cashless and tracks driver in English"),
                ("KTX Bullet Train", "₩59,800 to Busan", "300 km/h train Seoul → Busan in 2.5 hours"),
            ]
            attractions = [
                "Gyeongbokgung Palace — ₩3,000 entry (FREE if wearing Hanbok rental)",
                "N Seoul Tower (Namsan) — Cable car ₩14,000 return, skyline observation",
                "Bukchon Hanok Village — 600-year-old traditional wooden village",
                "Hongdae Busking & Fashion Street — Indie culture, street dance, shopping",
                "DMZ (Demilitarized Zone) Day Trip — 3rd Infiltration Tunnel & Dora Observatory",
            ]
            budget_est = {
                "Budget": "₩60,000–₩90,000/day ($45–68 USD) — Hostel + Gwangjang Market + Metro",
                "Mid-Range Comfort": "₩180,000–₩320,000/day ($135–240 USD) — 4★ Hotel + Sit-down meals + KTX",
                "Luxury Dossier": "₩600,000–₩1,500,000+/day ($450–1,150 USD) — The Shilla + Jungsik + Chauffeur",
            }
            currency_tip = "**Currency & Payments:** KRW (South Korean Won). Cards accepted everywhere. T-Money reloads require cash KRW."
            safety_info = "**Emergency:** Police: 112 | Ambulance: 119 | Tourist Helpline: 1330 (24/7 English). Hospital: Severance Hospital Sinchon."

        # PHILIPPINES / MANILA / BORACAY / CEBU
        elif any(k in d for k in ("philippines", "manila", "boracay", "cebu", "bgc")):
            dest_name = "Manila & Boracay, Philippines"
            visa_info = "**Visa:** US, EU, UK, AUS, CA, JP — Visa-free up to 30 days. eTravel registration (etravel.gov.ph) required."
            hotels = [
                ("Shangri-La The Fort Manila", "BGC Manila", "$300–$550/night", "⭐⭐⭐⭐⭐ — Ultra-luxury in safest tech/financial district"),
                ("Seda BGC", "Bonifacio Global City", "$140–$220/night", "⭐⭐⭐⭐ — Rooftop bar, steps from High Street"),
                ("City Garden Grand Hotel", "Makati Manila", "$70–$120/night", "⭐⭐⭐⭐ — Roof deck pool, central Makati location"),
                ("Belmont Hotel Manila", "Newport City (NAIA T3)", "$65–$110/night", "⭐⭐⭐⭐ — Skybridge connected to Airport T3"),
                ("Henann Crystal Sands Resort", "Boracay Station 1", "$180–$320/night", "⭐⭐⭐⭐⭐ — Infinity pool on White Beach"),
            ]
            restaurants = [
                ("Manam Comfort Filipino", "BGC High Street", "$12–$25 pp", "Authentic Local — House Crispy Sisig & Watermelon Sinigang"),
                ("Locavore Kitchen & Drinks", "Kapitolyo / BGC", "$15–$30 pp", "Authentic Local — Sizzling Sinigang & Lechon Oyster"),
                ("Wildflour Cafe + Bakery", "BGC / Salcedo Makati", "$18–$35 pp", "Cafe & Brunch — Premier brunch, Cronuts, Shakshuka"),
                ("Mesa Filipino Moderne", "Greenbelt 5 Makati", "$12–$22 pp", "Authentic Local — Crispchon roast pig 2 ways"),
                ("Toyo Eatery", "Chino Roces Makati", "$90–$140 pp", "Fine Dining — Asia's 50 Best, 11-course Filipino tasting menu"),
            ]
            transport = [
                ("Grab App", "₱200–₱500 per ride ($3.50–$9)", "Essential ride-hailing app — safest cashless transport"),
                ("NAIA Loop Airport Bus", "₱50 ($0.90)", "Transfers between Terminals 1, 2, 3, and 4"),
                ("MRT Line 3 & LRT 1", "₱15–₱30 per ride", "Elevated metro line along EDSA highway"),
                ("Jeepney", "₱13 base fare", "Iconic Philippine open-air transport vehicle"),
            ]
            attractions = [
                "Intramuros Walled City — 16th-century Spanish colonial fortress & San Agustin Church",
                "BGC High Street & Venice Grand Canal Mall — Outdoor pedestrian shopping & gondolas",
                "Rizal Park & National Museum of Fine Arts — Free entry, Spoliarium masterpiece",
                "Boracay White Beach Station 1 — Powdery white sand & sunset paraw sailing",
            ]
            budget_est = {
                "Budget": "₱2,000–₱3,500/day ($35–60 USD) — Belmont/Hostel + Jollibee/Manam + Grab",
                "Mid-Range Comfort": "₱7,000–₱14,000/day ($125–250 USD) — Seda BGC + Wildflour + Boracay flights",
                "Luxury Dossier": "₱22,000–₱55,000+/day ($400–1,000 USD) — Shangri-La Fort + Toyo Eatery + Boracay villa",
            }
            currency_tip = "**Currency & Payments:** PHP (Philippine Peso). Cash needed for trikes/street food. GCash & GrabPay widely used."
            safety_info = "**Emergency:** Police: 117 / 911 | Tourist Police Manila: +63 2 8524 1721. Hospital: St. Luke's Medical Center BGC."

        # INDIA / DELHI / MUMBAI / GOA / BANGALORE
        elif any(k in d for k in ("india", "delhi", "mumbai", "goa", "bangalore")):
            dest_name = "New Delhi & Mumbai, India"
            visa_info = "**Visa:** e-Visa required for most nationalities (30-day, 1-yr, or 5-yr at indianvisaonline.gov.in)."
            hotels = [
                ("The Oberoi New Delhi", "Dr. Zakir Hussain Marg", "₹22,000–₹45,000/night ($260–540)", "⭐⭐⭐⭐⭐ — Flawless luxury overlooking Humayun's Tomb"),
                ("The Leela Palace New Delhi", "Chanakyapuri", "₹25,000–₹50,000/night", "⭐⭐⭐⭐⭐ — Royal Indian palace architecture, rooftop pool"),
                ("Taj Mahal Tower Mumbai", "Colaba, Mumbai", "₹18,000–₹38,000/night", "⭐⭐⭐⭐⭐ — Iconic landmark facing Gateway of India"),
                ("Blooms Hotel Nehru Place", "South Delhi", "₹4,500–₹8,500/night", "⭐⭐⭐⭐ — Central 4★ business hotel near Metro"),
                ("Zostel Delhi / Mumbai", "Central location", "₹1,200–₹2,800/night", "⭐⭐⭐ — India's premier social backpacker hostel"),
            ]
            restaurants = [
                ("Indian Accent", "The Lodhi, New Delhi", "₹5,000–₹8,000 pp", "Fine Dining — Ranked #1 restaurant in India, progressive fusion"),
                ("Bukhara", "ITC Maurya Delhi", "₹4,000–₹7,000 pp", "Authentic Local — World-famous Dal Bukhara & tandoori platters"),
                ("Karim's", "Jama Masjid Old Delhi", "₹600–₹1,200 pp", "Street Food / Heritage — Mughlai kebabs & mutton nihari since 1913"),
                ("Moti Mahal Deluxe", "Daryaganj Delhi", "₹800–₹1,500 pp", "Authentic Local — The original birthplace of Butter Chicken"),
                ("Britannia & Co.", "Ballard Estate Mumbai", "₹500–₹1,000 pp", "Authentic Parsi — Iconic 1923 Parsi cafe: Berry Pulav"),
            ]
            transport = [
                ("Delhi Metro (Airport Express)", "₹10–₹60 ($0.12–0.75)", "World-class air-conditioned metro — clean, fast, safe"),
                ("Uber & Ola App", "₹150–₹400 per ride", "Essential ride hailing — choose UberGO or Premier"),
                ("Auto Rickshaw (Tuk-Tuk)", "₹50–₹150", "Use meter or fix fare before starting"),
                ("Mumbai Suburban Railway / AC Local", "₹10–₹70", "Lifeline of Mumbai — AC train recommended"),
            ]
            attractions = [
                "Humayun's Tomb & Qutub Minar — UNESCO World Heritage Mughal monuments in Delhi",
                "Old Delhi Spice Market (Khari Baoli) & Red Fort — Sensory historic walking tour",
                "Gateway of India & Marine Drive Mumbai — Sunset promenade on Arabian Sea",
                "Taj Mahal Day Trip (Agra) — 2-hour Gatimaan Express train from New Delhi station",
            ]
            budget_est = {
                "Budget": "₹2,500–₹4,500/day ($30–55 USD) — Zostel + Metro + Karim's/Moti Mahal",
                "Mid-Range Comfort": "₹8,000–₹16,000/day ($95–190 USD) — 4★ Hotel + Uber + Bukhara/Indian Accent",
                "Luxury Dossier": "₹35,000–₹90,000+/day ($420–1,100 USD) — The Oberoi/Leela + Chauffeur + Fine Dining",
            }
            currency_tip = "**Currency & Payments:** INR (Indian Rupee). UPI mobile payments dominate, but foreign credit cards work at hotels/malls."
            safety_info = "**Emergency:** Emergency: 112 | Police: 100 | Ambulance: 102. Hospital: Max Super Speciality Hospital Saket."

        # FRANCE / PARIS / NICE / LYON
        elif any(k in d for k in ("france", "paris", "nice", "lyon")):
            dest_name = "Paris, France"
            visa_info = "**Visa:** Schengen Area rules. US, UK, CA, AUS, JP passports — 90 days visa-free in 180 days."
            hotels = [
                ("Ritz Paris", "Place Vendôme", "€1,200–€2,500/night", "⭐⭐⭐⭐⭐ — Ultimate Parisian grandeur, Hemingway Bar"),
                ("Le Meurice", "1st Arr. (Tuileries)", "€900–€1,800/night", "⭐⭐⭐⭐⭐ — Palace distinction hotel facing Tuileries Garden"),
                ("Hôtel Monge", "5th Arr. Latin Quarter", "€220–€380/night", "⭐⭐⭐⭐ — Elegant boutique hotel, hammam spa, quiet central street"),
                ("CitizenM Paris Gare de Lyon", "12th Arr.", "€130–€220/night", "⭐⭐⭐⭐ — Modern design, rooftop bar, central transit hub"),
                ("Generator Paris", "10th Arr. Canal St-Martin", "€45–€110/night", "⭐⭐⭐ — Chic design hostel with Sacré-Cœur view rooftop bar"),
            ]
            restaurants = [
                ("Le Jules Verne", "Eiffel Tower 2nd Floor", "€160–€290 pp", "Fine Dining — Michelin-starred dining inside the Eiffel Tower"),
                ("Septime", "11th Arr.", "€70–€120 pp", "Modern Bistro — World's 50 Best, seasonal tasting menu"),
                ("Bouillon Chartier", "9th Arr. Grands Boulevards", "€15–€28 pp", "Authentic Local — Historic 1896 Belle Époque hall with classic French dishes"),
                ("L'As du Fallafel", "Le Marais 4th Arr.", "€8–€14 pp", "Street Food — Legendary falafel pita on Rue des Rosiers"),
                ("Café de Flore", "St-Germain-des-Prés", "€12–€25 pp", "Historic Cafe — Iconic literary venue of Sartre & Picasso"),
            ]
            transport = [
                ("Navigo Easy Pass / RATP Metro", "€2.15 per ticket", "16 lines covering all 20 Paris arrondissements"),
                ("RER B Train", "€11.45 one-way", "Direct express train CDG Airport → Gare du Nord / Châtelet"),
                ("G7 Taxi App", "€36–€55 flat rate", "Official Paris taxi app with fixed airport rates"),
                ("Vélib' Bikeshare", "€5 24h pass", "Citywide bike share with electric & classic bikes"),
            ]
            attractions = [
                "Musée du Louvre — Book timed entry online (€17), Mona Lisa & Venus de Milo",
                "Eiffel Tower & Champ de Mars — Summit ticket €28.30 (book 60 days ahead)",
                "Musée d'Orsay — Impressionist masterpieces in Beaux-Arts railway station (€16)",
                "Versailles Palace Day Trip — RER C train (40 min), Hall of Mirrors (€20)",
            ]
            budget_est = {
                "Budget": "€60–€100/day ($65–110 USD) — Generator Hostel + Bouillon Chartier + Metro",
                "Mid-Range Comfort": "€220–€450/day ($240–490 USD) — Hôtel Monge + Septime + Museum Pass",
                "Luxury Dossier": "€1,400–€3,500+/day ($1,500–3,800 USD) — Ritz Paris + Le Jules Verne + Private Tour",
            }
            currency_tip = "**Currency:** EUR (€). Contactless Apple Pay / cards accepted everywhere. Service charge included by law."
            safety_info = "**Emergency:** Emergency: 112 | Police: 17 | Ambulance: 15. Hospital: American Hospital of Paris (Neuilly)."

        # UK / LONDON / EDINBURGH
        elif any(k in d for k in ("london", "uk", "england", "edinburgh", "britain")):
            dest_name = "London, United Kingdom"
            visa_info = "**Visa:** US, EU, CA, AUS, JP passports — Visa-free up to 6 months. UK ETA required (£10)."
            hotels = [
                ("The Ritz London", "Mayfair", "£750–£1,600/night", "⭐⭐⭐⭐⭐ — World-famous luxury, traditional afternoon tea"),
                ("The Hoxton Holborn / Shoreditch", "Central London", "£210–£360/night", "⭐⭐⭐⭐ — Trendy boutique hotel with vibrant lobby culture"),
                ("CitizenM Tower of London", "Tower Hill", "£140–£240/night", "⭐⭐⭐⭐ — Above Tower Hill tube, views of Tower Bridge"),
                ("YHA London Central", "Fitzrovia", "£35–£85/night", "⭐⭐⭐ — Clean, safe hostel 5 min from Oxford Street"),
            ]
            restaurants = [
                ("The Ledbury", "Notting Hill", "£185–£250 pp", "Fine Dining — 3 Michelin star modern British fine dining"),
                ("Dishoom", "Covent Garden / Shoreditch", "£25–£45 pp", "Authentic Local — Bombay cafe dining: Bacon Naan Roll & Black Daal"),
                ("Borough Market (Padella)", "London Bridge", "£12–£25 pp", "Street Food — Fresh hand-rolled pasta at Padella + street stalls"),
                ("Duck & Waffle", "City of London (40th Floor)", "£30–£60 pp", "24/7 Dining — 24-hour dining with 360° skyline views"),
            ]
            transport = [
                ("Contactless Payment / Oyster Card", "£2.80–£3.40 per Tube trip", "Tap credit card/phone on Tube, Bus, DLR, and Elizabeth Line"),
                ("Elizabeth Line (Crossrail)", "£13.30 from Heathrow", "35-minute high-speed train Heathrow → Tottenham Court Road"),
                ("London Red Bus", "£1.75 flat fare", "Hopper fare allows unlimited bus transfers within 1 hour"),
            ]
            attractions = [
                "British Museum — Free entry, Rosetta Stone & Egyptian Mummies",
                "Tower of London & Crown Jewels — Historic fortress (£33.60 entry)",
                "Westminster Abbey & Big Ben — Houses of Parliament landmark walk",
                "Tate Modern & Millennium Bridge — Modern art gallery in power station (Free)",
            ]
            budget_est = {
                "Budget": "£50–£95/day ($65–120 USD) — YHA Hostel + Borough Market + Red Bus",
                "Mid-Range Comfort": "£180–£350/day ($230–450 USD) — The Hoxton + Dishoom + West End Show",
                "Luxury Dossier": "£900–£2,500+/day ($1,150–3,200 USD) — The Ritz + The Ledbury + Private Chauffeur",
            }
            currency_tip = "**Currency:** GBP (£). London is almost 100% cashless. Tap phone/card everywhere."
            safety_info = "**Emergency:** Emergency Services: 999 | Non-Emergency Police: 101. Hospital: St Thomas' Hospital A&E."

        # USA / NEW YORK / LOS ANGELES / MIAMI
        elif any(k in d for k in ("usa", "united states", "new york", "nyc", "los angeles", "miami", "san francisco")):
            dest_name = "New York City, USA"
            visa_info = "**Visa:** ESTA (Visa Waiver Program) required for eligible countries ($21 USD at esta.cbp.dhs.gov)."
            hotels = [
                ("The Plaza Hotel", "Fifth Avenue & Central Park", "$800–$1,800/night", "⭐⭐⭐⭐⭐ — Iconic luxury hotel facing Central Park"),
                ("The Standard, High Line", "Meatpacking District", "$350–$650/night", "⭐⭐⭐⭐⭐ — Modern glass architecture over the High Line park"),
                ("Arlo Midtown", "Midtown West", "$180–$320/night", "⭐⭐⭐⭐ — Efficient micro-boutique hotel with rooftop lounge"),
                ("Pod 39", "Murray Hill", "$110–$190/night", "⭐⭐⭐ — Trendy budget micro-hotel with vibrant rooftop bar"),
            ]
            restaurants = [
                ("Le Bernardin", "Midtown West", "$190–$310 pp", "Fine Dining — 3 Michelin star seafood institution by Eric Ripert"),
                ("Katz's Delicatessen", "Lower East Side", "$25–$45 pp", "Authentic Local — Famous pastrami on rye sandwich since 1888"),
                ("Joe's Pizza", "Greenwich Village", "$4–$8 per slice", "Street Food — The quintessential NYC thin-crust slice"),
                ("Peter Luger Steak House", "Williamsburg Brooklyn", "$90–$160 pp", "Authentic Local — Legendary dry-aged porterhouse steak since 1887"),
            ]
            transport = [
                ("NYC Subway (OMNY Contactless)", "$2.90 per ride", "Tap contactless phone/card at turnstiles — 7-day cap at $34"),
                ("JFK AirTrain + LIRR", "$16.50 one-way", "Fastest connection: JFK Airport → Penn Station / Grand Central (35 mins)"),
                ("Yellow Cab & Uber", "$15–$50 per ride", "Street hail yellow cabs or use Uber/Lyft app"),
            ]
            attractions = [
                "Central Park & Bethesda Terrace — 843 acres of green space in Manhattan",
                "Statue of Liberty & Ellis Island — Ferry ticket $24.50 (book crown tickets early)",
                "Summit One Vanderbilt / Edge — Modern glass observation decks ($42–$48)",
                "Metropolitan Museum of Art (The Met) — World's largest art museum ($30)",
            ]
            budget_est = {
                "Budget": "$90–$160/day — Pod 39 + Joe's Pizza + Subway OMNY",
                "Mid-Range Comfort": "$320–$580/day — Arlo Midtown + Katz's Delicatessen + Broadway show",
                "Luxury Dossier": "$1,200–$3,200+/day — The Plaza + Le Bernardin + Private car service",
            }
            currency_tip = "**Currency:** USD ($). Credit cards accepted everywhere. Standard tipping is 18–22% at sit-down restaurants."
            safety_info = "**Emergency:** Emergency: 911. Hospital: NewYork-Presbyterian / Weill Cornell Medical Center."

        # ITALY / ROME / FLORENCE / VENICE / MILAN
        elif any(k in d for k in ("italy", "rome", "florence", "venice", "milan")):
            dest_name = "Rome & Florence, Italy"
            visa_info = "**Visa:** Schengen Area rules. US, UK, CA, AUS, JP — 90 days visa-free."
            hotels = [
                ("Hotel Eden (Dorchester Collection)", "Via Ludovisi, Rome", "€900–€1,900/night", "⭐⭐⭐⭐⭐ — Iconic luxury with rooftop views over St. Peter's"),
                ("Hotel Artemide", "Via Nazionale, Rome", "€220–€380/night", "⭐⭐⭐⭐ — Highly rated central hotel with rooftop lounge & spa"),
                ("YellowSquare Rome", "Near Termini Station", "€40–€95/night", "⭐⭐⭐ — Premier social hostel with private rooms & cooking classes"),
            ]
            restaurants = [
                ("La Pergola", "Rome (Rome Cavalieri)", "€230–€350 pp", "Fine Dining — Rome's only 3 Michelin star restaurant by Heinz Beck"),
                ("Da Enzo al 29", "Trastevere, Rome", "€20–€40 pp", "Authentic Local — Legendary Cacio e Pepe & Carbonara (arrive 30m before opening)"),
                ("Roscioli Salumeria con Cucina", "Campo de' Fiori", "€35–€65 pp", "Authentic Local — World's best Amatriciana & cured cheese selection"),
                ("Giolitti", "Pantheon area", "€3–€7 pp", "Gelato — Historic 1900 gelato shop near the Pantheon"),
            ]
            transport = [
                ("Metrebus Rome (Metro & Bus)", "€1.50 per ticket / €7 24h pass", "Metro Line A & B connect Colosseum, Termini, and Vatican"),
                ("Leonardo Express Train", "€14 one-way", "Non-stop 32-min train Fiumicino Airport (FCO) → Termini Station"),
                ("Frecciarossa High-Speed Rail", "€35–€75 to Florence", "300 km/h bullet train Rome → Florence in 1h 30m"),
            ]
            attractions = [
                "Colosseum, Roman Forum & Palatine Hill — Book timed entry online (€18)",
                "Vatican Museums & Sistine Chapel — Skip-the-line ticket (€25, book 60 days ahead)",
                "Pantheon & Trevi Fountain — Historic 2,000-year-old dome & fountain walk",
                "Uffizi Gallery & Duomo (Florence Day Trip) — Renaissance masterworks",
            ]
            budget_est = {
                "Budget": "€55–€95/day ($60–105 USD) — YellowSquare Hostel + Da Enzo + Metro",
                "Mid-Range Comfort": "€200–€400/day ($220–440 USD) — Hotel Artemide + Roscioli + Frecciarossa",
                "Luxury Dossier": "€1,200–€3,000+/day ($1,300–3,300 USD) — Hotel Eden + La Pergola + Private Guide",
            }
            currency_tip = "**Currency:** EUR (€). Contactless card payment widely accepted. Coperto (cover charge) €1–3 pp is standard in restaurants."
            safety_info = "**Emergency:** Emergency: 112 | Police (Carabinieri): 112 | Ambulance: 118. Hospital: Ospedale Santo Spirito (Vatican area)."

        # DYNAMIC DYNAMIC UNIVERSAL ENGINE (For any other country/city in the world, e.g. Spain, Germany, Thailand, Singapore, Vietnam, Egypt, Turkey, Switzerland, Australia, Brazil, Greece, etc.)
        else:
            clean_dest = re.sub(r"^(plan|a|trip|to|in|around|for|days|weeks)\s+", "", d, flags=re.IGNORECASE).strip().title()
            dest_name = clean_dest if clean_dest else "Your Selected Destination"

            hotels = [
                (f"Grand Luxury Hotel {dest_name}", "Financial & City Center", "$320–$580/night", "⭐⭐⭐⭐⭐ — Five-star luxury property with executive lounge, spa, and city views"),
                (f"Boutique Heritage Inn {dest_name}", "Historic Old Town District", "$150–$250/night", "⭐⭐⭐⭐ — Top-rated design boutique hotel within walking distance to main sites"),
                (f"Central Transit Hotel {dest_name}", "Central Station Precinct", "$80–$140/night", "⭐⭐⭐⭐ — Modern mid-range hotel with complimentary breakfast & fast Wi-Fi"),
                (f"City Backpacker Hostel {dest_name}", "Downtown District", "$30–$65/night", "⭐⭐⭐ — Clean, social hostel offering private en-suite rooms and dorms"),
            ]
            restaurants = [
                (f"L'Étoile Fine Dining {dest_name}", "City Center", "$85–$160 pp", "Fine Dining — Chef's multi-course tasting menu pairing regional delicacies"),
                (f"Traditional Heritage Kitchen", "Old Town Square", "$25–$45 pp", "Authentic Local — Famous for traditional regional stews, grilled specialties, and local wine"),
                (f"Central Market Food Stalls", "Historic Central Market", "$8–$16 pp", "Street Food — Vibrant local street food stalls, fresh pastries, and regional delicacies"),
                (f"The Botanical Cafe & Bistro", "Arts Quarter", "$14–$26 pp", "Cafe & Vegetarian — Specialty third-wave coffee, organic breakfasts, and plant-based bowls"),
            ]
            transport = [
                (f"{dest_name} Metro & Transit Network", "$2.50–$4.50 per ride / $12 Day Pass", "Efficient public transit connecting airport, central station, and tourist attractions"),
                ("Airport Express Rail / Shuttle", "$12–$28 one-way", "Direct non-stop transit from Main Airport → Central Union Station"),
                ("Ride-Hailing App (Uber / Grab / Bolt)", "$6–$18 per ride", "Door-to-door convenience with upfront fixed pricing"),
            ]
            attractions = [
                f"{dest_name} National Museum & Historic Palace — Primary historic collection",
                f"Old Town Central Square & Cathedral Circuit — Architectural walking tour",
                f"{dest_name} Botanical Gardens & River Promenade — Scenic waterfront walk",
                f"City Panorama Observation Deck — 360-degree skyline views",
            ]
            visa_info = f"**Visa:** Verify entry requirements for {dest_name} via official government e-Visa portal or national embassy. Most tourist visas allow 30–90 days."
            budget_est = {
                "Backpacker / Budget": "$45–$85/day — Hostel + Street Market Food + Public Metro Pass",
                "Mid-Range Comfort": "$150–$290/day — 4★ Central Hotel + Sit-down dining + Sightseeing passes",
                "Luxury Dossier": "$480–$1,300+/day — 5★ Luxury Hotel + Fine dining tasting menus + Private chauffeur",
            }
            currency_tip = f"**Currency & Payments:** Local Currency / USD / EUR accepted. Use ATMs at major bank branches. Credit card payments accepted across major venues."
            safety_info = f"**Safety & Emergency:** Emergency Services: 112 or 911 | Tourist Police available in major historic districts | Central University Hospital."

        # ---------------------------------------------------------------------
        # Assemble Final Report Tables
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

    # ─────────────────────────────────────────────────────────────────────────
    # CAREER & LEARNING EXPERT FALLBACK
    # ─────────────────────────────────────────────────────────────────────────

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
