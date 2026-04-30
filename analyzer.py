# ─────────────────────────────────────────────────────────────────
# MaaSakhi Symptom Analyzer
# Powered by Groq AI (Llama 3.3) — FREE, fast, no credit card
# Backed by WHO + NHM + FOGSI medical guidelines
# Language: uses user's chosen language, falls back to auto-detect
# ─────────────────────────────────────────────────────────────────

import os
from groq import Groq
from symptoms import WHO_DANGER_SIGNS, NHM_MODERATE_SIGNS
from myths import PREGNANCY_MYTHS
from tips import get_weekly_tip

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


# ─────────────────────────────────────────────────────────────────
# LANGUAGE DETECTION
# Only used as fallback when user hasn't set a language preference
# ─────────────────────────────────────────────────────────────────

def detect_language_from_text(text):
    """
    Detects language from message content.
    Used ONLY as fallback when user hasn't set a preferred language.
    Unicode script ranges checked first — most reliable.
    Falls back to Hinglish keyword detection for Roman-script Hindi.
    """

    # Unicode script range detection
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return "Hindi"
        elif '\u0B80' <= char <= '\u0BFF':
            return "Tamil"
        elif '\u0C00' <= char <= '\u0C7F':
            return "Telugu"
        elif '\u0980' <= char <= '\u09FF':
            return "Bengali"
        elif '\u0A80' <= char <= '\u0AFF':
            return "Gujarati"
        elif '\u0C80' <= char <= '\u0CFF':
            return "Kannada"
        elif '\u0A00' <= char <= '\u0A7F':
            return "Punjabi"
        elif '\u0D00' <= char <= '\u0D7F':
            return "Malayalam"
        elif '\u0B00' <= char <= '\u0B7F':
            return "Odia"
        elif '\u0A80' <= char <= '\u0AFF':
            return "Gujarati"

    # Hinglish — Hindi typed in Roman script
    hinglish_words = [
        "mujhe", "meri", "mera", "mere", "maine", "mujhko",
        "hai", "hain", "tha", "thi", "hoga", "hogi",
        "kya", "kaise", "kab", "kyun", "kyunki", "kaun",
        "nahi", "nahi hai", "mat", "na",
        "bahut", "thoda", "zyada", "bilkul",
        "aur", "lekin", "toh", "ki", "ke", "ka",
        "dard", "sar", "sir", "pet", "pair", "haath",
        "bukhar", "chakkar", "kamzori", "khoon", "ulti",
        "theek", "bura", "achha", "acha", "accha",
        "takleef", "pareshaan", "darr", "dar",
        "batao", "bataiye", "help karo", "kya karu",
        "baby", "baccha", "garbh",
        "ho raha", "ho rahi", "lag raha", "lag rahi",
        "feel ho", "feel kar", "hua", "hui",
        "please", "bhai", "didi", "auntie"
    ]

    text_lower = text.lower()
    if any(word in text_lower for word in hinglish_words):
        return "Hindi"

    # Default
    return "English"


# ─────────────────────────────────────────────────────────────────
# LANGUAGE-SPECIFIC RESPONSE TEMPLATES
# Used in rule-based fallback only (when Groq is unavailable)
# ─────────────────────────────────────────────────────────────────

