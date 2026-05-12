# MaaSakhi — AI Maternal Health Companion for Rural India

> **माँ की सखी** — Mother's Friend
> An AI-powered WhatsApp bot that gives every rural pregnant woman a knowledgeable health companion available 24/7 in her own language.

**Live URL:** `maasakhi-production.up.railway.app`
**WhatsApp Bot:** `+1 415 523 8886` (send `join kitchen-highest`)
**GitHub:** `github.com/PriyancySingal/MaaSakhi`

---

## Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Solution](#solution)
- [System Architecture](#system-architecture)
- [5-Tier Hierarchy](#5-tier-hierarchy)
- [Features — All 4 Months](#features)
- [WhatsApp Bot Flow](#whatsapp-bot-flow)
- [Symptom Triage System](#symptom-triage-system)
- [Alert and Escalation System](#alert-and-escalation-system)
- [Care Loop](#care-loop)
- [Month 3 — Analytics and NHM Exports](#month-3--analytics-and-nhm-exports)
- [Month 4 — Postpartum and Child Health](#month-4--postpartum-and-child-health)
- [Smart ASHA Assignment](#smart-asha-assignment)
- [Database Schema](#database-schema)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Medical Sources](#medical-sources)
- [Team](#team)

---

## Project Overview

MaaSakhi is an AI-powered maternal health companion built entirely inside WhatsApp. Pregnant women register once via WhatsApp and receive full end-to-end care — from symptom triage to postpartum support to child immunization tracking — all in their own language, with zero app download required.

The system operates on a **5-tier NHM hierarchy**: District Health Officer → Block Medical Officer → ASHA Supervisor (ANM) → ASHA Worker → Patient, with automated escalation if alerts go unattended.

**No app download. No English required. No new device needed.**

---

## Problem Statement

- **136 mothers die every day** in India from largely preventable complications
- India has **96 maternal deaths per 100,000 births** — 10x worse than the UK
- Rural women have **zero real-time health support** between monthly checkups
- Average gap between a danger symptom and ASHA response: **18 hours**
- **1 million ASHA workers** cover 5–6 villages each with paper registers and Rs. 2,000/month salary
- Health myths spread on the same WhatsApp channel rural women trust

### The Three Users MaaSakhi Serves

**Lakshmi Devi (28)** — 7 months pregnant, lives 34km from hospital. No way to report 2am danger symptoms. Receives harmful pregnancy myths on WhatsApp.

**Meena Kumari (34)** — ASHA worker tracking 40+ women via paper register. Cannot monitor simultaneously. Receives chaotic unstructured messages. No digital tool.

**Dr. Rajesh Sharma (45)** — District Health Officer overseeing 200+ villages. No real-time data. Monthly reports are incomplete. No way to measure ASHA performance.

---

## Solution

```
Woman sends symptom on WhatsApp (text / voice note / image)
            |
            v
[If voice] Groq Whisper Large V3 transcribes in Hindi / 100+ languages
            |
            v
[If postpartum] Route to postpartum / newborn danger sign engine
[If visual]     Ask for photo → forward to ASHA worker
            |
            v
Groq Llama 3.3 70B analyzes vs WHO ANC 2016 + NHM Module 6
            |
    ________|________
   |        |        |
GREEN    AMBER      RED
Reassure  Monitor   ASHA alert < 30 seconds
  +tip    24h f/u   + Maps link + hospital advice
            |
            v
ASHA marks "Attended" on dashboard
            |
            v
Patient receives WhatsApp: "Kya aap ab theek hain?"
            |
      ______|______
     |              |
"I am better"   "Still unwell"
 RESOLVED          New alert fires
```

---

## System Architecture

```
+----------------------------------------------------------+
|                      USER LAYER                          |
|               WhatsApp (500M+ users)                     |
+-------------------------+--------------------------------+
                          |
+-------------------------v--------------------------------+
|                    TWILIO API                            |
|           WhatsApp Sandbox / Cloud API                   |
|           Voice notes / Images / Text                    |
+------+-------------------+------------------+-----------+
       |                   |                  |
+------v------+  +---------v------+  +--------v---------+
|  GROQ AI    |  | GROQ WHISPER   |  |   POSTGRESQL     |
| Llama 3.3   |  | Voice to Text  |  |   Railway DB     |
| Triage AI   |  | Hindi + 100+   |  | 16 tables, 5-tier|
+-------------+  +----------------+  +------------------+
       |
+------v------------------------------------------------------+
|                    FLASK BACKEND                            |
|  app.py / analyzer.py / alerts.py / dashboard.py           |
|  admin.py / supervisor.py / escalation.py / maps.py        |
|  analytics.py / performance.py / reports.py                |
|  nhm_export.py / postpartum.py / child_health.py           |
|  reminders.py / database.py / voice.py / tracker.py        |
+-------------------------------------------------------------+
```

---

## 5-Tier Hierarchy

```
+-----------------------------------------------+
|  TIER 1: District Health Officer (DHO / Admin) |
|  - District analytics dashboard                |
|  - NHM exports (10 CSVs + ZIP + PDF report)    |
|  - ASHA performance management                 |
|  - Village risk heatmaps                       |
|  Login: /admin/login  (username + password)    |
+-------------------+--------------------------+
                    | manages
+-------------------v--------------------------+
|  TIER 2: Block Medical Officer (BMO)         |
|  - Block-level escalated alerts              |
|  - Resolve / escalate to DHO                 |
|  - All patients in block view                |
|  Login: /bmo/<bmo_id>  (phone number)        |
+-------------------+--------------------------+
                    | manages
+-------------------v--------------------------+
|  TIER 3: ASHA Supervisor (ANM)               |
|  - All alerts across her ASHA workers        |
|  - Manual escalation to BMO                  |
|  - ASHA performance leaderboard              |
|  Login: /supervisor/<id>  (phone number)     |
+-------------------+--------------------------+
                    | manages
+-------------------v--------------------------+
|  TIER 4: ASHA Worker                         |
|  - Her patients only                         |
|  - Attend alerts / log visits / ANC / PNC    |
|  - Vaccines, growth, schemes                 |
|  Login: /dashboard/<id>  (phone number)      |
+-------------------+--------------------------+
                    | monitors
+-------------------v--------------------------+
|  TIER 5: Pregnant Patient                    |
|  - Register via WhatsApp                     |
|  - Report symptoms (text/voice/image)        |
|  - Postpartum + baby tracking                |
|  Access: WhatsApp +14155238886               |
+----------------------------------------------+
```

---

## Features

### Month 1 — Core WhatsApp Bot

| Feature | Description |
|---|---|
| Registration flow | Language select → name → week → village (fuzzy match) → address → registered |
| Voice notes | Groq Whisper Large V3 transcribes Hindi and 100+ Indian languages |
| Image upload | Visual symptoms trigger photo request → forwarded to ASHA worker |
| AI symptom triage | WHO ANC 2016 + NHM Module 6 → GREEN / AMBER / RED classification |
| ASHA alerts | RED symptoms trigger WhatsApp alert to ASHA with Maps navigation link |
| Govt scheme queries | PMMVY, JSY, JSSK benefit information on demand |
| Progress tracker | Weekly baby size comparisons and personalized tips |
| Myth busting | FOGSI 2021 guideline-based pregnancy myth correction |
| Health log | Every symptom saved permanently with cumulative risk score |
| Recovery confirmation | "I am better" / "Still unwell" keyword detection → resolves or re-escalates |
| Google Maps | Address geocoded → static map + navigation link sent to ASHA |
| Visit logging | ASHA logs outcome: stable / referred PHC / referred hospital / called 108 |
| ANC logging | ASHA records ANC visit number, date, notes |
| Scheme delivery logging | ASHA records scheme benefit delivered to patient |

### Month 2 — Supervisor Layer and Escalation

| Feature | Description |
|---|---|
| 5-tier hierarchy | DHO → BMO → Supervisor (ANM) → ASHA → Patient |
| Auto-escalation engine | Pending alerts > 2 hours escalate to supervisor automatically |
| Manual escalation | Supervisor / BMO can force-escalate to next tier |
| Escalation log | Full audit trail: from_role → to_role, timestamp, reason |
| Supervisor dashboard | All ASHA alerts in her block, ASHA performance table |
| BMO dashboard | Block-level escalated alerts, resolve / escalate to DHO |
| Unified login | Single /login endpoint detects ASHA / supervisor / BMO by phone number |
| Performance rating | GREEN / AMBER / RED per ASHA based on response time and resolution rate |
| Cron endpoint | /cron/escalate runs every 15 minutes via Railway cron |

### Month 3 — Analytics and NHM Exports

| Feature | Description |
|---|---|
| District analytics dashboard | 10 live KPI cards + stacked area trend chart (server-side SVG) |
| Village risk heatmap table | 20 villages ranked by avg risk score with HIGH / MOD / LOW badges |
| ASHA leaderboard | Composite score: resolution 40% + response speed 30% + escalation 20% |
| ANC compliance funnel | 4-bar chart showing % of patients at each ANC visit vs NHM target |
| Symptom breakdown donut | RED / AMBER / GREEN distribution with counts |
| Performance dashboard | 4-tab page: leaderboard / district overview / full table / needs support |
| NHM patient CSV | HMIS Form 3 — all mothers with full hierarchy data |
| ANC visit CSV | HMIS Form 14 |
| Delivery register CSV | HMIS Form 10 |
| Child immunization CSV | RCH register with Yes/No per vaccine |
| ASHA performance CSV | Monthly activity report using performance engine |
| Alert audit log CSV | Full escalation trail |
| Scheme delivery CSV | Benefit register |
| Symptom log CSV | Disease surveillance export |
| Village risk summary CSV | All-time aggregation |
| Full NHM ZIP | All 10 CSVs + README.txt bundled |
| Monthly PDF report | 7-page NHM submission: cover, patient/ANC, alerts, ASHA table, village risks, child health, signature block |
| JSON API endpoints | /admin/api/trends, /admin/api/village-risks, /admin/api/nhm-summary |

### Month 4 — Postpartum Care and Child Health

| Feature | Description |
|---|---|
| Delivery registration | "baby born" keyword triggers date collection → patient status = postpartum |
| Postpartum symptom routing | Separate danger sign detection for postpartum vs newborn (0–28 days) |
| PNC schedule | Day 1 / 3 / 7 / 14 / 42 with ±1 day tolerance window |
| PNC reminders | Auto WhatsApp to mother AND ASHA on each PNC day |
| PPD screening | Edinburgh-scale mini-check at Day 14 and Day 42 |
| Postpartum counselling | Weekly trimester-appropriate messages |
| NHM UIP immunization | Full schedule birth → 5 years (21 vaccines including BCG, Pentavalent, MR, JE) |
| WHO growth Z-scores | Weight-for-age Z-score calculator with Normal / MAM / SAM / Severe SAM classification |
| NRC referral alerts | Severe undernutrition triggers alert to ASHA and WhatsApp to mother |
| Newborn danger signs | 0–28 day specific RED / AMBER / GREEN routing |
| Vitamin A schedule | 9 doses from 9 months to 5 years |
| Deworming schedule | Albendazole reminders on February 1 and August 1 (National Deworming Day) |
| Immunization completion rate | % of age-appropriate vaccines given per child |
| 8 automated reminder types | PNC / vaccines / ANC / weekly tips / scheme notifications / iron tablets / PPD screening / deworming |
| /cron/reminders | Single endpoint runs all 8 reminder functions daily |

---

## WhatsApp Bot Flow

### Registration Flow

```
Patient sends: "Register" / "Hello" / "Hi" / "Namaste"
    |
    v
Select language: 1=English  2=Hindi  3=Hinglish
    |
    v
Enter name
    |
    v
Enter weeks pregnant (number)
    |
    v
Enter village name
    |
    v -- exact match found?
    |         YES --> assign ASHA (fewest patients in village)
    |          NO --> show up to 5 suggestions (fuzzy match)
    |                Patient picks number or retypes
    |
    v
Enter home address --> geocode --> store Maps link
    |
    v
REGISTERED -- welcome message + first health tip
    |
    v (when delivery happens)
Patient sends "baby born"
    |
    v
Enter delivery date (DD/MM/YYYY)
    |
    v
Status = postpartum -- PNC schedule begins
```

### Symptom Reporting (Registered Patient)

```
Patient sends message
    |
    +-- Voice note? --> Whisper AI transcribes
    |
    +-- Image? --> Ask permission --> Forward to ASHA
    |
    +-- Status = postpartum?
    |       |
    |       +-- Days <= 28? --> Newborn danger sign engine
    |       +-- Days > 28?  --> Postpartum danger sign engine
    |
    +-- Recovery confirmation? --> "I am better" / "still unwell"
    |
    +-- Scheme query? --> List PMMVY / JSY / JSSK benefits
    |
    +-- Progress tracker? --> Baby size + weekly tip
    |
    +-- Visual symptom? --> Ask for photo
    |
    v
Groq Llama 3.3 70B analyzes (WHO ANC 2016 + NHM Module 6)
    |
    v
GREEN  -- Reassurance + tip
AMBER  -- Monitor + 24h follow up
RED    -- Save alert + Maps link + notify ASHA + hospital advice
```

---

## Symptom Triage System

### RED — Danger Signs (WHO ANC 2016)

Triggers immediate ASHA WhatsApp alert and Maps navigation link:

- Severe headache with blurry vision (preeclampsia)
- Heavy vaginal bleeding
- Severe abdominal pain
- Fever above 38°C
- No fetal movement for 12+ hours
- Convulsions or fits
- Difficulty breathing
- Unconsciousness

### RED — Postpartum Danger Signs (Month 4)

- Heavy bleeding (more than 2–3 pads per hour)
- Fever above 38°C
- Wound infection or pus discharge
- Breathlessness or chest pain
- Mastitis signs
- Persistent sadness or self-harm thoughts (PPD)

### RED — Newborn Danger Signs (Month 4, 0–28 days)

- Not feeding at all
- Hypothermia (cold to touch)
- Jaundice beyond Day 3
- Fast or absent breathing
- Seizures or convulsions
- Umbilical cord infection

### AMBER — Moderate Signs (NHM Module 6)

Logged and monitored, follow-up in 24 hours: mild headache, nausea, mild swelling, fatigue, mild back pain.

### GREEN — Normal Symptoms

Reassurance with tips: normal pregnancy discomforts, general questions, nutrition queries.

---

## Alert and Escalation System

### How Alerts Work

```
1. Patient reports RED symptom
        |
2. Alert saved to asha_alerts table:
   - phone, name, week, symptom
   - asha_id, supervisor_id, bmo_id
   - maps_link (geocoded address)
   - status: Pending, escalation_level: 0
        |
3. WhatsApp sent to ASHA worker:
   Patient name, week, symptom, phone
   Maps navigation link
        |
4. Alert visible on ASHA dashboard
```

### Auto-Escalation (Month 2)

```
Every 15 minutes (/cron/escalate):

If alert Pending > 2 hours AND escalation_level = 0
    --> escalation_level = 1
    --> WhatsApp to Supervisor (ANM)

If still Pending after another 2 hours AND escalation_level = 1
    --> escalation_level = 2
    --> WhatsApp to BMO

If still Pending AND escalation_level = 2
    --> escalation_level = 3
    --> WhatsApp to DHO
```

### Alert Status Flow

```
PENDING (RED)  -->  ATTENDED (AMBER)  -->  RESOLVED (GREEN)
```

| Status | Meaning | Who Changes It |
|---|---|---|
| Pending | Alert fired, no action | System (automatic) |
| Attended | ASHA has visited | ASHA clicks button on dashboard |
| Resolved | Patient confirmed recovery | Patient replies "I am better" on WhatsApp |

---

## Care Loop

```
Step 1: Patient sends danger symptom
        Status: PENDING
        ASHA gets WhatsApp alert with Maps link

Step 2: ASHA visits patient
        ASHA clicks "Mark as Attended"
        Status: ATTENDED
        Patient automatically receives WhatsApp:
        "Aapki ASHA worker ne aapka case attend kar liya.
         Kya aap ab theek feel kar rahi hain?
         Reply: 'I am better'  OR  'Still not feeling well'"

Step 3A: Patient replies "I am better" / "theek hoon"
         Status: RESOLVED
         Alert count decreases, safe count increases

Step 3B: Patient replies "still not well"
         NEW alert fires automatically
         ASHA gets fresh escalation alert
         Status: PENDING again
         Cycle repeats until resolved
```

---

## Month 3 — Analytics and NHM Exports

### Analytics Dashboard (/admin/analytics)

The analytics dashboard renders entirely server-side (no JavaScript charting library required) using SVG built in Python.

Tabs: Overview | Trends | Villages | ASHA Performance | Health Metrics | Export

**Overview:** 8 KPI cards (patients, ASHAs, supervisors, BMOs, pending alerts, escalated, resolved today, total deliveries) + risk distribution donut chart + visit outcomes.

**Trends:** 30-day stacked area chart (RED / AMBER / GREEN layers) + top 8 reported symptoms bar chart + weekly registrations + escalation breakdown by level.

**Villages:** 20 villages ranked by avg risk score with progress bars and HIGH / MOD / LOW badges.

**ASHA Performance:** Leaderboard ranked by composite score + full table with resolution rate colour coding + "Needs Support" cards for underperformers.

**Health Metrics:** ANC compliance funnel + postpartum and child health KPIs + scheme delivery bar chart.

**Export:** Download buttons for all NHM files.

### Performance Engine (/admin/performance)

```python
composite_score = (
    resolution_rate  * 0.40 +
    speed_score      * 0.30 +   # max(0, 100 - avg_response_hrs * 20)
    escalation_score * 0.20 +   # max(0, 100 - escalation_rate * 2)
    visit_rate       * 0.10
)

Performance Rating:
    GREEN  = avg_response <= 1h AND escalation_rate <= 10%
    AMBER  = avg_response <= 3h AND escalation_rate <= 30%
    RED    = everything else
```

### NHM Exports

All 10 CSV files are UTF-8 encoded with BOM for direct Excel compatibility.

| File | NHM Format | Contents |
|---|---|---|
| 01_patients.csv | HMIS Form 3 | All mothers with full 5-tier hierarchy |
| 02_anc_visits.csv | HMIS Form 14 | All ANC records |
| 03_deliveries.csv | HMIS Form 10 | Delivery register |
| 04_children_immunization.csv | RCH Register | Yes/No per vaccine per child |
| 05_asha_performance.csv | Activity Report | Metrics from performance engine |
| 06_alerts.csv | Audit Log | Full escalation trail |
| 07_scheme_deliveries.csv | Benefit Register | Scheme delivery records |
| 08_symptom_logs.csv | Surveillance | Disease surveillance data |
| 09_village_risk_summary.csv | All-time | Village risk aggregation |
| 10_escalation_log.csv | Audit Trail | Every escalation with from/to roles |
| monthly_report.pdf | NHM Submission | 7-page formatted report with signature block |

---

## Month 4 — Postpartum and Child Health

### PNC Schedule (WHO + NHM)

| Visit | Day | Key Checks |
|---|---|---|
| PNC 1 | Day 1 | Bleeding, fever, breastfeeding initiation, Iron + FA |
| PNC 2 | Day 3 | Jaundice beyond Day 3, wound, umbilical cord |
| PNC 3 | Day 7 | Mastitis, PPD signs, Vitamin A dose, cord falling |
| PNC 4 | Day 14 | Baby weight vs birth weight, BCG + OPV-0 done? |
| PNC 5 | Day 42 | Full review, family planning, Edinburgh PPD screen |

### Immunization Schedule (NHM UIP)

| Age | Vaccines |
|---|---|
| Birth | BCG, OPV-0, Hepatitis B-1 |
| 6 weeks | OPV-1, Pentavalent-1, IPV-1, Rotavirus-1, PCV-1 |
| 10 weeks | OPV-2, Pentavalent-2, Rotavirus-2, PCV-2 |
| 14 weeks | OPV-3, Pentavalent-3, IPV-2, Rotavirus-3, PCV-Booster |
| 9 months | MR-1, JE-1, Vitamin A (1 lakh IU) |
| 16 months | MR-2, DPT Booster-1, OPV Booster |
| 18 months | Vitamin A (2 lakh IU) |
| 5 years | DPT Booster-2 |

### WHO Growth Z-Score Classification

| Z-Score | Status | Action |
|---|---|---|
| >= -1 | Normal / Well Nourished | Continue breastfeeding and complementary feeding |
| >= -2 | MAM (Moderate Acute Malnutrition) | Increase feeding, refer to Anganwadi for supplementary nutrition |
| >= -3 | SAM (Severe Acute Malnutrition) | URGENT: Refer to NRC immediately |
| < -3 | Severe Wasting | CRITICAL: Immediate hospitalisation |

### 8 Automated Reminder Types

| Reminder | Trigger | Recipients |
|---|---|---|
| PNC Reminder | PNC day (±1 day window) | Mother + ASHA worker |
| Vaccine Reminder | 3 days before + due day + 3–7 days overdue | Mother + ASHA worker |
| ANC Reminder | When gestational week enters each ANC window | Mother + ASHA worker |
| Weekly Tips | Every Monday | All active patients (trimester-appropriate) |
| Scheme Notification | When patient crosses eligibility threshold | Mother (once-ever per scheme) |
| Iron Tablet Nudge | Day 7 and Day 30 after registration | Mother |
| PPD Screening | Day 14 and Day 42 postpartum | Mother |
| Deworming | February 1 and August 1 (NDD) | All eligible children's mothers |

---

## Smart ASHA Assignment

When a patient registers and enters her village name, MaaSakhi uses a 5-level fuzzy matching algorithm to find the correct ASHA worker even if the patient types a partial or misspelled name.

**Matching strategies (tried in order):**

1. Exact case-insensitive match — "rampur" matches "Rampur"
2. DB village contains typed text — "rampur" matches "Rampur Khera"
3. Typed text contains DB village — "rampur khera village" matches "Rampur Khera"
4. First-word match — "rampur" matches "Rampur Kalan"
5. Any significant word match (4+ letters, non-stop-word) — "khera" matches "Rampur Khera"

If no match is found, the system shows up to 5 similar village names for the patient to choose from (confirm_village step).

Among all matching ASHAs, the one with the **fewest active patients** is assigned (load balancing).

---

## Database Schema

16 tables total across the 5-tier hierarchy.

### Core Tables

**admins** — DHO / district admin accounts

**block_officers** — BMOs: bmo_id, name, phone, block_name, district, is_active

**asha_supervisors** — ANMs: supervisor_id, name, phone, block_name, district, bmo_id, is_active

**asha_workers** — ASHA workers: asha_id, name, phone, village, block_name, district, supervisor_id, is_active, latitude, longitude

**patients** — phone (PK), name, week, step, language, asha_id, supervisor_id, bmo_id, village, block_name, district, address, status, latitude, longitude, maps_url

### Health Data Tables

**symptom_logs** — phone, week, message, level (GREEN/AMBER/RED)

**asha_alerts** — full alert with phone, name, week, symptom, address, village, maps_link, asha_id, supervisor_id, bmo_id, status, escalation_level, escalated_at, resolved_notes

**asha_visits** — alert_id, phone, patient_name, asha_id, visit_time, outcome, notes, referred_to

**escalation_log** — alert_id, from_role, to_role, to_phone, reason, sent_at

**anc_records** — phone, visit_number, visit_date, asha_id, notes

**scheme_deliveries** — phone, patient_name, scheme_name, amount, delivered_by, delivery_date

### Month 4 Tables

**deliveries** — phone (UNIQUE), delivery_date, birth_weight, delivery_mode, facility, asha_id

**children** — id, mother_phone, child_name, dob, gender, birth_weight, asha_id

**child_growth_logs** — child_id, mother_phone, weight_kg, height_cm, age_months, log_date, z_score, status

**immunization_records** — child_id, mother_phone, vaccine_name, dose_number, given_date, due_date, given_by

**reminder_log** — reminder_type, phone, message_preview, sent_at (prevents duplicate sends)

### Risk Score Calculation

```
score = (red_count x 40) + (amber_count x 15) + (green_count x 2)
score = min(score, 100)

if last 3 reports contain 2+ RED:
    score = min(score + 20, 100)

HIGH     = score >= 60 OR red_count >= 2
MODERATE = score >= 30 OR red_count >= 1
LOW      = everything else
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| AI Triage | Groq Llama 3.3 70B | Fastest LLM, 100+ Indian languages, free tier |
| Voice AI | Groq Whisper Large V3 | Best Hindi and Indian language accuracy |
| Backend | Python + Flask | Lightweight, no triple-quote strings (version safe) |
| Database | PostgreSQL on Railway | Permanent storage, DPDP 2023 compliant |
| ORM | SQLAlchemy + Psycopg2 | Reliable PostgreSQL, INTERVAL via f-string (not :param) |
| Messaging | Twilio WhatsApp Business API | Real WhatsApp, 500M Indian users |
| Messaging (planned) | Meta WhatsApp Cloud API | Production scale, unlimited messages |
| Deployment | Railway Cloud | 24/7 auto-deploy on git push, no laptop needed |
| Maps | Google Maps Geocoding API | Address to coordinates, static map images, navigation links |
| Reports | fpdf2 | 7-page NHM monthly PDF with no external dependencies |
| Medical Data | WHO + NHM + FOGSI + ICMR | Government-backed clinical guidelines |

---

## Project Structure

```
MaaSakhi/
|-- app.py              Main Flask app + all routes (all 4 months)
|-- analyzer.py         Groq AI symptom analysis (pregnancy + postpartum)
|-- alerts.py           ASHA WhatsApp alert system
|-- dashboard.py        ASHA worker dashboard (6 tabs)
|-- admin.py            Admin panel (9 tabs, no triple quotes)
|-- supervisor.py       Supervisor dashboard
|-- database.py         PostgreSQL layer — all DB functions (16 tables)
|-- escalation.py       Auto-escalation engine (2h window per tier)
|-- maps.py             Google Maps geocoding + static maps
|-- analytics.py        District analytics dashboard (server-side SVG)
|-- performance.py      ASHA performance engine + leaderboard
|-- reports.py          Monthly PDF generator (fpdf2, 7 pages)
|-- nhm_export.py       10 CSV exports + ZIP bundle
|-- postpartum.py       PNC schedule, danger signs, counselling
|-- child_health.py     Immunization schedule, WHO Z-scores, growth
|-- reminders.py        8 reminder types, run_all_reminders()
|-- voice.py            Groq Whisper voice transcription
|-- tracker.py          Pregnancy progress tracker
|-- symptoms.py         WHO/NHM symptom database
|-- myths.py            FOGSI myths database
|-- tips.py             Weekly pregnancy tips
|-- config.py           Environment variable config
|-- requirements.txt
|-- Procfile            Railway process file
```

---

## Setup and Installation

### Prerequisites

- Python 3.8+ (no triple-quoted strings used — version compatible)
- PostgreSQL database
- Twilio account with WhatsApp sandbox
- Groq API key
- Google Maps API key (for geocoding)

### Local Setup

```bash
git clone https://github.com/PriyancySingal/MaaSakhi.git
cd MaaSakhi

pip install -r requirements.txt

cp .env.example .env
# Fill in your API keys in .env

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
fpdf2
```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| DATABASE_URL | PostgreSQL connection URL | postgresql://user:pass@host/db |
| TWILIO_ACCOUNT_SID | Twilio Account SID | ACxxxxxxxxxxxxxxxxx |
| TWILIO_AUTH_TOKEN | Twilio Auth Token | xxxxxxxxxxxxxxxx |
| GROQ_API_KEY | Groq API Key | gsk_xxxxxxxxxxxxxxxxx |
| GOOGLE_MAPS_API_KEY | Maps geocoding + static maps | AIzaxxxxxxxxxxxxxx |
| SECRET_KEY | Flask session secret | maasakhi2026secret |
| TWILIO_SMS_FROM | SMS fallback number | +91xxxxxxxxxx |
| DHO_PHONE | DHO WhatsApp for Level 3 escalation | whatsapp:+91xxxxxxx |
| CRON_SECRET | Header secret for cron endpoints | any-random-string |
| PORT | Server port | 8080 |

---

## API Endpoints

### WhatsApp Bot

| Method | Endpoint | Description |
|---|---|---|
| POST | /whatsapp | Twilio webhook — all bot logic |

### Auth and Login

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | /login | Unified login — ASHA / supervisor / BMO by phone |
| GET/POST | /admin/login | Admin login (username + password) |
| GET | /admin/logout | Admin logout |

### ASHA Worker

| Method | Endpoint | Description |
|---|---|---|
| GET | /dashboard/<asha_id> | ASHA dashboard (6 tabs) |
| POST | /dashboard/<id>/attend/<alert_id> | Mark alert attended |
| POST | /dashboard/<id>/log-visit/<alert_id> | Log visit outcome |
| POST | /dashboard/<id>/log-anc | Log ANC visit |
| POST | /dashboard/<id>/log-scheme | Log scheme delivery |
| POST | /dashboard/<id>/register-delivery | Register patient delivery |
| POST | /dashboard/<id>/log-pnc/<phone> | Log PNC visit |
| POST | /dashboard/<id>/log-growth/<child_id> | Log child growth measurement |
| POST | /dashboard/<id>/log-vaccine/<child_id> | Log vaccine given |

### Supervisor

| Method | Endpoint | Description |
|---|---|---|
| GET | /supervisor/<supervisor_id> | Supervisor dashboard |
| POST | /supervisor/<id>/escalate/<alert_id> | Manual escalation to BMO |
| POST | /supervisor/<id>/resolve/<alert_id> | Resolve alert |

### Block Medical Officer

| Method | Endpoint | Description |
|---|---|---|
| GET | /bmo/<bmo_id> | BMO dashboard |
| POST | /bmo/<id>/escalate/<alert_id> | Escalate to DHO |
| POST | /bmo/<id>/resolve/<alert_id> | Resolve alert |

### Admin — Management

| Method | Endpoint | Description |
|---|---|---|
| GET | /admin | Admin panel (9 tabs) |
| POST | /admin/add-asha | Add ASHA worker |
| POST | /admin/toggle-asha | Activate / deactivate ASHA |
| POST | /admin/delete-asha | Delete ASHA worker |
| POST | /admin/add-supervisor | Add supervisor |
| POST | /admin/toggle-supervisor | Toggle supervisor status |
| POST | /admin/delete-supervisor | Delete supervisor |
| POST | /admin/add-bmo | Add BMO |
| POST | /admin/toggle-bmo | Toggle BMO status |
| POST | /admin/delete-bmo | Delete BMO |

### Admin — Analytics and Exports

| Method | Endpoint | Description |
|---|---|---|
| GET | /admin/analytics | Full analytics dashboard |
| GET | /admin/performance | ASHA performance dashboard |
| GET | /admin/api/trends | JSON trend data |
| GET | /admin/api/village-risks | JSON village risk scores |
| GET | /admin/api/nhm-summary | JSON NHM submission summary |
| GET | /admin/export/nhm-csv | NHM patient CSV download |
| GET | /admin/export/nhm-zip | Full NHM ZIP (10 CSVs + README) |
| GET | /admin/export/monthly-pdf | Monthly NHM PDF report |

### Cron Jobs (secured by X-Cron-Secret header)

| Method | Endpoint | Description |
|---|---|---|
| GET | /cron/escalate | Auto-escalate pending alerts (every 15 min) |
| GET | /cron/reminders | Run all 8 reminder types (daily 8am IST) |
| GET | /health | Health check |

---

## Deployment

MaaSakhi is deployed on Railway with automatic GitHub deployment.

**Live URL:** maasakhi-production.up.railway.app

### Railway Setup

1. Connect GitHub repository to Railway
2. Add PostgreSQL database service
3. Set all environment variables in Railway dashboard
4. Set RAILPACK_PYTHON_VERSION=3.11
5. Railway auto-deploys on every git push to main

### Railway Cron Jobs

Add these in Railway dashboard under "Cron Jobs":

```
*/15 * * * *   curl -H "X-Cron-Secret: YOUR_SECRET" https://your-url/cron/escalate
0 2 * * *      curl -H "X-Cron-Secret: YOUR_SECRET" https://your-url/cron/reminders
```

(2:30 AM UTC = 8:00 AM IST)

### Twilio WhatsApp Sandbox

- Number: +1 415 523 8886
- Join code: join kitchen-highest
- Webhook URL: https://maasakhi-production.up.railway.app/whatsapp

---

## Medical Sources

| Source | Used For |
|---|---|
| WHO Antenatal Care Guidelines 2016 (Table 3.1) | RED danger sign detection |
| NHM India ASHA Training Module 6 | AMBER moderate symptom monitoring |
| NHM UIP Universal Immunization Programme | Full child vaccine schedule |
| NHM RMNCH+A Framework | Postpartum and newborn care protocols |
| FOGSI Clinical Practice Guidelines 2021 | Pregnancy myth correction |
| ICMR Dietary Guidelines 2020 | Nutrition and food advice |
| WHO Child Growth Standards 2006 | Weight-for-age Z-score reference medians |
| Edinburgh Postnatal Depression Scale | PPD screening questions (Day 14 and Day 42) |
| NHM HMIS Technical Manual v3.0 | CSV export column formats |

---

## Team

| Member | Role |
|---|---|
| Priyancy Singal | AI Developer and Backend Engineer — WhatsApp bot, Groq AI integration, PostgreSQL, 5-tier hierarchy, analytics, NHM exports, postpartum engine, Railway deployment |
| Tanisha Sati | Research and Product Designer — WHO/NHM medical research, UX design, solution architecture, clinical data validation |

**Team AIPAGLUS** — WitchHunt 2026, Health Track, AI4India / HopeWorks

---

## License

Built during WitchHunt 2026 hackathon. All medical guidance is based on WHO, NHM, FOGSI and ICMR published guidelines. MaaSakhi is a triage tool — not a medical diagnosis system. Always consult a qualified doctor for clinical decisions.

---

*MaaSakhi — Because every mother deserves a knowledgeable friend available at 3am, who speaks her language, and knows when to call for help.*
