# ─────────────────────────────────────────────────────────────────
# MaaSakhi Symptom Database
# Source 1: WHO Antenatal Care Guidelines 2016 — Table 3.1
# Source 2: NHM India ASHA Training Module 6 (2019)
# Source 3: ICMR Maternal Health Protocols 2022
# ─────────────────────────────────────────────────────────────────


# ── RED: Danger Signs (WHO ANC 2016 — Table 3.1) ─────────────────
# These require IMMEDIATE referral to health facility

WHO_DANGER_SIGNS = [
    # Neurological
    "severe headache",
    "blurry vision",
    "blurred vision",
    "vision problem",
    "seeing stars",
    "convulsion",
    "seizure",
    "fits",
    "unconscious",
    "fainted",
    "collapsed",

    # Bleeding
    "heavy bleeding",
    "heavy vaginal bleeding",
    "lots of blood",
    "bleeding heavily",

    # Fetal
    "no fetal movement",
    "baby not moving",
    "no movement",
    "stopped moving",
    "fetal movement stopped",

    # Respiratory
    "chest pain",
    "difficulty breathing",
    "cant breathe",
    "cannot breathe",
    "shortness of breath severe",

    # Fever
    "high fever",
    "fever above 38",
    "very high temperature",

    # Pain
    "severe abdominal pain",
    "severe stomach pain",
    "severe pain",
    "unbearable pain",

    # Swelling — severe
    "swelling face",
    "swollen face",
    "face swollen",
    "swelling hands",
    "swollen hands",
    "hands swollen",

    # Labour signs
    "water broke",
    "fluid leaking",
    "bag of waters",
    "amniotic fluid",

    # Conditions
    "preeclampsia",
    "eclampsia",
    "cord prolapse",
    "placenta",
]


# ── AMBER: Moderate Risk (NHM ASHA Training Module 6) ────────────
# These need monitoring and follow-up within 24 hours

NHM_MODERATE_SIGNS = [
    # Head and vision
    "mild headache",
    "headache",
    "dizziness",
    "lightheaded",
    "feeling faint",

    # Bleeding — mild
    "light bleeding",
    "spotting",
    "slight bleeding",
    "pink discharge",
    "brown discharge",

    # Swelling — mild
    "slight swelling",
    "swollen feet",
    "swollen legs",
    "ankle swelling",
    "puffy feet",
    "feet swollen",

    # Digestive
    "nausea",
    "vomiting",
    "morning sickness",
    "constipation",
    "heartburn",
    "acidity",
    "indigestion",

    # Pain — mild
    "back pain",
    "backache",
    "pelvic pain",
    "hip pain",
    "round ligament pain",
    "leg cramps",
    "cramps",

    # General
    "fatigue",
    "tired",
    "weakness",
    "exhausted",
    "no energy",
    "pale",

    # Fever — mild
    "mild fever",
    "low grade fever",
    "slight temperature",

    # Fetal — reduced
    "reduced movement",
    "less movement",
    "baby moving less",
    "not moving much",

    # Breathing — mild
    "breathless",
    "slightly breathless",

    # Skin
    "itching",
    "rash",
    "skin irritation",

    # Infection
    "burning urination",
    "painful urination",
    "uti",
    "urinary infection",
    "vaginal discharge",
    "unusual discharge",

    # Mental health
    "anxiety",
    "stress",
    "depression",
    "feeling sad",
    "mood swings",
    "not sleeping",
    "insomnia",
]


# ── GREEN: Normal Pregnancy Symptoms ─────────────────────────────
# Common symptoms that are expected and safe

NORMAL_SIGNS = [
    "mild nausea",
    "food cravings",
    "frequent urination",
    "needing to pee often",
    "breast tenderness",
    "sore breasts",
    "bloating",
    "gas",
    "slight fatigue",
    "emotional",
    "crying",
    "sensitive",
    "stuffy nose",
    "nasal congestion",
    "bleeding gums",
    "gum sensitivity",
    "vivid dreams",
    "strange dreams",
]
