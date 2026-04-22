# ─────────────────────────────────────────────────────────────────
# MaaSakhi Database Layer
# PostgreSQL via SQLAlchemy
# Full 5-Tier Hierarchy:
# District Health Officer → Block Medical Officer →
# ASHA Supervisor (ANM) → ASHA Worker → Patient
# ─────────────────────────────────────────────────────────────────

import os
from datetime import datetime
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None


# ─────────────────────────────────────────────────────────────────
# INIT — Create all tables and seed defaults
# ─────────────────────────────────────────────────────────────────

def init_db():
    if not engine:
        print("No database URL — using memory mode")
        return

    with engine.connect() as conn:

        # ── TIER 1: District Health Officers (DHO/Admin) ──────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id          SERIAL PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                name        TEXT,
                district    TEXT DEFAULT 'All Districts',
                phone       TEXT,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))
        # Add new columns to existing admins table safely
        conn.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS district TEXT DEFAULT 'All Districts'"))
        conn.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS phone TEXT"))

        # ── TIER 2: Block Medical Officers (BMO) ─────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS block_officers (
                bmo_id      TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                phone       TEXT UNIQUE NOT NULL,
                block_name  TEXT NOT NULL,
                district    TEXT NOT NULL,
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── TIER 3: ASHA Supervisors (ANM) ───────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_supervisors (
                supervisor_id   TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                phone           TEXT UNIQUE NOT NULL,
                block_name      TEXT NOT NULL,
                district        TEXT NOT NULL,
                bmo_id          TEXT,
                is_active       BOOLEAN DEFAULT TRUE,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── TIER 4: ASHA Workers ──────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_workers (
                asha_id         TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                phone           TEXT UNIQUE NOT NULL,
                village         TEXT NOT NULL,
                block_name      TEXT,
                district        TEXT,
                supervisor_id   TEXT,
                is_active       BOOLEAN DEFAULT TRUE,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """))
        # Add new columns to existing asha_workers safely
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS block_name TEXT"))
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))

        # ── TIER 5: Patients ──────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS patients (
                phone           TEXT PRIMARY KEY,
                name            TEXT,
                week            INTEGER,
                step            TEXT DEFAULT 'welcome',
                language        TEXT DEFAULT 'Hindi',
                asha_id         TEXT,
                supervisor_id   TEXT,
                bmo_id          TEXT,
                village         TEXT,
                block_name      TEXT,
                district        TEXT,
                address         TEXT,
                delivery_date   TEXT,
                status          TEXT DEFAULT 'active',
                created_at      TIMESTAMP DEFAULT NOW(),
                updated_at      TIMESTAMP DEFAULT NOW()
            )
        """))
        # Add new columns to existing patients table safely
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS address TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS bmo_id TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS block_name TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS district TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS delivery_date TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active'"))

        # ── Symptom Logs ──────────────────────────────────────────
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

        # ── ASHA Alerts (with full escalation chain) ──────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_alerts (
                id                  SERIAL PRIMARY KEY,
                phone               TEXT,
                name                TEXT,
                week                INTEGER,
                symptom             TEXT,
                address             TEXT,
                village             TEXT,
                maps_link           TEXT,
                asha_id             TEXT,
                supervisor_id       TEXT,
                bmo_id              TEXT,
                status              TEXT DEFAULT 'Pending',
                escalation_level    INTEGER DEFAULT 0,
                escalated_at        TIMESTAMP,
                resolved_notes      TEXT,
                created_at          TIMESTAMP DEFAULT NOW()
            )
        """))
        # Add new columns to existing asha_alerts safely
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS address TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS village TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS maps_link TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS bmo_id TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS resolved_notes TEXT"))

        # ── ASHA Visit Records ────────────────────────────────────
        # Logs what actually happened after ASHA attended an alert
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS asha_visits (
                id              SERIAL PRIMARY KEY,
                alert_id        INTEGER,
                phone           TEXT,
                patient_name    TEXT,
                asha_id         TEXT,
                visit_time      TIMESTAMP DEFAULT NOW(),
                outcome         TEXT,
                notes           TEXT,
                referred_to     TEXT,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── Escalation Log ────────────────────────────────────────
        # Tracks every escalation up the hierarchy
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS escalation_log (
                id              SERIAL PRIMARY KEY,
                alert_id        INTEGER,
                from_role       TEXT,
                to_role         TEXT,
                to_phone        TEXT,
                reason          TEXT,
                sent_at         TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── ANC Records ───────────────────────────────────────────
        # Tracks which ANC visits each patient has completed
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS anc_records (
                id              SERIAL PRIMARY KEY,
                phone           TEXT,
                visit_number    INTEGER,
                visit_date      TEXT,
                asha_id         TEXT,
                notes           TEXT,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── Scheme Deliveries ─────────────────────────────────────
        # Tracks govt scheme benefits delivered to patients
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS scheme_deliveries (
                id              SERIAL PRIMARY KEY,
                phone           TEXT,
                patient_name    TEXT,
                scheme_name     TEXT,
                amount          TEXT,
                delivered_by    TEXT,
                delivery_date   TEXT,
                created_at      TIMESTAMP DEFAULT NOW()
            )
        """))

        # ── Seed default District Admin ───────────────────────────
        conn.execute(text("""
            INSERT INTO admins (username, password, name, district)
            VALUES ('admin', 'maasakhi2026', 'District Admin', 'All Districts')
            ON CONFLICT (username) DO NOTHING
        """))

        conn.commit()
        print("Database tables created successfully — Full 5-tier hierarchy ready!")


