# ─────────────────────────────────────────────────────────────────
# MaaSakhi Schemes & Government Benefits
# Service Flow: Government → Patient (Top to Bottom)
#
# Schemes covered:
# 1. JSY    — Janani Suraksha Yojana (₹1400 cash on delivery)
# 2. PMMVY  — Pradhan Mantri Matru Vandana Yojana (₹5000)
# 3. JSSK   — Janani Shishu Suraksha Karyakram (free services)
# 4. PMSMA  — PM Surakshit Matritva Abhiyan (free ANC checkups)
# 5. Free medicines — Iron, Folic Acid, Calcium via AWC/PHC
# 6. 108    — Emergency ambulance
# 7. RCH    — Reproductive Child Health portal registration
# ─────────────────────────────────────────────────────────────────

import os
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


# ─────────────────────────────────────────────────────────────────
# SCHEME DATABASE
# All schemes with eligibility, benefits, how to claim
# Source: NHM India, Ministry of Health & Family Welfare
# ─────────────────────────────────────────────────────────────────

SCHEMES = {
    "JSY": {
        "name":        "Janani Suraksha Yojana (JSY)",
        "name_hindi":  "जननी सुरक्षा योजना",
        "benefit":     "₹1,400 cash assistance after institutional delivery in government hospital",
        "who":         "All pregnant women who deliver in government hospitals",
        "how_to_claim": "Register at nearest PHC/CHC. ASHA worker will help with paperwork. Cash given within 7 days of delivery.",
        "documents":   ["Aadhaar card", "BPL card (if available)", "Bank account details"],
        "contact":     "Your ASHA worker or nearest PHC",
        "source":      "NHM India — JSY Guidelines 2023"
    },

    "PMMVY": {
        "name":        "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "name_hindi":  "प्रधानमंत्री मातृ वंदना योजना",
        "benefit":     "₹5,000 in 3 installments for first live birth",
        "who":         "All pregnant and lactating women for their first live birth",
        "how_to_claim": (
            "Installment 1 (₹1000): After early registration of pregnancy\n"
            "Installment 2 (₹2000): After 6 months of pregnancy + 1 ANC checkup\n"
            "Installment 3 (₹2000): After child birth + first vaccination cycle"
        ),
        "documents":   ["Aadhaar card", "Bank account linked to Aadhaar", "MCP card"],
        "contact":     "Anganwadi Centre (AWC) or nearest PHC",
        "source":      "Ministry of Women & Child Development — PMMVY 2023"
    },

    "JSSK": {
        "name":        "Janani Shishu Suraksha Karyakram (JSSK)",
        "name_hindi":  "जननी शिशु सुरक्षा कार्यक्रम",
        "benefit":     "Completely FREE delivery and newborn care in government hospitals",
        "who":         "All pregnant women delivering in government hospitals",
        "how_to_claim": (
            "Simply go to nearest government hospital.\n"
            "Free services include: delivery, C-section, medicines, "
            "blood transfusion, diet, transport, stay for 3 days after delivery"
        ),
        "documents":   ["Any ID proof"],
        "contact":     "Nearest Government Hospital / CHC / PHC",
        "source":      "NHM India — JSSK Guidelines"
    },

    "PMSMA": {
        "name":        "PM Surakshit Matritva Abhiyan (PMSMA)",
        "name_hindi":  "प्रधानमंत्री सुरक्षित मातृत्व अभियान",
        "benefit":     "FREE comprehensive ANC checkup on 9th of every month at PHC/CHC",
        "who":         "All pregnant women",
        "how_to_claim": (
            "Visit your nearest PHC or CHC on the 9th of every month.\n"
            "No appointment needed. Free blood tests, ultrasound, doctor consultation."
        ),
        "documents":   ["MCP card or any pregnancy record"],
        "contact":     "Nearest PHC/CHC — visit on 9th of month",
        "source":      "Ministry of Health & Family Welfare — PMSMA"
    },

    "FREE_MEDICINES": {
        "name":        "Free Medicines — Iron, Folic Acid, Calcium",
        "name_hindi":  "मुफ्त दवाइयाँ",
        "benefit":     "Free Iron-Folic Acid tablets and Calcium tablets every month",
        "who":         "All registered pregnant women",
        "how_to_claim": (
            "Collect from your nearest Anganwadi Centre (AWC) every month.\n"
            "Your ASHA worker can also bring them to your home.\n"
            "Iron tablet: 1 daily after meals\n"
            "Folic acid: 1 daily\n"
            "Calcium: 500mg twice daily after week 16"
        ),
        "documents":   ["MCP card or ASHA registration"],
        "contact":     "Anganwadi Centre or your ASHA worker",
        "source":      "NHM India — IFA Supplementation Protocol 2019"
    },

    "AMBULANCE_108": {
        "name":        "108 Emergency Ambulance",
        "name_hindi":  "108 एम्बुलेंस सेवा",
        "benefit":     "FREE emergency ambulance for pregnant women — available 24/7",
        "who":         "Any pregnant woman with danger symptoms",
        "how_to_claim": "Call 108 from any phone. FREE for maternal emergencies. No charge.",
        "documents":   ["None required"],
        "contact":     "Call 108",
        "source":      "NHM Emergency Transport Scheme"
    },

    "RCH": {
        "name":        "RCH Portal Registration",
        "name_hindi":  "आरसीएच पोर्टल पंजीकरण",
        "benefit":     "Official government pregnancy registration — enables all scheme benefits",
        "who":         "All pregnant women",
        "how_to_claim": (
            "Register through your ASHA worker or at nearest PHC.\n"
            "You get an MCP (Mother and Child Protection) card.\n"
            "This card unlocks ALL government benefits."
        ),
        "documents":   ["Aadhaar card", "Age proof"],
        "contact":     "Your ASHA worker or nearest PHC",
        "source":      "Ministry of Health — RCH Portal"
    }
}


