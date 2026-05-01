# -----------------------------------------------------------------
# MaaSakhi Database Layer
# PostgreSQL via SQLAlchemy
# Full 5-Tier Hierarchy:
# District Health Officer -> Block Medical Officer ->
# ASHA Supervisor (ANM) -> ASHA Worker -> Patient
# NO triple-quoted strings (Python version compatibility)
# -----------------------------------------------------------------

import os
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL) if DATABASE_URL else None


# -----------------------------------------------------------------
# INIT
# -----------------------------------------------------------------

def init_db():
    if not engine:
        print("No database URL -- using memory mode")
        return

    with engine.connect() as conn:

        # TIER 1: Admins
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS admins ("
            "id SERIAL PRIMARY KEY,"
            "username TEXT UNIQUE NOT NULL,"
            "password TEXT NOT NULL,"
            "name TEXT,"
            "district TEXT DEFAULT 'All Districts',"
            "phone TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))
        conn.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS district TEXT DEFAULT 'All Districts'"))
        conn.execute(text("ALTER TABLE admins ADD COLUMN IF NOT EXISTS phone TEXT"))

        # TIER 2: Block Medical Officers
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS block_officers ("
            "bmo_id TEXT PRIMARY KEY,"
            "name TEXT NOT NULL,"
            "phone TEXT UNIQUE NOT NULL,"
            "block_name TEXT NOT NULL,"
            "district TEXT NOT NULL,"
            "is_active BOOLEAN DEFAULT TRUE,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # TIER 3: ASHA Supervisors
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS asha_supervisors ("
            "supervisor_id TEXT PRIMARY KEY,"
            "name TEXT NOT NULL,"
            "phone TEXT UNIQUE NOT NULL,"
            "block_name TEXT NOT NULL,"
            "district TEXT NOT NULL,"
            "bmo_id TEXT,"
            "is_active BOOLEAN DEFAULT TRUE,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # TIER 4: ASHA Workers
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS asha_workers ("
            "asha_id TEXT PRIMARY KEY,"
            "name TEXT NOT NULL,"
            "phone TEXT UNIQUE NOT NULL,"
            "village TEXT NOT NULL,"
            "block_name TEXT,"
            "district TEXT,"
            "supervisor_id TEXT,"
            "is_active BOOLEAN DEFAULT TRUE,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS block_name TEXT"))
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS latitude FLOAT"))
        conn.execute(text("ALTER TABLE asha_workers ADD COLUMN IF NOT EXISTS longitude FLOAT"))

        # TIER 5: Patients
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS patients ("
            "phone TEXT PRIMARY KEY,"
            "name TEXT,"
            "week INTEGER,"
            "step TEXT DEFAULT 'welcome',"
            "language TEXT DEFAULT 'Hindi',"
            "asha_id TEXT,"
            "supervisor_id TEXT,"
            "bmo_id TEXT,"
            "village TEXT,"
            "block_name TEXT,"
            "district TEXT,"
            "address TEXT,"
            "delivery_date TEXT,"
            "status TEXT DEFAULT 'active',"
            "latitude FLOAT,"
            "longitude FLOAT,"
            "maps_url TEXT,"
            "created_at TIMESTAMP DEFAULT NOW(),"
            "updated_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS address TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS bmo_id TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS block_name TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS district TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS delivery_date TEXT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active'"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS latitude FLOAT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS longitude FLOAT"))
        conn.execute(text("ALTER TABLE patients ADD COLUMN IF NOT EXISTS maps_url TEXT"))

        # Symptom Logs
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS symptom_logs ("
            "id SERIAL PRIMARY KEY,"
            "phone TEXT,"
            "week INTEGER,"
            "message TEXT,"
            "level TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # ASHA Alerts
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS asha_alerts ("
            "id SERIAL PRIMARY KEY,"
            "phone TEXT,"
            "name TEXT,"
            "week INTEGER,"
            "symptom TEXT,"
            "address TEXT,"
            "village TEXT,"
            "maps_link TEXT,"
            "asha_id TEXT,"
            "supervisor_id TEXT,"
            "bmo_id TEXT,"
            "status TEXT DEFAULT 'Pending',"
            "escalation_level INTEGER DEFAULT 0,"
            "escalated_at TIMESTAMP,"
            "resolved_notes TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS address TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS village TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS maps_link TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS supervisor_id TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS bmo_id TEXT"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMP"))
        conn.execute(text("ALTER TABLE asha_alerts ADD COLUMN IF NOT EXISTS resolved_notes TEXT"))

        # ASHA Visits
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS asha_visits ("
            "id SERIAL PRIMARY KEY,"
            "alert_id INTEGER,"
            "phone TEXT,"
            "patient_name TEXT,"
            "asha_id TEXT,"
            "visit_time TIMESTAMP DEFAULT NOW(),"
            "outcome TEXT,"
            "notes TEXT,"
            "referred_to TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Escalation Log
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS escalation_log ("
            "id SERIAL PRIMARY KEY,"
            "alert_id INTEGER,"
            "from_role TEXT,"
            "to_role TEXT,"
            "to_phone TEXT,"
            "reason TEXT,"
            "sent_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # ANC Records
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS anc_records ("
            "id SERIAL PRIMARY KEY,"
            "phone TEXT,"
            "visit_number INTEGER,"
            "visit_date TEXT,"
            "asha_id TEXT,"
            "notes TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Scheme Deliveries
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS scheme_deliveries ("
            "id SERIAL PRIMARY KEY,"
            "phone TEXT,"
            "patient_name TEXT,"
            "scheme_name TEXT,"
            "amount TEXT,"
            "delivered_by TEXT,"
            "delivery_date TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Deliveries (Month 4)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS deliveries ("
            "id SERIAL PRIMARY KEY,"
            "phone TEXT UNIQUE,"
            "delivery_date TEXT NOT NULL,"
            "birth_weight TEXT,"
            "delivery_mode TEXT,"
            "facility TEXT,"
            "asha_id TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Children (Month 4)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS children ("
            "id SERIAL PRIMARY KEY,"
            "mother_phone TEXT,"
            "child_name TEXT,"
            "dob TEXT,"
            "gender TEXT,"
            "birth_weight TEXT,"
            "asha_id TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Child Growth Logs (Month 4)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS child_growth_logs ("
            "id SERIAL PRIMARY KEY,"
            "child_id INTEGER,"
            "mother_phone TEXT,"
            "weight_kg FLOAT,"
            "height_cm FLOAT,"
            "age_months INTEGER,"
            "log_date TEXT,"
            "z_score FLOAT,"
            "status TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Immunization Records (Month 4)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS immunization_records ("
            "id SERIAL PRIMARY KEY,"
            "child_id INTEGER,"
            "mother_phone TEXT,"
            "vaccine_name TEXT,"
            "dose_number INTEGER,"
            "given_date TEXT,"
            "due_date TEXT,"
            "given_by TEXT,"
            "created_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Reminder Log (Month 4)
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS reminder_log ("
            "id SERIAL PRIMARY KEY,"
            "reminder_type TEXT,"
            "phone TEXT,"
            "message_preview TEXT,"
            "sent_at TIMESTAMP DEFAULT NOW()"
            ")"
        ))

        # Seed default admin
        conn.execute(text(
            "INSERT INTO admins (username, password, name, district) "
            "VALUES ('admin', 'maasakhi2026', 'District Admin', 'All Districts') "
            "ON CONFLICT (username) DO NOTHING"
        ))

        conn.commit()
        print("Database tables created -- Full 5-tier hierarchy ready!")


# =================================================================
# TIER 1 -- ADMIN / DHO
# =================================================================

def verify_admin(username, password):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(
                text("SELECT * FROM admins WHERE username = :u AND password = :p"),
                {"u": username, "p": password}
            ).fetchone()
            if r:
                return {
                    "id":       r.id,
                    "name":     r.name,
                    "username": r.username,
                    "district": r.district if r.district else "All Districts",
                    "role":     "admin"
                }
            return None
    except Exception as e:
        print("Admin verify error: " + str(e))
        return None


def get_district_stats():
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_patients    = conn.execute(text("SELECT COUNT(*) FROM patients WHERE step = 'registered'")).scalar() or 0
            high_risk         = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE status != 'Resolved'")).scalar() or 0
            total_ashas       = conn.execute(text("SELECT COUNT(*) FROM asha_workers WHERE is_active = TRUE")).scalar() or 0
            total_supervisors = conn.execute(text("SELECT COUNT(*) FROM asha_supervisors WHERE is_active = TRUE")).scalar() or 0
            total_bmos        = conn.execute(text("SELECT COUNT(*) FROM block_officers WHERE is_active = TRUE")).scalar() or 0
            alerts_today      = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE DATE(created_at) = CURRENT_DATE")).scalar() or 0
            escalated         = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE escalation_level > 0 AND status != 'Resolved'")).scalar() or 0
            resolved_today    = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE status = 'Resolved' AND DATE(created_at) = CURRENT_DATE")).scalar() or 0
            return {
                "total_patients":     total_patients,
                "high_risk":          high_risk,
                "total_ashas":        total_ashas,
                "total_supervisors":  total_supervisors,
                "total_bmos":         total_bmos,
                "alerts_today":       alerts_today,
                "escalated_alerts":   escalated,
                "resolved_today":     resolved_today,
                "safe_patients":      max(total_patients - high_risk, 0)
            }
    except Exception as e:
        print("Get district stats error: " + str(e))
        return {}


def get_district_trends(days=30):
    # FIX: Cannot use :interval parameter for INTERVAL -- use f-string with safe int
    if not engine:
        return []
    safe_days = int(days)
    try:
        with engine.connect() as conn:
            sql = (
                "SELECT DATE(created_at) AS day, COUNT(*) AS total,"
                " SUM(CASE WHEN level = 'RED'   THEN 1 ELSE 0 END) AS red_count,"
                " SUM(CASE WHEN level = 'AMBER' THEN 1 ELSE 0 END) AS amber_count,"
                " SUM(CASE WHEN level = 'GREEN' THEN 1 ELSE 0 END) AS green_count"
                " FROM symptom_logs"
                " WHERE created_at >= NOW() - INTERVAL '" + str(safe_days) + " days'"
                " GROUP BY DATE(created_at)"
                " ORDER BY day ASC"
            )
            results = conn.execute(text(sql)).fetchall()
            return [{
                "day":         str(r.day),
                "total":       int(r.total),
                "red_count":   int(r.red_count   or 0),
                "amber_count": int(r.amber_count or 0),
                "green_count": int(r.green_count or 0),
            } for r in results]
    except Exception as e:
        print("Get district trends error: " + str(e))
        return []


def get_village_risk_scores():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            sql = (
                "SELECT p.village,"
                " COUNT(DISTINCT p.phone) AS total_patients,"
                " COUNT(DISTINCT CASE WHEN aa.status != 'Resolved' THEN aa.id END) AS active_alerts,"
                " AVG(CASE WHEN sl.level='RED' THEN 40 WHEN sl.level='AMBER' THEN 15"
                "     WHEN sl.level='GREEN' THEN 2 ELSE 0 END) AS avg_risk"
                " FROM patients p"
                " LEFT JOIN asha_alerts aa ON aa.phone = p.phone"
                " LEFT JOIN symptom_logs sl ON sl.phone = p.phone"
                " WHERE p.step = 'registered'"
                " GROUP BY p.village"
                " ORDER BY avg_risk DESC NULLS LAST"
            )
            results = conn.execute(text(sql)).fetchall()
            return [{
                "village":        r.village,
                "total_patients": int(r.total_patients),
                "active_alerts":  int(r.active_alerts or 0),
                "avg_risk":       round(float(r.avg_risk), 1) if r.avg_risk else 0
            } for r in results]
    except Exception as e:
        print("Get village risk scores error: " + str(e))
        return []


# =================================================================
# TIER 2 -- BMO
# =================================================================

def add_block_officer(bmo_id, name, phone, block_name, district):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO block_officers (bmo_id, name, phone, block_name, district)"
                " VALUES (:bmo_id, :name, :phone, :block_name, :district)"
                " ON CONFLICT (bmo_id) DO UPDATE SET"
                " name=:name, phone=:phone, block_name=:block_name, district=:district"
            ), {"bmo_id": bmo_id, "name": name, "phone": phone,
                "block_name": block_name, "district": district})
            conn.commit()
            return True
    except Exception as e:
        print("Add BMO error: " + str(e))
        return False


def get_all_block_officers():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM block_officers ORDER BY district, block_name")).fetchall()
            return [{"bmo_id": r.bmo_id, "name": r.name, "phone": r.phone,
                     "block_name": r.block_name, "district": r.district,
                     "is_active": r.is_active} for r in rows]
    except Exception as e:
        print("Get all BMO error: " + str(e))
        return []


def verify_bmo(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(
                text("SELECT * FROM block_officers WHERE phone = :phone AND is_active = TRUE"),
                {"phone": phone}
            ).fetchone()
            if r:
                return {"bmo_id": r.bmo_id, "name": r.name, "phone": r.phone,
                        "block_name": r.block_name, "district": r.district, "role": "bmo"}
            return None
    except Exception as e:
        print("BMO verify error: " + str(e))
        return None


def toggle_bmo_status(bmo_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE block_officers SET is_active = NOT is_active WHERE bmo_id = :id"), {"id": bmo_id})
            conn.commit()
            return True
    except Exception as e:
        print("Toggle BMO error: " + str(e))
        return False


def delete_block_officer(bmo_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM block_officers WHERE bmo_id = :id"), {"id": bmo_id})
            conn.commit()
            return True
    except Exception as e:
        print("Delete BMO error: " + str(e))
        return False


def get_bmo_stats(bmo_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_supervisors = conn.execute(text(
                "SELECT COUNT(*) FROM asha_supervisors WHERE bmo_id = :id AND is_active = TRUE"
            ), {"id": bmo_id}).scalar() or 0

            total_ashas = conn.execute(text(
                "SELECT COUNT(*) FROM asha_workers aw"
                " JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id"
                " WHERE s.bmo_id = :id AND aw.is_active = TRUE"
            ), {"id": bmo_id}).scalar() or 0

            total_patients = conn.execute(text(
                "SELECT COUNT(*) FROM patients p"
                " JOIN asha_workers aw ON p.asha_id = aw.asha_id"
                " JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id"
                " WHERE s.bmo_id = :id AND p.step = 'registered'"
            ), {"id": bmo_id}).scalar() or 0

            escalated = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts"
                " WHERE bmo_id = :id AND status != 'Resolved' AND escalation_level >= 2"
            ), {"id": bmo_id}).scalar() or 0

            pending_in_block = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts aa"
                " JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id"
                " WHERE s.bmo_id = :id AND aa.status = 'Pending'"
            ), {"id": bmo_id}).scalar() or 0

            return {
                "total_supervisors": total_supervisors,
                "total_ashas":       total_ashas,
                "total_patients":    total_patients,
                "escalated_alerts":  escalated,
                "pending_in_block":  pending_in_block
            }
    except Exception as e:
        print("Get BMO stats error: " + str(e))
        return {}


def get_bmo_alerts(bmo_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT aa.*, aw.name as asha_name, aw.village"
                " FROM asha_alerts aa"
                " LEFT JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " WHERE aa.bmo_id = :bmo_id AND aa.escalation_level >= 2"
                " ORDER BY aa.created_at DESC"
            ), {"bmo_id": bmo_id}).fetchall()
            return [{
                "id": r.id, "name": r.name, "week": r.week,
                "symptom": r.symptom, "phone": r.phone,
                "address":   r.address   or "",
                "village":   r.village   or "",
                "maps_link": r.maps_link or "",
                "status":    r.status,
                "asha_name": r.asha_name,
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in rows]
    except Exception as e:
        print("Get BMO alerts error: " + str(e))
        return []


def get_patients_by_bmo(bmo_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT p.*, aw.name as asha_name FROM patients p"
                " JOIN asha_workers aw ON p.asha_id = aw.asha_id"
                " JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id"
                " WHERE s.bmo_id = :bmo_id AND p.step = 'registered'"
                " ORDER BY p.village, p.name"
            ), {"bmo_id": bmo_id}).fetchall()
            return {r.phone: {
                "phone": r.phone, "name": r.name, "week": r.week,
                "village": r.village or "", "address": r.address or "",
                "asha_name": r.asha_name, "status": r.status or "active"
            } for r in rows}
    except Exception as e:
        print("Get patients by BMO error: " + str(e))
        return {}


# =================================================================
# TIER 3 -- SUPERVISOR
# =================================================================

def add_asha_supervisor(supervisor_id, name, phone, block_name, district, bmo_id=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO asha_supervisors"
                " (supervisor_id, name, phone, block_name, district, bmo_id)"
                " VALUES (:supervisor_id, :name, :phone, :block_name, :district, :bmo_id)"
                " ON CONFLICT (supervisor_id) DO UPDATE SET"
                " name=:name, phone=:phone, block_name=:block_name,"
                " district=:district, bmo_id=:bmo_id"
            ), {"supervisor_id": supervisor_id, "name": name, "phone": phone,
                "block_name": block_name, "district": district, "bmo_id": bmo_id})
            conn.commit()
            return True
    except Exception as e:
        print("Add supervisor error: " + str(e))
        return False


def get_all_supervisors():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM asha_supervisors ORDER BY district, block_name, name"
            )).fetchall()
            return [{"supervisor_id": r.supervisor_id, "name": r.name, "phone": r.phone,
                     "block_name": r.block_name, "district": r.district,
                     "bmo_id": r.bmo_id, "is_active": r.is_active} for r in rows]
    except Exception as e:
        print("Get all supervisors error: " + str(e))
        return []


def verify_supervisor(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                "SELECT * FROM asha_supervisors WHERE phone = :phone AND is_active = TRUE"
            ), {"phone": phone}).fetchone()
            if r:
                return {"supervisor_id": r.supervisor_id, "name": r.name,
                        "phone": r.phone, "block_name": r.block_name,
                        "district": r.district, "bmo_id": r.bmo_id, "role": "supervisor"}
            return None
    except Exception as e:
        print("Supervisor verify error: " + str(e))
        return None


def toggle_supervisor_status(supervisor_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE asha_supervisors SET is_active = NOT is_active"
                " WHERE supervisor_id = :id"
            ), {"id": supervisor_id})
            conn.commit()
            return True
    except Exception as e:
        print("Toggle supervisor error: " + str(e))
        return False