# ═════════════════════════════════════════════════════════════════
# TIER 1 — DISTRICT HEALTH OFFICER / ADMIN FUNCTIONS
# ═════════════════════════════════════════════════════════════════

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
                return {
                    "id":       result.id,
                    "name":     result.name,
                    "username": result.username,
                    "district": result.district if result.district else "All Districts",
                    "role":     "admin"
                }
            return None
    except Exception as e:
        print(f"Admin verify error: {e}")
        return None


def get_district_stats():
    """Full district overview for DHO dashboard."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_patients = conn.execute(
                text("SELECT COUNT(*) FROM patients WHERE step = 'registered'")
            ).fetchone()[0]

            high_risk = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts WHERE status != 'Resolved'")
            ).fetchone()[0]

            total_ashas = conn.execute(
                text("SELECT COUNT(*) FROM asha_workers WHERE is_active = TRUE")
            ).fetchone()[0]

            total_alerts_today = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts WHERE DATE(created_at) = CURRENT_DATE")
            ).fetchone()[0]

            escalated = conn.execute(
                text("SELECT COUNT(*) FROM asha_alerts WHERE escalation_level > 0 AND status != 'Resolved'")
            ).fetchone()[0]

            return {
                "total_patients":     total_patients,
                "high_risk":          high_risk,
                "total_ashas":        total_ashas,
                "alerts_today":       total_alerts_today,
                "escalated_alerts":   escalated,
                "safe_patients":      max(total_patients - high_risk, 0)
            }
    except Exception as e:
        print(f"Get district stats error: {e}")
        return {}


# ═════════════════════════════════════════════════════════════════
# TIER 2 — BLOCK MEDICAL OFFICER (BMO) FUNCTIONS
# ═════════════════════════════════════════════════════════════════

def add_block_officer(bmo_id, name, phone, block_name, district):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO block_officers
                    (bmo_id, name, phone, block_name, district)
                VALUES
                    (:bmo_id, :name, :phone, :block_name, :district)
                ON CONFLICT (bmo_id) DO UPDATE SET
                    name       = :name,
                    phone      = :phone,
                    block_name = :block_name,
                    district   = :district
            """), {
                "bmo_id":     bmo_id,
                "name":       name,
                "phone":      phone,
                "block_name": block_name,
                "district":   district
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Add BMO error: {e}")
        return False


def get_all_block_officers():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT * FROM block_officers ORDER BY district, block_name")
            ).fetchall()
            return [{
                "bmo_id":     r.bmo_id,
                "name":       r.name,
                "phone":      r.phone,
                "block_name": r.block_name,
                "district":   r.district,
                "is_active":  r.is_active
            } for r in results]
    except Exception as e:
        print(f"Get all BMO error: {e}")
        return []


