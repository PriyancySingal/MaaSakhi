# ─────────────────────────────────────────────────────────────────
# MaaSakhi Pregnancy Progress Tracker
# Personalized weekly milestone updates
# Source: WHO ANC 2016 + NHM India + Mayo Clinic Pregnancy Guide
# ─────────────────────────────────────────────────────────────────

import os
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Baby size comparisons by week ─────────────────────────────────
# Makes it relatable and fun for rural Indian women

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

# ── Key milestones by week ────────────────────────────────────────

MILESTONES = {
    6:  "Baby's heart starts beating! 💗",
    8:  "All major organs are forming!",
    10: "Baby can now make tiny movements!",
    12: "First trimester complete! Risk of miscarriage drops significantly.",
    16: "Baby can hear your voice now! Talk and sing to them. 🎵",
    18: "Baby's gender can be seen on ultrasound now.",
    20: "Halfway there! You may start feeling movements soon.",
    24: "Baby's face is fully formed with eyebrows and eyelashes!",
    28: "Third trimester begins! Baby can open their eyes.",
    32: "Baby is practicing breathing movements!",
    36: "Baby is considered early term. Could arrive any time now!",
    37: "Baby is full term! 🎉",
    40: "Due date! Your baby is ready to meet you! 🌸",
}


def get_progress_update(week, name, language="Hindi"):
    """
    Generates a personalized pregnancy progress update
    for the woman's current week using Groq AI.
    """
    # Get baby size info
    closest_week = min(BABY_SIZE.keys(), key=lambda x: abs(x - week))
    english_size, hindi_size, length = BABY_SIZE[closest_week]

    # Check for milestone
    milestone = ""
    for m_week, m_text in MILESTONES.items():
        if abs(week - m_week) <= 1:
            milestone = m_text
            break

    try:
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""You are MaaSakhi, a warm maternal health companion for Indian women.

Generate a personalized pregnancy progress update for:
- Woman's name: {name}
- Current week: {week}
- Baby size this week: like a {english_size} ({hindi_size}) — {length} long
- Special milestone this week: {milestone if milestone else "steady growth"}

Reply in {language} language.

Include in your response:
1. Warm greeting using her name
2. Baby size comparison using the Indian fruit/vegetable name
3. What is developing in baby this week (1-2 interesting facts)
4. One specific thing she should do this week (from WHO/NHM guidelines)
5. One warning sign specific to this week to watch for
6. Encouraging closing line

Keep it warm, simple, and personal. Max 8 lines.
Use emoji naturally. Make her feel special and cared for."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            temperature=0.4,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Tracker error: {e}")
        return get_fallback_update(week, name, english_size,
                                   hindi_size, length, milestone)


def get_fallback_update(week, name, eng_size,
                        hindi_size, length, milestone):
    """Fallback update if AI fails."""
    return (
        f"🌸 Week {week} Update for {name}!\n\n"
        f"Your baby is now the size of a {hindi_size} "
        f"({eng_size}) — about {length} long!\n\n"
        f"{milestone}\n\n"
        f"Keep taking your iron and folic acid tablets daily.\n"
        f"Drink plenty of water and rest well.\n\n"
        f"You are doing amazingly! 💚\n"
        f"Source: WHO ANC Guidelines 2016"
    )


# ── Trigger words that activate the tracker ──────────────────────

TRACKER_TRIGGERS = [
    "progress", "update", "this week", "baby size",
    "baby update", "week update", "how is my baby",
    "mera baby", "baby kesa hai", "is week",
    "pregnancy update", "weekly update", "milestone",
    "baby growth", "kitna bada", "how big"
]


def is_tracker_request(message):
    """Check if woman is asking for progress update."""
    text = message.lower()
    return any(trigger in text for trigger in TRACKER_TRIGGERS)