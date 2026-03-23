# ─────────────────────────────────────────────────────────────────
# MaaSakhi Database Layer
# PostgreSQL via SQLAlchemy
# 3-Tier: Admin → ASHA Workers → Patients
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None


def init_db():
    if not engine:
        print("No database URL — using memory mode")
        return

    with engine.connect() as conn:

        # Admin table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id          SERIAL PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                name        TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # ASHA workers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_workers (
                asha_id     TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                phone       TEXT UNIQUE NOT NULL,
                village     TEXT NOT NULL,
                district    TEXT,
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Patients table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patients (
                phone       TEXT PRIMARY KEY,
                name        TEXT,
                week        INTEGER,
                step        TEXT DEFAULT 'welcome',
                language    TEXT DEFAULT 'Hindi',
                asha_id     TEXT,
                village     TEXT,
                created_at  TIMESTAMP DEFAULT NOW(),
                updated_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Symptom logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS symptom_logs (
                id          SERIAL PRIMARY KEY,
                phone       TEXT,
                week        INTEGER,
                message     TEXT,
                level       TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # ASHA alerts table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_alerts (
                id          SERIAL PRIMARY KEY,
                phone       TEXT,
                name        TEXT,
                week        INTEGER,
                symptom     TEXT,
                asha_id     TEXT,
                status      TEXT DEFAULT 'Pending',
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Seed default admin
        conn.execute(text("""
            INSERT INTO admins (username, password, name)
            VALUES ('admin', 'maasakhi2026', 'District Admin')
            ON CONFLICT (username) DO NOTHING
        """))

        conn.commit()
        print("Database tables created successfully!")


# ── ADMIN FUNCTIONS ───────────────────────────────────────────────

def verify_admin(username, password):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM admins WHERE username = :u AND password = :p"),
                {"u": username, "p": password}
            ).fetchone()
            if result:
                return {"id": result.id, "name": result.name, "username": result.username}
            return None
    except Exception as e:
        print(f"Admin verify error: {e}")
        return None


# ── ASHA WORKER FUNCTIONS ─────────────────────────────────────────

def add_asha_worker(asha_id, name, phone, village, district=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_workers (asha_id, name, phone, village, district)
                VALUES (:asha_id, :name, :phone, :village, :district)
                ON CONFLICT (asha_id) DO UPDATE SET
                    name     = :name,
                    phone    = :phone,
                    village  = :village,
                    district = :district
            """), {
                "asha_id":  asha_id,
                "name":     name,
                "phone":    phone,
                "village":  village,
                "district": district
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Add ASHA error: {e}")
        return False


def get_all_asha_workers():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT * FROM asha_workers ORDER BY village, name")
            ).fetchall()
            return [{
                "asha_id":   r.asha_id,
                "name":      r.name,
                "phone":     r.phone,
                "village":   r.village,
                "district":  r.district,
                "is_active": r.is_active
            } for r in results]
    except Exception as e:
        print(f"Get all ASHA error: {e}")
        return []


def get_asha_by_village(village):
    """Smart assignment — assigns ASHA with fewest patients in village."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT
                    a.asha_id,
                    a.name,
                    a.phone,
                    a.village,
                    COUNT(p.phone) AS patient_count
                FROM asha_workers a
                LEFT JOIN patients p
                    ON p.asha_id = a.asha_id
                    AND p.step = 'registered'
                WHERE LOWER(a.village) = LOWER(:village)
                AND a.is_active = TRUE
                GROUP BY a.asha_id, a.name, a.phone, a.village
                ORDER BY patient_count ASC
                LIMIT 1
            """), {"village": village}).fetchone()

            if result:
                return {
                    "asha_id":       result.asha_id,
                    "name":          result.name,
                    "phone":         result.phone,
                    "patient_count": result.patient_count
                }
            return None
    except Exception as e:
        print(f"Get ASHA by village error: {e}")
        return None


def get_asha_by_phone(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM asha_workers WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "asha_id": result.asha_id,
                    "name":    result.name,
                    "phone":   result.phone,
                    "village": result.village
                }
            return None
    except Exception as e:
        print(f"Get ASHA by phone error: {e}")
        return None


def toggle_asha_status(asha_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE asha_workers
                SET is_active = NOT is_active
                WHERE asha_id = :asha_id
            """), {"asha_id": asha_id})
            conn.commit()
            return True
    except Exception as e:
        print(f"Toggle ASHA error: {e}")
        return False


def delete_asha_worker(asha_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "DELETE FROM asha_workers WHERE asha_id = :asha_id"
            ), {"asha_id": asha_id})
            conn.commit()
            return True
    except Exception as e:
        print(f"Delete ASHA error: {e}")
        return False


def get_asha_stats(asha_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total = conn.execute(
                text("SELECT COUNT(*) FROM patients WHERE asha_id = :id AND step = 'registered'"),
                {"id": asha_id}
            ).fetchone()[0]

            high_risk = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts WHERE asha_id = :id"),
                {"id": asha_id}
            ).fetchone()[0]

            return {
                "total_patients":   total,
                "high_risk_alerts": high_risk,
                "safe_patients":    max(total - high_risk, 0)
            }
    except Exception as e:
        print(f"Get ASHA stats error: {e}")
        return {"total_patients": 0, "high_risk_alerts": 0, "safe_patients": 0}


# ── PATIENT FUNCTIONS ─────────────────────────────────────────────

def get_patient(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM patients WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "phone":    result.phone,
                    "name":     result.name,
                    "week":     result.week,
                    "step":     result.step,
                    "language": result.language,
                    "asha_id":  result.asha_id if result.asha_id else "default_asha",
                    "village":  result.village if result.village else ""
                }
            return None
    except Exception as e:
        print(f"Get patient error: {e}")
        return None