def verify_bmo(phone):
    """Login for BMO — by phone number."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM block_officers WHERE phone = :phone AND is_active = TRUE"),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "bmo_id":     result.bmo_id,
                    "name":       result.name,
                    "phone":      result.phone,
                    "block_name": result.block_name,
                    "district":   result.district,
                    "role":       "bmo"
                }
            return None
    except Exception as e:
        print(f"BMO verify error: {e}")
        return None


def get_bmo_stats(bmo_id):
    """Stats for BMO dashboard — their block only."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_supervisors = conn.execute(
                text("SELECT COUNT(*) FROM asha_supervisors WHERE bmo_id = :id AND is_active = TRUE"),
                {"id": bmo_id}
            ).fetchone()[0]

            total_ashas = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_workers aw
                    JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id
                    WHERE s.bmo_id = :id AND aw.is_active = TRUE
                """),
                {"id": bmo_id}
            ).fetchone()[0]

            total_patients = conn.execute(
                text("""
                    SELECT COUNT(*) FROM patients p
                    JOIN asha_workers aw ON p.asha_id = aw.asha_id
                    JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id
                    WHERE s.bmo_id = :id AND p.step = 'registered'
                """),
                {"id": bmo_id}
            ).fetchone()[0]

            escalated = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE bmo_id = :id
                    AND status != 'Resolved'
                    AND escalation_level >= 2
                """),
                {"id": bmo_id}
            ).fetchone()[0]

            return {
                "total_supervisors": total_supervisors,
                "total_ashas":       total_ashas,
                "total_patients":    total_patients,
                "escalated_alerts":  escalated
            }
    except Exception as e:
        print(f"Get BMO stats error: {e}")
        return {}