# ─────────────────────────────────────────────────────────────────
# WEEK-BASED SCHEME NOTIFICATIONS
# Which schemes to tell a woman about based on her pregnancy week
# ─────────────────────────────────────────────────────────────────

def get_schemes_for_week(week):
    """
    Returns list of scheme keys relevant for this pregnancy week.
    Based on NHM scheme delivery timeline.
    """
    schemes = []

    # Always relevant
    schemes.append("FREE_MEDICINES")
    schemes.append("AMBULANCE_108")

    if week <= 12:
        # Early registration — most important
        schemes.append("RCH")
        schemes.append("PMMVY")   # First installment available
        schemes.append("PMSMA")

    elif week <= 27:
        # Mid-pregnancy
        schemes.append("PMMVY")   # Second installment at 6 months
        schemes.append("PMSMA")
        schemes.append("JSSK")

    else:
        # Third trimester — delivery planning
        schemes.append("JSY")
        schemes.append("JSSK")
        schemes.append("PMMVY")   # Remind about third installment after delivery

    return list(dict.fromkeys(schemes))  # Remove duplicates, preserve order


# ─────────────────────────────────────────────────────────────────
# FORMAT SCHEME MESSAGE — for WhatsApp
# ─────────────────────────────────────────────────────────────────

def format_scheme_whatsapp(scheme_key, language="Hindi"):
    """
    Formats a single scheme as a WhatsApp-friendly message.
    """
    scheme = SCHEMES.get(scheme_key)
    if not scheme:
        return ""

    if language == "Hindi":
        return (
            f"🏛 *{scheme['name']}*\n"
            f"({scheme.get('name_hindi', '')})\n\n"
            f"💰 *Labh (Benefit):* {scheme['benefit']}\n\n"
            f"👩 *Kaun apply kar sakti hai:* {scheme['who']}\n\n"
            f"📋 *Kaise prapt karein:*\n{scheme['how_to_claim']}\n\n"
            f"📍 *Kahan jaayein:* {scheme['contact']}\n\n"
            f"_Source: {scheme['source']}_"
        )
    else:
        return (
            f"🏛 *{scheme['name']}*\n\n"
            f"💰 *Benefit:* {scheme['benefit']}\n\n"
            f"👩 *Who can apply:* {scheme['who']}\n\n"
            f"📋 *How to claim:*\n{scheme['how_to_claim']}\n\n"
            f"📍 *Where to go:* {scheme['contact']}\n\n"
            f"_Source: {scheme['source']}_"
        )


# ─────────────────────────────────────────────────────────────────
# REGISTRATION SCHEME NOTIFICATION
# Sent to every new patient on registration
# ─────────────────────────────────────────────────────────────────

def get_registration_schemes_message(week, name, language="Hindi"):
    """
    Generates a schemes summary message sent to woman on registration.
    Tells her what government benefits she is entitled to.
    """
    relevant_keys = get_schemes_for_week(week)

    if language == "Hindi":
        msg = (
            f"🏛 *{name}, aap yeh sarkari suvidhaen le sakti hain:*\n\n"
        )
        benefit_lines = []
        for key in relevant_keys[:4]:  # Max 4 to keep message short
            s = SCHEMES.get(key, {})
            benefit_lines.append(f"✅ *{s.get('name_hindi', s.get('name',''))}* — {s['benefit']}")

        msg += "\n".join(benefit_lines)
        msg += (
            f"\n\n💡 Scheme details jaanne ke liye type karein:\n"
            f"*'Scheme batao'* ya *'Government help'*\n\n"
            f"Yeh sab MUFT hai — aapka haq hai! 💚"
        )
    else:
        msg = (
            f"🏛 *{name}, you are eligible for these government benefits:*\n\n"
        )
        benefit_lines = []
        for key in relevant_keys[:4]:
            s = SCHEMES.get(key, {})
            benefit_lines.append(f"✅ *{s['name']}* — {s['benefit']}")

        msg += "\n".join(benefit_lines)
        msg += (
            f"\n\n💡 To know more type:\n"
            f"*'Scheme details'* or *'Government help'*\n\n"
            f"All of these are FREE — they are your right! 💚"
        )

    return msg


