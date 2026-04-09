# 🌿 MaaSakhi — AI Maternal Health Companion for Rural India

> **माँ की सखी** — Mother's Friend  
> An AI-powered WhatsApp bot that gives every rural pregnant woman a knowledgeable health companion available 24/7 in her own language.

---

## 📌 Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [3-Tier System](#3-tier-system)
- [WhatsApp Bot Flow](#whatsapp-bot-flow)
- [Symptom Triage System](#symptom-triage-system)
- [Alert System](#alert-system)
- [Care Loop — Pending → Attended → Resolved](#care-loop)
- [ASHA Worker Dashboard](#asha-worker-dashboard)
- [Admin Panel](#admin-panel)
- [Smart ASHA Assignment](#smart-asha-assignment)
- [Database Schema](#database-schema)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)
- [Medical Sources](#medical-sources)
- [Team](#team)

---

## Project Overview

MaaSakhi is an AI-powered maternal health companion built inside WhatsApp. Pregnant women register once and receive:

- Personalized weekly health tips
- AI-powered symptom triage (GREEN / AMBER / RED)
- Instant ASHA worker alerts for danger symptoms
- Hindi voice note support
- 100+ Indian language support
- ANC checkup and medicine reminders
- Pregnancy myth busting
- Personal health log with risk scoring
- Complete care loop from alert to resolution

**No app download. No English required. No new device needed.**

---

## Problem Statement

- **136 mothers die every day** in India from largely preventable complications
- India has **96 maternal deaths per 100,000 births** — 10x worse than UK
- Rural women have **zero real-time health support** between monthly checkups
- Average gap between a danger symptom and ASHA response: **18 hours**
- **1 million ASHA workers** cover 5-6 villages each with paper registers and ₹2,000/month salary
- Health myths spread on the same WhatsApp channel rural women trust

---

## Solution

```
Woman sends symptom on WhatsApp
            ↓
Groq Whisper transcribes voice (if voice note)
            ↓
Groq Llama 3.3 analyzes with WHO + NHM guidelines
            ↓
GREEN → Reassurance + tips
AMBER → Monitor + follow up
RED   → Instant ASHA WhatsApp alert (< 30 seconds)
            ↓
ASHA marks "Attended" on dashboard
            ↓
Patient receives WhatsApp asking if she is better
            ↓
Patient replies "I am better" → Case RESOLVED ✅
Patient replies "Still not well" → New escalation alert 🚨
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER LAYER                          │
│              WhatsApp (500M users)                      │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   TWILIO API                            │
│          WhatsApp Sandbox / Cloud API                   │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                 FLASK BACKEND                           │
│              Python 3.11 + Flask                        │
│         app.py / analyzer.py / alerts.py               │
└──────┬──────────────────┬──────────────────┬────────────┘
       │                  │                  │
┌──────▼──────┐  ┌────────▼───────┐  ┌──────▼──────────┐
│  GROQ AI    │  │  GROQ WHISPER  │  │   POSTGRESQL    │
│ Llama 3.3   │  │  Voice → Text  │  │   Railway DB    │
│ Symptom AI  │  │  Hindi + 100+  │  │  Permanent logs │
└─────────────┘  └────────────────┘  └─────────────────┘
```

---

## Features

### WhatsApp Bot Features
| Feature | Description |
|---|---|
| 📋 Registration | One-time registration — name, week, village |
| 🎤 Voice Notes | Hindi voice note transcription via Groq Whisper |
| 🌍 100+ Languages | Supports Hindi, Tamil, Telugu, Bengali, Gujarati, Kannada and more |
| 🧠 AI Symptom Triage | WHO ANC 2016 + NHM Module 6 based classification |
| 🚨 Danger Alerts | RED symptoms trigger instant ASHA WhatsApp alert |
| 💛 AMBER Monitoring | Moderate symptoms logged and monitored |
| ✅ GREEN Reassurance | Normal symptoms receive reassurance + tips |
| 💊 Medicine Reminders | Iron, folic acid, calcium schedule alerts |
| 🏥 ANC Reminders | NHM antenatal checkup schedule reminders |
| 📊 Progress Tracker | Personalized weekly updates with baby size comparisons |
| 🧾 Health Log | Every symptom saved to personal database permanently |
| 📈 Risk Score | Cumulative risk score calculated from symptom history |
| 🌱 Myth Busting | FOGSI 2021 guideline-based pregnancy myth correction |
| 🔄 Recovery Confirmation | Patient confirms recovery → case marked Resolved |
| 🚨 Re-escalation | "Still not well" → automatic new alert to ASHA |

### ASHA Dashboard Features
| Feature | Description |
|---|---|
| 👩 Patient List | All registered patients with risk scores and bars |
| ⚠️ Alert Cards | High risk alerts with color-coded status |
| ✅ Mark Attended | One-click to mark alert as attended |
| 📱 Auto Patient Message | Marks attended → patient gets WhatsApp asking recovery |
| 🟢 Resolved Status | Case closes when patient confirms recovery |
| 📊 Stats | High Risk / Total / Safe patient counts (updates in real-time) |
| 🔄 Auto Refresh | Dashboard refreshes every 30 seconds |

### Admin Panel Features
| Feature | Description |
|---|---|
| ➕ Add ASHA Workers | Add workers with ID, name, phone, village, district |
| 🗺️ Village Map | See all villages with ASHA workers mapped to each |
| 👩 All Patients | View every patient across all ASHA workers |
| 🚨 All Alerts | District-wide alert view with ASHA and village info |
| ✅ Activate/Deactivate | Toggle ASHA worker active status |
| 🗑️ Delete Worker | Remove ASHA workers from system |
| 📊 Per-ASHA Stats | Patient count and alert count per worker |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AI Triage | Groq Llama 3.3 70B | Fastest LLM, 100+ languages, free tier |
| Voice AI | Groq Whisper Large V3 | Best Hindi/Indian language accuracy |
| Backend | Python 3.11 + Flask | Lightweight, fast, easy deployment |
| Database | PostgreSQL on Railway | Permanent storage, DPDP 2023 compliant |
| Messaging | Twilio WhatsApp API | Real WhatsApp, 500M Indian users |
| Deployment | Railway Cloud | 24/7 auto-scaling, GitHub auto-deploy |
| ORM | SQLAlchemy + Psycopg2 | Reliable PostgreSQL connection |
| Medical Data | WHO + NHM + FOGSI + ICMR | Government-backed clinical guidelines |

---

## 3-Tier System

```
┌─────────────────────────────────┐
│         ADMIN / SUPERVISOR      │
│  - Add/manage ASHA workers      │
│  - View district-wide data      │
│  - Village mapping              │
│  - All alerts overview          │
│  Login: /admin/login            │
└────────────────┬────────────────┘
                 │ manages
┌────────────────▼────────────────┐
│         ASHA WORKER             │
│  - See her patients only        │
│  - Receive RED alerts           │
│  - Mark alerts attended         │
│  - Monitor village health       │
│  Login: /login                  │
└────────────────┬────────────────┘
                 │ monitors
┌────────────────▼────────────────┐
│         PREGNANT WOMAN          │
│  - Register via WhatsApp        │
│  - Report symptoms anytime      │
│  - Receive guidance in Hindi    │
│  - Confirm recovery             │
│  Access: WhatsApp +14155238886  │
└─────────────────────────────────┘
```

---

## WhatsApp Bot Flow

### Registration Flow
```
Woman sends: "Register" / "Hello" / "Hi" / "Namaste"
    ↓
Bot asks: "Apna naam batao" (Tell me your name)
    ↓
Woman enters name
    ↓
Bot asks: "Kitne hafte ki pregnant hain?" (How many weeks?)
    ↓
Woman enters week number (e.g. 26)
    ↓
Bot asks: "Aap kis gaon se hain?" (Which village?)
    ↓
Woman enters village name
    ↓
System auto-assigns least-loaded ASHA worker in that village
    ↓
✅ Registered! Woman receives welcome message + first tip
```

### Symptom Reporting Flow
```
Registered woman sends symptom (text or voice note)
    ↓
[If voice note] → Groq Whisper transcribes to text
    ↓
Groq Llama 3.3 analyzes:
  - Symptom text
  - Pregnancy week
  - Previous symptom history
  - WHO ANC 2016 danger signs
  - NHM Module 6 moderate signs
    ↓
GREEN → Reassurance message + tip + iron reminder
AMBER → Monitor message + follow up in 24 hours
RED   → Danger alert + ASHA WhatsApp + hospital advice
MYTH  → Myth correction from FOGSI guidelines
TIP   → Weekly tip response
```

---

## Symptom Triage System

### RED — Danger Signs (WHO ANC 2016)
Triggers immediate ASHA alert and hospital advice:
- Severe headache with blurry vision (preeclampsia)
- Heavy vaginal bleeding
- Severe abdominal pain
- Fever above 38°C
- No fetal movement for 12+ hours
- Convulsions / fits
- Difficulty breathing
- Unconsciousness

### AMBER — Moderate Signs (NHM Module 6)
Logged and monitored, follow-up in 24 hours:
- Mild headache
- Nausea and vomiting
- Mild swelling of feet
- Fatigue and weakness
- Mild back pain

### GREEN — Normal Symptoms
Reassurance with tips:
- Normal pregnancy discomforts
- General questions
- Nutrition queries

---

## Alert System

### How Alerts Work

```
1. Patient reports RED symptom on WhatsApp
          ↓
2. MaaSakhi saves alert to PostgreSQL:
   - Patient name, phone, week
   - Symptom text
   - ASHA worker ID
   - Status: PENDING
   - Timestamp
          ↓
3. Twilio sends real WhatsApp to ASHA worker:
   "🚨 HIGH RISK ALERT — MaaSakhi
    Patient: [name]
    Week: [week]
    Symptom: [symptom]
    Phone: [phone]
    Please contact immediately!"
          ↓
4. Alert appears on ASHA dashboard in RED
```

### Alert Status Flow
```
PENDING (🔴) → ATTENDED (🟡) → RESOLVED (🟢)
```

| Status | Meaning | Who Changes It |
|---|---|---|
| PENDING | Alert fired, no action yet | System (automatic) |
| ATTENDED | ASHA has visited patient | ASHA worker clicks button |
| RESOLVED | Patient confirmed recovery | Patient replies on WhatsApp |

---

## Care Loop

This is MaaSakhi's complete end-to-end care workflow:

```
Step 1: Patient sends danger symptom
        → Status: PENDING 🔴
        → ASHA gets WhatsApp alert

Step 2: ASHA visits patient
        → ASHA clicks "Mark as Attended" on dashboard
        → Status: ATTENDED 🟡
        → Patient AUTOMATICALLY receives WhatsApp:
          "Meena Kumari ne aapka case attend kar liya hai.
           Kya aap ab theek feel kar rahi hain?
           Reply: 'I am better' or 'Still not feeling well'"

Step 3A: Patient replies "I am better" / "theek hoon"
         → Status: RESOLVED 🟢
         → High risk count decreases
         → Safe patient count increases
         → Case closed ✅

Step 3B: Patient replies "Still not feeling well"
         → NEW alert fires automatically 🚨
         → ASHA gets fresh escalation alert
         → Status: PENDING again
         → Cycle continues until resolved
```

### Recovery Keywords Detected
**Patient is better:** i am better, i am fine, theek hoon, theek hu, better now, feeling better, mujhe theek, ab theek, recovered, all good, sahi hoon, achha feel

**Patient not well:** still not, abhi bhi, nahi theek, not better, still sick, still pain, still feeling well

---

## ASHA Worker Dashboard

**URL:** `/dashboard/<asha_id>`  
**Login:** `/login` — enter 10-digit mobile number

### Dashboard Sections

**Stats Row:**
- High Risk Alerts (Pending + Attended only — Resolved excluded)
- Total Registered Patients
- Safe Patients (Total minus active High Risk)

**Alert Cards:**
- Color coded: Red (Pending), Yellow (Attended), Green (Resolved)
- Shows: Patient name, week, symptom, phone, time
- Status flow indicator: Pending → Attended → Resolved
- "Mark as Attended" button (only on Pending alerts)
- Auto-message sent to patient when marked Attended

**Patient List:**
- All registered patients
- Risk bar (visual indicator)
- Risk level badge: HIGH / MODERATE / LOW
- Risk score: 0-100

---

## Admin Panel

**URL:** `/admin`  
**Login:** `/admin/login`  
**Default credentials:**
- Username: `admin`
- Password: `maasakhi2026`

### Tab 1: ASHA Workers
Add new ASHA workers with:
- ASHA ID (unique identifier)
- Full name
- WhatsApp phone number
- Village name
- District (optional)

Actions: Activate / Deactivate / Delete

### Tab 2: Village Map
Visual map showing:
- Every village covered
- All ASHA workers per village
- Patient count per ASHA worker (real-time)

### Tab 3: All Patients
District-wide patient view:
- Name, week, village, ASHA worker assigned
- Risk level for every patient

### Tab 4: All Alerts
District-wide alerts:
- All RED alerts across all ASHA workers
- ASHA worker name and village for each alert
- Status (Pending / Attended / Resolved)
- High risk stat card excludes Resolved alerts

---

## Smart ASHA Assignment

When a woman registers and enters her village name, MaaSakhi automatically assigns the ASHA worker with the **fewest active patients** in that village at that moment.

```sql
SELECT a.asha_id, a.name, COUNT(p.phone) AS patient_count
FROM asha_workers a
LEFT JOIN patients p ON p.asha_id = a.asha_id
WHERE LOWER(a.village) = LOWER(:village)
AND a.is_active = TRUE
GROUP BY a.asha_id, a.name
ORDER BY patient_count ASC
LIMIT 1
```

This ensures:
- No single ASHA worker gets overloaded
- Load balancing across multiple ASHAs in same village
- Real-time assignment based on current active patients

---

## Database Schema

### `admins`
| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| username | TEXT | Unique username |
| password | TEXT | Password |
| name | TEXT | Display name |
| created_at | TIMESTAMP | Creation time |

### `asha_workers`
| Column | Type | Description |
|---|---|---|
| asha_id | TEXT | Primary key |
| name | TEXT | Full name |
| phone | TEXT | WhatsApp number |
| village | TEXT | Village name |
| district | TEXT | District name |
| is_active | BOOLEAN | Active status |
| created_at | TIMESTAMP | Creation time |

### `patients`
| Column | Type | Description |
|---|---|---|
| phone | TEXT | Primary key (WhatsApp number) |
| name | TEXT | Patient name |
| week | INTEGER | Pregnancy week |
| step | TEXT | Registration step |
| language | TEXT | Detected language |
| asha_id | TEXT | Assigned ASHA worker |
| village | TEXT | Patient village |
| created_at | TIMESTAMP | Registration time |
| updated_at | TIMESTAMP | Last update time |

### `symptom_logs`
| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| phone | TEXT | Patient phone |
| week | INTEGER | Pregnancy week at report time |
| message | TEXT | Symptom text |
| level | TEXT | GREEN / AMBER / RED |
| created_at | TIMESTAMP | Report time |

### `asha_alerts`
| Column | Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| phone | TEXT | Patient phone |
| name | TEXT | Patient name |
| week | INTEGER | Pregnancy week |
| symptom | TEXT | Danger symptom |
| asha_id | TEXT | ASHA worker assigned |
| status | TEXT | Pending / Attended / Resolved |
| created_at | TIMESTAMP | Alert time |

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Twilio account with WhatsApp sandbox
- Groq API key

### Local Setup

```bash
# Clone the repository
git clone https://github.com/PriyancySingal/MaaSakhi.git
cd MaaSakhi

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Fill in your API keys in .env

# Run locally
python app.py
```

### requirements.txt
```
flask
twilio
groq
sqlalchemy
psycopg2-binary
requests
gunicorn
```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@host/db` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `ACxxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `xxxxxxxxxxxxxxxx` |
| `GROQ_API_KEY` | Groq API Key | `gsk_xxxxxxxxxxxxxxxxx` |
| `SECRET_KEY` | Flask session secret | `maasakhi2026secret` |
| `ASHA_NUMBER` | Fallback ASHA WhatsApp number | `whatsapp:+919XXXXXXXXX` |
| `PORT` | Server port | `5000` |

---

## Deployment

MaaSakhi is deployed on **Railway** with automatic GitHub deployment.

**Live URL:** `maasakhi-production.up.railway.app`

### Railway Setup
1. Connect GitHub repository to Railway
2. Add PostgreSQL database service
3. Set all environment variables
4. Add `RAILPACK_PYTHON_VERSION=3.11`
5. Railway auto-deploys on every `git push origin main`

### Twilio WhatsApp Sandbox
- Number: `+1 415 523 8886`
- Join code: `join kitchen-highest`
- URL: `https://maasakhi-production.up.railway.app/`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Homepage |
| POST | `/whatsapp` | Twilio WhatsApp webhook |
| GET | `/login` | ASHA worker login page |
| POST | `/login` | ASHA worker login submit |
| GET | `/dashboard/<asha_id>` | ASHA worker dashboard |
| POST | `/dashboard/<asha_id>/attend/<alert_id>` | Mark alert as attended |
| GET | `/admin/login` | Admin login page |
| POST | `/admin/login` | Admin login submit |
| GET | `/admin` | Admin panel |
| GET | `/admin?tab=asha` | ASHA workers tab |
| GET | `/admin?tab=map` | Village map tab |
| GET | `/admin?tab=patients` | All patients tab |
| GET | `/admin?tab=alerts` | All alerts tab |
| POST | `/admin/add-asha` | Add new ASHA worker |
| POST | `/admin/toggle-asha` | Activate/deactivate ASHA |
| POST | `/admin/delete-asha` | Delete ASHA worker |
| GET | `/admin/logout` | Admin logout |

---

## Medical Sources

| Source | Used For |
|---|---|
| WHO Antenatal Care Guidelines 2016 (Table 3.1) | RED danger sign detection |
| NHM India ASHA Training Module 6 | AMBER moderate symptom monitoring |
| FOGSI Clinical Practice Guidelines 2021 | Pregnancy myth corrections |
| ICMR Dietary Guidelines 2020 | Nutrition and food advice |
| Mayo Clinic Pregnancy Guide | Baby development milestones |

---

## Risk Score Calculation

Risk score (0-100) is calculated from each patient's complete symptom history:

```python
score = (red_count × 40) + (amber_count × 15) + (green_count × 2)
# Capped at 100

# Recent escalation bonus
if recent_reds >= 2:  # Last 3 reports
    score += 20

# Risk levels
HIGH     = score >= 60 OR red_count >= 2
MODERATE = score >= 30 OR red_count >= 1
LOW      = everything else
```

---

## Project Structure

```
MaaSakhi/
├── app.py          # Main Flask app + all routes
├── analyzer.py     # Groq AI symptom analysis
├── alerts.py       # ASHA WhatsApp alert system
├── dashboard.py    # ASHA worker dashboard HTML + render
├── admin.py        # Admin panel HTML + render
├── database.py     # PostgreSQL layer (all DB functions)
├── voice.py        # Groq Whisper voice transcription
├── tracker.py      # Pregnancy progress tracker
├── symptoms.py     # WHO/NHM symptom database
├── myths.py        # FOGSI myths database
├── tips.py         # Weekly pregnancy tips
├── health_log.py   # Health log utilities
├── config.py       # Environment variable config
├── requirements.txt
├── Procfile        # Railway/Heroku process file
└── static/
    └── logo.png    # MaaSakhi logo
```

---

## Team



| Member | Role |
|---|---|
| Priyancy Singal | AI Developer & Backend Engineer — WhatsApp bot, Groq AI integration, PostgreSQL, Railway deployment |
| Tanisha | Research & Product Designer — WHO/NHM medical research, UX design, ASHA worker integration |

---


## License

Built during hackathon. All medical guidance is based on WHO, NHM, FOGSI and ICMR published guidelines. MaaSakhi is a triage tool — not a medical diagnosis system. Always consult a doctor.

---

*🌿 MaaSakhi — Because every mother deserves a knowledgeable friend available at 3am, who speaks her language, and knows when to call for help.*