def get_bmo_alerts(bmo_id):
    """Alerts escalated to BMO level."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT aa.*, aw.name as asha_name, aw.village
                    FROM asha_alerts aa
                    LEFT JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    WHERE aa.bmo_id = :bmo_id
                    AND aa.escalation_level >= 2
                    ORDER BY aa.created_at DESC
                """),
                {"bmo_id": bmo_id}
            ).fetchall()
            return [{
                "id":          r.id,
                "name":        r.name,
                "week":        r.week,
                "symptom":     r.symptom,
                "phone":       r.phone,
                "address":     r.address if r.address else "",
                "village":     r.village if r.village else "",
                "maps_link":   r.maps_link if r.maps_link else "",
                "status":      r.status,
                "asha_name":   r.asha_name,
                "time":        r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in results]
    except Exception as e:
        print(f"Get BMO alerts error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# TIER 3 — ASHA SUPERVISOR (ANM) FUNCTIONS
# ═════════════════════════════════════════════════════════════════

def add_asha_supervisor(supervisor_id, name, phone, block_name, district, bmo_id=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_supervisors
                    (supervisor_id, name, phone, block_name, district, bmo_id)
                VALUES
                    (:supervisor_id, :name, :phone, :block_name, :district, :bmo_id)
                ON CONFLICT (supervisor_id) DO UPDATE SET
                    name        = :name,
                    phone       = :phone,
                    block_name  = :block_name,
                    district    = :district,
                    bmo_id      = :bmo_id
            """), {
                "supervisor_id": supervisor_id,
                "name":          name,
                "phone":         phone,
                "block_name":    block_name,
                "district":      district,
                "bmo_id":        bmo_id
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Add supervisor error: {e}")
        return False


def get_all_supervisors():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("SELECT * FROM asha_supervisors ORDER BY district, block_name, name")
            ).fetchall()
            return [{
                "supervisor_id": r.supervisor_id,
                "name":          r.name,
                "phone":         r.phone,
                "block_name":    r.block_name,
                "district":      r.district,
                "bmo_id":        r.bmo_id,
                "is_active":     r.is_active
            } for r in results]
    except Exception as e:
        print(f"Get all supervisors error: {e}")
        return []


def verify_supervisor(phone):
    """Login for ASHA Supervisor — by phone number."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM asha_supervisors
                    WHERE phone = :phone AND is_active = TRUE
                """),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "supervisor_id": result.supervisor_id,
                    "name":          result.name,
                    "phone":         result.phone,
                    "block_name":    result.block_name,
                    "district":      result.district,
                    "bmo_id":        result.bmo_id,
                    "role":          "supervisor"
                }
            return None
    except Exception as e:
        print(f"Supervisor verify error: {e}")
        return None


def get_supervisor_stats(supervisor_id):
    """Stats for supervisor dashboard — her ASHAs only."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_ashas = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_workers
                    WHERE supervisor_id = :id AND is_active = TRUE
                """),
                {"id": supervisor_id}
            ).fetchone()[0]

            total_patients = conn.execute(
                text("""
                    SELECT COUNT(*) FROM patients p
                    JOIN asha_workers aw ON p.asha_id = aw.asha_id
                    WHERE aw.supervisor_id = :id AND p.step = 'registered'
                """),
                {"id": supervisor_id}
            ).fetchone()[0]

            pending_alerts = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts aa
                    JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    WHERE aw.supervisor_id = :id AND aa.status = 'Pending'
                """),
                {"id": supervisor_id}
            ).fetchone()[0]

            escalated_to_me = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE supervisor_id = :id
                    AND escalation_level = 1
                    AND status != 'Resolved'
                """),
                {"id": supervisor_id}
            ).fetchone()[0]

            return {
                "total_ashas":       total_ashas,
                "total_patients":    total_patients,
                "pending_alerts":    pending_alerts,
                "escalated_to_me":   escalated_to_me
            }
    except Exception as e:
        print(f"Get supervisor stats error: {e}")
        return {}


def get_supervisor_ashas(supervisor_id):
    """Get all ASHA workers under a supervisor."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT
                        aw.*,
                        COUNT(p.phone) as patient_count,
                        COUNT(CASE WHEN aa.status = 'Pending'
                              THEN 1 END) as pending_alerts
                    FROM asha_workers aw
                    LEFT JOIN patients p
                        ON p.asha_id = aw.asha_id
                        AND p.step = 'registered'
                    LEFT JOIN asha_alerts aa
                        ON aa.asha_id = aw.asha_id
                        AND aa.status = 'Pending'
                    WHERE aw.supervisor_id = :id
                    GROUP BY aw.asha_id
                    ORDER BY pending_alerts DESC, patient_count DESC
                """),
                {"id": supervisor_id}
            ).fetchall()
            return [{
                "asha_id":       r.asha_id,
                "name":          r.name,
                "phone":         r.phone,
                "village":       r.village,
                "is_active":     r.is_active,
                "patient_count": r.patient_count,
                "pending_alerts": r.pending_alerts
            } for r in results]
    except Exception as e:
        print(f"Get supervisor ASHAs error: {e}")
        return []


def get_supervisor_alerts(supervisor_id):
    """Alerts from all ASHAs under this supervisor."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT aa.*, aw.name as asha_name, aw.village
                    FROM asha_alerts aa
                    JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    WHERE aw.supervisor_id = :id
                    ORDER BY
                        CASE aa.status
                            WHEN 'Pending'  THEN 1
                            WHEN 'Attended' THEN 2
                            ELSE 3
                        END,
                        aa.created_at DESC
                """),
                {"id": supervisor_id}
            ).fetchall()
            return [{
                "id":        r.id,
                "name":      r.name,
                "week":      r.week,
                "symptom":   r.symptom,
                "phone":     r.phone,
                "address":   r.address  if r.address  else "",
                "village":   r.village  if r.village  else "",
                "maps_link": r.maps_link if r.maps_link else "",
                "status":    r.status,
                "asha_name": r.asha_name,
                "asha_id":   r.asha_id,
                "level":     r.escalation_level,
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in results]
    except Exception as e:
        print(f"Get supervisor alerts error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# TIER 4 — ASHA WORKER FUNCTIONS
# ═════════════════════════════════════════════════════════════════

def add_asha_worker(asha_id, name, phone, village, district="",
                    block_name="", supervisor_id=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_workers
                    (asha_id, name, phone, village, district,
                     block_name, supervisor_id)
                VALUES
                    (:asha_id, :name, :phone, :village, :district,
                     :block_name, :supervisor_id)
                ON CONFLICT (asha_id) DO UPDATE SET
                    name          = :name,
                    phone         = :phone,
                    village       = :village,
                    district      = :district,
                    block_name    = :block_name,
                    supervisor_id = :supervisor_id
            """), {
                "asha_id":       asha_id,
                "name":          name,
                "phone":         phone,
                "village":       village,
                "district":      district,
                "block_name":    block_name,
                "supervisor_id": supervisor_id
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
                text("""
                    SELECT aw.*,
                           s.name as supervisor_name,
                           s.block_name
                    FROM asha_workers aw
                    LEFT JOIN asha_supervisors s
                        ON aw.supervisor_id = s.supervisor_id
                    ORDER BY aw.district, aw.village, aw.name
                """)
            ).fetchall()
            return [{
                "asha_id":         r.asha_id,
                "name":            r.name,
                "phone":           r.phone,
                "village":         r.village,
                "district":        r.district,
                "block_name":      r.block_name,
                "supervisor_id":   r.supervisor_id,
                "supervisor_name": r.supervisor_name,
                "is_active":       r.is_active
            } for r in results]
    except Exception as e:
        print(f"Get all ASHA error: {e}")
        return []


