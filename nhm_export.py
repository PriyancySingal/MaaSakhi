# ─────────────────────────────────────────────────────────────────
# MaaSakhi — nhm_export.py
# NHM / HMIS Data Export Engine (Month 3)
#
# Generates multiple export formats for the National Health Mission:
#   • export_patient_csv()       — HMIS mother registration format
#   • export_anc_csv()           — ANC visit register (Form 14)
#   • export_delivery_csv()      — Delivery register
#   • export_child_csv()         — Child health / immunization
#   • export_asha_csv()          — ASHA performance register
#   • export_alert_csv()         — Alert + escalation audit log
#   • export_scheme_csv()        — Scheme delivery register
#   • export_full_zip()          — All exports in one ZIP
#   • generate_nhm_summary()     — Summary dict for PDF / admin panel
#
# All functions return bytes (CSV / ZIP) safe to stream directly.
# ─────────────────────────────────────────────────────────────────

import csv
import io
import zipfile
from datetime import datetime, date


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _csv_bytes(headers: list, rows: list) -> bytes:
    """Write headers + rows to CSV and return UTF-8 bytes with BOM."""
    buf = io.StringIO()
    w   = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    w.writerow(headers)
    w.writerows(rows)
    # UTF-8 BOM so Excel opens it correctly
    return ("\ufeff" + buf.getvalue()).encode("utf-8")


def _safe(val, default="") -> str:
    """Convert any value to a clean string, replacing None."""
    if val is None:
        return default
    return str(val).strip()


def _fmt_date(val) -> str:
    """Format a date / datetime to DD/MM/YYYY."""
    if val is None:
        return ""
    if hasattr(val, "strftime"):
        return val.strftime("%d/%m/%Y")
    # Try to parse common string formats
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(val), fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return str(val)