def get_response_template(level, language, pregnancy_week):
    """
    Returns warm fallback response in the correct language.
    Only used when Groq AI is unavailable.
    For languages not in the template dict, defaults to English.
    """

    templates = {
        "Hindi": {
            "RED": (
                f"⚠️ Yeh symptom bahut serious hai! WHO guidelines ke "
                f"anusaar week {pregnancy_week} mein yeh ek danger sign hai. "
                f"Turant apne nearest health centre jaiye — please wait mat karein. "
                f"Aapki ASHA worker ko abhi alert kar diya gaya hai. "
                f"Aap akeli nahi hain. 🙏"
            ),
            "AMBER": (
                f"🟡 Yeh symptom week {pregnancy_week} mein dhyan dene wala hai. "
                f"NHM guidelines ke anusaar please rest karein aur paani piyen. "
                f"24 ghante mein apni ASHA worker ko zaroor batayein. "
                f"Agar symptoms badh jaayein toh turant message karein. 💛"
            ),
            "GREEN": (
                f"✅ Week {pregnancy_week} mein yeh aam taur par normal hai. "
                f"Aaram karein, paani piyen, aur iron ki goli lena mat bhoolein. "
                f"Aap aur aapka baby dono safe hain — main hamesha yahan hoon! 💚"
            ),
        },
        "Hinglish": {
            "RED": (
                f"⚠️ Yeh symptom bahut serious hai! WHO guidelines ke "
                f"anusaar week {pregnancy_week} mein yeh ek danger sign hai. "
                f"Please turant nearest health centre jaao — wait mat karo. "
                f"Aapki ASHA worker ko alert kar diya gaya hai. 🙏"
            ),
            "AMBER": (
                f"🟡 Week {pregnancy_week} mein yeh symptom dhyan dene wala hai. "
                f"Please rest karo aur paani piyo. "
                f"24 hours mein apni ASHA worker ko batao. 💛"
            ),
            "GREEN": (
                f"✅ Week {pregnancy_week} mein yeh normal hai. "
                f"Rest karo, paani piyo, aur iron tablet lena mat bhoolo. "
                f"Tum aur tumhara baby safe hain! 💚"
            ),
        },
        "English": {
            "RED": (
                f"⚠️ This symptom is serious! According to WHO guidelines, "
                f"at week {pregnancy_week} this is a danger sign. "
                f"Please go to your nearest health centre immediately — do not wait. "
                f"Your ASHA worker has been alerted right now. "
                f"You are not alone. 🙏"
            ),
            "AMBER": (
                f"🟡 This symptom needs attention at week {pregnancy_week}. "
                f"According to NHM guidelines, please rest and drink water. "
                f"Inform your ASHA worker within 24 hours. "
                f"If symptoms get worse, message me immediately. 💛"
            ),
            "GREEN": (
                f"✅ This is generally normal at week {pregnancy_week}. "
                f"Rest well, drink plenty of water, and don't forget your iron tablet. "
                f"Both you and your baby are safe — I am always here for you! 💚"
            ),
        },
        "Tamil": {
            "RED": (
                f"⚠️ இந்த அறிகுறி மிகவும் தீவிரமானது! "
                f"WHO வழிகாட்டுதல்களின்படி வாரம் {pregnancy_week}ல் "
                f"இது ஆபத்தான அறிகுறி. உடனடியாக அருகிலுள்ள "
                f"சுகாதார மையத்திற்கு செல்லுங்கள். "
                f"உங்கள் ASHA தொழிலாளர் அறிவிக்கப்பட்டார். 🙏"
            ),
            "AMBER": (
                f"🟡 வாரம் {pregnancy_week}ல் இந்த அறிகுறி கவனிக்கப்பட வேண்டும். "
                f"ஓய்வு எடுங்கள், தண்ணீர் குடியுங்கள். "
                f"24 மணி நேரத்திற்குள் ASHA தொழிலாளரிடம் தெரிவியுங்கள். 💛"
            ),
            "GREEN": (
                f"✅ வாரம் {pregnancy_week}ல் இது பொதுவாக இயல்பானது. "
                f"ஓய்வு எடுங்கள், தண்ணீர் குடியுங்கள். "
                f"நீங்களும் உங்கள் குழந்தையும் பாதுகாப்பாக இருக்கிறீர்கள்! 💚"
            ),
        },
        "Telugu": {
            "RED": (
                f"⚠️ ఈ లక్షణం చాలా తీవ్రమైనది! WHO మార్గదర్శకాల ప్రకారం "
                f"వారం {pregnancy_week}లో ఇది ప్రమాదకర సంకేతం. "
                f"వెంటనే సమీప ఆరోగ్య కేంద్రానికి వెళ్ళండి. "
                f"మీ ASHA వర్కర్‌కు అప్రమత్తం చేయబడింది. 🙏"
            ),
            "AMBER": (
                f"🟡 వారం {pregnancy_week}లో ఈ లక్షణం శ్రద్ధ అవసరం. "
                f"విశ్రాంతి తీసుకోండి, నీళ్ళు త్రాగండి. "
                f"24 గంటల్లో ASHA వర్కర్‌కు తెలియజేయండి. 💛"
            ),
            "GREEN": (
                f"✅ వారం {pregnancy_week}లో ఇది సాధారణంగా నార్మల్. "
                f"విశ్రాంతి తీసుకోండి మరియు నీళ్ళు త్రాగండి. "
                f"మీరు మరియు మీ శిశువు సురక్షితంగా ఉన్నారు! 💚"
            ),
        },
        "Bengali": {
            "RED": (
                f"⚠️ এই লক্ষণটি খুবই গুরুতর! WHO নির্দেশিকা অনুযায়ী "
                f"সপ্তাহ {pregnancy_week}-এ এটি একটি বিপদ সংকেত। "
                f"অবিলম্বে নিকটতম স্বাস্থ্য কেন্দ্রে যান। "
                f"আপনার ASHA কর্মীকে সতর্ক করা হয়েছে। 🙏"
            ),
            "AMBER": (
                f"🟡 সপ্তাহ {pregnancy_week}-এ এই লক্ষণটি মনোযোগ দরকার। "
                f"বিশ্রাম নিন এবং পানি পান করুন। "
                f"২৪ ঘণ্টার মধ্যে ASHA কর্মীকে জানান। 💛"
            ),
            "GREEN": (
                f"✅ সপ্তাহ {pregnancy_week}-এ এটি সাধারণত স্বাভাবিক। "
                f"বিশ্রাম নিন এবং আয়রন ট্যাবলেট খেতে ভুলবেন না। "
                f"আপনি এবং আপনার শিশু নিরাপদ! 💚"
            ),
        },
    }

    # Default to English if language not in templates
    lang_templates = templates.get(language, templates["English"])
    return lang_templates.get(level, lang_templates["GREEN"])