def get_asha_by_village(village):
    """Smart auto-assignment — ASHA with fewest patients in village."""
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
                    a.supervisor_id,
                    COUNT(p.phone) AS patient_count
                FROM asha_workers a
                LEFT JOIN patients p
                    ON p.asha_id = a.asha_id
                    AND p.step = 'registered'
                WHERE LOWER(a.village) = LOWER(:village)
                AND a.is_active = TRUE
                GROUP BY a.asha_id, a.name, a.phone,
                         a.village, a.supervisor_id
                ORDER BY patient_count ASC
                LIMIT 1
            """), {"village": village}).fetchone()

            if result:
                return {
                    "asha_id":       result.asha_id,
                    "name":          result.name,
                    "phone":         result.phone,
                    "supervisor_id": result.supervisor_id,
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
                    "asha_id":       result.asha_id,
                    "name":          result.name,
                    "phone":         result.phone,
                    "village":       result.village,
                    "supervisor_id": result.supervisor_id if result.supervisor_id else "",
                    "role":          "asha"
                }
            return None
    except Exception as e:
        print(f"Get ASHA by phone error: {e}")
        return None


def get_asha_stats(asha_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total = conn.execute(
                text("""
                    SELECT COUNT(*) FROM patients
                    WHERE asha_id = :id AND step = 'registered'
                """),
                {"id": asha_id}
            ).fetchone()[0]

            high_risk = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE asha_id = :id AND status = 'Pending'
                """),
                {"id": asha_id}
            ).fetchone()[0]

            attended = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE asha_id = :id AND status = 'Attended'
                """),
                {"id": asha_id}
            ).fetchone()[0]

            resolved = conn.execute(
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE asha_id = :id AND status = 'Resolved'
                """),
                {"id": asha_id}
            ).fetchone()[0]

            return {
                "total_patients":   total,
                "high_risk_alerts": high_risk,
                "attended":         attended,
                "resolved":         resolved,
                "safe_patients":    max(total - high_risk, 0)
            }
    except Exception as e:
        print(f"Get ASHA stats error: {e}")
        return {
            "total_patients":   0,
            "high_risk_alerts": 0,
            "attended":         0,
            "resolved":         0,
            "safe_patients":    0
        }


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


# ═════════════════════════════════════════════════════════════════
# TIER 5 — PATIENT FUNCTIONS
# ═════════════════════════════════════════════════════════════════

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
                    "phone":         result.phone,
                    "name":          result.name,
                    "week":          result.week,
                    "step":          result.step,
                    "language":      result.language,
                    "asha_id":       result.asha_id       if result.asha_id       else "default_asha",
                    "supervisor_id": result.supervisor_id if result.supervisor_id else "",
                    "bmo_id":        result.bmo_id        if result.bmo_id        else "",
                    "village":       result.village       if result.village       else "",
                    "block_name":    result.block_name    if result.block_name    else "",
                    "district":      result.district      if result.district      else "",
                    "address":       result.address       if result.address       else "",
                    "status":        result.status        if result.status        else "active"
                }
            return None
    except Exception as e:
        print(f"Get patient error: {e}")
        return None


def save_patient(phone, name, week, step, language="Hindi",
                 asha_id="default_asha", village="", address="",
                 supervisor_id="", bmo_id="",
                 block_name="", district=""):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO patients
                    (phone, name, week, step, language, asha_id,
                     village, address, supervisor_id, bmo_id,
                     block_name, district, updated_at)
                VALUES
                    (:phone, :name, :week, :step, :language, :asha_id,
                     :village, :address, :supervisor_id, :bmo_id,
                     :block_name, :district, NOW())
                ON CONFLICT (phone) DO UPDATE SET
                    name          = :name,
                    week          = :week,
                    step          = :step,
                    language      = :language,
                    asha_id       = :asha_id,
                    village       = :village,
                    address       = :address,
                    supervisor_id = :supervisor_id,
                    bmo_id        = :bmo_id,
                    block_name    = :block_name,
                    district      = :district,
                    updated_at    = NOW()
            """), {
                "phone":         phone,
                "name":          name,
                "week":          week,
                "step":          step,
                "language":      language,
                "asha_id":       asha_id,
                "village":       village,
                "address":       address,
                "supervisor_id": supervisor_id,
                "bmo_id":        bmo_id,
                "block_name":    block_name,
                "district":      district
            })
            conn.commit()
    except Exception as e:
        print(f"Save patient error: {e}")


def get_all_patients(asha_id="default_asha"):
    """Get patients for a specific ASHA worker."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM patients
                    WHERE step = 'registered'
                    AND asha_id = :asha_id
                    ORDER BY week DESC
                """),
                {"asha_id": asha_id}
            ).fetchall()
            patients = {}
            for r in results:
                patients[r.phone] = {
                    "phone":   r.phone,
                    "name":    r.name,
                    "week":    r.week,
                    "step":    r.step,
                    "language":r.language,
                    "village": r.village if r.village else "",
                    "address": r.address if r.address else "",
                    "status":  r.status  if r.status  else "active"
                }
            return patients
    except Exception as e:
        print(f"Get all patients error: {e}")
        return {}


def get_all_patients_admin():
    """Get ALL patients across all ASHA workers — for admin/DHO."""
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT p.*,
                           aw.name as asha_name
                    FROM patients p
                    LEFT JOIN asha_workers aw ON p.asha_id = aw.asha_id
                    WHERE p.step = 'registered'
                    ORDER BY p.village, p.name
                """)
            ).fetchall()
            patients = {}
            for r in results:
                patients[r.phone] = {
                    "phone":      r.phone,
                    "name":       r.name,
                    "week":       r.week,
                    "step":       r.step,
                    "language":   r.language,
                    "asha_id":    r.asha_id,
                    "asha_name":  r.asha_name,
                    "village":    r.village    if r.village    else "",
                    "district":   r.district   if r.district   else "",
                    "address":    r.address    if r.address    else "",
                    "status":     r.status     if r.status     else "active"
                }
            return patients
    except Exception as e:
        print(f"Get all patients admin error: {e}")
        return {}


