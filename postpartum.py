# ─────────────────────────────────────────────────────────────────
# MaaSakhi — postpartum.py
# Postpartum Care Engine (Month 4)
#
# Responsibilities:
#   • PNC check-in schedule (Day 1, 3, 7, 14, 42)
#   • Postpartum danger sign detection
#   • WhatsApp counselling messages per PNC day
#   • Auto-reminder dispatch (called by reminders.py)
#   • ASHA dashboard data for postpartum patients
#   • Postpartum patient status tracking
#   • render_postpartum_tab() — HTML for admin/supervisor views
# ─────────────────────────────────────────────────────────────────

from datetime import datetime, date, timedelta

# ─────────────────────────────────────────────────────────────────
# PNC SCHEDULE DEFINITION
# ─────────────────────────────────────────────────────────────────

# NHM / WHO PNC visit schedule (days after delivery)
PNC_DAYS = [1, 3, 7, 14, 42]

# Tolerance window: ± N days around each PNC day counts as "on time"
PNC_TOLERANCE_DAYS = 1

# Counselling content per PNC day (sent via WhatsApp to mother)
PNC_MESSAGES = {
    1: {
        "hi": (
            "🌸 *Aapki delivery ke baad — Pehla Din*\n\n"
            "Aapki ASHA worker aaj aapse milne aayengi. 💚\n\n"
            "*Aaj dhyan rakhein:*\n"
            "🩸 Bleeding — 2-3 pads se zyada nahi honi chahiye\n"
            "🌡 Bukhaar — agar 38°C se zyada ho toh call karein\n"
            "🤱 Breastfeeding — pehle ghante mein shuru karein\n"
            "💊 Iron + Folic Acid tablet lena shuru karein\n"
            "🚰 Zyada paani aur doodh piyen\n\n"
            "Koi bhi problem ho toh turant ASHA worker ko call karein. 📞"
        ),
        "en": (
            "🌸 *Day 1 After Delivery — First PNC Check-in*\n\n"
            "Your ASHA worker will visit you today. 💚\n\n"
            "*Watch for:*\n"
            "🩸 Heavy bleeding (more than 2–3 pads/hour)\n"
            "🌡 Fever above 38°C\n"
            "🤱 Difficulty breastfeeding — start within first hour\n"
            "💊 Begin Iron + Folic Acid tablets today\n"
            "🚰 Drink plenty of fluids\n\n"
            "Call your ASHA worker immediately if concerned. 📞"
        ),
    },
    3: {
        "hi": (
            "🌸 *Delivery ke 3 Din Baad — Doosra PNC Check-in*\n\n"
            "Aaj aapki ASHA worker check-in karengi. 💚\n\n"
            "*Aaj dhyan rakhein:*\n"
            "🔴 Teesre din ke baad bhi peela peedappan (jaundice) baby mein\n"
            "🩹 Tike ki jagah ya operation site pe lali ya pus\n"
            "🤱 Breastfeeding — din mein 8–12 baar\n"
            "😴 Aap bhi aaram zaroor karein\n"
            "🧴 Umbilical cord — saaf aur sukha rakkhein\n\n"
            "Koi bhi takleef ho toh ASHA worker ko batayein. 💚"
        ),
        "en": (
            "🌸 *Day 3 After Delivery — Second PNC Check-in*\n\n"
            "Your ASHA worker will visit today. 💚\n\n"
            "*Check for:*\n"
            "🔴 Jaundice in baby beyond Day 3\n"
            "🩹 Redness or discharge at stitches or C-section wound\n"
            "🤱 Breastfeeding 8–12 times per day\n"
            "😴 Rest as much as possible\n"
            "🧴 Keep umbilical cord clean and dry\n\n"
            "Contact your ASHA worker for any concerns. 💚"
        ),
    },
    7: {
        "hi": (
            "🌸 *Delivery ke 7 Din Baad — Teesra PNC Check-in*\n\n"
            "*Is hafte dhyan rakhein:*\n"
            "🧠 Baby ki neend, khana, roona — normal hai na?\n"
            "🤱 Mastitis ke signs — breast mein lali, dard, bukhaar\n"
            "😔 Gar aap bahut udaas, ro rahi hain ya khana nahi kha rahi — "
            "postpartum depression ho sakta hai. Apni ASHA worker ya doctor se batayein\n"
            "💊 Vitamin A ek dose — ASHA worker denge\n"
            "🧴 Baby ki navel string ab sukhni chahiye\n\n"
            "Aap bahut acchi kar rahi hain! Apna khayal rakhein. 🌸"
        ),
        "en": (
            "🌸 *Day 7 After Delivery — Third PNC Check-in*\n\n"
            "*This week watch for:*\n"
            "🧠 Baby sleeping, feeding and crying normally?\n"
            "🤱 Mastitis signs — breast redness, pain, fever\n"
            "😔 Persistent sadness or inability to care for baby may be "
            "postpartum depression — speak to your ASHA worker or doctor\n"
            "💊 Vitamin A dose — your ASHA will provide\n"
            "🧴 Umbilical cord should be drying and falling off\n\n"
            "You are doing great! Take care of yourself. 🌸"
        ),
    },
    14: {
        "hi": (
            "🌸 *Delivery ke 14 Din Baad — Chautha PNC Check-in*\n\n"
            "*Aaj ke check-in mein:*\n"
            "⚖️ Baby ka vajan — 2 hafte mein birth weight se zyada hona chahiye\n"
            "💉 BCG + OPV-0 + Hepatitis B — kya laga diya gaya?\n"
            "🤱 Breastfeeding theek chal raha hai?\n"
            "🩺 Maa ki health — wound, BP, koi infection?\n"
            "📋 Family planning — 6 hafte baad shuru kar sakte hain\n\n"
            "ASHA worker se poochhein agar koi bhi sawaal ho. 💚"
        ),
        "en": (
            "🌸 *Day 14 After Delivery — Fourth PNC Check-in*\n\n"
            "*Today's check covers:*\n"
            "⚖️ Baby weight — should exceed birth weight by 2 weeks\n"
            "💉 BCG + OPV-0 + Hepatitis B — have these been given?\n"
            "🤱 Breastfeeding going well?\n"
            "🩺 Mother's health — wound healing, BP, any infection?\n"
            "📋 Family planning counselling — options from 6 weeks\n\n"
            "Ask your ASHA worker any questions you have. 💚"
        ),
    },
    42: {
        "hi": (
            "🌸 *Delivery ke 42 Din Baad — Panchva aur Aakhri PNC Check-in*\n\n"
            "Aapne bahut achha kiya! 🎉\n\n"
            "*Aaj ke check-in mein:*\n"
            "🩺 Maa ki poori health jaan — BP, weight, koi takleef?\n"
            "👶 Baby ka vikas — vajan, poshan\n"
            "💉 Remaining vaccines — Pentavalent, OPV series\n"
            "💊 Family planning — aaj se shuru kar sakti hain\n"
            "🤱 Breastfeeding 6 mahine tak jaari rakhein\n"
            "📋 Postpartum depression screen — 2 sawaal zaroor poochhein\n\n"
            "MaaSakhi ki taraf se aapko aur aapke bacche ko dheron shubhkamnayen! 💚🌸"
        ),
        "en": (
            "🌸 *Day 42 After Delivery — Final PNC Check-in*\n\n"
            "Congratulations on completing postpartum care! 🎉\n\n"
            "*Today's full review:*\n"
            "🩺 Mother's complete health assessment — BP, weight, recovery\n"
            "👶 Baby growth assessment — weight, feeding, milestones\n"
            "💉 Pending vaccines in schedule\n"
            "💊 Family planning — all methods available from today\n"
            "🤱 Continue exclusive breastfeeding until 6 months\n"
            "📋 Postpartum depression screening — 2 Edinburgh Scale questions\n\n"
            "MaaSakhi wishes you and your baby the very best! 💚🌸"
        ),
    },
}