def delete_supervisor(supervisor_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM asha_supervisors WHERE supervisor_id = :id"), {"id": supervisor_id})
            conn.commit()
            return True
    except Exception as e:
        print("Delete supervisor error: " + str(e))
        return False


def get_supervisor_stats(supervisor_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            total_ashas = conn.execute(text(
                "SELECT COUNT(*) FROM asha_workers WHERE supervisor_id = :id AND is_active = TRUE"
            ), {"id": supervisor_id}).scalar() or 0

            total_patients = conn.execute(text(
                "SELECT COUNT(*) FROM patients p"
                " JOIN asha_workers aw ON p.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id AND p.step = 'registered'"
            ), {"id": supervisor_id}).scalar() or 0

            pending_alerts = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts aa"
                " JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id AND aa.status = 'Pending'"
            ), {"id": supervisor_id}).scalar() or 0

            escalated_to_me = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts"
                " WHERE supervisor_id = :id AND escalation_level = 1 AND status != 'Resolved'"
            ), {"id": supervisor_id}).scalar() or 0

            resolved_this_week = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts aa"
                " JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id AND aa.status = 'Resolved'"
                " AND aa.created_at >= NOW() - INTERVAL '7 days'"
            ), {"id": supervisor_id}).scalar() or 0

            return {
                "total_ashas":        total_ashas,
                "total_patients":     total_patients,
                "pending_alerts":     pending_alerts,
                "escalated_to_me":    escalated_to_me,
                "resolved_this_week": resolved_this_week
            }
    except Exception as e:
        print("Get supervisor stats error: " + str(e))
        return {}