# ─────────────────────────────────────────────────────────────────
# DETECT SCHEME QUERY — from WhatsApp message
# ─────────────────────────────────────────────────────────────────

SCHEME_TRIGGERS = [
    # Hindi
    "scheme", "yojana", "sarkar", "sarkari", "suvidha",
    "paisa", "paise", "labh", "benefit", "free medicine",
    "muft", "mufat", "dawai free", "paise milenge",
    "government help", "govt help", "help chahiye",
    "scheme batao", "kya milega", "kya milti hai",
    "ration", "anganwadi", "ambulance", "108",
    "jsy", "pmmvy", "jssk", "pmsma",
    "cash milega", "rupaye milenge",
    # English
    "benefit", "scheme", "government", "free",
    "ambulance", "cash", "money", "hospital free",
    "what schemes", "which schemes", "entitlement"
]

SPECIFIC_SCHEME_TRIGGERS = {
    "JSY":           ["jsy", "delivery paise", "prasav paise", "1400"],
    "PMMVY":         ["pmmvy", "5000", "matru vandana", "teen kist"],
    "JSSK":          ["jssk", "free delivery", "muft delivery", "prasav free"],
    "PMSMA":         ["pmsma", "9 tarikh", "9th", "free checkup", "muft checkup"],
    "FREE_MEDICINES":["dawai", "tablet free", "iron tablet", "goli free", "calcium"],
    "AMBULANCE_108": ["ambulance", "108", "emergency gaadi"],
    "RCH":           ["rch", "mcp card", "registration", "registration kaise"],
}


def is_scheme_request(message):
    """Check if user is asking about government schemes."""
    text = message.lower()
    return any(trigger in text for trigger in SCHEME_TRIGGERS)


def get_specific_scheme(message):
    """Check if user is asking about a specific scheme."""
    text = message.lower()
    for scheme_key, triggers in SPECIFIC_SCHEME_TRIGGERS.items():
        if any(t in text for t in triggers):
            return scheme_key
    return None


# ─────────────────────────────────────────────────────────────────
# MAIN RESPONSE FUNCTION — called from app.py
# ─────────────────────────────────────────────────────────────────

def get_scheme_response(message, week, name, language="Hindi"):
    """
    Main entry point called from app.py when scheme query detected.
    Returns formatted WhatsApp message about relevant schemes.
    """

    # Check if asking about a specific scheme
    specific = get_specific_scheme(message)
    if specific:
        return format_scheme_whatsapp(specific, language)

    # Otherwise give week-appropriate scheme summary
    relevant_keys = get_schemes_for_week(week)

    if language == "Hindi":
        msg = f"🏛 *{name}, aapke liye yeh sarkari suvidhaen available hain:*\n\n"

        for i, key in enumerate(relevant_keys, 1):
            s = SCHEMES.get(key, {})
            msg += (
                f"*{i}. {s.get('name_hindi', s.get('name',''))}*\n"
                f"   💰 {s['benefit']}\n"
                f"   📍 {s['contact']}\n\n"
            )

        msg += (
            f"Kisi bhi scheme ki poori jaankari ke liye us scheme ka "
            f"naam type karein.\n"
            f"Example: *'JSY scheme batao'* ya *'108 ambulance'*\n\n"
            f"Yeh sab MUFT hai — aapka adhikar hai! 💚"
        )
    else:
        msg = f"🏛 *{name}, these government schemes are available for you:*\n\n"

        for i, key in enumerate(relevant_keys, 1):
            s = SCHEMES.get(key, {})
            msg += (
                f"*{i}. {s['name']}*\n"
                f"   💰 {s['benefit']}\n"
                f"   📍 {s['contact']}\n\n"
            )

        msg += (
            f"For full details of any scheme, type its name.\n"
            f"Example: *'JSY scheme'* or *'108 ambulance'*\n\n"
            f"All of these are FREE — your right! 💚"
        )

    return msg


# ─────────────────────────────────────────────────────────────────
# AI-POWERED SCHEME EXPLAINER (optional, uses Groq)
# Called when user asks a complex question about a scheme
# ─────────────────────────────────────────────────────────────────

def explain_scheme_with_ai(scheme_key, question, language="Hindi"):
    """
    Uses Groq AI to answer complex questions about a specific scheme.
    Falls back to static response if AI unavailable.
    """
    scheme = SCHEMES.get(scheme_key)
    if not scheme:
        return get_scheme_response(question, 0, "aap", language)

    try:
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""You are MaaSakhi, helping a pregnant rural Indian woman 
understand government health schemes.

Scheme: {scheme['name']}
Benefit: {scheme['benefit']}
Eligibility: {scheme['who']}
How to claim: {scheme['how_to_claim']}
Documents: {', '.join(scheme['documents'])}
Contact: {scheme['contact']}

Woman's question: {question}

Answer in {language} only. Be simple, warm, and specific.
Maximum 5 sentences. Tell her exactly what to do next."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=200,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Scheme AI error: {e}")
        return format_scheme_whatsapp(scheme_key, language)