# ─────────────────────────────────────────────────────────────────
# DANGER SIGN DETECTION
# ─────────────────────────────────────────────────────────────────

# Keywords that trigger a RED alert in postpartum phase
POSTPARTUM_RED_SIGNS = [
    # Bleeding
    "bahut bleeding", "heavy bleeding", "zyada khoon", "blood clot",
    "khoon band nahi", "bleeding not stopping",

    # Infection / fever
    "bukhaar", "fever", "temperature high", "garmi lag rahi",
    "wound infection", "tike mein pus", "operation wound",
    "pus discharge", "badbu aa rahi", "foul smell",

    # Respiratory / BP
    "saans nahi", "breathless", "chest pain", "seene mein dard",
    "bp high", "BP zyada", "headache severe", "sir dard tez",
    "seizure", "convulsion", "behosh",

    # Mental health emergency
    "khud ko hurt", "suicide", "baby ko hurt", "nahi rehna",

    # Mastitis / breast
    "breast mein bahut dard", "mastitis", "breast fever",
    "breast lal", "breast abscess",
]

# Keywords for AMBER (needs monitoring, not emergency)
POSTPARTUM_AMBER_SIGNS = [
    "dard", "pain", "thakaan", "fatigue", "buxaar thoda",
    "mild fever", "udaas", "sad", "neend nahi", "nahi kha rahi",
    "baby nahi pi raha", "baby not feeding", "baby rona",
    "breast dard", "stitches pain", "lochia", "discharge",
    "swelling", "sujan", "wound nahi bhar raha",
]