def get_supervisor_ashas(supervisor_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT aw.*,"
                " COUNT(DISTINCT p.phone) AS patient_count,"
                " COUNT(DISTINCT CASE WHEN aa.status='Pending' THEN aa.id END) AS pending_alerts,"
                " COUNT(DISTINCT CASE WHEN aa.status='Resolved' THEN aa.id END) AS resolved_alerts,"
                " COUNT(DISTINCT CASE WHEN aa.escalation_level>0 THEN aa.id END) AS escalated_alerts,"
                " AVG(CASE WHEN aa.status='Resolved' AND aa.escalated_at IS NOT NULL"
                "     THEN EXTRACT(EPOCH FROM (aa.escalated_at - aa.created_at))/3600.0 END) AS avg_response_hrs"
                " FROM asha_workers aw"
                " LEFT JOIN patients p ON p.asha_id = aw.asha_id AND p.step = 'registered'"
                " LEFT JOIN asha_alerts aa ON aa.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id"
                " GROUP BY aw.asha_id"
                " ORDER BY pending_alerts DESC, patient_count DESC"
            ), {"id": supervisor_id}).fetchall()
            return [{
                "asha_id":          r.asha_id,
                "name":             r.name,
                "phone":            r.phone,
                "village":          r.village,
                "is_active":        r.is_active,
                "patient_count":    int(r.patient_count),
                "pending_alerts":   int(r.pending_alerts),
                "resolved_alerts":  int(r.resolved_alerts),
                "escalated_alerts": int(r.escalated_alerts),
                "avg_response_hrs": round(float(r.avg_response_hrs), 1) if r.avg_response_hrs else None
            } for r in rows]
    except Exception as e:
        print("Get supervisor ASHAs error: " + str(e))
        return []


