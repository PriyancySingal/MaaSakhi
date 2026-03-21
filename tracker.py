# ─────────────────────────────────────────────────────────────────
# MaaSakhi Pregnancy Progress Tracker
# Generates PERSONALIZED updates based on woman's actual health log
# Source: WHO ANC 2016 + NHM India + Mayo Clinic Pregnancy Guide
# ─────────────────────────────────────────────────────────────────

import os
from groq import Groq
from health_log import get_health_log, get_risk_score, get_symptom_pattern

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

BABY_SIZE = {
    4:  ("poppy seed", "khus khus ka beej", "0.1 cm"),
    5:  ("sesame seed", "til ka beej", "0.2 cm"),
    6:  ("lentil", "masoor dal", "0.6 cm"),
    7:  ("blueberry", "jamun", "1.3 cm"),
    8:  ("kidney bean", "rajma", "1.6 cm"),
    9:  ("grape", "angoor", "2.3 cm"),
    10: ("strawberry", "strawberry", "3.1 cm"),
    11: ("fig", "anjeer", "4.1 cm"),
    12: ("lime", "nimbu", "5.4 cm"),
    13: ("pea pod", "matar ki phali", "7.4 cm"),
    14: ("lemon", "bada nimbu", "8.7 cm"),
    15: ("apple", "seb", "10.1 cm"),
    16: ("avocado", "makhanphal", "11.6 cm"),
    17: ("pear", "nashpati", "13 cm"),
    18: ("bell pepper", "shimla mirch", "14.2 cm"),
    19: ("mango", "aam", "15.3 cm"),
    20: ("banana", "kela", "16.4 cm"),
    21: ("carrot", "gajar", "26.7 cm"),
    22: ("papaya", "papita", "27.8 cm"),
    23: ("grapefruit", "chakotra", "28.9 cm"),
    24: ("corn", "makka", "30 cm"),
    25: ("cauliflower", "gobhi", "34.6 cm"),
    26: ("lettuce", "salad patta", "35.6 cm"),
    27: ("cabbage", "patta gobhi", "36.6 cm"),
    28: ("eggplant", "baingan", "37.6 cm"),
    29: ("butternut squash", "kaddu", "38.6 cm"),
    30: ("cucumber", "kheera", "39.9 cm"),
    31: ("coconut", "nariyal", "41.1 cm"),
    32: ("squash", "tori", "42.4 cm"),
    33: ("pineapple", "ananas", "43.7 cm"),
    34: ("cantaloupe", "kharbooja", "45 cm"),
    35: ("honeydew melon", "melon", "46.2 cm"),
    36: ("romaine lettuce", "salad", "47.4 cm"),
    37: ("winter melon", "petha", "48.6 cm"),
    38: ("watermelon", "tarbooz", "49.8 cm"),
    39: ("pumpkin", "kaddu", "50.7 cm"),
    40: ("jackfruit", "kathal", "51.2 cm"),
}

MILESTONES = {
    6:  "Baby's heart starts beating! 💗",
    8:  "All major organs are forming!",
    10: "Baby can now make tiny movements!",
    12: "First trimester complete! Risk drops significantly.",
    16: "Baby can hear your voice now! Talk and sing to them. 🎵",
    18: "Baby's gender can be seen on ultrasound now.",
    20: "Halfway there! You may start feeling movements.",
    24: "Baby's face is fully formed with eyebrows and eyelashes!",
    28: "Third trimester begins! Baby can open their eyes.",
    32: "Baby is practicing breathing movements!",
    36: "Baby is considered early term!",
    37: "Baby is full term! 🎉",
    40: "Due date! Your baby is ready to meet you! 🌸",
}


def get_progress_update(week, name, phone, language="Hindi"):
    """
    Generates PERSONALIZED progress update using:
    - Woman's actual symptom history
    - Her real risk score
    - WHO + NHM weekly guidelines
    """

    # Get her real health data
    score, risk_level, summary   = get_risk_score(phone)
    symptom_pattern              = get_symptom_pattern(phone)
    log                          = get_health_log(phone)
    total_reports                = len(log)

    # Get baby size
    closest_week   = min(BABY_SIZE.keys(), key=lambda x: abs(x - week))
    eng_size, hindi_size, length = BABY_SIZE[closest_week]

    # Get milestone
    milestone = ""
    for m_week, m_text in MILESTONES.items():
        if abs(week - m_week) <= 1:
            milestone = m_text
            break

    try:
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""You are MaaSakhi, a warm and caring maternal health 
companion for Indian women.

Generate a PERSONALIZED pregnancy progress update for this specific woman:

WOMAN'S PROFILE:
- Name: {name}
- Current week: {week}
- Total symptom reports submitted: {total_reports}
- Overall risk score: {score}/100
- Risk level: {risk_level}

HER ACTUAL SYMPTOM HISTORY:
{symptom_pattern}

BABY THIS WEEK:
- Size: like a {hindi_size} ({eng_size}) — {length} long
- Milestone: {milestone if milestone else "steady healthy growth"}

YOUR TASK:
Write a warm personalized update that:
1. Greets her by name warmly
2. Mentions her baby's size using the Indian comparison
3. Acknowledges her specific symptom history — if she had RED symptoms 
   recently, express concern and remind her to stay vigilant. If all GREEN,
   praise her for staying healthy.
4. Give her ONE specific advice based on her risk level:
   - HIGH risk: urge immediate ANC checkup
   - MODERATE risk: monitor closely, visit ASHA worker this week
   - LOW risk: keep up the good work, routine checkup reminder
5. Share the baby milestone if there is one
6. End with an encouraging personal message

Reply in {language} language only.
Be warm, personal, and caring — like a trusted friend who knows her story.
Max 10 lines. Use emoji naturally."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Tracker error: {e}")
        return get_fallback_update(
            week, name, eng_size,
            hindi_size, length,
            milestone, risk_level, score
        )


def get_fallback_update(week, name, eng_size, hindi_size,
                        length, milestone, risk_level, score):
    risk_advice = {
        "HIGH":     "⚠️ Please visit your doctor or health centre this week.",
        "MODERATE": "🟡 Please visit your ASHA worker this week.",
        "LOW":      "✅ Keep up the great work!"
    }
    return (
        f"🌸 Week {week} Update for {name}!\n\n"
        f"Your baby is now the size of a {hindi_size} "
        f"({eng_size}) — about {length} long!\n\n"
        f"{milestone}\n\n"
        f"Your health risk score: {score}/100 ({risk_level} risk)\n"
        f"{risk_advice.get(risk_level, '')}\n\n"
        f"Keep taking iron and folic acid daily. 💚\n"
        f"Source: WHO ANC Guidelines 2016 + NHM India"
    )


TRACKER_TRIGGERS = [
    "progress", "update", "this week", "baby size",
    "baby update", "week update", "how is my baby",
    "mera baby", "baby kesa hai", "is week",
    "pregnancy update", "weekly update", "milestone",
    "baby growth", "kitna bada", "how big", "report",
    "meri report", "health update", "mera progress"
]


def is_tracker_request(message):
    text = message.lower()
    return any(trigger in text for trigger in TRACKER_TRIGGERS)