# Postpartum-specific danger sign check messages
DANGER_SIGN_RESPONSES = {
    "RED": {
        "hi": (
            "🚨 *EMERGENCY — Turant Madad Zaroor!*\n\n"
            "Aapne jo bataya hai woh postpartum ka khatarnak sign hai.\n\n"
            "🏥 *Abhi karo:*\n"
            "1️⃣ Apni ASHA worker ko call karein\n"
            "2️⃣ Nearest PHC / hospital jaayein\n"
            "3️⃣ Agar bahut emergency hai — 108 call karein\n\n"
            "Aap akeli nahi hain. Hum aapke saath hain. 💚"
        ),
        "en": (
            "🚨 *EMERGENCY — Seek Help Immediately!*\n\n"
            "The symptom you described is a postpartum danger sign.\n\n"
            "🏥 *Do this now:*\n"
            "1️⃣ Call your ASHA worker\n"
            "2️⃣ Go to nearest PHC / hospital\n"
            "3️⃣ If very urgent — call 108\n\n"
            "You are not alone. We are with you. 💚"
        ),
    },
    "AMBER": {
        "hi": (
            "⚠️ *Dhyan Zaroor Rakhein*\n\n"
            "Aapne jo bataya woh normal bhi ho sakta hai, "
            "lekin aapki ASHA worker ko iske baare mein zaroor batayein.\n\n"
            "Agar yeh problem 24 ghante mein theek na ho ya badh jaaye — "
            "turant PHC jaayein.\n\n"
            "Aaram karein, paani piyen. 💚"
        ),
        "en": (
            "⚠️ *Keep a Close Watch*\n\n"
            "What you described may be normal, but please inform "
            "your ASHA worker at your next visit.\n\n"
            "If the problem worsens or doesn't improve in 24 hours — "
            "visit your PHC.\n\n"
            "Rest and stay hydrated. 💚"
        ),
    },
}


def analyse_postpartum_message(message: str, language: str = "Hindi") -> tuple[str, str]:
    """
    Analyse a WhatsApp message from a postpartum patient.

    Returns (level, reply_text)
    level: 'RED', 'AMBER', or 'GREEN'

    Called from analyzer.py when patient status == 'postpartum'.
    """
    msg_lower = message.lower()
    lang_key  = "en" if language.lower() in ("english", "en") else "hi"

    # Check RED danger signs first
    for sign in POSTPARTUM_RED_SIGNS:
        if sign in msg_lower:
            return "RED", DANGER_SIGN_RESPONSES["RED"][lang_key]

    # Check AMBER signs
    for sign in POSTPARTUM_AMBER_SIGNS:
        if sign in msg_lower:
            return "AMBER", DANGER_SIGN_RESPONSES["AMBER"][lang_key]

    # GREEN — general wellbeing message
    if lang_key == "hi":
        reply = (
            "🌸 Shukriya batane ke liye!\n\n"
            "Lagta hai sab theek chal raha hai. 💚\n\n"
            "Yaad rakhein:\n"
            "🤱 Breastfeeding jaari rakhein\n"
            "💊 Iron tablet roz lein\n"
            "😴 Aaram zaroor karein\n\n"
            "Koi bhi takleef ho toh mujhe batayein ya ASHA worker ko call karein. 💚"
        )
    else:
        reply = (
            "🌸 Thank you for sharing!\n\n"
            "Things seem to be going well. 💚\n\n"
            "Remember:\n"
            "🤱 Continue breastfeeding\n"
            "💊 Take Iron tablets daily\n"
            "😴 Rest when you can\n\n"
            "Contact me or your ASHA worker for any concerns. 💚"
        )
    return "GREEN", reply


# ─────────────────────────────────────────────────────────────────
# PNC SCHEDULE CALCULATOR
# ─────────────────────────────────────────────────────────────────

def get_pnc_schedule(delivery_date_str: str) -> list[dict]:
    """
    Given a delivery date string, return the full PNC schedule.

    Each entry:
        {
            "day":        int,      # Day number (1/3/7/14/42)
            "due_date":   date,     # Actual calendar date
            "status":     str,      # 'overdue' / 'due_today' / 'upcoming'
            "days_away":  int,      # Negative = past, 0 = today, positive = future
            "label":      str,      # e.g. "Day 1 — 25 Apr 2026"
        }
    """
    try:
        for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                ddate = datetime.strptime(delivery_date_str, fmt).date()
                break
            except ValueError:
                continue
        else:
            return []
    except Exception:
        return []

    today    = date.today()
    schedule = []

    for day in PNC_DAYS:
        due       = ddate + timedelta(days=day)
        days_away = (due - today).days

        if days_away < -PNC_TOLERANCE_DAYS:
            status = "overdue"
        elif abs(days_away) <= PNC_TOLERANCE_DAYS:
            status = "due_today"
        else:
            status = "upcoming"

        schedule.append({
            "day":       day,
            "due_date":  due,
            "status":    status,
            "days_away": days_away,
            "label":     f"Day {day} — {due.strftime('%d %b %Y')}",
        })

    return schedule