# ─────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — AI Brain
# Language rule is injected dynamically per request
# ─────────────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are MaaSakhi — an AI-powered maternal health
companion for pregnant women across India.
Built using WHO ANC 2016, NHM ASHA Training Module 6, FOGSI Guidelines 2021.

CLASSIFICATION RULES (based on WHO ANC 2016 Table 3.1):

RED — Immediate danger. Refer to hospital NOW. Trigger ASHA alert.
Includes: severe headache, blurry vision, heavy bleeding, no fetal
movement, chest pain, difficulty breathing, high fever, seizures,
convulsions, severe abdominal pain, swollen face or hands, water breaking,
preeclampsia, eclampsia.

AMBER — Monitor closely. Follow up within 24 hours.
Includes: mild headache, dizziness, back pain, swollen feet, nausea,
vomiting, light bleeding, spotting, leg cramps, fatigue, mild fever,
reduced fetal movement, breathlessness, UTI symptoms, anxiety, stress.

GREEN — Normal pregnancy symptom. Reassure the woman.
Includes: food cravings, frequent urination, breast tenderness,
bloating, mild fatigue, emotional sensitivity, stuffy nose, vivid dreams.

MYTH — Woman has asked about a pregnancy myth.
Common myths: papaya causes miscarriage, pineapple is dangerous,
avoid water, exercise is harmful, eating for two, saffron makes baby fair,
ghee eases delivery, cold food harms baby, heartburn means baby has hair.

TIP — Woman is asking for advice or weekly guidance.

RESPONSE FORMAT — always respond in EXACTLY this format, no deviations:
LEVEL: (RED or AMBER or GREEN or MYTH or TIP)
MESSAGE: (your warm response — max 4 sentences)
ASHA_ALERT: (YES or NO)

IMPORTANT RULES:
- Never diagnose. Never prescribe medicine.
- Always cite WHO or NHM when classifying danger signs.
- For RED — always say ASHA worker has been notified.
- Be warm and caring like a trusted friend.
- Maximum 4 sentences in MESSAGE."""


def build_prompt_with_language(language):
    """
    Injects a hard language instruction at the TOP of the prompt.
    Putting it first makes Groq treat it as highest priority.
    Supports ANY language the user types — not just a fixed list.
    """
    lang_lock = f"""
══════════════════════════════════════════
LANGUAGE INSTRUCTION — MANDATORY — HIGHEST PRIORITY
══════════════════════════════════════════
The user's preferred language is: {language}

YOU MUST:
✅ Write your ENTIRE response in {language} only.
✅ Every single word in MESSAGE must be in {language}.
✅ This applies to ALL Indian and world languages —
   Hindi, English, Hinglish, Tamil, Telugu, Bengali,
   Marathi, Gujarati, Odia, Punjabi, Urdu, Kannada,
   Malayalam, Assamese, Maithili, Bhojpuri, Rajasthani,
   Konkani, Manipuri, Sindhi, Dogri, Kashmiri, Santali,
   and any other language the user has chosen.
✅ If {language} is Hinglish — use Hindi words in Roman
   script (e.g. "Aapko doctor ke paas jana chahiye").
✅ If {language} has its own script — use that script.
✅ If {language} is less common and you are unsure of the
   script — transliterate into Roman script in that language
   rather than switching to Hindi or English.

YOU MUST NOT:
❌ Switch to English or Hindi because the language is less common.
❌ Mix in another language unless the user themselves mixed it.
❌ Ignore this instruction for any reason whatsoever.

This language rule overrides everything else.
══════════════════════════════════════════