def get_supervisor_alerts(supervisor_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT aa.*, aw.name as asha_name, aw.village, aw.phone as asha_phone"
                " FROM asha_alerts aa"
                " JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id"
                " ORDER BY CASE aa.status WHEN 'Pending' THEN 1 WHEN 'Attended' THEN 2 ELSE 3 END,"
                " aa.created_at DESC"
            ), {"id": supervisor_id}).fetchall()
            return [{
                "id":        r.id, "name": r.name, "week": r.week,
                "symptom":   r.symptom, "phone": r.phone,
                "address":   r.address   or "",
                "village":   r.village   or "",
                "maps_link": r.maps_link or "",
                "status":    r.status,
                "asha_name": r.asha_name,
                "asha_id":   r.asha_id,
                "asha_phone":r.asha_phone or "",
                "level":     r.escalation_level,
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p")
            } for r in rows]
    except Exception as e:
        print("Get supervisor alerts error: " + str(e))
        return []


def get_patients_by_supervisor(supervisor_id):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT p.*, aw.name as asha_name FROM patients p"
                " JOIN asha_workers aw ON p.asha_id = aw.asha_id"
                " WHERE aw.supervisor_id = :id AND p.step = 'registered'"
                " ORDER BY p.village, p.name"
            ), {"id": supervisor_id}).fetchall()
            return {r.phone: {
                "phone": r.phone, "name": r.name, "week": r.week,
                "village": r.village or "", "address": r.address or "",
                "asha_name": r.asha_name, "status": r.status or "active"
            } for r in rows}
    except Exception as e:
        print("Get patients by supervisor error: " + str(e))
        return {}


# =================================================================
# TIER 4 -- ASHA WORKER
# =================================================================

def add_asha_worker(asha_id, name, phone, village, district="",
                    block_name="", supervisor_id=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO asha_workers"
                " (asha_id, name, phone, village, district, block_name, supervisor_id)"
                " VALUES (:asha_id, :name, :phone, :village, :district, :block_name, :supervisor_id)"
                " ON CONFLICT (asha_id) DO UPDATE SET"
                " name=:name, phone=:phone, village=:village,"
                " district=:district, block_name=:block_name, supervisor_id=:supervisor_id"
            ), {"asha_id": asha_id, "name": name, "phone": phone, "village": village,
                "district": district, "block_name": block_name, "supervisor_id": supervisor_id})
            conn.commit()
            return True
    except Exception as e:
        print("Add ASHA error: " + str(e))
        return False


def get_all_asha_workers():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT aw.*, s.name as supervisor_name, s.block_name as s_block"
                " FROM asha_workers aw"
                " LEFT JOIN asha_supervisors s ON aw.supervisor_id = s.supervisor_id"
                " ORDER BY aw.district, aw.village, aw.name"
            )).fetchall()
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
            } for r in rows]
    except Exception as e:
        print("Get all ASHA error: " + str(e))
        return []


def get_asha_by_village(village):
    """
    Smart ASHA auto-assignment with 5-level fuzzy matching.
    Tries exact -> DB-contains-typed -> typed-contains-DB ->
            first-word -> any-significant-word
    Returns ASHA with fewest patients among all matches.
    """
    if not engine or not village:
        return None

    village_clean = village.strip()

    BASE = (
        "SELECT a.asha_id, a.name, a.phone, a.village, a.supervisor_id,"
        " COUNT(p.phone) AS patient_count"
        " FROM asha_workers a"
        " LEFT JOIN patients p ON p.asha_id = a.asha_id AND p.step = 'registered'"
        " WHERE a.is_active = TRUE AND {WHERE}"
        " GROUP BY a.asha_id, a.name, a.phone, a.village, a.supervisor_id"
        " ORDER BY patient_count ASC LIMIT 1"
    )

    def _run(where, params):
        try:
            with engine.connect() as conn:
                return conn.execute(text(BASE.format(WHERE=where)), params).fetchone()
        except Exception as e:
            print("Village match error: " + str(e))
            return None

    def _row_to_dict(r):
        if not r:
            return None
        return {
            "asha_id":       r.asha_id,
            "name":          r.name,
            "phone":         r.phone,
            "village":       r.village,
            "supervisor_id": r.supervisor_id or "",
            "patient_count": int(r.patient_count),
        }

    v = village_clean

    # Strategy 1: Exact case-insensitive
    r = _run("LOWER(a.village) = LOWER(:v)", {"v": v})
    if r:
        print("[village] EXACT: '" + v + "' -> '" + r.village + "'")
        return _row_to_dict(r)

    # Strategy 2: DB village contains typed text
    r = _run("LOWER(a.village) LIKE LOWER(:v)", {"v": "%" + v + "%"})
    if r:
        print("[village] DB-CONTAINS: '" + v + "' -> '" + r.village + "'")
        return _row_to_dict(r)

    # Strategy 3: Typed text contains DB village
    try:
        with engine.connect() as conn:
            all_rows = conn.execute(text(
                "SELECT a.asha_id, a.name, a.phone, a.village, a.supervisor_id,"
                " COUNT(p.phone) AS patient_count"
                " FROM asha_workers a"
                " LEFT JOIN patients p ON p.asha_id = a.asha_id AND p.step = 'registered'"
                " WHERE a.is_active = TRUE"
                " GROUP BY a.asha_id, a.name, a.phone, a.village, a.supervisor_id"
            )).fetchall()
            typed_lower = v.lower()
            candidates  = [row for row in all_rows if row.village and row.village.lower() in typed_lower]
            if candidates:
                best = min(candidates, key=lambda x: x.patient_count)
                print("[village] TYPED-CONTAINS: '" + v + "' -> '" + best.village + "'")
                return _row_to_dict(best)
    except Exception as e:
        print("Village strategy 3 error: " + str(e))

    # Strategy 4: First-word match
    parts = v.split()
    first = parts[0] if parts else v
    if len(first) >= 3:
        r = _run("LOWER(a.village) LIKE LOWER(:fw)", {"fw": first + "%"})
        if r:
            print("[village] FIRST-WORD: '" + v + "' -> '" + r.village + "'")
            return _row_to_dict(r)

    # Strategy 5: Any significant word
    STOP = {"ka", "ki", "ke", "la", "the", "a", "an", "and",
            "new", "old", "east", "west", "north", "south", "village", "gaon"}
    words = [w for w in v.lower().split() if len(w) >= 4 and w not in STOP]
    for word in words:
        r = _run("LOWER(a.village) LIKE LOWER(:w)", {"w": "%" + word + "%"})
        if r:
            print("[village] ANY-WORD '" + word + "': '" + v + "' -> '" + r.village + "'")
            return _row_to_dict(r)

    print("[village] NO MATCH for '" + v + "' -- will use default_asha")
    return None