def get_next_pnc(delivery_date_str: str) -> dict | None:
    """
    Returns the next upcoming (or due today) PNC visit, or None if complete.
    """
    schedule = get_pnc_schedule(delivery_date_str)
    for entry in schedule:
        if entry["status"] in ("due_today", "upcoming"):
            return entry
    return None


def is_pnc_due_today(delivery_date_str: str) -> tuple[bool, int | None]:
    """
    Returns (True, day_number) if a PNC visit is due today, else (False, None).
    """
    today = date.today()
    try:
        for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                ddate = datetime.strptime(delivery_date_str, fmt).date()
                break
            except ValueError:
                continue
        else:
            return False, None
    except Exception:
        return False, None

    for day in PNC_DAYS:
        due = ddate + timedelta(days=day)
        if abs((today - due).days) <= PNC_TOLERANCE_DAYS:
            return True, day

    return False, None


def days_since_delivery(delivery_date_str: str) -> int | None:
    """Returns number of days since delivery, or None if date unparseable."""
    try:
        for fmt in ("%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                ddate = datetime.strptime(delivery_date_str, fmt).date()
                return (date.today() - ddate).days
            except ValueError:
                continue
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────
# PNC WHATSAPP MESSAGE BUILDER
# ─────────────────────────────────────────────────────────────────

def build_pnc_reminder(
    patient_name: str,
    pnc_day: int,
    delivery_date_str: str,
    language: str = "Hindi",
    include_asha_name: str = "",
) -> str:
    """
    Build the WhatsApp PNC reminder message for a given PNC day.

    Called by reminders.py to dispatch day-of reminders.
    """
    lang_key = "en" if language.lower() in ("english", "en") else "hi"
    template = PNC_MESSAGES.get(pnc_day, {}).get(lang_key, "")

    if not template:
        if lang_key == "hi":
            template = (
                f"🌸 Namaste {patient_name}!\n\n"
                f"Aaj aapka PNC Day {pnc_day} check-in hai. "
                "Aapki ASHA worker aaj aapse milne aayengi. 💚\n\n"
                "Koi takleef ho toh turant batayein."
            )
        else:
            template = (
                f"🌸 Hello {patient_name}!\n\n"
                f"Today is your Day {pnc_day} PNC check-in. "
                "Your ASHA worker will visit you today. 💚\n\n"
                "Please reach out if you have any concerns."
            )
        return template

    greeting = f"Namaste {patient_name}! " if lang_key == "hi" else f"Hello {patient_name}! "
    msg      = greeting + "\n\n" + template

    if include_asha_name:
        if lang_key == "hi":
            msg += f"\n\n👩 Aapki ASHA worker: *{include_asha_name}*"
        else:
            msg += f"\n\n👩 Your ASHA worker: *{include_asha_name}*"

    return msg


def build_asha_pnc_alert(
    patient_name: str,
    patient_phone: str,
    patient_address: str,
    pnc_day: int,
    delivery_date_str: str,
    birth_weight: str = "",
    maps_link: str = "",
) -> str:
    """
    WhatsApp message sent to ASHA worker when a PNC visit is due.
    """
    maps_line = f"\n📌 Navigate: {maps_link}" if maps_link else ""
    weight_line = f"\n⚖️ Birth weight: {birth_weight} kg" if birth_weight else ""

    return (
        f"👶 *PNC Visit Due — Day {pnc_day}*\n\n"
        f"Patient: *{patient_name}*\n"
        f"Phone: {patient_phone}\n"
        f"Address: {patient_address}\n"
        f"Delivery Date: {delivery_date_str}"
        f"{weight_line}"
        f"{maps_line}\n\n"
        f"Please complete the Day {pnc_day} PNC check-in today. 🌸\n"
        f"Log the outcome on your MaaSakhi dashboard."
    )


# ─────────────────────────────────────────────────────────────────
# POSTPARTUM PATIENTS FOR ASHA DASHBOARD
# ─────────────────────────────────────────────────────────────────

def get_postpartum_dashboard_data(asha_id: str) -> dict:
    """
    Returns all postpartum data for a single ASHA's dashboard tab.

    {
        "due_today":         list of patients with PNC due today
        "overdue":           list of patients with missed PNC visits
        "all_postpartum":    full list of postpartum patients
        "completed":         patients who have finished all 5 PNC visits
        "stats": {
            "total":         int
            "due_today":     int
            "overdue":       int
            "completed":     int
        }
    }
    """
    from database import engine
    if not engine:
        return _empty_dashboard_data()

    from sqlalchemy import text

    result = {
        "due_today":      [],
        "overdue":        [],
        "all_postpartum": [],
        "completed":      [],
        "stats":          {"total": 0, "due_today": 0, "overdue": 0, "completed": 0},
    }

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    p.phone, p.name, p.village, p.address,
                    d.delivery_date, d.birth_weight, d.delivery_mode, d.facility,
                    aw.name  AS asha_name,
                    p.asha_id
                FROM patients p
                JOIN deliveries d ON d.phone = p.phone
                JOIN asha_workers aw ON aw.asha_id = p.asha_id
                WHERE p.asha_id = :asha_id
                  AND p.status  = 'postpartum'
                ORDER BY d.delivery_date DESC
            """), {"asha_id": asha_id}).fetchall()

            # Fetch maps links
            maps_rows = conn.execute(text("""
                SELECT phone, maps_url FROM patients
                WHERE asha_id = :asha_id AND maps_url IS NOT NULL
            """), {"asha_id": asha_id}).fetchall()
            maps_map = {r.phone: r.maps_url for r in maps_rows}

        today = date.today()
        for r in rows:
            dd_str = r.delivery_date or ""
            schedule = get_pnc_schedule(dd_str)
            days_pp  = days_since_delivery(dd_str)
            due_today_day = None
            is_overdue    = False
            all_complete  = True

            for entry in schedule:
                if entry["status"] == "due_today":
                    due_today_day = entry["day"]
                if entry["status"] == "overdue":
                    is_overdue = True
                if entry["status"] in ("due_today", "upcoming"):
                    all_complete = False

            patient = {
                "phone":         r.phone,
                "name":          r.name,
                "village":       r.village or "",
                "address":       r.address or "",
                "delivery_date": dd_str,
                "birth_weight":  r.birth_weight or "",
                "delivery_mode": r.delivery_mode or "",
                "facility":      r.facility or "",
                "asha_name":     r.asha_name,
                "days_since":    days_pp,
                "schedule":      schedule,
                "due_today_day": due_today_day,
                "is_overdue":    is_overdue,
                "is_complete":   all_complete,
                "maps_link":     maps_map.get(r.phone, ""),
            }

            result["all_postpartum"].append(patient)

            if due_today_day:
                result["due_today"].append(patient)
            if is_overdue:
                result["overdue"].append(patient)
            if all_complete:
                result["completed"].append(patient)

        result["stats"] = {
            "total":     len(result["all_postpartum"]),
            "due_today": len(result["due_today"]),
            "overdue":   len(result["overdue"]),
            "completed": len(result["completed"]),
        }

    except Exception as e:
        print(f"postpartum.py get_postpartum_dashboard_data error: {e}")

    return result


def _empty_dashboard_data() -> dict:
    return {
        "due_today":      [],
        "overdue":        [],
        "all_postpartum": [],
        "completed":      [],
        "stats":          {"total": 0, "due_today": 0, "overdue": 0, "completed": 0},
    }


# ─────────────────────────────────────────────────────────────────
# SUPERVISOR-LEVEL VIEW: all postpartum patients in block
# ─────────────────────────────────────────────────────────────────

def get_block_postpartum_data(supervisor_id: str) -> dict:
    """
    Aggregates postpartum data across all ASHA workers under
    a supervisor. Returns same structure as get_postpartum_dashboard_data().
    """
    from database import get_supervisor_ashas

    ashas  = get_supervisor_ashas(supervisor_id)
    merged = _empty_dashboard_data()

    for a in ashas:
        d = get_postpartum_dashboard_data(a["asha_id"])
        # Tag each patient with ASHA info
        for key in ("due_today", "overdue", "all_postpartum", "completed"):
            for p in d[key]:
                p["asha_id"] = a["asha_id"]
            merged[key].extend(d[key])

    merged["stats"] = {
        "total":     len(merged["all_postpartum"]),
        "due_today": len(merged["due_today"]),
        "overdue":   len(merged["overdue"]),
        "completed": len(merged["completed"]),
    }
    return merged


# ─────────────────────────────────────────────────────────────────
# POSTPARTUM COUNSELLING CONTENT (by week post-delivery)
# ─────────────────────────────────────────────────────────────────

def get_weekly_counsel(days_postpartum: int, language: str = "Hindi") -> str:
    """
    Returns a counselling message appropriate for how many days
    postpartum the patient is. Sent on demand or via weekly reminders.
    """
    lang_key = "en" if language.lower() in ("english", "en") else "hi"

    if days_postpartum <= 7:
        msgs = {
            "hi": (
                "🌸 *Pehla Hafte — Postpartum Shuruaat*\n\n"
                "• Sirf breastfeed karein — paani ya formula mat dein\n"
                "• Roz nahayein, wound saaf rakhein\n"
                "• Iron + Folic Acid tablet roz lein\n"
                "• 6 ghante ki neend zaroor lein (tukdon mein bhi theek hai)\n"
                "• Ghar ke kaam family ko dein — aap aaram karein\n\n"
                "Koi bhi takleef ho toh ASHA worker ko call karein. 💚"
            ),
            "en": (
                "🌸 *Week 1 — Early Postpartum*\n\n"
                "• Exclusive breastfeeding — no water or formula\n"
                "• Bathe daily, keep wound clean and dry\n"
                "• Take Iron + Folic Acid tablet daily\n"
                "• Get 6 hours of sleep (in segments is fine)\n"
                "• Let family handle household tasks — you rest\n\n"
                "Call your ASHA worker for any concerns. 💚"
            ),
        }
    elif days_postpartum <= 14:
        msgs = {
            "hi": (
                "🌸 *Doosra Hafte — Theek Hona Jaari*\n\n"
                "• Baby ka vajan check zaroor karein — birth weight se zyada hona chahiye\n"
                "• Tike khud girengi 7–10 din mein\n"
                "• Breastfeeding regular rakhein\n"
                "• Perineum dard 1–2 hafte tak normal hai\n"
                "• Agar bahut udaas hain — yeh postpartum blues ho sakta hai, normal hai\n\n"
                "Agar udaasi 2 hafte se zyada ho — doctor se milein. 💚"
            ),
            "en": (
                "🌸 *Week 2 — Recovery Continues*\n\n"
                "• Weigh baby — should be back at birth weight\n"
                "• Stitches will dissolve/fall off around 7–10 days\n"
                "• Keep breastfeeding regularly\n"
                "• Perineum soreness for 1–2 weeks is normal\n"
                "• Feeling sad or weepy — 'baby blues' is very common\n\n"
                "If sadness lasts more than 2 weeks — see a doctor. 💚"
            ),
        }
    elif days_postpartum <= 42:
        msgs = {
            "hi": (
                "🌸 *Teesre–Chhate Hafte — Sudhaar Ka Samay*\n\n"
                "• Zyada aaram karein aur ghar ke log madad karein\n"
                "• Family planning ke baare mein sochein — 6 hafte baad start kar sakti hain\n"
                "• Exercise dheere dheere shuru karein — pehle sirf walk\n"
                "• Breastfeeding 6 mahine tak exclusively\n"
                "• Baby ko 6 hafte mein doctor ke paas le jaayein regular check ke liye\n\n"
                "Aap bahut acchi kar rahi hain! 🌸💚"
            ),
            "en": (
                "🌸 *Weeks 3–6 — Recovery in Progress*\n\n"
                "• Rest and accept help from family\n"
                "• Think about family planning — options available from 6 weeks\n"
                "• Gentle exercise — start with short walks only\n"
                "• Exclusive breastfeeding for 6 months\n"
                "• Take baby for 6-week check at clinic\n\n"
                "You are doing an amazing job! 🌸💚"
            ),
        }
    else:
        msgs = {
            "hi": (
                "🌸 *6 Hafte Ke Baad — Naya Adhyaya*\n\n"
                "Aapki postpartum recovery puri ho gayi hai! 🎉\n\n"
                "• Breastfeeding 6 mahine tak jaari rakhein\n"
                "• Baby ke vaccines schedule pe zaroor lagwayein\n"
                "• Family planning method shuru kar lein\n"
                "• Apni sehat ka khayal rakhein — BP, khoon ki kami check karwayein\n\n"
                "MaaSakhi hamesha aapke saath hai. 💚🌸"
            ),
            "en": (
                "🌸 *Beyond 6 Weeks — A New Chapter*\n\n"
                "Your postpartum recovery is complete! 🎉\n\n"
                "• Continue breastfeeding until 6 months\n"
                "• Keep baby's vaccine schedule on track\n"
                "• Start your chosen family planning method\n"
                "• Monitor your own health — BP, anaemia\n\n"
                "MaaSakhi is always here for you. 💚🌸"
            ),
        }

    return msgs[lang_key]


# ─────────────────────────────────────────────────────────────────
# POSTPARTUM STATS FOR ANALYTICS
# ─────────────────────────────────────────────────────────────────

def get_postpartum_stats() -> dict:
    """
    District-wide postpartum summary for analytics dashboard.
    """
    from database import engine
    if not engine:
        return {}

    from sqlalchemy import text
    stats = {}

    try:
        with engine.connect() as conn:
            stats["total_postpartum"] = conn.execute(text(
                "SELECT COUNT(*) FROM patients WHERE status='postpartum'"
            )).scalar() or 0

            stats["total_deliveries"] = conn.execute(text(
                "SELECT COUNT(*) FROM deliveries"
            )).scalar() or 0

            stats["deliveries_this_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
                WHERE DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())
            """)).scalar() or 0

            stats["home_deliveries"] = conn.execute(text(
                "SELECT COUNT(*) FROM deliveries WHERE facility ILIKE '%home%'"
            )).scalar() or 0

            stats["institutional_deliveries"] = conn.execute(text(
                "SELECT COUNT(*) FROM deliveries WHERE facility NOT ILIKE '%home%'"
            )).scalar() or 0

            # Average birth weight
            avg_bw = conn.execute(text("""
                SELECT AVG(CAST(birth_weight AS FLOAT))
                FROM deliveries
                WHERE birth_weight IS NOT NULL
                  AND birth_weight != ''
                  AND birth_weight ~ '^[0-9.]+$'
            """)).scalar()
            stats["avg_birth_weight"] = round(float(avg_bw), 2) if avg_bw else None

            # Low birth weight count (<2.5 kg)
            stats["low_birth_weight"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
                WHERE birth_weight IS NOT NULL
                  AND birth_weight ~ '^[0-9.]+$'
                  AND CAST(birth_weight AS FLOAT) < 2.5
            """)).scalar() or 0

            # PNC compliance — patients who had at least Day 1 visit
            stats["pnc_started"] = conn.execute(text("""
                SELECT COUNT(DISTINCT p.phone)
                FROM patients p
                JOIN deliveries d ON d.phone = p.phone
                JOIN anc_records ar ON ar.phone = p.phone AND ar.notes ILIKE '%PNC Day 1%'
                WHERE p.status = 'postpartum'
            """)).scalar() or 0

    except Exception as e:
        print(f"postpartum.py get_postpartum_stats error: {e}")

    return stats


# ─────────────────────────────────────────────────────────────────
# HTML RENDER — postpartum section for admin/supervisor
# ─────────────────────────────────────────────────────────────────

POSTPARTUM_ADMIN_HTML = """
<div style="padding:0 28px 20px">

  <!-- Stats strip -->
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));
              gap:12px;margin-bottom:18px">
    {% for label, val, color in stat_items %}
    <div style="background:white;border-radius:12px;padding:14px 12px;text-align:center;
                border:1px solid #dde6ed;box-shadow:0 2px 8px rgba(0,0,0,0.05)">
      <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                  color:{{ color }}">{{ val }}</div>
      <div style="font-size:10px;color:#5a7184;margin-top:3px;text-transform:uppercase;
                  letter-spacing:.05em;font-weight:600">{{ label }}</div>
    </div>
    {% endfor %}
  </div>

  <!-- Danger signs banner -->
  <div style="background:#fdecea;border:1.5px solid #fecaca;border-radius:10px;
              padding:12px 16px;margin-bottom:16px;
              display:flex;align-items:flex-start;gap:10px">
    <div style="font-size:20px;flex-shrink:0">⚠️</div>
    <div style="font-size:12px;color:#991b1b;line-height:1.7;font-weight:500">
      <strong>Postpartum Danger Signs — counsel all mothers:</strong><br>
      Excessive bleeding · Fever &gt;38°C · Wound infection or pus ·
      Breathlessness · Severe headache · Mastitis · Persistent sadness (PPD)
    </div>
  </div>

  <!-- Due Today -->
  {% if due_today %}
  <div style="font-size:11px;font-weight:700;color:#7c3aed;text-transform:uppercase;
              letter-spacing:.08em;margin-bottom:8px">
    👶 PNC Due Today — {{ due_today|length }} patients
  </div>
  {% for p in due_today %}
  <div style="background:white;border-radius:12px;padding:16px;
              border-left:4px solid #7c3aed;margin-bottom:10px;
              box-shadow:0 2px 10px rgba(124,58,237,0.08)">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <div style="font-weight:700;font-size:14px">{{ p.name }}</div>
        <div style="font-size:11.5px;color:#5a7184;margin-top:2px">
          📅 Delivered: {{ p.delivery_date }}
          {% if p.birth_weight %} · Baby: {{ p.birth_weight }} kg{% endif %}
        </div>
        <div style="font-size:11px;color:#94aab8">
          📍 {{ p.village }} · 👩 ASHA: {{ p.asha_name }}
        </div>
      </div>
      <span style="background:#f5f3ff;color:#6d28d9;border:1px solid #ddd6fe;
                   padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700">
        Day {{ p.due_today_day }} Due
      </span>
    </div>
    <!-- PNC timeline -->
    <div style="display:flex;gap:5px;margin-top:10px;flex-wrap:wrap">
      {% for entry in p.schedule %}
      <span style="padding:4px 11px;border-radius:20px;font-size:10.5px;font-weight:600;
                   {% if entry.status == 'due_today' %}
                     background:#fef3c7;color:#92400e;border:1px solid #fcd34d;
                   {% elif entry.status == 'overdue' %}
                     background:#fdecea;color:#991b1b;border:1px solid #fecaca;
                   {% else %}
                     background:#f1f5f9;color:#94a3b8;border:1px solid #e2e8f0;
                   {% endif %}">
        Day {{ entry.day }}
      </span>
      {% endfor %}
    </div>
    <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
      <a href="tel:{{ p.phone }}"
         style="padding:6px 14px;background:#7c3aed;color:white;border-radius:8px;
                font-size:11px;font-weight:600;text-decoration:none">📞 Call Patient</a>
      {% if p.maps_link %}
      <a href="{{ p.maps_link }}" target="_blank"
         style="padding:6px 14px;background:#1565c0;color:white;border-radius:8px;
                font-size:11px;font-weight:600;text-decoration:none">📌 Navigate</a>
      {% endif %}
    </div>
  </div>
  {% endfor %}
  {% else %}
  <div style="text-align:center;padding:30px;color:#94aab8;font-size:13px">
    <div style="font-size:32px;margin-bottom:8px">👶</div>
    No PNC visits due today
  </div>
  {% endif %}

  <!-- Overdue visits -->
  {% if overdue %}
  <div style="font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;
              letter-spacing:.08em;margin:14px 0 8px">
    ⚠️ Overdue PNC Visits — {{ overdue|length }}
  </div>
  {% for p in overdue %}
  <div style="background:white;border-radius:10px;padding:12px 14px;
              border-left:4px solid #dc2626;margin-bottom:8px;
              box-shadow:0 2px 8px rgba(220,38,38,0.08)">
    <div style="font-weight:600;font-size:13px">{{ p.name }}</div>
    <div style="font-size:11.5px;color:#5a7184">
      Delivered: {{ p.delivery_date }} · {{ p.days_since }} days ago
    </div>
    <div style="font-size:11px;color:#94aab8">
      ASHA: {{ p.asha_name }} · 📞 {{ p.phone }}
    </div>
  </div>
  {% endfor %}
  {% endif %}