# ═════════════════════════════════════════════════════════════════
# SYMPTOM LOG FUNCTIONS
# ═════════════════════════════════════════════════════════════════

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


# ═════════════════════════════════════════════════════════════════
# ASHA ALERT FUNCTIONS (with full escalation chain)
# ═════════════════════════════════════════════════════════════════

def save_asha_alert_db(phone, name, week, symptom, asha_id,
                       address="", village="", maps_link="",
                       supervisor_id="", bmo_id=""):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO asha_alerts
                    (phone, name, week, symptom, asha_id,
                     address, village, maps_link,
                     supervisor_id, bmo_id)
                VALUES
                    (:phone, :name, :week, :symptom, :asha_id,
                     :address, :village, :maps_link,
                     :supervisor_id, :bmo_id)
                RETURNING id
            """), {
                "phone":         phone,
                "name":          name,
                "week":          week,
                "symptom":       symptom,
                "asha_id":       asha_id,
                "address":       address,
                "village":       village,
                "maps_link":     maps_link,
                "supervisor_id": supervisor_id,
                "bmo_id":        bmo_id
            })
            alert_id = result.fetchone()[0]
            conn.commit()
            return alert_id
    except Exception as e:
        print(f"Save ASHA alert error: {e}")
        return None


def get_all_asha_alerts(asha_id):
    """Alerts for a specific ASHA worker."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM asha_alerts
                    WHERE asha_id = :asha_id
                    ORDER BY
                        CASE status
                            WHEN 'Pending'  THEN 1
                            WHEN 'Attended' THEN 2
                            ELSE 3
                        END,
                        created_at DESC
                """),
                {"asha_id": asha_id}
            ).fetchall()
            return [{
                "id":        r.id,
                "name":      r.name,
                "week":      r.week,
                "symptom":   r.symptom,
                "phone":     r.phone,
                "address":   r.address   if r.address   else "",
                "village":   r.village   if r.village   else "",
                "maps_link": r.maps_link if r.maps_link else "",
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":    r.status,
                "level":     r.escalation_level
            } for r in results]
    except Exception as e:
        print(f"Get ASHA alerts error: {e}")
        return []


def get_all_alerts_admin():
    """All alerts across entire district — for DHO/Admin."""
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT
                        aa.*,
                        aw.name  as asha_name,
                        aw.village as asha_village
                    FROM asha_alerts aa
                    LEFT JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    ORDER BY
                        CASE aa.status
                            WHEN 'Pending'  THEN 1
                            WHEN 'Attended' THEN 2
                            ELSE 3
                        END,
                        aa.created_at DESC
                """)
            ).fetchall()
            return [{
                "id":        r.id,
                "name":      r.name,
                "week":      r.week,
                "symptom":   r.symptom,
                "phone":     r.phone,
                "address":   r.address     if r.address     else "",
                "village":   r.village     if r.village     else "",
                "maps_link": r.maps_link   if r.maps_link   else "",
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":    r.status,
                "asha_id":   r.asha_id,
                "asha_name": r.asha_name,
                "level":     r.escalation_level
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
                text("""
                    SELECT COUNT(*) FROM asha_alerts
                    WHERE asha_id = :asha_id
                    AND status != 'Resolved'
                """),
                {"asha_id": asha_id}
            ).fetchone()
            return result[0]
    except Exception as e:
        print(f"Get alert count error: {e}")
        return 0


def update_alert_status(alert_id, status, notes=""):
    """Update alert status — Pending → Attended → Resolved."""
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE asha_alerts
                SET status         = :status,
                    resolved_notes = CASE
                        WHEN :notes != '' THEN :notes
                        ELSE resolved_notes
                    END
                WHERE id = :id
            """), {"status": status, "id": alert_id, "notes": notes})
            conn.commit()
            return True
    except Exception as e:
        print(f"Update alert status error: {e}")
        return False


def get_alert_by_patient_phone(phone):
    """Get latest pending/attended alert for a patient."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM asha_alerts
                    WHERE phone = :phone
                    AND status != 'Resolved'
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"phone": phone}
            ).fetchone()
            if result:
                return {
                    "id":      result.id,
                    "name":    result.name,
                    "week":    result.week,
                    "symptom": result.symptom,
                    "status":  result.status,
                    "asha_id": result.asha_id
                }
            return None
    except Exception as e:
        print(f"Get alert by phone error: {e}")
        return None


