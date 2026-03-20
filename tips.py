# ─────────────────────────────────────────────────────────────────
# MaaSakhi Weekly Pregnancy Tips
# Source: WHO ANC Guidelines 2016
#       + NHM Maternal Health Protocol 2019
#       + ICMR Dietary Guidelines 2020
# ─────────────────────────────────────────────────────────────────


def get_weekly_tip(week):

    # ── First Trimester (Weeks 1 to 12) ──────────────────────────
    if week <= 12:
        return (
            f"🌱 Week {week} — First Trimester\n\n"
            "What is happening: Your baby's brain, heart and spine are forming.\n\n"
            "What you must do:\n"
            "• Take folic acid 400mcg every day — prevents brain defects (WHO)\n"
            "• Book your first ANC checkup immediately if not done\n"
            "• Avoid alcohol, tobacco, and raw or undercooked food\n"
            "• Rest when tired — fatigue is completely normal\n"
            "• Eat small frequent meals if nausea is a problem\n\n"
            "Warning signs to report immediately:\n"
            "• Heavy bleeding\n"
            "• Severe pain\n"
            "• High fever\n\n"
            "Source: WHO ANC Guidelines 2016 + NHM Module 6"
        )

    # ── Second Trimester (Weeks 13 to 27) ────────────────────────
    elif week <= 27:
        return (
            f"🌸 Week {week} — Second Trimester\n\n"
            "What is happening: Your baby is growing fast and you should feel movements.\n\n"
            "What you must do:\n"
            "• Take iron and folic acid tablet every day (NHM protocol)\n"
            "• Take calcium supplement as advised by your doctor\n"
            "• Attend ANC checkup every 4 weeks\n"
            "• Sleep on your left side — better blood flow to baby\n"
            "• Eat iron rich foods: spinach, lentils, dates, jaggery\n"
            "• Drink 8 to 10 glasses of water every day\n\n"
            "Warning signs to report immediately:\n"
            "• Severe headache or blurry vision\n"
            "• Heavy bleeding\n"
            "• No fetal movement after week 20\n"
            "• Swelling in face or hands\n\n"
            "Source: NHM ASHA Training Module 6 + WHO ANC 2016"
        )

    # ── Third Trimester (Weeks 28 to 40) ─────────────────────────
    else:
        return (
            f"🌺 Week {week} — Third Trimester\n\n"
            "What is happening: Baby is preparing for birth. You are nearly there!\n\n"
            "What you must do:\n"
            "• ANC checkup every 2 weeks from week 28\n"
            "• Count fetal movements daily — should feel at least 10 per 2 hours\n"
            "• Pack your hospital bag now\n"
            "• Know your nearest health centre and how to get there\n"
            "• Make sure your ASHA worker has your correct phone number\n"
            "• Continue iron, folic acid and calcium tablets\n\n"
            "Warning signs requiring IMMEDIATE hospital visit:\n"
            "• Severe headache + blurry vision (preeclampsia risk)\n"
            "• Water breaking or fluid leaking\n"
            "• Heavy bleeding\n"
            "• Baby stops moving\n"
            "• Contractions before week 37\n\n"
            "Source: WHO ANC Guidelines 2016 + NHM Delivery Preparedness Protocol"
        )