def get_village_suggestions(typed, limit=5):
    """
    Returns up to `limit` stored village names closest to what
    the patient typed. Used in WhatsApp bot confirmation flow.
    """
    if not engine or not typed:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT DISTINCT village FROM asha_workers"
                " WHERE is_active = TRUE AND village IS NOT NULL ORDER BY village"
            )).fetchall()
        typed_lower = typed.lower().strip()
        matches = []
        for r in rows:
            v = r.village or ""
            vl = v.lower()
            if vl == typed_lower:
                score = 100
            elif vl.startswith(typed_lower):
                score = 80
            elif typed_lower in vl:
                score = 60
            elif vl in typed_lower:
                score = 50
            elif any(w in vl for w in typed_lower.split() if len(w) >= 3):
                score = 30
            else:
                continue
            matches.append((score, v))
        matches.sort(key=lambda x: -x[0])
        return [v for _, v in matches[:limit]]
    except Exception as e:
        print("get_village_suggestions error: " + str(e))
        return []


def get_asha_by_phone(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(
                text("SELECT * FROM asha_workers WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            if r:
                return {
                    "asha_id":       r.asha_id,
                    "name":          r.name,
                    "phone":         r.phone,
                    "village":       r.village,
                    "supervisor_id": r.supervisor_id or "",
                    "role":          "asha"
                }
            return None
    except Exception as e:
        print("Get ASHA by phone error: " + str(e))
        return None


def get_asha_stats(asha_id):
    if not engine:
        return {"total_patients": 0, "high_risk_alerts": 0,
                "attended": 0, "resolved": 0, "safe_patients": 0}
    try:
        with engine.connect() as conn:
            total    = conn.execute(text("SELECT COUNT(*) FROM patients WHERE asha_id=:id AND step='registered'"), {"id": asha_id}).scalar() or 0
            high     = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id AND status='Pending'"), {"id": asha_id}).scalar() or 0
            attended = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id AND status='Attended'"), {"id": asha_id}).scalar() or 0
            resolved = conn.execute(text("SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id AND status='Resolved'"), {"id": asha_id}).scalar() or 0
            return {
                "total_patients":   int(total),
                "high_risk_alerts": int(high),
                "attended":         int(attended),
                "resolved":         int(resolved),
                "safe_patients":    max(int(total) - int(high), 0)
            }
    except Exception as e:
        print("Get ASHA stats error: " + str(e))
        return {"total_patients": 0, "high_risk_alerts": 0,
                "attended": 0, "resolved": 0, "safe_patients": 0}


def get_asha_performance(asha_id, days=30):
    # FIX: use f-string for INTERVAL -- cannot use :param for interval values
    if not engine:
        return {}
    safe_days = int(days)
    interval  = str(safe_days) + " days"
    try:
        with engine.connect() as conn:
            total_alerts = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id"
                " AND created_at >= NOW() - INTERVAL '" + interval + "'"
            ), {"id": asha_id}).scalar() or 0

            resolved_alerts = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id AND status='Resolved'"
                " AND created_at >= NOW() - INTERVAL '" + interval + "'"
            ), {"id": asha_id}).scalar() or 0

            escalated_alerts = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:id AND escalation_level>0"
                " AND created_at >= NOW() - INTERVAL '" + interval + "'"
            ), {"id": asha_id}).scalar() or 0

            visit_count = conn.execute(text(
                "SELECT COUNT(*) FROM asha_visits WHERE asha_id=:id"
                " AND created_at >= NOW() - INTERVAL '" + interval + "'"
            ), {"id": asha_id}).scalar() or 0

            avg_resp = conn.execute(text(
                "SELECT AVG(EXTRACT(EPOCH FROM (av.visit_time - aa.created_at))/3600.0)"
                " FROM asha_visits av JOIN asha_alerts aa ON av.alert_id = aa.id"
                " WHERE av.asha_id=:id"
                " AND av.created_at >= NOW() - INTERVAL '" + interval + "'"
            ), {"id": asha_id}).scalar()

            total_i    = int(total_alerts)
            res_rate   = round(int(resolved_alerts)  / total_i * 100, 1) if total_i > 0 else 0.0
            esc_rate   = round(int(escalated_alerts) / total_i * 100, 1) if total_i > 0 else 0.0
            avg_hrs    = round(float(avg_resp), 1) if avg_resp else None

            if avg_hrs is None:
                rating = "unknown"
            elif avg_hrs <= 1 and esc_rate <= 10:
                rating = "GREEN"
            elif avg_hrs <= 3 and esc_rate <= 30:
                rating = "AMBER"
            else:
                rating = "RED"

            return {
                "total_alerts":       total_i,
                "resolved_alerts":    int(resolved_alerts),
                "escalated_alerts":   int(escalated_alerts),
                "visit_count":        int(visit_count),
                "resolution_rate":    res_rate,
                "escalation_rate":    esc_rate,
                "avg_response_hrs":   avg_hrs,
                "performance_rating": rating
            }
    except Exception as e:
        print("Get ASHA performance error: " + str(e))
        return {}