def get_alert_by_id(alert_id):
    """Get full alert details by ID — used in escalation."""
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM asha_alerts WHERE id = :id"),
                {"id": alert_id}
            ).fetchone()
            if result:
                return {
                    "id":            result.id,
                    "phone":         result.phone,
                    "name":          result.name,
                    "week":          result.week,
                    "symptom":       result.symptom,
                    "address":       result.address     if result.address     else "",
                    "village":       result.village     if result.village     else "",
                    "maps_link":     result.maps_link   if result.maps_link   else "",
                    "asha_id":       result.asha_id,
                    "supervisor_id": result.supervisor_id if result.supervisor_id else "",
                    "bmo_id":        result.bmo_id        if result.bmo_id        else "",
                    "status":        result.status,
                    "level":         result.escalation_level,
                    "created_at":    result.created_at
                }
            return None
    except Exception as e:
        print(f"Get alert by ID error: {e}")
        return None


def escalate_alert(alert_id, new_level):
    """Bump escalation level and record escalation time."""
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE asha_alerts
                SET escalation_level = :level,
                    escalated_at     = NOW()
                WHERE id = :id
            """), {"level": new_level, "id": alert_id})
            conn.commit()
            return True
    except Exception as e:
        print(f"Escalate alert error: {e}")
        return False


def log_escalation(alert_id, from_role, to_role, to_phone, reason):
    """Audit trail for every escalation."""
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO escalation_log
                    (alert_id, from_role, to_role, to_phone, reason)
                VALUES
                    (:alert_id, :from_role, :to_role, :to_phone, :reason)
            """), {
                "alert_id":  alert_id,
                "from_role": from_role,
                "to_role":   to_role,
                "to_phone":  to_phone,
                "reason":    reason
            })
            conn.commit()
    except Exception as e:
        print(f"Log escalation error: {e}")