"""
    return lang_lock + BASE_SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────────
# MAIN ANALYZE FUNCTION
# ─────────────────────────────────────────────────────────────────

def analyze(message, pregnancy_week, language=None, postpartum=False):
    """
    Main entry point.
    1. Uses user's saved language preference if provided.
    2. Falls back to auto-detecting language from message.
    3. Calls Groq AI with language-locked prompt.
    4. Falls back to rule-based if AI fails.
    Returns: (level, response_message, asha_alert_needed)
    """

    text = message.lower().strip()

    # ── Step 1: Rule-based myth check (fast, no AI needed) ───────
    for keyword, data in PREGNANCY_MYTHS.items():
        if keyword in text:
            response = (
                f"ℹ️ Yeh ek common myth hai!\n\n"
                f"Myth: {data['myth']}\n\n"
                f"Sach: {data['fact']}\n\n"
                f"Source: {data['source']}\n\n"
                f"Koi aur sawaal ho toh zaroor poochho! 💚"
            )
            return "MYTH", response, "NO"

    # ── Step 2: Use user's saved language OR auto-detect ─────────
    if not language:
        language = detect_language_from_text(message)
        print(f"[Language detected: {language}] for message: {message[:50]}")
    else:
        print(f"[Language from profile: {language}] for message: {message[:50]}")

    # ── Step 3: Try Groq AI with language-locked prompt ──────────
    try:
        client = Groq(api_key=GROQ_API_KEY)

        system_prompt = build_prompt_with_language(language)

        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=350,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": (
                        f"Pregnant woman, week {pregnancy_week}.\n"
                        f"Her preferred language is: {language}.\n"
                        f"Her message: '{message}'\n\n"
                        f"IMPORTANT: Your entire MESSAGE field must be "
                        f"written in {language} only. "
                        f"This includes all Indian regional languages — "
                        f"Odia, Bhojpuri, Assamese, Maithili, Urdu, "
                        f"Marathi, Gujarati, Punjabi, and any other language. "
                        f"Do NOT switch to English or Hindi."
                    )
                }
            ]
        )

        result = chat.choices[0].message.content.strip()
        print(f"[Groq raw response]: {result[:100]}")

        # ── Parse AI response ─────────────────────────────────────
        level      = ""
        ai_message = ""
        asha_alert = "NO"

        for line in result.split("\n"):
            line = line.strip()
            if line.startswith("LEVEL:"):
                level = line.replace("LEVEL:", "").strip()
            elif line.startswith("MESSAGE:"):
                ai_message = line.replace("MESSAGE:", "").strip()
            elif line.startswith("ASHA_ALERT:"):
                asha_alert = line.replace("ASHA_ALERT:", "").strip()

        # Handle multi-line MESSAGE (sometimes AI wraps it)
        if not ai_message:
            lines = result.split("\n")
            for i, line in enumerate(lines):
                if "MESSAGE:" in line:
                    msg_parts = [line.replace("MESSAGE:", "").strip()]
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("ASHA_ALERT:"):
                            break
                        if lines[j].strip():
                            msg_parts.append(lines[j].strip())
                    ai_message = " ".join(msg_parts).strip()
                    break

        # ── Return if valid ───────────────────────────────────────
        if level in ["RED", "AMBER", "GREEN", "MYTH", "TIP"] and ai_message:
            return level, ai_message, asha_alert

        # If parsing failed but we have a result — use full result
        if result and len(result) > 20:
            print(f"[Parse fallback] Using full response")
            return "GREEN", result, "NO"

    except Exception as e:
        print(f"[Groq AI error — using rule-based fallback]: {e}")

    # ── Step 4: Rule-based fallback if AI fails ───────────────────
    return rule_based_analyze(message, pregnancy_week, language)


# ─────────────────────────────────────────────────────────────────
# RULE-BASED FALLBACK
# Used only when Groq AI is unavailable
# ─────────────────────────────────────────────────────────────────

def rule_based_analyze(message, pregnancy_week, language="English"):
    """
    Backup rule-based analyzer using WHO + NHM symptom lists.
    Uses the user's saved language for responses.
    """

    text = message.lower().strip()

    # Check myths
    for keyword, data in PREGNANCY_MYTHS.items():
        if keyword in text:
            response = (
                f"Yeh ek common myth hai! "
                f"{data['fact']} "
                f"Source: {data['source']}. "
                f"Koi aur sawaal ho toh zaroor poochho!"
            )
            return "MYTH", response, "NO"

    # Check tips request
    tip_triggers = [
        "tip", "advice", "what should i do", "guide",
        "help", "suggest", "this week", "what to eat",
        "kya khana", "kya karna", "batao", "bataiye",
        "is hafte", "weekly"
    ]
    if any(t in text for t in tip_triggers):
        return "TIP", get_weekly_tip(pregnancy_week), "NO"

    # Check RED danger signs (WHO ANC 2016)
    for sign in WHO_DANGER_SIGNS:
        if sign in text:
            return "RED", get_response_template("RED", language, pregnancy_week), "YES"

    # Check AMBER moderate signs (NHM Module 6)
    for sign in NHM_MODERATE_SIGNS:
        if sign in text:
            return "AMBER", get_response_template("AMBER", language, pregnancy_week), "NO"

    # Default GREEN
    return "GREEN", get_response_template("GREEN", language, pregnancy_week), "NO"