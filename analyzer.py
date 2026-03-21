# ─────────────────────────────────────────────────────────────────
# MaaSakhi Symptom Analyzer
# Powered by Groq AI (Llama 3) — FREE, fast, no credit card
# Backed by WHO + NHM + FOGSI medical guidelines
# ─────────────────────────────────────────────────────────────────
import os
from groq import Groq
from symptoms import WHO_DANGER_SIGNS, NHM_MODERATE_SIGNS
from myths import PREGNANCY_MYTHS
from tips import get_weekly_tip

GROQ_API_KEY = os.environ.get("GROQ_API_KEY","")

# ─────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — This is the AI's brain
# Trained on WHO ANC 2016 + NHM Module 6 + FOGSI Guidelines
# ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are MaaSakhi — an AI-powered maternal health companion
for pregnant women across India. You were built using WHO Antenatal Care
Guidelines 2016, NHM India ASHA Training Module 6, and FOGSI Clinical
Practice Guidelines 2021.

LANGUAGE DETECTION AND RESPONSE RULE — MOST IMPORTANT:
Detect which language the woman is using and ALWAYS reply in that SAME language.
Supported languages:
- Hindi (हिंदी) — most common
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)
- Marathi (मराठी)
- Gujarati (ગુજરાતી)
- Kannada (ಕನ್ನಡ)
- English
- Hinglish (Hindi + English mixed)

If the woman writes in Tamil — reply in Tamil.
If she writes in Telugu — reply in Telugu.
If she writes in Hindi — reply in Hindi.
If she writes in English — reply in English.
NEVER reply in a different language than what she used.

Your job is to:
1. Detect the language of the message
2. Understand symptoms in ANY Indian language
3. Classify the risk level based on WHO + NHM guidelines
4. Respond warmly in the SAME language she used

CLASSIFICATION RULES (based on WHO ANC 2016 Table 3.1):

RED — Immediate danger. Refer to hospital NOW. Trigger ASHA alert.
These include: severe headache, blurry vision, heavy bleeding, no fetal
movement, chest pain, difficulty breathing, high fever, seizures,
convulsions, severe abdominal pain, swollen face or hands, water breaking,
preeclampsia symptoms, eclampsia.

AMBER — Monitor closely. Follow up within 24 hours.
These include: mild headache, dizziness, back pain, swollen feet, nausea,
vomiting, light bleeding, spotting, leg cramps, fatigue, mild fever,
reduced fetal movement, breathlessness, UTI symptoms, anxiety, stress.

GREEN — Normal pregnancy symptom. Reassure the woman.
These include: food cravings, frequent urination, breast tenderness,
bloating, mild fatigue, emotional sensitivity, stuffy nose, vivid dreams.

MYTH — Woman has asked about a pregnancy myth.
Common myths: papaya causes miscarriage, pineapple is dangerous,
avoid water, exercise is harmful, eating for two, saffron makes baby fair,
ghee eases delivery, cold food harms baby, heartburn means baby has hair.

TIP — Woman is asking for advice or weekly guidance.

RESPONSE FORMAT — always respond in exactly this format:
LEVEL: (RED or AMBER or GREEN or MYTH or TIP)
MESSAGE: (your warm response in the SAME language she used, max 4 sentences)
ASHA_ALERT: (YES or NO)

IMPORTANT RULES:
- Never diagnose. Never prescribe medicine.
- Always cite WHO or NHM when classifying danger signs.
- For RED — always say ASHA worker has been notified
- Be warm and caring like a knowledgeable friend
- Maximum 4 sentences in MESSAGE
- ALWAYS match the language of the woman"""

def analyze(message, pregnancy_week):
    """
    Uses Groq AI (Llama 3) to analyze symptoms.
    Falls back to rule-based if API fails.
    Returns: (level, response_message, asha_alert_needed)
    """

    # ── Try AI first ──────────────────────────────────────────────
    try:
        client = Groq(api_key=GROQ_API_KEY)

        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Pregnant woman, week {pregnancy_week}, says: '{message}'"
                }
            ]
        )

        result = chat.choices[0].message.content.strip()

        # Parse AI response
        level      = ""
        ai_message = ""
        asha_alert = "NO"

        for line in result.split("\n"):
            if line.startswith("LEVEL:"):
                level = line.replace("LEVEL:", "").strip()
            elif line.startswith("MESSAGE:"):
                ai_message = line.replace("MESSAGE:", "").strip()
            elif line.startswith("ASHA_ALERT:"):
                asha_alert = line.replace("ASHA_ALERT:", "").strip()

        # If AI gave valid response return it
        if level in ["RED", "AMBER", "GREEN", "MYTH", "TIP"] and ai_message:
            return level, ai_message, asha_alert

    except Exception as e:
        print(f"Groq AI error — falling back to rules: {e}")

    # ── Fallback to rule-based if AI fails ────────────────────────
    return rule_based_analyze(message, pregnancy_week)


def rule_based_analyze(message, pregnancy_week):
    """
    Backup rule-based analyzer using WHO + NHM symptom lists.
    Used only if Groq AI is unavailable.
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

    # Check tips
    tip_triggers = ["tip", "advice", "what should i do", "guide",
                    "help", "suggest", "this week", "what to eat"]
    if any(t in text for t in tip_triggers):
        return "TIP", get_weekly_tip(pregnancy_week), "NO"

    # Check RED danger signs
    for sign in WHO_DANGER_SIGNS:
        if sign in text:
            return "RED", (
                f"Yeh symptom serious hai — WHO guidelines ke according "
                f"yeh danger sign hai. Week {pregnancy_week} mein turant "
                f"nearest health centre jaiye. Aapki ASHA worker ko "
                f"alert kar diya gaya hai. Aap akeli nahi hain."
            ), "YES"

    # Check AMBER moderate signs
    for sign in NHM_MODERATE_SIGNS:
        if sign in text:
            return "AMBER", (
                f"NHM guidelines ke according yeh symptom monitor karna "
                f"zaroori hai. Week {pregnancy_week} mein rest karein, "
                f"paani piyen, aur 24 ghante mein ASHA worker ko batayein. "
                f"Agar worse ho jaaye toh turant message karein."
            ), "NO"

    # Default
    return "GREEN", (
        f"Week {pregnancy_week} mein yeh generally normal hai. "
        f"Rest karein, paani piyen, iron ki goli lena mat bhoolein. "
        f"Aap safe hain — main hamesha yahan hoon aapke liye!"
    ), "NO"