def get_unresponded_alerts(hours=2):
    """
    Returns all Pending alerts older than X hours.
    Used by escalation engine to trigger auto-escalation.
    """
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT aa.*,
                           aw.supervisor_id,
                           aw.name as asha_name,
                           aw.phone as asha_phone
                    FROM asha_alerts aa
                    JOIN asha_workers aw ON aa.asha_id = aw.asha_id
                    WHERE aa.status = 'Pending'
                    AND aa.created_at < NOW() - INTERVAL ':hours hours'
                    AND aa.escalation_level = 0
                    ORDER BY aa.created_at ASC
                """.replace(":hours hours", f"{hours} hours"))
            ).fetchall()
            return [{
                "id":            r.id,
                "phone":         r.phone,
                "name":          r.name,
                "week":          r.week,
                "symptom":       r.symptom,
                "address":       r.address     if r.address     else "",
                "village":       r.village     if r.village     else "",
                "maps_link":     r.maps_link   if r.maps_link   else "",
                "asha_id":       r.asha_id,
                "asha_phone":    r.asha_phone,
                "supervisor_id": r.supervisor_id if r.supervisor_id else "",
                "bmo_id":        r.bmo_id        if r.bmo_id        else "",
                "created_at":    r.created_at
            } for r in results]
    except Exception as e:
        print(f"Get unresponded alerts error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# ASHA VISIT RECORDS
# ═════════════════════════════════════════════════════════════════

def save_asha_visit(alert_id, phone, patient_name, asha_id,
                    outcome, notes="", referred_to=""):
    """
    Saves what happened after ASHA attended a patient.
    outcome options: 'stable', 'referred_phc', 'referred_hospital',
                     'called_108', 'not_found'
    """
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO asha_visits
                    (alert_id, phone, patient_name, asha_id,
                     outcome, notes, referred_to)
                VALUES
                    (:alert_id, :phone, :patient_name, :asha_id,
                     :outcome, :notes, :referred_to)
            """), {
                "alert_id":     alert_id,
                "phone":        phone,
                "patient_name": patient_name,
                "asha_id":      asha_id,
                "outcome":      outcome,
                "notes":        notes,
                "referred_to":  referred_to
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Save visit error: {e}")
        return False


def get_asha_visits(asha_id, limit=20):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM asha_visits
                    WHERE asha_id = :asha_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"asha_id": asha_id, "limit": limit}
            ).fetchall()
            return [{
                "alert_id":     r.alert_id,
                "patient_name": r.patient_name,
                "outcome":      r.outcome,
                "notes":        r.notes,
                "referred_to":  r.referred_to,
                "visit_time":   r.visit_time.strftime("%d %b %Y, %I:%M %p")
            } for r in results]
    except Exception as e:
        print(f"Get visits error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# UNIFIED LOGIN — detects role automatically
# ═════════════════════════════════════════════════════════════════

def unified_login(phone):
    """
    Single login endpoint — checks all role tables in order.
    Returns user dict with 'role' field set correctly.
    Priority: ASHA Worker → Supervisor → BMO → Admin
    """
    # Normalise phone — strip whatsapp: prefix if present
    clean_phone = phone.replace("whatsapp:", "").strip()
    wa_phone    = "whatsapp:" + clean_phone

    # Check ASHA worker (most common login)
    for p in [clean_phone, wa_phone]:
        user = get_asha_by_phone(p)
        if user:
            return user  # role = "asha"

    # Check Supervisor
    for p in [clean_phone, wa_phone]:
        user = verify_supervisor(p)
        if user:
            return user  # role = "supervisor"

    # Check BMO
    for p in [clean_phone, wa_phone]:
        user = verify_bmo(p)
        if user:
            return user  # role = "bmo"

    return None  # Not found in any role table


# ═════════════════════════════════════════════════════════════════
# ANC RECORDS
# ═════════════════════════════════════════════════════════════════

def save_anc_record(phone, visit_number, visit_date, asha_id, notes=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO anc_records
                    (phone, visit_number, visit_date, asha_id, notes)
                VALUES
                    (:phone, :visit_number, :visit_date, :asha_id, :notes)
            """), {
                "phone":        phone,
                "visit_number": visit_number,
                "visit_date":   visit_date,
                "asha_id":      asha_id,
                "notes":        notes
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Save ANC record error: {e}")
        return False


def get_anc_records(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM anc_records
                    WHERE phone = :phone
                    ORDER BY visit_number ASC
                """),
                {"phone": phone}
            ).fetchall()
            return [{
                "visit_number": r.visit_number,
                "visit_date":   r.visit_date,
                "notes":        r.notes
            } for r in results]
    except Exception as e:
        print(f"Get ANC records error: {e}")
        return []


# ═════════════════════════════════════════════════════════════════
# SCHEME DELIVERY FUNCTIONS
# ═════════════════════════════════════════════════════════════════

def save_scheme_delivery(phone, patient_name, scheme_name,
                         amount, delivered_by):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO scheme_deliveries
                    (phone, patient_name, scheme_name,
                     amount, delivered_by, delivery_date)
                VALUES
                    (:phone, :patient_name, :scheme_name,
                     :amount, :delivered_by, :delivery_date)
            """), {
                "phone":        phone,
                "patient_name": patient_name,
                "scheme_name":  scheme_name,
                "amount":       amount,
                "delivered_by": delivered_by,
                "delivery_date": datetime.now().strftime("%d %b %Y")
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Save scheme delivery error: {e}")
        return False


def get_scheme_deliveries(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT * FROM scheme_deliveries
                    WHERE phone = :phone
                    ORDER BY created_at DESC
                """),
                {"phone": phone}
            ).fetchall()
            return [{
                "scheme_name":  r.scheme_name,
                "amount":       r.amount,
                "delivered_by": r.delivered_by,
                "date":         r.delivery_date
            } for r in results]
    except Exception as e:
        print(f"Get scheme deliveries error: {e}")
        return []