def _month_range(month: int, year: int):
    """Return (start_date, end_date) for a calendar month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _filename(prefix: str, month: int = None, year: int = None) -> str:
    now = datetime.now()
    m   = month or now.month
    y   = year  or now.year
    return f"MaaSakhi_{prefix}_{y}_{m:02d}.csv"


# ─────────────────────────────────────────────────────────────────
# 1. PATIENT / MOTHER REGISTRATION  (HMIS Form 3)
# ─────────────────────────────────────────────────────────────────

PATIENT_HEADERS = [
    "Mother_ID",
    "Mother_Name",
    "Village",
    "Block_Name",
    "District",
    "Registration_Date",
    "Gestational_Weeks_at_Registration",
    "Assigned_ASHA_ID",
    "Assigned_ASHA_Name",
    "Supervisor_ID",
    "Supervisor_Name",
    "BMO_ID",
    "Language",
    "Status",
    "Address",
    "Phone",
]


def export_patient_csv(month: int = None, year: int = None) -> bytes:
    """
    All registered patients in NHM HMIS mother registration format.
    If month/year given, filter to patients registered in that period.
    Otherwise exports all-time.
    """
    from database import engine
    if not engine:
        return _csv_bytes(PATIENT_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    p.phone,
                    p.name,
                    p.village,
                    p.block_name,
                    p.district,
                    p.created_at,
                    p.week,
                    p.asha_id,
                    aw.name        AS asha_name,
                    p.supervisor_id,
                    s.name         AS supervisor_name,
                    p.bmo_id,
                    p.language,
                    p.status,
                    p.address
                FROM patients p
                LEFT JOIN asha_workers     aw ON aw.asha_id       = p.asha_id
                LEFT JOIN asha_supervisors s  ON s.supervisor_id  = p.supervisor_id
                WHERE p.step = 'registered'
                ORDER BY p.district, p.village, p.name
            """)).fetchall()

        data = []
        for r in rows:
            data.append([
                _safe(r.phone),
                _safe(r.name),
                _safe(r.village),
                _safe(r.block_name),
                _safe(r.district),
                _fmt_date(r.created_at),
                _safe(r.week),
                _safe(r.asha_id),
                _safe(r.asha_name),
                _safe(r.supervisor_id),
                _safe(r.supervisor_name),
                _safe(r.bmo_id),
                _safe(r.language),
                _safe(r.status, "active"),
                _safe(r.address),
                _safe(r.phone),    # phone doubled as contact field
            ])

        return _csv_bytes(PATIENT_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_patient_csv error: {e}")
        return _csv_bytes(PATIENT_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 2. ANC VISIT REGISTER  (HMIS Form 14)
# ─────────────────────────────────────────────────────────────────

ANC_HEADERS = [
    "Mother_ID",
    "Mother_Name",
    "Village",
    "Block_Name",
    "District",
    "Gestational_Weeks",
    "ANC_Visit_Number",
    "ANC_Visit_Date",
    "ASHA_ID",
    "ASHA_Name",
    "Notes",
    "Record_Created_At",
]


def export_anc_csv(month: int = None, year: int = None) -> bytes:
    """ANC visit records in NHM Form 14 format."""
    from database import engine
    if not engine:
        return _csv_bytes(ANC_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    ar.phone,
                    p.name,
                    p.village,
                    p.block_name,
                    p.district,
                    p.week,
                    ar.visit_number,
                    ar.visit_date,
                    ar.asha_id,
                    aw.name   AS asha_name,
                    ar.notes,
                    ar.created_at
                FROM anc_records ar
                LEFT JOIN patients     p  ON p.phone   = ar.phone
                LEFT JOIN asha_workers aw ON aw.asha_id = ar.asha_id
                WHERE ar.created_at >= :s AND ar.created_at < :e
                ORDER BY ar.created_at DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.phone), _safe(r.name), _safe(r.village),
            _safe(r.block_name), _safe(r.district), _safe(r.week),
            _safe(r.visit_number), _fmt_date(r.visit_date),
            _safe(r.asha_id), _safe(r.asha_name),
            _safe(r.notes), _fmt_date(r.created_at),
        ] for r in rows]

        return _csv_bytes(ANC_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_anc_csv error: {e}")
        return _csv_bytes(ANC_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 3. DELIVERY REGISTER  (HMIS Form 10)
# ─────────────────────────────────────────────────────────────────

DELIVERY_HEADERS = [
    "Mother_ID",
    "Mother_Name",
    "Village",
    "Block_Name",
    "District",
    "Delivery_Date",
    "Birth_Weight_Kg",
    "Delivery_Mode",
    "Delivery_Facility",
    "ASHA_ID",
    "ASHA_Name",
    "Current_Status",
    "Record_Created_At",
]


def export_delivery_csv(month: int = None, year: int = None) -> bytes:
    """Delivery records in NHM Form 10 format."""
    from database import engine
    if not engine:
        return _csv_bytes(DELIVERY_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    d.phone,
                    p.name,
                    p.village,
                    p.block_name,
                    p.district,
                    d.delivery_date,
                    d.birth_weight,
                    d.delivery_mode,
                    d.facility,
                    d.asha_id,
                    aw.name    AS asha_name,
                    p.status,
                    d.created_at
                FROM deliveries d
                LEFT JOIN patients     p  ON p.phone   = d.phone
                LEFT JOIN asha_workers aw ON aw.asha_id = d.asha_id
                WHERE d.created_at >= :s AND d.created_at < :e
                ORDER BY d.delivery_date DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.phone), _safe(r.name), _safe(r.village),
            _safe(r.block_name), _safe(r.district),
            _fmt_date(r.delivery_date), _safe(r.birth_weight),
            _safe(r.delivery_mode, "Normal"), _safe(r.facility),
            _safe(r.asha_id), _safe(r.asha_name),
            _safe(r.status, "postpartum"), _fmt_date(r.created_at),
        ] for r in rows]

        return _csv_bytes(DELIVERY_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_delivery_csv error: {e}")
        return _csv_bytes(DELIVERY_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 4. CHILD HEALTH + IMMUNIZATION  (RCH Register)
# ─────────────────────────────────────────────────────────────────

CHILD_HEADERS = [
    "Child_ID",
    "Child_Name",
    "Mother_ID",
    "Mother_Name",
    "Date_of_Birth",
    "Gender",
    "Birth_Weight_Kg",
    "Village",
    "District",
    "ASHA_ID",
    "BCG_Given",
    "OPV0_Given",
    "Pentavalent1_Given",
    "Pentavalent2_Given",
    "Pentavalent3_Given",
    "MR1_Given",
    "MR2_Given",
    "DPT_Booster_Given",
    "Total_Vaccines_Given",
    "Latest_Weight_Kg",
    "Latest_Age_Months",
    "Latest_Z_Score",
    "Nutrition_Status",
]


def export_child_csv(month: int = None, year: int = None) -> bytes:
    """Child health and immunization records in RCH format."""
    from database import engine
    if not engine:
        return _csv_bytes(CHILD_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year

    # Key vaccines to track (column order matches CHILD_HEADERS)
    VACCINE_COLS = [
        "BCG", "OPV-0", "Pentavalent-1",
        "Pentavalent-2", "Pentavalent-3",
        "Measles-Rubella-1", "Measles-Rubella-2", "DPT-Booster",
    ]

    try:
        with engine.connect() as conn:
            children = conn.execute(text("""
                SELECT
                    c.id, c.child_name, c.mother_phone, c.dob,
                    c.gender, c.birth_weight, c.asha_id,
                    p.name   AS mother_name,
                    p.village, p.district
                FROM children c
                LEFT JOIN patients p ON p.phone = c.mother_phone
                ORDER BY c.created_at DESC
            """)).fetchall()

            data = []
            for c in children:
                # Get all vaccines for this child
                vacc_rows = conn.execute(text("""
                    SELECT vaccine_name FROM immunization_records
                    WHERE child_id = :cid
                """), {"cid": c.id}).fetchall()
                given_set = {r.vaccine_name for r in vacc_rows}
                total_vax = len(given_set)

                # Latest growth log
                growth = conn.execute(text("""
                    SELECT weight_kg, age_months, z_score, status
                    FROM child_growth_logs
                    WHERE child_id = :cid
                    ORDER BY age_months DESC LIMIT 1
                """), {"cid": c.id}).fetchone()

                vax_flags = ["Yes" if v in given_set else "No" for v in VACCINE_COLS]

                data.append([
                    _safe(c.id),
                    _safe(c.child_name),
                    _safe(c.mother_phone),
                    _safe(c.mother_name),
                    _fmt_date(c.dob),
                    _safe(c.gender),
                    _safe(c.birth_weight),
                    _safe(c.village),
                    _safe(c.district),
                    _safe(c.asha_id),
                    *vax_flags,
                    str(total_vax),
                    _safe(growth.weight_kg   if growth else ""),
                    _safe(growth.age_months  if growth else ""),
                    _safe(growth.z_score     if growth else ""),
                    _safe(growth.status      if growth else ""),
                ])

        return _csv_bytes(CHILD_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_child_csv error: {e}")
        return _csv_bytes(CHILD_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 5. ASHA PERFORMANCE REGISTER
# ─────────────────────────────────────────────────────────────────

ASHA_PERF_HEADERS = [
    "ASHA_ID",
    "ASHA_Name",
    "Phone",
    "Village",
    "Block_Name",
    "District",
    "Supervisor_Name",
    "Is_Active",
    "Total_Patients",
    "Alerts_This_Month",
    "Resolved_This_Month",
    "Escalated_This_Month",
    "Visits_This_Month",
    "ANC_Visits_Logged",
    "Scheme_Deliveries",
    "Resolution_Rate_Pct",
    "Avg_Response_Hrs",
    "Performance_Rating",
    "Composite_Score",
]


def export_asha_csv(month: int = None, year: int = None) -> bytes:
    """ASHA performance data using the performance engine."""
    from database import get_all_asha_workers

    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year

    try:
        from performance import calc_asha_metrics
        ashas = [a for a in get_all_asha_workers() if a.get("is_active")]
        data  = []

        for a in ashas:
            m = calc_asha_metrics(a["asha_id"], days=31)
            data.append([
                _safe(a["asha_id"]),
                _safe(a["name"]),
                _safe(a["phone"]),
                _safe(a["village"]),
                _safe(a.get("block_name", "")),
                _safe(a.get("district", "")),
                _safe(m.get("supervisor_name", "")),
                "Yes" if a.get("is_active") else "No",
                _safe(m["total_patients"]),
                _safe(m["total_alerts"]),
                _safe(m["resolved_alerts"]),
                _safe(m["escalated_alerts"]),
                _safe(m["visit_count"]),
                _safe(m["total_anc_visits"]),
                _safe(m["total_scheme_deliveries"]),
                f"{m['resolution_rate']:.1f}",
                f"{m['avg_response_hrs']:.1f}" if m["avg_response_hrs"] else "",
                _safe(m["performance_rating"]),
                _safe(m["composite_score"]),
            ])

        return _csv_bytes(ASHA_PERF_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_asha_csv error: {e}")
        return _csv_bytes(ASHA_PERF_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 6. ALERT + ESCALATION AUDIT LOG
# ─────────────────────────────────────────────────────────────────

ALERT_HEADERS = [
    "Alert_ID",
    "Mother_ID",
    "Mother_Name",
    "Village",
    "Gestational_Weeks",
    "Symptom_Reported",
    "Alert_Status",
    "Escalation_Level",
    "ASHA_ID",
    "ASHA_Name",
    "Supervisor_ID",
    "BMO_ID",
    "Maps_Link",
    "Alert_Raised_At",
    "Escalated_At",
    "Resolved_Notes",
]


def export_alert_csv(month: int = None, year: int = None) -> bytes:
    """Full alert and escalation audit log."""
    from database import engine
    if not engine:
        return _csv_bytes(ALERT_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    aa.id, aa.phone, aa.name, aa.week,
                    aa.symptom, aa.status,
                    aa.escalation_level,
                    aa.asha_id,
                    aw.name        AS asha_name,
                    aa.supervisor_id, aa.bmo_id,
                    aa.maps_link,
                    aa.created_at,
                    aa.escalated_at,
                    aa.resolved_notes,
                    p.village
                FROM asha_alerts aa
                LEFT JOIN asha_workers aw ON aw.asha_id = aa.asha_id
                LEFT JOIN patients     p  ON p.phone    = aa.phone
                WHERE aa.created_at >= :s AND aa.created_at < :e
                ORDER BY aa.created_at DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.id),
            _safe(r.phone),
            _safe(r.name),
            _safe(r.village),
            _safe(r.week),
            _safe(r.symptom)[:120],
            _safe(r.status),
            _safe(r.escalation_level, "0"),
            _safe(r.asha_id),
            _safe(r.asha_name),
            _safe(r.supervisor_id),
            _safe(r.bmo_id),
            _safe(r.maps_link),
            _fmt_date(r.created_at),
            _fmt_date(r.escalated_at),
            _safe(r.resolved_notes),
        ] for r in rows]

        return _csv_bytes(ALERT_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_alert_csv error: {e}")
        return _csv_bytes(ALERT_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 7. SCHEME DELIVERY REGISTER
# ─────────────────────────────────────────────────────────────────

SCHEME_HEADERS = [
    "Record_ID",
    "Mother_ID",
    "Mother_Name",
    "Village",
    "District",
    "Scheme_Name",
    "Benefit_Amount",
    "Delivered_By_ASHA",
    "Delivery_Date",
    "Record_Created_At",
]


def export_scheme_csv(month: int = None, year: int = None) -> bytes:
    """Govt scheme delivery register."""
    from database import engine
    if not engine:
        return _csv_bytes(SCHEME_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    sd.id,
                    sd.phone,
                    sd.patient_name,
                    p.village,
                    p.district,
                    sd.scheme_name,
                    sd.amount,
                    sd.delivered_by,
                    sd.delivery_date,
                    sd.created_at
                FROM scheme_deliveries sd
                LEFT JOIN patients p ON p.phone = sd.phone
                WHERE sd.created_at >= :s AND sd.created_at < :e
                ORDER BY sd.created_at DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.id),
            _safe(r.phone),
            _safe(r.patient_name),
            _safe(r.village),
            _safe(r.district),
            _safe(r.scheme_name),
            _safe(r.amount),
            _safe(r.delivered_by),
            _fmt_date(r.delivery_date),
            _fmt_date(r.created_at),
        ] for r in rows]

        return _csv_bytes(SCHEME_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_scheme_csv error: {e}")
        return _csv_bytes(SCHEME_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 8. SYMPTOM LOG EXPORT
# ─────────────────────────────────────────────────────────────────

SYMPTOM_HEADERS = [
    "Log_ID",
    "Mother_ID",
    "Mother_Name",
    "Village",
    "Gestational_Weeks",
    "Message",
    "Risk_Level",
    "Logged_At",
]


def export_symptom_csv(month: int = None, year: int = None) -> bytes:
    """Symptom log export — useful for NHM disease surveillance."""
    from database import engine
    if not engine:
        return _csv_bytes(SYMPTOM_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    sl.id, sl.phone, p.name, p.village,
                    sl.week, sl.message, sl.level, sl.created_at
                FROM symptom_logs sl
                LEFT JOIN patients p ON p.phone = sl.phone
                WHERE sl.created_at >= :s AND sl.created_at < :e
                ORDER BY sl.created_at DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.id), _safe(r.phone), _safe(r.name),
            _safe(r.village), _safe(r.week),
            _safe(r.message)[:100],
            _safe(r.level), _fmt_date(r.created_at),
        ] for r in rows]

        return _csv_bytes(SYMPTOM_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_symptom_csv error: {e}")
        return _csv_bytes(SYMPTOM_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 9. VILLAGE RISK SUMMARY EXPORT
# ─────────────────────────────────────────────────────────────────

VILLAGE_HEADERS = [
    "Village",
    "Block_Name",
    "District",
    "Total_Patients",
    "Active_Alerts",
    "Resolved_Alerts",
    "Avg_Risk_Score",
    "Risk_Level",
    "Total_ANC_Visits",
    "Total_Deliveries",
]


def export_village_csv() -> bytes:
    """Village-level risk and health summary."""
    from database import engine
    if not engine:
        return _csv_bytes(VILLAGE_HEADERS, [])

    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT
                    p.village,
                    p.block_name,
                    p.district,
                    COUNT(DISTINCT p.phone)                                     AS patients,
                    COUNT(DISTINCT CASE WHEN aa.status != 'Resolved'
                          THEN aa.id END)                                       AS active_alerts,
                    COUNT(DISTINCT CASE WHEN aa.status = 'Resolved'
                          THEN aa.id END)                                       AS resolved_alerts,
                    AVG(CASE WHEN sl.level='RED'   THEN 40
                             WHEN sl.level='AMBER' THEN 15
                             ELSE 2 END)                                        AS avg_risk,
                    COUNT(DISTINCT ar.id)                                       AS anc_visits,
                    COUNT(DISTINCT d.id)                                        AS deliveries
                FROM patients p
                LEFT JOIN asha_alerts  aa ON aa.phone = p.phone
                LEFT JOIN symptom_logs sl ON sl.phone = p.phone
                LEFT JOIN anc_records  ar ON ar.phone = p.phone
                LEFT JOIN deliveries    d ON d.phone  = p.phone
                WHERE p.step = 'registered'
                GROUP BY p.village, p.block_name, p.district
                ORDER BY avg_risk DESC NULLS LAST
            """)).fetchall()

        data = []
        for r in rows:
            score = round(float(r.avg_risk), 1) if r.avg_risk else 0.0
            level = (
                "HIGH"   if score >= 30 else
                "MEDIUM" if score >= 12 else
                "LOW"
            )
            data.append([
                _safe(r.village),
                _safe(r.block_name),
                _safe(r.district),
                int(r.patients),
                int(r.active_alerts   or 0),
                int(r.resolved_alerts or 0),
                score,
                level,
                int(r.anc_visits   or 0),
                int(r.deliveries   or 0),
            ])

        return _csv_bytes(VILLAGE_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_village_csv error: {e}")
        return _csv_bytes(VILLAGE_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 10. ESCALATION AUDIT TRAIL
# ─────────────────────────────────────────────────────────────────

ESCALATION_HEADERS = [
    "Log_ID",
    "Alert_ID",
    "From_Role",
    "To_Role",
    "To_Phone",
    "Reason",
    "Escalated_At",
]


def export_escalation_log_csv(month: int = None, year: int = None) -> bytes:
    """Full escalation audit trail."""
    from database import engine
    if not engine:
        return _csv_bytes(ESCALATION_HEADERS, [])

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT id, alert_id, from_role, to_role,
                       to_phone, reason, sent_at
                FROM escalation_log
                WHERE sent_at >= :s AND sent_at < :e
                ORDER BY sent_at DESC
            """), {"s": start, "e": end}).fetchall()

        data = [[
            _safe(r.id), _safe(r.alert_id),
            _safe(r.from_role), _safe(r.to_role),
            _safe(r.to_phone), _safe(r.reason)[:100],
            _fmt_date(r.sent_at),
        ] for r in rows]

        return _csv_bytes(ESCALATION_HEADERS, data)

    except Exception as e:
        print(f"nhm_export export_escalation_log_csv error: {e}")
        return _csv_bytes(ESCALATION_HEADERS, [])


# ─────────────────────────────────────────────────────────────────
# 11. FULL ZIP — all exports bundled
# ─────────────────────────────────────────────────────────────────

def export_full_zip(month: int = None, year: int = None,
                    district: str = "District") -> bytes:
    """
    Bundle all CSV exports into a single ZIP file.
    Returns bytes ready to stream as application/zip.

    Includes:
      • patients.csv
      • anc_visits.csv
      • deliveries.csv
      • children_immunization.csv
      • asha_performance.csv
      • alerts.csv
      • scheme_deliveries.csv
      • symptom_logs.csv
      • village_risk.csv
      • escalation_log.csv
      • README.txt
    """
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    label = datetime(year, month, 1).strftime("%B_%Y")

    exports = [
        (f"01_patients_{label}.csv",                export_patient_csv(month, year)),
        (f"02_anc_visits_{label}.csv",              export_anc_csv(month, year)),
        (f"03_deliveries_{label}.csv",              export_delivery_csv(month, year)),
        (f"04_children_immunization_{label}.csv",   export_child_csv(month, year)),
        (f"05_asha_performance_{label}.csv",        export_asha_csv(month, year)),
        (f"06_alerts_{label}.csv",                  export_alert_csv(month, year)),
        (f"07_scheme_deliveries_{label}.csv",       export_scheme_csv(month, year)),
        (f"08_symptom_logs_{label}.csv",            export_symptom_csv(month, year)),
        (f"09_village_risk_summary.csv",            export_village_csv()),
        (f"10_escalation_log_{label}.csv",          export_escalation_log_csv(month, year)),
    ]

    readme = _build_readme(month, year, district, now)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        for fname, csv_bytes in exports:
            zf.writestr(fname, csv_bytes)

    buf.seek(0)
    return buf.read()


def _build_readme(month: int, year: int, district: str,
                  generated_at: datetime) -> str:
    label = datetime(year, month, 1).strftime("%B %Y")
    return f"""MaaSakhi — NHM Data Export Package
=====================================

Reporting Period : {label}
District         : {district}
Generated At     : {generated_at.strftime("%d %b %Y, %I:%M %p")}
System           : MaaSakhi v2.0 — AI-Powered Maternal Health Monitoring

FILES INCLUDED
--------------
01_patients_*.csv               All registered pregnant women (HMIS Form 3)
02_anc_visits_*.csv             Antenatal care visit register (HMIS Form 14)
03_deliveries_*.csv             Institutional/home delivery register (HMIS Form 10)
04_children_immunization_*.csv  Child health + RCH immunization register
05_asha_performance_*.csv       ASHA worker performance + activity report
06_alerts_*.csv                 High-risk alert + escalation log
07_scheme_deliveries_*.csv      Government scheme benefit delivery register
08_symptom_logs_*.csv           Patient symptom reporting log
09_village_risk_summary.csv     Village-level risk aggregation (all-time)
10_escalation_log_*.csv         Full escalation audit trail

COLUMN REFERENCE
----------------
Mother_ID        : Patient WhatsApp phone number (unique identifier)
ASHA_ID          : ASHA worker's unique system ID
Risk_Level       : LOW / MEDIUM / HIGH (based on symptom scoring)
Resolution_Rate  : Percentage of alerts resolved by ASHA without escalation
Avg_Risk_Score   : Weighted average — RED=40, AMBER=15, GREEN=2 points
Performance_Rating: GREEN / AMBER / RED — see system documentation

DATA NOTES
----------
- All dates are in DD/MM/YYYY format
- Phone numbers are patient WhatsApp identifiers (may include country code)
- Files are UTF-8 encoded with BOM for Excel compatibility
- Village risk scores are cumulative (all-time, not period-specific)
- ASHA performance metrics cover the reporting period only

GUIDELINES
----------
WHO ANC Guidelines (2016) | NHM RMNCH+A Framework | FOGSI Maternal Care
NHM HMIS Technical Manual v3.0

For support: Contact your District Health Officer
MaaSakhi System — Empowering Every Mother in Rural India
"""


# ─────────────────────────────────────────────────────────────────
# 12. SUMMARY DICT — for admin panel display
# ─────────────────────────────────────────────────────────────────

def generate_nhm_summary(month: int = None, year: int = None) -> dict:
    """
    Returns a structured summary dict for the admin panel export tab.
    Used by analytics.py and admin.py to show NHM submission stats.
    """
    from database import engine
    if not engine:
        return {}

    from sqlalchemy import text
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year
    start, end = _month_range(month, year)

    summary = {
        "month_label":              datetime(year, month, 1).strftime("%B %Y"),
        "generated_at":             now.strftime("%d %b %Y, %I:%M %p"),
        "total_patients":           0,
        "new_registrations":        0,
        "anc1_coverage":            0,
        "anc4_coverage":            0,
        "institutional_deliveries": 0,
        "high_risk_identified":     0,
        "cases_resolved":           0,
        "asha_active":              0,
        "scheme_deliveries":        0,
        "children_tracked":         0,
        "vaccines_given":           0,
    }

    try:
        with engine.connect() as conn:
            summary["total_patients"] = conn.execute(text(
                "SELECT COUNT(*) FROM patients WHERE step='registered'"
            )).scalar() or 0

            summary["new_registrations"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients
                WHERE step='registered' AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            summary["anc1_coverage"] = conn.execute(text(
                "SELECT COUNT(DISTINCT phone) FROM anc_records WHERE visit_number=1"
            )).scalar() or 0

            summary["anc4_coverage"] = conn.execute(text(
                "SELECT COUNT(DISTINCT phone) FROM anc_records WHERE visit_number=4"
            )).scalar() or 0

            summary["institutional_deliveries"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
                WHERE created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            summary["high_risk_identified"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE escalation_level > 0
                  AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            summary["cases_resolved"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE status='Resolved'
                  AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            summary["asha_active"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_workers WHERE is_active=TRUE"
            )).scalar() or 0

            summary["scheme_deliveries"] = conn.execute(text("""
                SELECT COUNT(*) FROM scheme_deliveries
                WHERE created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            summary["children_tracked"] = conn.execute(text(
                "SELECT COUNT(*) FROM children"
            )).scalar() or 0

            summary["vaccines_given"] = conn.execute(text(
                "SELECT COUNT(*) FROM immunization_records"
            )).scalar() or 0

    except Exception as e:
        print(f"nhm_export generate_nhm_summary error: {e}")

    return summary


# ─────────────────────────────────────────────────────────────────
# SELF-TEST  (python nhm_export.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    now = datetime.now()
    print(f"=== MaaSakhi nhm_export.py self-test — {now.strftime('%B %Y')} ===\n")

    tests = [
        ("Patient CSV",          export_patient_csv),
        ("ANC CSV",              export_anc_csv),
        ("Delivery CSV",         export_delivery_csv),
        ("Child/Immuniz. CSV",   export_child_csv),
        ("ASHA Performance CSV", export_asha_csv),
        ("Alert CSV",            export_alert_csv),
        ("Scheme CSV",           export_scheme_csv),
        ("Symptom Log CSV",      export_symptom_csv),
        ("Village Risk CSV",     lambda: export_village_csv()),
        ("Escalation Log CSV",   export_escalation_log_csv),
    ]

    for name, fn in tests:
        try:
            b = fn() if name == "Village Risk CSV" else fn(now.month, now.year)
            lines = b.decode("utf-8-sig").strip().split("\n")
            print(f"  ✓ {name:<28} {len(b):>7,} bytes  |  {len(lines)-1} data rows")
        except Exception as e:
            print(f"  ✗ {name}: {e}")

    print("\nGenerating full ZIP...")
    try:
        zb = export_full_zip(now.month, now.year, "Test District")
        with open("/tmp/maasakhi_nhm_export.zip", "wb") as f:
            f.write(zb)
        print(f"  ✓ ZIP: {len(zb):,} bytes → /tmp/maasakhi_nhm_export.zip")
    except Exception as e:
        print(f"  ✗ ZIP error: {e}")

    print("\nSummary dict:")
    s = generate_nhm_summary()
    for k, v in s.items():
        print(f"  {k:<30} {v}")

    print("\nSelf-test complete.")