</div>
"""


def render_postpartum_admin_section(supervisor_id: str = None,
                                    asha_id: str = None) -> str:
    """
    Renders the postpartum HTML section.
    Pass supervisor_id for block-level view or asha_id for single ASHA.
    """
    from flask import render_template_string

    if supervisor_id:
        data = get_block_postpartum_data(supervisor_id)
    elif asha_id:
        data = get_postpartum_dashboard_data(asha_id)
    else:
        data = _empty_dashboard_data()

    stats  = data["stats"]
    due    = data["due_today"]
    overdue = data["overdue"]

    stat_items = [
        ("Total Postpartum",   stats["total"],     "#7c3aed"),
        ("PNC Due Today",      stats["due_today"], "#f4a61a"),
        ("Overdue Visits",     stats["overdue"],   "#dc2626"),
        ("PNC Complete",       stats["completed"], "#0d8f72"),
    ]

    return render_template_string(
        POSTPARTUM_ADMIN_HTML,
        stat_items = stat_items,
        due_today  = due,
        overdue    = overdue,
    )


# ─────────────────────────────────────────────────────────────────
# SELF-TEST
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== postpartum.py self-test ===\n")

    test_date = (date.today() - timedelta(days=7)).strftime("%d %b %Y")
    print(f"Delivery date: {test_date}")
    sched = get_pnc_schedule(test_date)
    for s in sched:
        print(f"  Day {s['day']:2d} — {s['label']} — {s['status']}")

    print()
    due, day = is_pnc_due_today(test_date)
    print(f"PNC due today: {due} (Day {day})")

    print()
    level, reply = analyse_postpartum_message("bahut bleeding ho rahi hai")
    print(f"Danger sign test: {level}\n{reply[:80]}...")

    print()
    msg = build_pnc_reminder("Sunita Devi", 7, test_date)
    print(f"PNC reminder preview:\n{msg[:200]}...")

    print()
    counsel = get_weekly_counsel(7)
    print(f"Week 1 counsel:\n{counsel[:200]}...")
    print("\nSelf-test complete.")