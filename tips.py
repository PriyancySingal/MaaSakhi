# ─────────────────────────────────────────────────────────────────
# MaaSakhi Weekly Pregnancy Tips
# Multilingual — AI generates in woman's language
# Source: WHO ANC Guidelines 2016 + NHM Module 6
# ─────────────────────────────────────────────────────────────────

import os
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def get_weekly_tip(week, language="Hindi"):
    """
    Generates weekly tip in the woman's language using Groq AI.
    Falls back to English if AI fails.
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)

        prompt = f"""You are MaaSakhi, a maternal health companion for Indian women.

Generate a warm, helpful weekly pregnancy tip for week {week} of pregnancy.
Reply in {language} language only.
Keep it simple and friendly — max 5 bullet points.
Include: what is happening with baby, what to eat, what to watch for.
Base it on WHO ANC 2016 and NHM India guidelines.
End with an encouraging line."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Tips generation error: {e}")
        return get_fallback_tip(week)


def get_fallback_tip(week):
    """Fallback tip in English if AI fails."""
    if week <= 12:
        return (
            f"🌱 Week {week} — First Trimester\n\n"
            "• Take folic acid 400mcg daily (WHO recommendation)\n"
            "• Book your first ANC checkup\n"
            "• Avoid alcohol and tobacco\n"
            "• Rest when tired — fatigue is normal\n"
            "• Eat small frequent meals for nausea\n\n"
            "You are doing great! 💚"
        )
    elif week <= 27:
        return (
            f"🌸 Week {week} — Second Trimester\n\n"
            "• Take iron and folic acid daily (NHM protocol)\n"
            "• Attend ANC checkup every 4 weeks\n"
            "• Sleep on your left side\n"
            "• Eat iron rich foods: spinach, lentils, dates\n"
            "• Watch for swelling in face or hands\n\n"
            "You are halfway there! 💚"
        )
    else:
        return (
            f"🌺 Week {week} — Third Trimester\n\n"
            "• ANC checkup every 2 weeks now\n"
            "• Count fetal movements daily\n"
            "• Pack your hospital bag\n"
            "• Know your nearest health centre\n"
            "• Watch for labour signs\n\n"
            "Almost there — you are so brave! 💚"
        )