def save_patient(phone, name, week, step, language="Hindi", asha_id="default_asha", village=""):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO patients
                    (phone, name, week, step, language, asha_id, village, updated_at)
                VALUES
                    (:phone, :name, :week, :step, :language, :asha_id, :village, NOW())
                ON CONFLICT (phone) DO UPDATE SET
                    name       = :name,
                    week       = :week,
                    step       = :step,
                    language   = :language,
                    asha_id    = :asha_id,
                    village    = :village,
                    updated_at = NOW()
            """), {
                "phone":    phone,
                "name":     name,
                "week":     week,
                "step":     step,
                "language": language,
                "asha_id":  asha_id,
                "village":  village
            })
            conn.commit()
    except Exception as e:
        print(f"Save patient error: {e}")


def get_all_patients(asha_id="default_asha"):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM patients
                    WHERE step = 'registered'
                    AND asha_id = :asha_id
                """),
                {"asha_id": asha_id}
            ).fetchall()
            patients = {}
            for r in results:
                patients[r.phone] = {
                    "phone":    r.phone,
                    "name":     r.name,
                    "week":     r.week,
                    "step":     r.step,
                    "language": r.language,
                    "village":  r.village if r.village else ""
                }
            return patients
    except Exception as e:
        print(f"Get all patients error: {e}")
        return {}


def get_all_patients_admin():
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT * FROM patients WHERE step = 'registered' ORDER BY village")
            ).fetchall()
            patients = {}
            for r in results:
                patients[r.phone] = {
                    "phone":    r.phone,
                    "name":     r.name,
                    "week":     r.week,
                    "step":     r.step,
                    "language": r.language,
                    "asha_id":  r.asha_id,
                    "village":  r.village if r.village else ""
                }
            return patients
    except Exception as e:
        print(f"Get all patients admin error: {e}")
        return {}


# ── SYMPTOM LOG FUNCTIONS ─────────────────────────────────────────

def save_symptom_log(phone, week, message, level):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO symptom_logs (phone, week, message, level)
                VALUES (:phone, :week, :message, :level)
            """), {
                "phone":   phone,
                "week":    week,
                "message": message,
                "level":   level
            })
            conn.commit()
    except Exception as e:
        print(f"Save symptom log error: {e}")


def get_symptom_logs(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM symptom_logs
                    WHERE phone = :phone
                    ORDER BY created_at ASC
                """),
                {"phone": phone}
            ).fetchall()
            return [{
                "week":    r.week,
                "message": r.message,
                "level":   r.level,
                "time":    r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in results]
    except Exception as e:
        print(f"Get symptom logs error: {e}")
        return []


def get_risk_score_from_db(phone):
    logs = get_symptom_logs(phone)
    if not logs:
        return 0, "Unknown", "No reports yet"

    red_count   = sum(1 for e in logs if e["level"] == "RED")
    amber_count = sum(1 for e in logs if e["level"] == "AMBER")
    green_count = sum(1 for e in logs if e["level"] == "GREEN")
    total       = len(logs)

    score = min(100, (red_count * 40) + (amber_count * 15) + (green_count * 2))
    recent      = logs[-3:] if len(logs) >= 3 else logs
    recent_reds = sum(1 for e in recent if e["level"] == "RED")
    if recent_reds >= 2:
        score = min(100, score + 20)

    if score >= 60 or red_count >= 2:
        risk_level = "HIGH"
    elif score >= 30 or red_count >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    summary = (
        f"Total: {total} | Danger: {red_count} | "
        f"Warning: {amber_count} | Normal: {green_count}"
    )
    return score, risk_level, summary


# ── ASHA ALERT FUNCTIONS ──────────────────────────────────────────

def save_asha_alert_db(phone, name, week, symptom, asha_id):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_alerts (phone, name, week, symptom, asha_id)
                VALUES (:phone, :name, :week, :symptom, :asha_id)
            """), {
                "phone":   phone,
                "name":    name,
                "week":    week,
                "symptom": symptom,
                "asha_id": asha_id
            })
            conn.commit()
    except Exception as e:
        print(f"Save ASHA alert error: {e}")


def get_all_asha_alerts(asha_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM asha_alerts
                    WHERE asha_id = :asha_id
                    ORDER BY created_at DESC
                """),
                {"asha_id": asha_id}
            ).fetchall()
            return [{
                "name":    r.name,
                "week":    r.week,
                "symptom": r.symptom,
                "phone":   r.phone,
                "time":    r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":  r.status
            } for r in results]
    except Exception as e:
        print(f"Get ASHA alerts error: {e}")
        return []


def get_all_alerts_admin():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT
                        aa.id,
                        aa.phone,
                        aa.name,
                        aa.week,
                        aa.symptom,
                        aa.asha_id,
                        aa.status,
                        aa.created_at,
                        aw.name as asha_name,
                        aw.village
                    FROM asha_alerts aa
                    LEFT JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    ORDER BY aa.created_at DESC
                """)
            ).fetchall()
            return [{
                "name":      r.name,
                "week":      r.week,
                "symptom":   r.symptom,
                "phone":     r.phone,
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":    r.status,
                "asha_id":   r.asha_id,
                "asha_name": r.asha_name,
                "village":   r.village
            } for r in results]
    except Exception as e:
        print(f"Get all alerts admin error: {e}")
        return []


def get_alert_count_db(asha_id="default_asha"):
    if not engine:
        return 0
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts WHERE asha_id = :asha_id"),
                {"asha_id": asha_id}
            ).fetchone()
            return result[0]
    except Exception as e:
        print(f"Get alert count error: {e}")
        return 0