def toggle_asha_status(asha_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE asha_workers SET is_active = NOT is_active WHERE asha_id=:id"), {"id": asha_id})
            conn.commit()
            return True
    except Exception as e:
        print("Toggle ASHA error: " + str(e))
        return False


def delete_asha_worker(asha_id):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM asha_workers WHERE asha_id=:id"), {"id": asha_id})
            conn.commit()
            return True
    except Exception as e:
        print("Delete ASHA error: " + str(e))
        return False


# =================================================================
# TIER 5 -- PATIENT
# =================================================================

def get_patient(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT * FROM patients WHERE phone=:phone"), {"phone": phone}).fetchone()
            if r:
                return {
                    "phone":         r.phone,
                    "name":          r.name,
                    "week":          r.week,
                    "step":          r.step,
                    "language":      r.language,
                    "asha_id":       r.asha_id       or "default_asha",
                    "supervisor_id": r.supervisor_id or "",
                    "bmo_id":        r.bmo_id        or "",
                    "village":       r.village       or "",
                    "block_name":    r.block_name    or "",
                    "district":      r.district      or "",
                    "address":       r.address       or "",
                    "status":        r.status        or "active"
                }
            return None
    except Exception as e:
        print("Get patient error: " + str(e))
        return None


def save_patient(phone, name, week, step, language="Hindi",
                 asha_id="default_asha", village="", address="",
                 supervisor_id="", bmo_id="", block_name="", district=""):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO patients"
                " (phone,name,week,step,language,asha_id,village,address,"
                "  supervisor_id,bmo_id,block_name,district,updated_at)"
                " VALUES"
                " (:phone,:name,:week,:step,:language,:asha_id,:village,:address,"
                "  :supervisor_id,:bmo_id,:block_name,:district,NOW())"
                " ON CONFLICT (phone) DO UPDATE SET"
                " name=:name, week=:week, step=:step, language=:language,"
                " asha_id=:asha_id, village=:village, address=:address,"
                " supervisor_id=:supervisor_id, bmo_id=:bmo_id,"
                " block_name=:block_name, district=:district, updated_at=NOW()"
            ), {"phone": phone, "name": name, "week": week, "step": step,
                "language": language, "asha_id": asha_id, "village": village,
                "address": address, "supervisor_id": supervisor_id,
                "bmo_id": bmo_id, "block_name": block_name, "district": district})
            conn.commit()
    except Exception as e:
        print("Save patient error: " + str(e))


def update_patient_status(phone, status):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE patients SET status=:status, updated_at=NOW() WHERE phone=:phone"
            ), {"status": status, "phone": phone})
            conn.commit()
            return True
    except Exception as e:
        print("Update patient status error: " + str(e))
        return False


def get_all_patients(asha_id="default_asha"):
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM patients WHERE step='registered' AND asha_id=:asha_id ORDER BY week DESC"
            ), {"asha_id": asha_id}).fetchall()
            return {r.phone: {
                "phone": r.phone, "name": r.name, "week": r.week,
                "step": r.step, "language": r.language,
                "village": r.village or "", "address": r.address or "",
                "status": r.status or "active"
            } for r in rows}
    except Exception as e:
        print("Get all patients error: " + str(e))
        return {}


def get_all_patients_admin():
    if not engine:
        return {}
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT p.*, aw.name as asha_name FROM patients p"
                " LEFT JOIN asha_workers aw ON p.asha_id = aw.asha_id"
                " WHERE p.step = 'registered'"
                " ORDER BY p.village, p.name"
            )).fetchall()
            return {r.phone: {
                "phone": r.phone, "name": r.name, "week": r.week,
                "step": r.step, "language": r.language,
                "asha_id": r.asha_id, "asha_name": r.asha_name,
                "village": r.village or "", "district": r.district or "",
                "address": r.address or "", "status": r.status or "active"
            } for r in rows}
    except Exception as e:
        print("Get all patients admin error: " + str(e))
        return {}


# =================================================================
# SYMPTOM LOGS
# =================================================================

def save_symptom_log(phone, week, message, level):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO symptom_logs (phone,week,message,level) VALUES (:phone,:week,:message,:level)"
            ), {"phone": phone, "week": week, "message": message, "level": level})
            conn.commit()
    except Exception as e:
        print("Save symptom log error: " + str(e))


def get_symptom_logs(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM symptom_logs WHERE phone=:phone ORDER BY created_at ASC"
            ), {"phone": phone}).fetchall()
            return [{"week": r.week, "message": r.message, "level": r.level,
                     "time": r.created_at.strftime("%d %b %Y, %I:%M %p")} for r in rows]
    except Exception as e:
        print("Get symptom logs error: " + str(e))
        return []


def get_risk_score_from_db(phone):
    logs = get_symptom_logs(phone)
    if not logs:
        return 0, "Unknown", "No reports yet"
    red   = sum(1 for e in logs if e["level"] == "RED")
    amber = sum(1 for e in logs if e["level"] == "AMBER")
    green = sum(1 for e in logs if e["level"] == "GREEN")
    total = len(logs)
    score = min(100, (red * 40) + (amber * 15) + (green * 2))
    recent_reds = sum(1 for e in (logs[-3:] if len(logs) >= 3 else logs) if e["level"] == "RED")
    if recent_reds >= 2:
        score = min(100, score + 20)
    if score >= 60 or red >= 2:
        risk_level = "HIGH"
    elif score >= 30 or red >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
    summary = "Total: " + str(total) + " | Danger: " + str(red) + " | Warning: " + str(amber) + " | Normal: " + str(green)
    return score, risk_level, summary


# =================================================================
# ASHA ALERTS
# =================================================================

def save_asha_alert_db(phone, name, week, symptom, asha_id,
                       address="", village="", maps_link="",
                       supervisor_id="", bmo_id=""):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                "INSERT INTO asha_alerts"
                " (phone,name,week,symptom,asha_id,address,village,maps_link,supervisor_id,bmo_id)"
                " VALUES (:phone,:name,:week,:symptom,:asha_id,:address,:village,:maps_link,:supervisor_id,:bmo_id)"
                " RETURNING id"
            ), {"phone": phone, "name": name, "week": week, "symptom": symptom,
                "asha_id": asha_id, "address": address, "village": village,
                "maps_link": maps_link, "supervisor_id": supervisor_id, "bmo_id": bmo_id})
            alert_id = r.fetchone()[0]
            conn.commit()
            return alert_id
    except Exception as e:
        print("Save ASHA alert error: " + str(e))
        return None


def get_all_asha_alerts(asha_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM asha_alerts WHERE asha_id=:asha_id"
                " ORDER BY CASE status WHEN 'Pending' THEN 1 WHEN 'Attended' THEN 2 ELSE 3 END,"
                " created_at DESC"
            ), {"asha_id": asha_id}).fetchall()
            return [{
                "id": r.id, "name": r.name, "week": r.week,
                "symptom": r.symptom, "phone": r.phone,
                "address":   r.address   or "",
                "village":   r.village   or "",
                "maps_link": r.maps_link or "",
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":    r.status,
                "level":     r.escalation_level,
                "resolved_notes": r.resolved_notes or ""
            } for r in rows]
    except Exception as e:
        print("Get ASHA alerts error: " + str(e))
        return []


def get_all_alerts_admin():
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT aa.*, aw.name as asha_name, aw.village as asha_village"
                " FROM asha_alerts aa"
                " LEFT JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " ORDER BY CASE aa.status WHEN 'Pending' THEN 1 WHEN 'Attended' THEN 2 ELSE 3 END,"
                " aa.created_at DESC"
            )).fetchall()
            return [{
                "id": r.id, "name": r.name, "week": r.week,
                "symptom": r.symptom, "phone": r.phone,
                "address":   r.address   or "",
                "village":   r.village   or "",
                "maps_link": r.maps_link or "",
                "time":      r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "status":    r.status,
                "asha_id":   r.asha_id,
                "asha_name": r.asha_name,
                "level":     r.escalation_level
            } for r in rows]
    except Exception as e:
        print("Get all alerts admin error: " + str(e))
        return []


