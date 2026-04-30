# ─────────────────────────────────────────────────────────────────
# MaaSakhi — child_health.py
# Child Health Engine (Month 4)
#
# Responsibilities:
#   • NHM immunization schedule (birth → 5 years)
#   • WHO growth standards (weight/height-for-age Z-scores)
#   • Newborn danger sign detection
#   • Immunization due-date calculator
#   • Growth chart data for dashboard
#   • WhatsApp counselling messages per milestone
#   • Child nutrition status classification
#   • Vitamin A & deworming schedule
#   • District-wide child health stats for analytics
# ─────────────────────────────────────────────────────────────────

from datetime import datetime, date, timedelta
from flask import render_template_string

# ─────────────────────────────────────────────────────────────────
# NHM IMMUNIZATION SCHEDULE
# Source: Government of India Universal Immunization Programme (UIP)
# ─────────────────────────────────────────────────────────────────

# Each entry: (vaccine_name, due_age_days, description, given_at)
# due_age_days: 0 = birth, 42 = 6 weeks, etc.

IMMUNIZATION_SCHEDULE = [
    # ── At Birth ──────────────────────────────────────────────────
    {
        "vaccine":      "BCG",
        "due_age_days": 0,
        "label":        "BCG",
        "description":  "Protects against Tuberculosis (TB)",
        "given_at":     "Hospital / PHC at birth",
        "dose":         1,
    },
    {
        "vaccine":      "OPV-0",
        "due_age_days": 0,
        "label":        "OPV 0 (Birth Dose)",
        "description":  "Oral Polio Vaccine — first dose at birth",
        "given_at":     "Hospital / PHC at birth",
        "dose":         1,
    },
    {
        "vaccine":      "Hepatitis B-1",
        "due_age_days": 0,
        "label":        "Hepatitis B (Birth)",
        "description":  "Protects against Hepatitis B infection",
        "given_at":     "Hospital / PHC at birth",
        "dose":         1,
    },

    # ── 6 Weeks (42 days) ─────────────────────────────────────────
    {
        "vaccine":      "OPV-1",
        "due_age_days": 42,
        "label":        "OPV 1",
        "description":  "Oral Polio Vaccine — second dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },
    {
        "vaccine":      "Pentavalent-1",
        "due_age_days": 42,
        "label":        "Pentavalent 1 (DPT + HepB + Hib)",
        "description":  "Protects against Diphtheria, Pertussis, Tetanus, Hepatitis B & Hib",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },
    {
        "vaccine":      "IPV-1",
        "due_age_days": 42,
        "label":        "IPV 1 (Inactivated Polio)",
        "description":  "Injectable Polio Vaccine — first dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },
    {
        "vaccine":      "Rotavirus-1",
        "due_age_days": 42,
        "label":        "Rotavirus 1",
        "description":  "Protects against severe diarrhoea from Rotavirus",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },
    {
        "vaccine":      "PCV-1",
        "due_age_days": 42,
        "label":        "PCV 1 (Pneumococcal)",
        "description":  "Protects against Pneumonia and Meningitis",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },

    # ── 10 Weeks (70 days) ────────────────────────────────────────
    {
        "vaccine":      "OPV-2",
        "due_age_days": 70,
        "label":        "OPV 2",
        "description":  "Oral Polio Vaccine — third dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         3,
    },
    {
        "vaccine":      "Pentavalent-2",
        "due_age_days": 70,
        "label":        "Pentavalent 2",
        "description":  "Second dose of DPT + HepB + Hib",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },
    {
        "vaccine":      "Rotavirus-2",
        "due_age_days": 70,
        "label":        "Rotavirus 2",
        "description":  "Second dose against Rotavirus diarrhoea",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },
    {
        "vaccine":      "PCV-2",
        "due_age_days": 70,
        "label":        "PCV 2",
        "description":  "Second Pneumococcal dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },

    # ── 14 Weeks (98 days) ────────────────────────────────────────
    {
        "vaccine":      "OPV-3",
        "due_age_days": 98,
        "label":        "OPV 3",
        "description":  "Oral Polio Vaccine — fourth dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         4,
    },
    {
        "vaccine":      "Pentavalent-3",
        "due_age_days": 98,
        "label":        "Pentavalent 3",
        "description":  "Third dose of DPT + HepB + Hib",
        "given_at":     "Sub-centre / PHC",
        "dose":         3,
    },
    {
        "vaccine":      "IPV-2",
        "due_age_days": 98,
        "label":        "IPV 2",
        "description":  "Injectable Polio — second dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },
    {
        "vaccine":      "Rotavirus-3",
        "due_age_days": 98,
        "label":        "Rotavirus 3",
        "description":  "Third and final Rotavirus dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         3,
    },
    {
        "vaccine":      "PCV-Booster",
        "due_age_days": 98,
        "label":        "PCV Booster",
        "description":  "Pneumococcal booster dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         3,
    },

    # ── 9 Months (270 days) ───────────────────────────────────────
    {
        "vaccine":      "Measles-Rubella-1",
        "due_age_days": 270,
        "label":        "MR 1 (Measles-Rubella)",
        "description":  "Protects against Measles and Rubella",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },
    {
        "vaccine":      "JE-1",
        "due_age_days": 270,
        "label":        "JE 1 (Japanese Encephalitis)",
        "description":  "Protects against Japanese Encephalitis (endemic areas)",
        "given_at":     "Sub-centre / PHC",
        "dose":         1,
    },
    {
        "vaccine":      "Vitamin-A-1",
        "due_age_days": 270,
        "label":        "Vitamin A (1st dose — 1 lakh IU)",
        "description":  "Prevents night blindness and immune support",
        "given_at":     "Sub-centre / Anganwadi",
        "dose":         1,
    },

    # ── 16–24 Months ──────────────────────────────────────────────
    {
        "vaccine":      "Measles-Rubella-2",
        "due_age_days": 487,    # ~16 months
        "label":        "MR 2 (Booster)",
        "description":  "Second dose of Measles-Rubella vaccine",
        "given_at":     "Sub-centre / PHC",
        "dose":         2,
    },
    {
        "vaccine":      "DPT-Booster-1",
        "due_age_days": 487,
        "label":        "DPT Booster 1",
        "description":  "Booster dose for Diphtheria, Pertussis, Tetanus",
        "given_at":     "Sub-centre / PHC",
        "dose":         4,
    },
    {
        "vaccine":      "OPV-Booster",
        "due_age_days": 487,
        "label":        "OPV Booster",
        "description":  "Booster polio dose",
        "given_at":     "Sub-centre / PHC",
        "dose":         5,
    },
    {
        "vaccine":      "Vitamin-A-2",
        "due_age_days": 548,   # 18 months
        "label":        "Vitamin A (2nd dose — 2 lakh IU)",
        "description":  "Second Vitamin A dose",
        "given_at":     "Sub-centre / Anganwadi",
        "dose":         2,
    },

    # ── 5 Years ───────────────────────────────────────────────────
    {
        "vaccine":      "DPT-Booster-2",
        "due_age_days": 1825,   # 5 years
        "label":        "DPT Booster 2 (5 Years)",
        "description":  "Final childhood DPT booster",
        "given_at":     "School / PHC",
        "dose":         5,
    },
]

# ── Vitamin A schedule: doses every 6 months from 9m to 5 years
VITAMIN_A_DOSES = [
    (270,   "1 lakh IU",  1),   # 9 months
    (548,   "2 lakh IU",  2),   # 18 months
    (730,   "2 lakh IU",  3),   # 2 years
    (912,   "2 lakh IU",  4),   # 2.5 years
    (1095,  "2 lakh IU",  5),   # 3 years
    (1277,  "2 lakh IU",  6),   # 3.5 years
    (1460,  "2 lakh IU",  7),   # 4 years
    (1642,  "2 lakh IU",  8),   # 4.5 years
    (1825,  "2 lakh IU",  9),   # 5 years
]

# ─────────────────────────────────────────────────────────────────
# IMMUNIZATION CALCULATOR
# ─────────────────────────────────────────────────────────────────

def get_immunization_schedule(dob_str: str) -> list[dict]:
    """
    Given a date-of-birth string, return the full immunization schedule
    with due dates and status for each vaccine.

    Each entry:
        {
            "vaccine":      str,
            "label":        str,
            "description":  str,
            "given_at":     str,
            "due_date":     date,
            "due_age_days": int,
            "status":       "given" | "due_today" | "overdue" | "upcoming",
            "days_away":    int,   # negative = past
        }
    """
    try:
        dob = _parse_date(dob_str)
    except Exception:
        return []

    today    = date.today()
    schedule = []

    for item in IMMUNIZATION_SCHEDULE:
        due_date  = dob + timedelta(days=item["due_age_days"])
        days_away = (due_date - today).days

        if days_away < -3:
            status = "overdue"
        elif abs(days_away) <= 3:
            status = "due_today"
        else:
            status = "upcoming"

        schedule.append({
            **item,
            "due_date":  due_date,
            "days_away": days_away,
            "status":    status,
        })

    return schedule


def mark_given_vaccines(schedule: list[dict], given_set: set) -> list[dict]:
    """
    Mark vaccines in the schedule as 'given' if they appear in given_set.
    given_set: set of vaccine name strings from immunization_records table.
    """
    for item in schedule:
        if item["vaccine"] in given_set:
            item["status"] = "given"
    return schedule


def get_next_due_vaccines(child_id: int, dob_str: str,
                           limit: int = 3) -> list[dict]:
    """
    Returns the next N vaccines due for a child (not yet given).
    Fetches given vaccines from DB automatically.
    """
    from database import get_immunization_records
    given = {r["vaccine_name"] for r in get_immunization_records(child_id)}
    schedule = get_immunization_schedule(dob_str)
    schedule = mark_given_vaccines(schedule, given)

    due = [
        s for s in schedule
        if s["status"] in ("overdue", "due_today", "upcoming")
    ]
    return due[:limit]


def get_overdue_vaccines(child_id: int, dob_str: str) -> list[dict]:
    """Returns all overdue vaccines for a child."""
    from database import get_immunization_records
    given = {r["vaccine_name"] for r in get_immunization_records(child_id)}
    schedule = get_immunization_schedule(dob_str)
    schedule = mark_given_vaccines(schedule, given)
    return [s for s in schedule if s["status"] == "overdue"]


def immunization_completion_rate(child_id: int, dob_str: str) -> float:
    """
    Returns % of age-appropriate vaccines given so far (0.0 – 100.0).
    Only counts vaccines that were due by today.
    """
    from database import get_immunization_records
    given    = {r["vaccine_name"] for r in get_immunization_records(child_id)}
    schedule = get_immunization_schedule(dob_str)

    should_have = [
        s for s in schedule
        if s["days_away"] <= 0   # due date has passed
    ]
    if not should_have:
        return 100.0

    given_count = sum(1 for s in should_have if s["vaccine"] in given)
    return round(given_count / len(should_have) * 100, 1)


# ─────────────────────────────────────────────────────────────────
# WHO GROWTH STANDARDS
# Simplified weight-for-age medians (boys, approximate)
# Source: WHO Child Growth Standards 2006
# ─────────────────────────────────────────────────────────────────

# (age_months: median_weight_kg) — boys reference, approximate
WHO_WEIGHT_MEDIANS_BOYS = {
    0:  3.3,  1:  4.5,  2:  5.6,  3:  6.4,
    4:  7.0,  5:  7.5,  6:  7.9,  7:  8.3,
    8:  8.6,  9:  9.0, 10:  9.2, 11:  9.4,
    12: 9.6, 15: 10.3, 18: 10.9, 21: 11.5,
    24: 12.2, 30: 13.3, 36: 14.3, 42: 15.3,
    48: 16.3, 54: 17.3, 60: 18.3,
}

# Girls reference (slightly lower)
WHO_WEIGHT_MEDIANS_GIRLS = {
    0:  3.2,  1:  4.2,  2:  5.1,  3:  5.8,
    4:  6.4,  5:  6.9,  6:  7.3,  7:  7.6,
    8:  7.9,  9:  8.2, 10:  8.5, 11:  8.7,
    12: 8.9, 15: 9.6,  18: 10.2, 21: 10.9,
    24: 11.5, 30: 12.7, 36: 13.9, 42: 14.9,
    48: 15.9, 54: 16.9, 60: 17.9,
}

# Height-for-age medians (boys, cm)
WHO_HEIGHT_MEDIANS_BOYS = {
    0:  49.9,  3: 61.4,  6: 67.6,  9: 72.3,
    12: 75.7, 18: 82.3, 24: 87.8, 36: 96.1,
    48: 103.3, 60: 110.0,
}

WHO_HEIGHT_MEDIANS_GIRLS = {
    0:  49.1,  3: 59.8,  6: 65.7,  9: 70.1,
    12: 74.0, 18: 80.7, 24: 86.4, 36: 95.1,
    48: 102.7, 60: 109.4,
}


def _closest_age(medians: dict, age_months: int) -> float:
    """Return the median for the closest age key."""
    closest = min(medians.keys(), key=lambda x: abs(x - age_months))
    return medians[closest]


def calc_weight_z_score(weight_kg: float, age_months: int,
                         gender: str = "male") -> float:
    """
    Calculate approximate WHO weight-for-age Z-score.
    Uses simplified formula: Z = (weight - median) / (SD ≈ median × 0.13)
    """
    medians = (
        WHO_WEIGHT_MEDIANS_GIRLS
        if gender.lower() in ("female", "girl", "f")
        else WHO_WEIGHT_MEDIANS_BOYS
    )
    median = _closest_age(medians, age_months)
    sd     = median * 0.13    # approximate standard deviation
    return round((weight_kg - median) / sd, 2)


def calc_height_z_score(height_cm: float, age_months: int,
                          gender: str = "male") -> float:
    """Calculate approximate WHO height-for-age Z-score."""
    medians = (
        WHO_HEIGHT_MEDIANS_GIRLS
        if gender.lower() in ("female", "girl", "f")
        else WHO_HEIGHT_MEDIANS_BOYS
    )
    median = _closest_age(medians, age_months)
    sd     = median * 0.05
    return round((height_cm - median) / sd, 2)


def classify_nutrition(weight_z: float) -> dict:
    """
    Classify child nutrition status from weight-for-age Z-score.
    Returns {status, label, color, action, whatsapp_msg}
    """
    if weight_z >= -1:
        return {
            "status":       "Normal",
            "label":        "Well Nourished",
            "color":        "#10b981",
            "bg_color":     "#f0fdf4",
            "action":       "Continue breastfeeding and complementary feeding.",
            "whatsapp_msg": (
                "✅ *Baby ka vikas bilkul normal hai!*\n\n"
                "Breastfeeding aur aahar jaari rakhein. 💚"
            ),
        }
    elif weight_z >= -2:
        return {
            "status":       "MAM",
            "label":        "Moderate Acute Malnutrition",
            "color":        "#f59e0b",
            "bg_color":     "#fffbeb",
            "action":       "Increase feeding frequency. Refer to ICDS/Anganwadi for supplementary nutrition.",
            "whatsapp_msg": (
                "⚠️ *Baby ka vajan thoda kam hai.*\n\n"
                "Kya karein:\n"
                "🥛 Breastfeeding zyada baar karein\n"
                "🥗 Aahar mein doodh, dal, anday shaamil karein\n"
                "📍 Anganwadi se poshan aahar lein\n\n"
                "Aapki ASHA worker aapko madad karegi. 💚"
            ),
        }
    elif weight_z >= -3:
        return {
            "status":       "SAM",
            "label":        "Severe Acute Malnutrition",
            "color":        "#ef4444",
            "bg_color":     "#fef2f2",
            "action":       "URGENT: Refer to Nutrition Rehabilitation Centre (NRC) immediately.",
            "whatsapp_msg": (
                "🚨 *EMERGENCY — Baby ka vajan bahut kam hai!*\n\n"
                "Aapki ASHA worker ko abhi call karein.\n"
                "Apne najdeeki NRC (Nutrition Rehabilitation Centre) jaayein.\n\n"
                "Yeh bahut zaroori hai. 🏥💚"
            ),
        }
    else:
        return {
            "status":       "Severe SAM",
            "label":        "Severe Wasting",
            "color":        "#7c2d12",
            "bg_color":     "#fef2f2",
            "action":       "CRITICAL: Immediate hospitalisation at NRC/District Hospital.",
            "whatsapp_msg": (
                "🚨 *CRITICAL — Baby ko turant hospital le jaayein!*\n\n"
                "Yeh bahut khatarnak sthiti hai.\n"
                "Abhi District Hospital ya NRC jaayein. 108 call karein.\n\n"
                "Aap akeli nahi hain. 💚"
            ),
        }


# ─────────────────────────────────────────────────────────────────
# NEWBORN DANGER SIGN DETECTION
# ─────────────────────────────────────────────────────────────────

NEWBORN_RED_SIGNS = [
    # Feeding
    "nahi pi raha", "not feeding", "feed nahi", "doodh nahi pi",
    "breastfeed nahi", "kuch nahi kha raha",

    # Temperature
    "thanda", "cold to touch", "hypothermia", "badan thanda",
    "bukhaar", "fever", "garmi", "temperature high",

    # Jaundice
    "peela", "jaundice", "yellow", "pili aankhen",
    "pagdi peeli", "skin yellow",

    # Breathing
    "saans nahi", "breathless", "tez saans", "fast breathing",
    "saans rokna", "apnoea", "apnea",

    # Seizures / consciousness
    "fits", "convulsion", "seizure", "behosh", "unconscious",
    "body hil raha", "akad",

    # Umbilical
    "navel infection", "nabi mein pus", "nabi lal", "umbilical pus",
    "nabi se khoon", "umbilical bleeding",

    # Colour
    "neela", "blue lips", "cyanosis",

    # Cry / movement
    "rona band", "not crying", "movement nahi", "bilkul nahi hil raha",
]

NEWBORN_AMBER_SIGNS = [
    "thoda peela", "mild jaundice", "slight fever",
    "rona zyada", "crying a lot", "loose motion",
    "diarrhea", "potty zyada", "urine kam",
    "navel thoda lal", "eye discharge", "aankh se pani",
]


def analyse_newborn_message(message: str,
                             language: str = "Hindi") -> tuple[str, str]:
    """
    Analyse a WhatsApp message about a newborn (0–28 days).
    Returns (level, reply_text) — level: 'RED', 'AMBER', or 'GREEN'.
    Called from analyzer.py for postpartum patients with young infants.
    """
    msg_lower = message.lower()
    lang_key  = "en" if language.lower() in ("english", "en") else "hi"

    for sign in NEWBORN_RED_SIGNS:
        if sign in msg_lower:
            return "RED", _newborn_red_reply(lang_key)

    for sign in NEWBORN_AMBER_SIGNS:
        if sign in msg_lower:
            return "AMBER", _newborn_amber_reply(lang_key)

    return "GREEN", _newborn_green_reply(lang_key)


def _newborn_red_reply(lang: str) -> str:
    if lang == "hi":
        return (
            "🚨 *EMERGENCY — Baby ke liye Turant Madad Zaroor!*\n\n"
            "Aapne jo bataya woh newborn ka khatarnak sign hai.\n\n"
            "🏥 *Abhi karo:*\n"
            "1️⃣ 108 ambulance call karein\n"
            "2️⃣ Apni ASHA worker ko call karein\n"
            "3️⃣ Najdeeki District Hospital jaayein\n\n"
            "Baby ko garam rakhein aur breastfeed karte rahein.\n"
            "Aap akeli nahi hain. 💚"
        )
    return (
        "🚨 *EMERGENCY — Baby Needs Urgent Care!*\n\n"
        "What you described is a newborn danger sign.\n\n"
        "🏥 *Do this now:*\n"
        "1️⃣ Call 108 ambulance\n"
        "2️⃣ Call your ASHA worker\n"
        "3️⃣ Go to nearest District Hospital\n\n"
        "Keep baby warm and continue breastfeeding.\n"
        "You are not alone. 💚"
    )


def _newborn_amber_reply(lang: str) -> str:
    if lang == "hi":
        return (
            "⚠️ *Baby ka dhyan rakhein*\n\n"
            "Aapne jo bataya woh normal bhi ho sakta hai, lekin ASHA worker "
            "ko aaj zaroor batayein.\n\n"
            "Agar yeh problem 24 ghante mein theek na ho — PHC jaayein.\n\n"
            "Baby ko garam rakhein, breastfeed jaari rakhein. 💚"
        )
    return (
        "⚠️ *Keep a Close Watch on Baby*\n\n"
        "What you described may be normal, but please inform your ASHA "
        "worker today.\n\n"
        "If it doesn't improve in 24 hours — visit your PHC.\n\n"
        "Keep baby warm and continue breastfeeding. 💚"
    )


def _newborn_green_reply(lang: str) -> str:
    if lang == "hi":
        return (
            "🌸 *Baby bilkul theek lag raha hai!*\n\n"
            "Kuch zaroori baatein:\n"
            "🤱 Breastfeed din mein 8–12 baar\n"
            "🌡 Baby ka temperature 36.5–37.5°C hona chahiye\n"
            "💛 3 din ke baad peela (jaundice) ho toh turant batayein\n"
            "🧴 Navel saaf aur sukha rakhein\n"
            "💤 Neend mein saans regular honi chahiye\n\n"
            "Koi bhi sawaal ho toh batayein. 💚"
        )
    return (
        "🌸 *Baby seems to be doing well!*\n\n"
        "Important reminders:\n"
        "🤱 Breastfeed 8–12 times per day\n"
        "🌡 Baby temperature should be 36.5–37.5°C\n"
        "💛 Jaundice beyond Day 3 — report immediately\n"
        "🧴 Keep umbilical cord clean and dry\n"
        "💤 Breathing should be regular during sleep\n\n"
        "Ask me anything. 💚"
    )


# ─────────────────────────────────────────────────────────────────
# AGE CALCULATOR
# ─────────────────────────────────────────────────────────────────

def child_age_months(dob_str: str) -> int | None:
    """Returns child age in complete months from DOB string."""
    try:
        dob   = _parse_date(dob_str)
        today = date.today()
        months = (today.year - dob.year) * 12 + (today.month - dob.month)
        if today.day < dob.day:
            months -= 1
        return max(months, 0)
    except Exception:
        return None


def child_age_days(dob_str: str) -> int | None:
    """Returns child age in days from DOB string."""
    try:
        dob = _parse_date(dob_str)
        return (date.today() - dob).days
    except Exception:
        return None


def _parse_date(date_str: str) -> date:
    """Parse a date string in multiple formats."""
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
                "%d %B %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


# ─────────────────────────────────────────────────────────────────
# IMMUNIZATION WHATSAPP REMINDERS
# ─────────────────────────────────────────────────────────────────

def build_vaccine_reminder(
    mother_name:    str,
    child_name:     str,
    vaccines_due:   list[dict],
    language:       str = "Hindi",
    asha_name:      str = "",
) -> str:
    """
    Build a WhatsApp reminder for upcoming vaccines.
    vaccines_due: list of vaccine schedule dicts from get_next_due_vaccines()
    """
    lang_key = "en" if language.lower() in ("english", "en") else "hi"

    if not vaccines_due:
        if lang_key == "hi":
            return (
                f"✅ {mother_name}, {child_name} ke saare aage ke "
                "vaccines abhi due nahi hain. 💚\nApni ASHA worker se "
                "agla schedule poochhein."
            )
        return (
            f"✅ {mother_name}, {child_name}'s next vaccines are not "
            "due yet. 💚\nAsk your ASHA worker about the next schedule."
        )

    next_v   = vaccines_due[0]
    due_str  = next_v["due_date"].strftime("%d %b %Y")
    vax_list = "\n".join(f"  • {v['label']}" for v in vaccines_due[:3])

    if lang_key == "hi":
        msg = (
            f"💉 *{child_name} ka Vaccine Due Hai!*\n\n"
            f"Namaste {mother_name}!\n\n"
            f"Agla vaccine {due_str} ko lagana hai:\n"
            f"{vax_list}\n\n"
            f"📍 Kahan jaayein: {next_v['given_at']}\n\n"
            f"Vaccines samay par lagwana bahut zaroori hai —\n"
            f"yeh bacche ko serious bimariyon se bachata hai. 💚"
        )
    else:
        msg = (
            f"💉 *{child_name}'s Vaccine is Due!*\n\n"
            f"Hello {mother_name}!\n\n"
            f"Next vaccine due on {due_str}:\n"
            f"{vax_list}\n\n"
            f"📍 Where to go: {next_v['given_at']}\n\n"
            f"Timely vaccination is very important —\n"
            f"it protects your child from serious diseases. 💚"
        )

    if asha_name:
        if lang_key == "hi":
            msg += f"\n\n👩 Aapki ASHA worker *{asha_name}* aapki madad karegi."
        else:
            msg += f"\n\n👩 Your ASHA worker *{asha_name}* will assist you."

    return msg


def build_overdue_vaccine_asha_alert(
    mother_name:   str,
    mother_phone:  str,
    child_name:    str,
    overdue:       list[dict],
) -> str:
    """
    Alert sent to ASHA worker when a child has overdue vaccines.
    """
    vax_list = "\n".join(
        f"  • {v['label']} (was due {v['due_date'].strftime('%d %b')})"
        for v in overdue[:4]
    )
    return (
        f"⚠️ *Overdue Vaccines Alert*\n\n"
        f"Child: {child_name}\n"
        f"Mother: {mother_name}\n"
        f"Phone: {mother_phone}\n\n"
        f"Missing vaccines:\n{vax_list}\n\n"
        f"Please follow up with this family at your next visit. 💚"
    )


# ─────────────────────────────────────────────────────────────────
# DEWORMING SCHEDULE
# ─────────────────────────────────────────────────────────────────

# National Deworming Day — twice yearly for children 1–19 years
DEWORMING_AGES_MONTHS = [12, 24, 30, 36, 42, 48, 54, 60]


def is_deworming_due(dob_str: str) -> bool:
    """Returns True if child is in 12–60 month range (eligible for deworming)."""
    age = child_age_months(dob_str)
    if age is None:
        return False
    return 12 <= age <= 60


def deworming_counsel(language: str = "Hindi") -> str:
    lang_key = "en" if language.lower() in ("english", "en") else "hi"
    if lang_key == "hi":
        return (
            "💊 *Deworming (Keeda Nikalne ki Dawai)*\n\n"
            "1–5 saal ke bacchon ko saal mein 2 baar deworming tablet "
            "(Albendazole 400mg) di jaati hai.\n\n"
            "Yeh bacche ke pet ke keede maarta hai aur poshan behtar karta hai.\n"
            "Anganwadi ya PHC mein available hai. 💚"
        )
    return (
        "💊 *Deworming Tablet*\n\n"
        "Children aged 1–5 years receive deworming tablets (Albendazole 400mg) "
        "twice a year under the National Deworming Programme.\n\n"
        "This removes intestinal worms and improves nutrition absorption.\n"
        "Available at Anganwadi or PHC. 💚"
    )


# ─────────────────────────────────────────────────────────────────
# GROWTH CHART DATA
# ─────────────────────────────────────────────────────────────────

def get_growth_chart_data(child_id: int) -> dict:
    """
    Returns structured data for rendering a growth chart.
    {
        "months":       [0, 2, 4, 6, ...]
        "weights":      [3.2, 4.1, 5.5, ...]
        "who_median":   [3.3, 5.6, 7.0, ...]
        "who_minus2sd": [2.1, 3.6, 4.6, ...]
        "who_plus2sd":  [4.5, 7.5, 9.4, ...]
        "z_scores":     [-0.1, 0.3, ...]
        "statuses":     ["Normal", "Normal", ...]
        "latest_z":     float
        "latest_status": str
    }
    """
    from database import get_growth_logs

    logs = get_growth_logs(child_id)

    months   = []
    weights  = []
    z_scores = []
    statuses = []

    for log in logs:
        months.append(log["age_months"])
        weights.append(float(log["weight_kg"]) if log["weight_kg"] else 0)
        z_scores.append(float(log["z_score"]) if log["z_score"] else 0)
        statuses.append(log["status"] or "Unknown")

    # WHO reference lines for the observed age range
    age_range      = list(range(0, max(months or [12]) + 3, 3))
    who_median     = [_closest_age(WHO_WEIGHT_MEDIANS_BOYS, m) for m in age_range]
    who_minus2sd   = [round(v * (1 - 2 * 0.13), 2) for v in who_median]
    who_plus2sd    = [round(v * (1 + 2 * 0.13), 2) for v in who_median]

    return {
        "months":         months,
        "weights":        weights,
        "z_scores":       z_scores,
        "statuses":       statuses,
        "who_age_range":  age_range,
        "who_median":     who_median,
        "who_minus2sd":   who_minus2sd,
        "who_plus2sd":    who_plus2sd,
        "latest_z":       z_scores[-1]  if z_scores  else None,
        "latest_status":  statuses[-1]  if statuses  else "No data",
        "data_points":    len(logs),
    }


def _growth_sparkline_svg(weights: list, w: int = 100, h: int = 36) -> str:
    """Tiny inline SVG sparkline for weight trend."""
    if not weights or len(weights) < 2:
        return ""
    mx = max(weights)
    mn = min(weights)
    rng = mx - mn or 1
    n   = len(weights)
    pts = []
    for i, v in enumerate(weights):
        x = round(i / (n - 1) * w, 1)
        y = round(h - ((v - mn) / rng * (h - 4)) - 2, 1)
        pts.append(f"{x},{y}")
    path = "M " + " L ".join(pts)
    fill_pts = pts + [f"{w},{h}", f"0,{h}"]
    fp   = "M " + " L ".join(fill_pts) + " Z"
    last = pts[-1].split(",")
    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="{fp}" fill="#0d8f72" fill-opacity="0.15"/>'
        f'<path d="{path}" stroke="#0d8f72" stroke-width="2" '
        f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last[0]}" cy="{last[1]}" r="3" fill="#0d8f72"/>'
        f'</svg>'
    )


# ─────────────────────────────────────────────────────────────────
# FULL CHILD HEALTH DATA FOR DASHBOARD
# ─────────────────────────────────────────────────────────────────

def get_child_dashboard_data(mother_phone: str) -> list[dict]:
    """
    Returns all child health data for a mother — ready for dashboard rendering.
    Each child dict includes:
        identity, growth_chart, immunization_schedule, overdue_vaccines,
        next_due_vaccines, nutrition_status, age_months, age_days
    """
    from database import (
        get_children, get_growth_logs,
        get_immunization_records,
    )

    children = get_children(mother_phone)
    result   = []

    for child in children:
        dob_str   = child.get("dob", "")
        gender    = child.get("gender", "male")
        child_id  = child["id"]

        age_m  = child_age_months(dob_str)
        age_d  = child_age_days(dob_str)

        # Growth
        growth_logs  = get_growth_logs(child_id)
        growth_chart = get_growth_chart_data(child_id)

        # Latest nutrition status
        if growth_logs:
            latest = growth_logs[-1]
            w_kg   = float(latest["weight_kg"]) if latest["weight_kg"] else None
            if w_kg and age_m is not None:
                z     = calc_weight_z_score(w_kg, age_m, gender)
                nutri = classify_nutrition(z)
            else:
                nutri = classify_nutrition(0)
        else:
            nutri = {"status": "No data", "label": "No growth data",
                     "color": "#94a3b8", "bg_color": "#f8fafc",
                     "action": "Log first weight measurement.", "whatsapp_msg": ""}

        # Immunization
        given_records = get_immunization_records(child_id)
        given_set     = {r["vaccine_name"] for r in given_records}
        schedule      = get_immunization_schedule(dob_str)
        schedule      = mark_given_vaccines(schedule, given_set)
        overdue       = [s for s in schedule if s["status"] == "overdue"]
        due_today     = [s for s in schedule if s["status"] == "due_today"]
        next_due      = [s for s in schedule if s["status"] in ("due_today", "upcoming")][:3]
        completion    = immunization_completion_rate(child_id, dob_str) if dob_str else 0.0

        # Growth sparkline
        weights   = [float(g["weight_kg"]) for g in growth_logs if g["weight_kg"]]
        sparkline = _growth_sparkline_svg(weights)

        # Deworming
        deworming_eligible = is_deworming_due(dob_str) if dob_str else False

        result.append({
            **child,
            "age_months":           age_m,
            "age_days":             age_d,
            "growth_logs":          growth_logs,
            "growth_chart":         growth_chart,
            "nutrition":            nutri,
            "weight_sparkline":     sparkline,
            "immunizations_given":  list(given_set),
            "full_schedule":        schedule,
            "overdue_vaccines":     overdue,
            "due_today_vaccines":   due_today,
            "next_due_vaccines":    next_due,
            "immunization_rate":    completion,
            "total_given":          len(given_set),
            "total_due_by_now":     len([s for s in schedule if s["days_away"] <= 0]),
            "deworming_eligible":   deworming_eligible,
        })

    return result


# ─────────────────────────────────────────────────────────────────
# DISTRICT-WIDE CHILD HEALTH STATS
# ─────────────────────────────────────────────────────────────────

def get_district_child_stats() -> dict:
    """District-wide child health summary for analytics dashboard."""
    from database import engine
    if not engine:
        return {}

    from sqlalchemy import text
    stats = {}

    try:
        with engine.connect() as conn:
            stats["total_children"] = conn.execute(text(
                "SELECT COUNT(*) FROM children"
            )).scalar() or 0

            stats["total_vaccines_given"] = conn.execute(text(
                "SELECT COUNT(*) FROM immunization_records"
            )).scalar() or 0

            stats["total_growth_logs"] = conn.execute(text(
                "SELECT COUNT(*) FROM child_growth_logs"
            )).scalar() or 0

            # BCG coverage (most basic indicator)
            stats["bcg_coverage"] = conn.execute(text("""
                SELECT COUNT(DISTINCT child_id) FROM immunization_records
                WHERE vaccine_name = 'BCG'
            """)).scalar() or 0

            # Fully immunized (MR-2 given = roughly complete schedule)
            stats["fully_immunized"] = conn.execute(text("""
                SELECT COUNT(DISTINCT child_id) FROM immunization_records
                WHERE vaccine_name = 'Measles-Rubella-2'
            """)).scalar() or 0

            # Nutrition distribution from growth logs
            nutrition_rows = conn.execute(text("""
                SELECT status, COUNT(*) AS cnt
                FROM child_growth_logs
                WHERE age_months = (
                    SELECT MAX(age_months) FROM child_growth_logs cgl2
                    WHERE cgl2.child_id = child_growth_logs.child_id
                )
                GROUP BY status
            """)).fetchall()
            stats["nutrition_breakdown"] = {r.status: int(r.cnt) for r in nutrition_rows}

            # Vaccine breakdown
            vax_rows = conn.execute(text("""
                SELECT vaccine_name, COUNT(DISTINCT child_id) AS cnt
                FROM immunization_records
                GROUP BY vaccine_name
                ORDER BY cnt DESC
                LIMIT 10
            """)).fetchall()
            stats["vaccine_coverage"] = [
                {"vaccine": r.vaccine_name, "count": int(r.cnt)}
                for r in vax_rows
            ]

            # Average birth weight
            avg_bw = conn.execute(text("""
                SELECT AVG(CAST(birth_weight AS FLOAT))
                FROM deliveries
                WHERE birth_weight IS NOT NULL
                  AND birth_weight != ''
                  AND birth_weight ~ '^[0-9.]+$'
            """)).scalar()
            stats["avg_birth_weight_kg"] = round(float(avg_bw), 2) if avg_bw else None

            # Low birth weight
            stats["low_birth_weight_count"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
                WHERE birth_weight IS NOT NULL
                  AND birth_weight ~ '^[0-9.]+$'
                  AND CAST(birth_weight AS FLOAT) < 2.5
            """)).scalar() or 0

    except Exception as e:
        print(f"child_health.py get_district_child_stats error: {e}")

    return stats


# ─────────────────────────────────────────────────────────────────
# HTML RENDER — child health card for ASHA dashboard
# ─────────────────────────────────────────────────────────────────

CHILD_CARD_HTML = """
<div style="background:white;border-radius:14px;padding:16px 18px;
            border:1px solid #ede9fe;box-shadow:0 2px 10px rgba(124,58,237,0.07);
            margin-bottom:12px">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div style="font-weight:700;font-size:14px">{{ child.child_name }}</div>
      <div style="font-size:11.5px;color:#64748b;margin-top:2px">
        DOB: {{ child.dob }}
        {% if child.age_months is not none %}
          &nbsp;·&nbsp; {{ child.age_months }} months old
        {% endif %}
        {% if child.gender %} &nbsp;·&nbsp; {{ child.gender }}{% endif %}
      </div>
      {% if child.birth_weight %}
      <div style="font-size:11px;color:#94a3b8">
        Birth weight: {{ child.birth_weight }} kg
      </div>
      {% endif %}
    </div>
    <!-- Nutrition badge -->
    <span style="padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;
                 background:{{ child.nutrition.bg_color }};color:{{ child.nutrition.color }};
                 border:1px solid {{ child.nutrition.color }}40">
      {{ child.nutrition.label }}
    </span>
  </div>

  <!-- Weight sparkline -->
  {% if child.weight_sparkline %}
  <div style="margin-top:8px">
    {{ child.weight_sparkline }}
  </div>
  {% endif %}

  <!-- Immunization progress bar -->
  <div style="margin-top:10px">
    <div style="display:flex;justify-content:space-between;
                font-size:10.5px;color:#64748b;margin-bottom:3px">
      <span>Immunization Coverage</span>
      <span style="font-weight:700;color:#0d8f72">
        {{ child.immunization_rate }}% ({{ child.total_given }}/{{ child.total_due_by_now }})
      </span>
    </div>
    <div style="height:5px;background:#f1f5f9;border-radius:3px;overflow:hidden">
      <div style="height:100%;border-radius:3px;background:#0d8f72;
                  width:{{ child.immunization_rate }}%;transition:width 1.2s ease">
      </div>
    </div>
  </div>

  <!-- Overdue vaccines warning -->
  {% if child.overdue_vaccines %}
  <div style="margin-top:10px;padding:8px 12px;background:#fdecea;
              border:1px solid #fecaca;border-radius:8px">
    <div style="font-size:11.5px;font-weight:600;color:#991b1b;margin-bottom:4px">
      ⚠️ {{ child.overdue_vaccines|length }} Overdue Vaccine(s)
    </div>
    {% for v in child.overdue_vaccines[:3] %}
    <div style="font-size:11px;color:#dc2626">
      • {{ v.label }} (was due {{ v.due_date.strftime('%d %b') }})
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Due today vaccines -->
  {% if child.due_today_vaccines %}
  <div style="margin-top:8px;padding:8px 12px;background:#fffbeb;
              border:1px solid #fde68a;border-radius:8px">
    <div style="font-size:11.5px;font-weight:600;color:#92400e">
      💉 Due Today:
      {% for v in child.due_today_vaccines %}
        {{ v.label }}{% if not loop.last %}, {% endif %}
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Next upcoming vaccines -->
  {% if child.next_due_vaccines and not child.due_today_vaccines %}
  <div style="margin-top:8px">
    <div style="font-size:10.5px;color:#64748b;font-weight:600;margin-bottom:4px">
      NEXT VACCINES DUE
    </div>
    {% for v in child.next_due_vaccines[:2] %}
    <div style="font-size:11px;color:#0d8f72;display:flex;justify-content:space-between">
      <span>• {{ v.label }}</span>
      <span style="color:#94a3b8">{{ v.due_date.strftime('%d %b %Y') }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Deworming badge -->
  {% if child.deworming_eligible %}
  <div style="margin-top:8px;display:inline-block;padding:3px 10px;
              background:#f0fdf4;border:1px solid #bbf7d0;
              border-radius:20px;font-size:10.5px;font-weight:600;color:#16a34a">
    ✓ Eligible for Deworming (Albendazole)
  </div>
  {% endif %}

  <!-- Action buttons -->
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
    <button onclick="toggleForm('growth-{{ child.id }}')"
            style="padding:6px 14px;background:#0d8f72;color:white;border:none;
                   border-radius:8px;font-size:11px;font-weight:600;cursor:pointer">
      📏 Log Growth
    </button>
    <button onclick="toggleForm('vaccine-{{ child.id }}')"
            style="padding:6px 14px;background:#7c3aed;color:white;border:none;
                   border-radius:8px;font-size:11px;font-weight:600;cursor:pointer">
      💉 Log Vaccine
    </button>
  </div>

</div>
"""


def render_child_card(child: dict) -> str:
    """Render a single child health card for the ASHA dashboard."""
    return render_template_string(CHILD_CARD_HTML, child=child)


def render_all_child_cards(mother_phone: str) -> str:
    """Render all child health cards for a mother."""
    children = get_child_dashboard_data(mother_phone)
    if not children:
        return (
            '<div style="text-align:center;padding:20px;color:#94a3b8;font-size:12px">'
            '<div style="font-size:28px;margin-bottom:6px">👶</div>'
            'No children registered yet for this mother.'
            '</div>'
        )
    return "".join(render_child_card(c) for c in children)


# ─────────────────────────────────────────────────────────────────
# SELF-TEST
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== child_health.py self-test ===\n")

    dob_str = (date.today() - timedelta(days=75)).strftime("%d %b %Y")
    print(f"DOB: {dob_str}")
    print(f"Age: {child_age_months(dob_str)} months / {child_age_days(dob_str)} days")

    schedule = get_immunization_schedule(dob_str)
    print(f"\nImmunization schedule ({len(schedule)} vaccines):")
    for v in schedule:
        print(f"  [{v['status']:10}] {v['label']:<35} due {v['due_date']}")

    print("\nZ-score tests:")
    for w, age, gender in [(5.5, 2, "male"), (7.0, 6, "female"), (2.5, 3, "male")]:
        z  = calc_weight_z_score(w, age, gender)
        cn = classify_nutrition(z)
        print(f"  {w}kg at {age}m ({gender}): Z={z:+.2f} → {cn['status']}")

    print("\nDanger sign tests:")
    for msg in ["nahi pi raha baby", "baby bilkul theek hai", "baby thoda peela"]:
        lvl, _ = analyse_newborn_message(msg)
        print(f"  '{msg}' → {lvl}")

    print("\nVaccine reminder:")
    sched = get_immunization_schedule(dob_str)
    next3 = [s for s in sched if s["status"] in ("due_today", "upcoming")][:3]
    reminder = build_vaccine_reminder("Sunita Devi", "Baby Ram", next3)
    print(reminder[:300])

    print("\nSelf-test complete.")