def get_alert_count_db(asha_id="default_asha"):
    if not engine:
        return 0
    try:
        with engine.connect() as conn:
            return conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE asha_id=:asha_id AND status!='Resolved'"
            ), {"asha_id": asha_id}).scalar() or 0
    except Exception as e:
        print("Get alert count error: " + str(e))
        return 0


def update_alert_status(alert_id, status, notes=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE asha_alerts SET status=:status,"
                " resolved_notes = CASE WHEN :notes != '' THEN :notes ELSE resolved_notes END"
                " WHERE id=:id"
            ), {"status": status, "id": alert_id, "notes": notes})
            conn.commit()
            return True
    except Exception as e:
        print("Update alert status error: " + str(e))
        return False


def get_alert_by_patient_phone(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                "SELECT * FROM asha_alerts WHERE phone=:phone AND status!='Resolved'"
                " ORDER BY created_at DESC LIMIT 1"
            ), {"phone": phone}).fetchone()
            if r:
                return {"id": r.id, "name": r.name, "week": r.week,
                        "symptom": r.symptom, "status": r.status, "asha_id": r.asha_id}
            return None
    except Exception as e:
        print("Get alert by phone error: " + str(e))
        return None


def get_alert_by_id(alert_id):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT * FROM asha_alerts WHERE id=:id"), {"id": alert_id}).fetchone()
            if r:
                return {
                    "id":            r.id,
                    "phone":         r.phone,
                    "name":          r.name,
                    "week":          r.week,
                    "symptom":       r.symptom,
                    "address":       r.address       or "",
                    "village":       r.village       or "",
                    "maps_link":     r.maps_link     or "",
                    "asha_id":       r.asha_id,
                    "supervisor_id": r.supervisor_id or "",
                    "bmo_id":        r.bmo_id        or "",
                    "status":        r.status,
                    "level":         r.escalation_level,
                    "created_at":    r.created_at
                }
            return None
    except Exception as e:
        print("Get alert by ID error: " + str(e))
        return None


def escalate_alert(alert_id, new_level):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "UPDATE asha_alerts SET escalation_level=:level, escalated_at=NOW() WHERE id=:id"
            ), {"level": new_level, "id": alert_id})
            conn.commit()
            return True
    except Exception as e:
        print("Escalate alert error: " + str(e))
        return False


def log_escalation(alert_id, from_role, to_role, to_phone, reason):
    if not engine:
        return
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO escalation_log (alert_id,from_role,to_role,to_phone,reason)"
                " VALUES (:alert_id,:from_role,:to_role,:to_phone,:reason)"
            ), {"alert_id": alert_id, "from_role": from_role, "to_role": to_role,
                "to_phone": to_phone, "reason": reason})
            conn.commit()
    except Exception as e:
        print("Log escalation error: " + str(e))


def get_unresponded_alerts(hours=2):
    if not engine:
        return []
    safe_hours = int(hours)
    try:
        with engine.connect() as conn:
            sql = (
                "SELECT aa.*, aw.supervisor_id, aw.name as asha_name, aw.phone as asha_phone"
                " FROM asha_alerts aa"
                " JOIN asha_workers aw ON aa.asha_id = aw.asha_id"
                " WHERE aa.status = 'Pending'"
                " AND aa.created_at < NOW() - INTERVAL '" + str(safe_hours) + " hours'"
                " AND aa.escalation_level = 0"
                " ORDER BY aa.created_at ASC"
            )
            rows = conn.execute(text(sql)).fetchall()
            return [{
                "id":            r.id,
                "phone":         r.phone,
                "name":          r.name,
                "week":          r.week,
                "symptom":       r.symptom,
                "address":       r.address       or "",
                "village":       r.village       or "",
                "maps_link":     r.maps_link     or "",
                "asha_id":       r.asha_id,
                "asha_phone":    r.asha_phone,
                "supervisor_id": r.supervisor_id or "",
                "bmo_id":        r.bmo_id        or "",
                "created_at":    r.created_at
            } for r in rows]
    except Exception as e:
        print("Get unresponded alerts error: " + str(e))
        return []


# =================================================================
# ASHA VISITS
# =================================================================

def save_asha_visit(alert_id, phone, patient_name, asha_id,
                    outcome, notes="", referred_to=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO asha_visits (alert_id,phone,patient_name,asha_id,outcome,notes,referred_to)"
                " VALUES (:alert_id,:phone,:patient_name,:asha_id,:outcome,:notes,:referred_to)"
            ), {"alert_id": alert_id, "phone": phone, "patient_name": patient_name,
                "asha_id": asha_id, "outcome": outcome, "notes": notes, "referred_to": referred_to})
            conn.commit()
            return True
    except Exception as e:
        print("Save visit error: " + str(e))
        return False


def get_asha_visits(asha_id, limit=20):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM asha_visits WHERE asha_id=:asha_id ORDER BY created_at DESC LIMIT :limit"
            ), {"asha_id": asha_id, "limit": limit}).fetchall()
            return [{"alert_id": r.alert_id, "patient_name": r.patient_name,
                     "outcome": r.outcome, "notes": r.notes,
                     "referred_to": r.referred_to,
                     "visit_time": r.visit_time.strftime("%d %b %Y, %I:%M %p")} for r in rows]
    except Exception as e:
        print("Get visits error: " + str(e))
        return []


# =================================================================
# UNIFIED LOGIN
# =================================================================

def unified_login(phone):
    clean  = phone.replace("whatsapp:", "").strip()
    wa     = "whatsapp:" + clean
    for p in [clean, wa]:
        u = get_asha_by_phone(p)
        if u:
            return u
    for p in [clean, wa]:
        u = verify_supervisor(p)
        if u:
            return u
    for p in [clean, wa]:
        u = verify_bmo(p)
        if u:
            return u
    return None


# =================================================================
# ANC RECORDS
# =================================================================

def save_anc_record(phone, visit_number, visit_date, asha_id, notes=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO anc_records (phone,visit_number,visit_date,asha_id,notes)"
                " VALUES (:phone,:visit_number,:visit_date,:asha_id,:notes)"
            ), {"phone": phone, "visit_number": visit_number, "visit_date": visit_date,
                "asha_id": asha_id, "notes": notes})
            conn.commit()
            return True
    except Exception as e:
        print("Save ANC record error: " + str(e))
        return False


def get_anc_records(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM anc_records WHERE phone=:phone ORDER BY visit_number ASC"
            ), {"phone": phone}).fetchall()
            return [{"visit_number": r.visit_number, "visit_date": r.visit_date, "notes": r.notes} for r in rows]
    except Exception as e:
        print("Get ANC records error: " + str(e))
        return []


# =================================================================
# SCHEME DELIVERIES
# =================================================================

def save_scheme_delivery(phone, patient_name, scheme_name, amount, delivered_by):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO scheme_deliveries (phone,patient_name,scheme_name,amount,delivered_by,delivery_date)"
                " VALUES (:phone,:patient_name,:scheme_name,:amount,:delivered_by,:delivery_date)"
            ), {"phone": phone, "patient_name": patient_name, "scheme_name": scheme_name,
                "amount": amount, "delivered_by": delivered_by,
                "delivery_date": datetime.now().strftime("%d %b %Y")})
            conn.commit()
            return True
    except Exception as e:
        print("Save scheme delivery error: " + str(e))
        return False


def get_scheme_deliveries(phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM scheme_deliveries WHERE phone=:phone ORDER BY created_at DESC"
            ), {"phone": phone}).fetchall()
            return [{"scheme_name": r.scheme_name, "amount": r.amount,
                     "delivered_by": r.delivered_by, "date": r.delivery_date} for r in rows]
    except Exception as e:
        print("Get scheme deliveries error: " + str(e))
        return []


# =================================================================
# POSTPARTUM + CHILD HEALTH (Month 4)
# =================================================================

def save_delivery_record(phone, delivery_date, birth_weight="",
                         delivery_mode="", facility="", asha_id=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO deliveries (phone,delivery_date,birth_weight,delivery_mode,facility,asha_id)"
                " VALUES (:phone,:delivery_date,:birth_weight,:delivery_mode,:facility,:asha_id)"
                " ON CONFLICT (phone) DO UPDATE SET"
                " delivery_date=:delivery_date, birth_weight=:birth_weight,"
                " delivery_mode=:delivery_mode, facility=:facility"
            ), {"phone": phone, "delivery_date": delivery_date, "birth_weight": birth_weight,
                "delivery_mode": delivery_mode, "facility": facility, "asha_id": asha_id})
            conn.commit()
        update_patient_status(phone, "postpartum")
        return True
    except Exception as e:
        print("Save delivery record error: " + str(e))
        return False


def get_delivery_record(phone):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT * FROM deliveries WHERE phone=:phone"), {"phone": phone}).fetchone()
            if r:
                return {"phone": r.phone, "delivery_date": r.delivery_date,
                        "birth_weight": r.birth_weight, "delivery_mode": r.delivery_mode,
                        "facility": r.facility, "asha_id": r.asha_id}
            return None
    except Exception as e:
        print("Get delivery record error: " + str(e))
        return None


def save_child(mother_phone, child_name, dob, gender, birth_weight="", asha_id=""):
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            r = conn.execute(text(
                "INSERT INTO children (mother_phone,child_name,dob,gender,birth_weight,asha_id)"
                " VALUES (:mother_phone,:child_name,:dob,:gender,:birth_weight,:asha_id) RETURNING id"
            ), {"mother_phone": mother_phone, "child_name": child_name, "dob": dob,
                "gender": gender, "birth_weight": birth_weight, "asha_id": asha_id})
            child_id = r.fetchone()[0]
            conn.commit()
            return child_id
    except Exception as e:
        print("Save child error: " + str(e))
        return None


def get_children(mother_phone):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM children WHERE mother_phone=:phone ORDER BY dob ASC"
            ), {"phone": mother_phone}).fetchall()
            return [{"id": r.id, "child_name": r.child_name, "dob": r.dob,
                     "gender": r.gender, "birth_weight": r.birth_weight} for r in rows]
    except Exception as e:
        print("Get children error: " + str(e))
        return []


def save_growth_log(child_id, mother_phone, weight_kg, height_cm,
                    age_months, z_score=None, status=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO child_growth_logs"
                " (child_id,mother_phone,weight_kg,height_cm,age_months,log_date,z_score,status)"
                " VALUES (:child_id,:mother_phone,:weight_kg,:height_cm,:age_months,:log_date,:z_score,:status)"
            ), {"child_id": child_id, "mother_phone": mother_phone,
                "weight_kg": weight_kg, "height_cm": height_cm, "age_months": age_months,
                "log_date": datetime.now().strftime("%d %b %Y"), "z_score": z_score, "status": status})
            conn.commit()
            return True
    except Exception as e:
        print("Save growth log error: " + str(e))
        return False


def get_growth_logs(child_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM child_growth_logs WHERE child_id=:child_id ORDER BY age_months ASC"
            ), {"child_id": child_id}).fetchall()
            return [{"age_months": r.age_months, "weight_kg": r.weight_kg,
                     "height_cm": r.height_cm, "z_score": r.z_score,
                     "status": r.status, "log_date": r.log_date} for r in rows]
    except Exception as e:
        print("Get growth logs error: " + str(e))
        return []


def save_immunization_record(child_id, mother_phone, vaccine_name,
                              dose_number, given_date, due_date="", given_by=""):
    if not engine:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO immunization_records"
                " (child_id,mother_phone,vaccine_name,dose_number,given_date,due_date,given_by)"
                " VALUES (:child_id,:mother_phone,:vaccine_name,:dose_number,:given_date,:due_date,:given_by)"
            ), {"child_id": child_id, "mother_phone": mother_phone, "vaccine_name": vaccine_name,
                "dose_number": dose_number, "given_date": given_date,
                "due_date": due_date, "given_by": given_by})
            conn.commit()
            return True
    except Exception as e:
        print("Save immunization record error: " + str(e))
        return False


def get_immunization_records(child_id):
    if not engine:
        return []
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT * FROM immunization_records WHERE child_id=:child_id ORDER BY given_date ASC"
            ), {"child_id": child_id}).fetchall()
            return [{"vaccine_name": r.vaccine_name, "dose_number": r.dose_number,
                     "given_date": r.given_date, "due_date": r.due_date,
                     "given_by": r.given_by} for r in rows]
    except Exception as e:
        print("Get immunization records error: " + str(e))
        return []


def get_postpartum_patients_due(asha_id):
    if not engine:
        return []
    pnc_days = [1, 3, 7, 14, 42]
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT p.name, p.phone, d.delivery_date, d.birth_weight"
                " FROM patients p JOIN deliveries d ON p.phone = d.phone"
                " WHERE p.asha_id=:asha_id AND p.status='postpartum'"
                " ORDER BY d.delivery_date DESC"
            ), {"asha_id": asha_id}).fetchall()

        due_today = []
        today = datetime.now().date()
        for r in rows:
            try:
                ddate      = datetime.strptime(r.delivery_date, "%d %b %Y").date()
                days_since = (today - ddate).days
                if days_since in pnc_days:
                    due_today.append({
                        "name":          r.name,
                        "phone":         r.phone,
                        "delivery_date": r.delivery_date,
                        "birth_weight":  r.birth_weight,
                        "days_since":    days_since
                    })
            except (ValueError, TypeError):
                continue
        return due_today
    except Exception as e:
        print("Get postpartum patients due error: " + str(e))
        return []
