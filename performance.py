# ─────────────────────────────────────────────────────────────────
# MaaSakhi — performance.py
# ASHA Worker Performance Engine
#
# Responsibilities:
#   • calc_asha_metrics()      — per-ASHA stats for any period
#   • calc_block_metrics()     — supervisor-level aggregate
#   • calc_district_metrics()  — DHO-level aggregate
#   • get_performance_rating() — GREEN / AMBER / RED classification
#   • render_performance()     — standalone HTML page for admin
#   • leaderboard_data()       — ranked list for dashboards
# ─────────────────────────────────────────────────────────────────

from datetime import datetime, timedelta
from flask import render_template_string

# ─────────────────────────────────────────────────────────────────
# THRESHOLDS  (tune these as programme matures)
# ─────────────────────────────────────────────────────────────────

THRESHOLDS = {
    # Average response time in hours
    "response_green":      1.0,   # ≤ 1 hr  → GREEN
    "response_amber":      3.0,   # ≤ 3 hrs → AMBER; else RED

    # Resolution rate %
    "resolution_green":    80.0,  # ≥ 80% → GREEN
    "resolution_amber":    50.0,  # ≥ 50% → AMBER; else RED

    # Escalation rate %
    "escalation_green":    10.0,  # ≤ 10% → GREEN
    "escalation_amber":    30.0,  # ≤ 30% → AMBER; else RED

    # Visit completion rate (visits / total alerts %)
    "visit_green":         70.0,
    "visit_amber":         40.0,
}


# ─────────────────────────────────────────────────────────────────
# RATING HELPER
# ─────────────────────────────────────────────────────────────────

def get_performance_rating(
    resolution_rate:  float,
    avg_response_hrs: float | None,
    escalation_rate:  float,
) -> str:
    """
    Composite performance rating.
    Returns 'GREEN', 'AMBER', 'RED', or 'unknown' (no data).

    Scoring:
      3 × GREEN  → GREEN
      Any RED    → RED
      Otherwise  → AMBER
    """
    if avg_response_hrs is None and resolution_rate == 0:
        return "unknown"

    def _rate_response(h):
        if h is None:
            return "unknown"
        if h <= THRESHOLDS["response_green"]:
            return "GREEN"
        if h <= THRESHOLDS["response_amber"]:
            return "AMBER"
        return "RED"

    def _rate_resolution(r):
        if r >= THRESHOLDS["resolution_green"]:
            return "GREEN"
        if r >= THRESHOLDS["resolution_amber"]:
            return "AMBER"
        return "RED"

    def _rate_escalation(e):
        if e <= THRESHOLDS["escalation_green"]:
            return "GREEN"
        if e <= THRESHOLDS["escalation_amber"]:
            return "AMBER"
        return "RED"

    ratings = [
        _rate_response(avg_response_hrs),
        _rate_resolution(resolution_rate),
        _rate_escalation(escalation_rate),
    ]

    if "RED" in ratings:
        return "RED"
    greens = sum(1 for r in ratings if r == "GREEN")
    if greens >= 2:
        return "GREEN"
    return "AMBER"


# ─────────────────────────────────────────────────────────────────
# PER-ASHA METRICS
# ─────────────────────────────────────────────────────────────────

def calc_asha_metrics(asha_id: str, days: int = 30) -> dict:
    """
    Compute comprehensive performance metrics for a single ASHA worker
    over the last `days` days.

    Returns a flat dict with all metrics + derived fields.
    Always safe to call — returns zero-filled dict on DB error.
    """
    from database import engine
    if not engine:
        return _empty_metrics(asha_id)

    from sqlalchemy import text
    m = _empty_metrics(asha_id)
    interval = f"{days} days"

    try:
        with engine.connect() as conn:

            # ── Identity ──────────────────────────────────────────
            row = conn.execute(text("""
                SELECT aw.asha_id, aw.name, aw.phone, aw.village,
                       aw.block_name, aw.district, aw.is_active,
                       s.name AS supervisor_name,
                       s.supervisor_id
                FROM asha_workers aw
                LEFT JOIN asha_supervisors s
                    ON s.supervisor_id = aw.supervisor_id
                WHERE aw.asha_id = :id
            """), {"id": asha_id}).fetchone()

            if not row:
                return m

            m.update({
                "asha_id":         row.asha_id,
                "name":            row.name,
                "phone":           row.phone,
                "village":         row.village      or "",
                "block_name":      row.block_name   or "",
                "district":        row.district     or "",
                "is_active":       row.is_active,
                "supervisor_name": row.supervisor_name or "—",
                "supervisor_id":   row.supervisor_id   or "",
            })

            # ── Patient load ──────────────────────────────────────
            m["total_patients"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients
                WHERE asha_id = :id AND step = 'registered'
            """), {"id": asha_id}).scalar() or 0

            m["postpartum_patients"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients
                WHERE asha_id = :id AND status = 'postpartum'
            """), {"id": asha_id}).scalar() or 0

            # ── Alert stats (period) ──────────────────────────────
            m["total_alerts"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            m["pending_alerts"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id AND status = 'Pending'
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            m["attended_alerts"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id AND status = 'Attended'
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            m["resolved_alerts"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id AND status = 'Resolved'
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            m["escalated_alerts"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id AND escalation_level > 0
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            m["alerts_today"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE asha_id = :id AND DATE(created_at) = CURRENT_DATE
            """), {"id": asha_id}).scalar() or 0

            # ── Visit stats ───────────────────────────────────────
            m["visit_count"] = conn.execute(text(f"""
                SELECT COUNT(*) FROM asha_visits
                WHERE asha_id = :id
                  AND created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar() or 0

            # Visit outcomes breakdown
            outcome_rows = conn.execute(text(f"""
                SELECT outcome, COUNT(*) AS cnt
                FROM asha_visits
                WHERE asha_id = :id
                  AND created_at >= NOW() - INTERVAL '{interval}'
                GROUP BY outcome
            """), {"id": asha_id}).fetchall()
            m["visit_outcomes"] = {r.outcome: int(r.cnt) for r in outcome_rows}

            # ── Response time (minutes → hours) ───────────────────
            # Avg time from alert creation to first visit
            avg_resp = conn.execute(text(f"""
                SELECT AVG(
                    EXTRACT(EPOCH FROM (av.visit_time - aa.created_at)) / 3600.0
                )
                FROM asha_visits av
                JOIN asha_alerts aa ON av.alert_id = aa.id
                WHERE av.asha_id = :id
                  AND av.created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).scalar()
            m["avg_response_hrs"] = round(float(avg_resp), 2) if avg_resp else None

            # Fastest / slowest response
            resp_range = conn.execute(text(f"""
                SELECT
                    MIN(EXTRACT(EPOCH FROM (av.visit_time - aa.created_at))/3600.0) AS fastest,
                    MAX(EXTRACT(EPOCH FROM (av.visit_time - aa.created_at))/3600.0) AS slowest
                FROM asha_visits av
                JOIN asha_alerts aa ON av.alert_id = aa.id
                WHERE av.asha_id = :id
                  AND av.created_at >= NOW() - INTERVAL '{interval}'
            """), {"id": asha_id}).fetchone()
            if resp_range:
                m["fastest_response_hrs"] = round(float(resp_range.fastest), 2) if resp_range.fastest else None
                m["slowest_response_hrs"] = round(float(resp_range.slowest), 2) if resp_range.slowest else None

            # ── ANC records ───────────────────────────────────────
            anc_rows = conn.execute(text("""
                SELECT visit_number, COUNT(*) AS cnt
                FROM anc_records WHERE asha_id = :id
                GROUP BY visit_number
            """), {"id": asha_id}).fetchall()
            m["anc_by_visit"] = {int(r.visit_number): int(r.cnt) for r in anc_rows}
            m["total_anc_visits"] = sum(m["anc_by_visit"].values())

            # ── Scheme deliveries ─────────────────────────────────
            scheme_rows = conn.execute(text(f"""
                SELECT scheme_name, COUNT(*) AS cnt
                FROM scheme_deliveries
                WHERE delivered_by = :id
                  AND created_at >= NOW() - INTERVAL '{interval}'
                GROUP BY scheme_name
            """), {"id": asha_id}).fetchall()
            m["scheme_deliveries"]       = {r.scheme_name: int(r.cnt) for r in scheme_rows}
            m["total_scheme_deliveries"] = sum(m["scheme_deliveries"].values())

            # ── Day-by-day alert trend (last 14 days) ─────────────
            trend_rows = conn.execute(text("""
                SELECT DATE(created_at) AS day, COUNT(*) AS cnt
                FROM asha_alerts
                WHERE asha_id = :id
                  AND created_at >= NOW() - INTERVAL '14 days'
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """), {"id": asha_id}).fetchall()
            trend_map = {str(r.day): int(r.cnt) for r in trend_rows}
            today     = datetime.now().date()
            m["alert_trend_14d"] = [
                trend_map.get(str(today - timedelta(days=i)), 0)
                for i in range(13, -1, -1)
            ]

            # ── Symptom log stats ─────────────────────────────────
            sym_rows = conn.execute(text(f"""
                SELECT sl.level, COUNT(*) AS cnt
                FROM symptom_logs sl
                JOIN patients p ON p.phone = sl.phone
                WHERE p.asha_id = :id
                  AND sl.created_at >= NOW() - INTERVAL '{interval}'
                GROUP BY sl.level
            """), {"id": asha_id}).fetchall()
            m["symptom_levels"] = {r.level: int(r.cnt) for r in sym_rows}

    except Exception as e:
        print(f"performance.py calc_asha_metrics error ({asha_id}): {e}")
        return m

    # ── Derived metrics ───────────────────────────────────────────
    total = m["total_alerts"]
    m["resolution_rate"]  = round(m["resolved_alerts"]  / total * 100, 1) if total else 0.0
    m["escalation_rate"]  = round(m["escalated_alerts"] / total * 100, 1) if total else 0.0
    m["attendance_rate"]  = round(
        (m["attended_alerts"] + m["resolved_alerts"]) / total * 100, 1
    ) if total else 0.0
    m["visit_rate"]       = round(m["visit_count"] / total * 100, 1) if total else 0.0

    # Overall performance rating
    m["performance_rating"] = get_performance_rating(
        m["resolution_rate"],
        m["avg_response_hrs"],
        m["escalation_rate"],
    )

    # Score 0–100 for leaderboard sorting
    m["composite_score"] = _composite_score(m)

    return m


def _empty_metrics(asha_id: str = "") -> dict:
    return {
        "asha_id":              asha_id,
        "name":                 "",
        "phone":                "",
        "village":              "",
        "block_name":           "",
        "district":             "",
        "is_active":            True,
        "supervisor_name":      "—",
        "supervisor_id":        "",
        "total_patients":       0,
        "postpartum_patients":  0,
        "total_alerts":         0,
        "pending_alerts":       0,
        "attended_alerts":      0,
        "resolved_alerts":      0,
        "escalated_alerts":     0,
        "alerts_today":         0,
        "visit_count":          0,
        "visit_outcomes":       {},
        "avg_response_hrs":     None,
        "fastest_response_hrs": None,
        "slowest_response_hrs": None,
        "total_anc_visits":     0,
        "anc_by_visit":         {},
        "scheme_deliveries":    {},
        "total_scheme_deliveries": 0,
        "alert_trend_14d":      [0] * 14,
        "symptom_levels":       {},
        "resolution_rate":      0.0,
        "escalation_rate":      0.0,
        "attendance_rate":      0.0,
        "visit_rate":           0.0,
        "performance_rating":   "unknown",
        "composite_score":      0,
    }


def _composite_score(m: dict) -> int:
    """
    0–100 composite score for leaderboard ranking.
    Weighted: resolution 40 + response speed 30 + low escalation 20 + visits 10.
    """
    s = 0
    s += min(m["resolution_rate"], 100) * 0.40
    if m["avg_response_hrs"] is not None:
        speed = max(0, 100 - m["avg_response_hrs"] * 20)
        s += min(speed, 100) * 0.30
    esc_score = max(0, 100 - m["escalation_rate"] * 2)
    s += esc_score * 0.20
    s += min(m["visit_rate"], 100) * 0.10
    return round(s)


# ─────────────────────────────────────────────────────────────────
# BLOCK-LEVEL METRICS (for Supervisor dashboard)
# ─────────────────────────────────────────────────────────────────

def calc_block_metrics(supervisor_id: str, days: int = 30) -> dict:
    """
    Aggregate performance across all ASHA workers under a supervisor.
    Returns block-level summary + list of individual ASHA metrics.
    """
    from database import get_supervisor_ashas
    ashas = get_supervisor_ashas(supervisor_id)

    individual = [calc_asha_metrics(a["asha_id"], days) for a in ashas]

    if not individual:
        return {
            "individual":           [],
            "avg_resolution_rate":  0.0,
            "avg_response_hrs":     None,
            "avg_escalation_rate":  0.0,
            "total_visits":         0,
            "total_alerts":         0,
            "total_patients":       0,
            "top_performer":        None,
            "needs_support":        None,
            "block_rating":         "unknown",
        }

    res_rates  = [m["resolution_rate"]  for m in individual]
    esc_rates  = [m["escalation_rate"]  for m in individual]
    resp_hrs   = [m["avg_response_hrs"] for m in individual if m["avg_response_hrs"] is not None]

    avg_res    = round(sum(res_rates)  / len(res_rates),  1)
    avg_esc    = round(sum(esc_rates)  / len(esc_rates),  1)
    avg_resp   = round(sum(resp_hrs)   / len(resp_hrs),   2) if resp_hrs else None

    top  = max(individual, key=lambda m: m["composite_score"], default=None)
    weak = min(individual, key=lambda m: m["composite_score"], default=None)

    return {
        "individual":          individual,
        "avg_resolution_rate": avg_res,
        "avg_response_hrs":    avg_resp,
        "avg_escalation_rate": avg_esc,
        "total_visits":        sum(m["visit_count"]     for m in individual),
        "total_alerts":        sum(m["total_alerts"]    for m in individual),
        "total_patients":      sum(m["total_patients"]  for m in individual),
        "top_performer":       top,
        "needs_support":       weak if weak and weak["composite_score"] < 40 else None,
        "block_rating":        get_performance_rating(avg_res, avg_resp, avg_esc),
    }


# ─────────────────────────────────────────────────────────────────
# DISTRICT-LEVEL METRICS (for DHO / Admin)
# ─────────────────────────────────────────────────────────────────

def calc_district_metrics(days: int = 30) -> dict:
    """
    Aggregate performance across ALL active ASHA workers in district.
    Returns district-level summary for the admin analytics page.
    """
    from database import get_all_asha_workers
    all_ashas = get_all_asha_workers()
    active    = [a for a in all_ashas if a.get("is_active")]

    if not active:
        return {
            "total_ashas":        0,
            "avg_resolution_rate":0.0,
            "avg_response_hrs":   None,
            "avg_escalation_rate":0.0,
            "top_performers":     [],
            "underperformers":    [],
            "district_rating":    "unknown",
        }

    individual = [calc_asha_metrics(a["asha_id"], days) for a in active]

    res_rates = [m["resolution_rate"]  for m in individual]
    esc_rates = [m["escalation_rate"]  for m in individual]
    resp_hrs  = [m["avg_response_hrs"] for m in individual if m["avg_response_hrs"] is not None]

    avg_res   = round(sum(res_rates) / len(res_rates), 1)
    avg_esc   = round(sum(esc_rates) / len(esc_rates), 1)
    avg_resp  = round(sum(resp_hrs)  / len(resp_hrs),  2) if resp_hrs else None

    sorted_by_score = sorted(individual, key=lambda m: m["composite_score"], reverse=True)

    return {
        "total_ashas":         len(active),
        "avg_resolution_rate": avg_res,
        "avg_response_hrs":    avg_resp,
        "avg_escalation_rate": avg_esc,
        "total_visits":        sum(m["visit_count"]    for m in individual),
        "total_alerts":        sum(m["total_alerts"]   for m in individual),
        "top_performers":      sorted_by_score[:5],
        "underperformers":     [m for m in sorted_by_score if m["composite_score"] < 30],
        "district_rating":     get_performance_rating(avg_res, avg_resp, avg_esc),
        "individual":          individual,
    }


# ─────────────────────────────────────────────────────────────────
# LEADERBOARD DATA  (used by supervisor.py + analytics.py)
# ─────────────────────────────────────────────────────────────────

def leaderboard_data(supervisor_id: str = None, days: int = 30) -> list:
    """
    Returns a list of ASHA metric dicts sorted by composite_score DESC.
    If supervisor_id is provided, scoped to that supervisor's workers.
    Otherwise district-wide.
    """
    from database import get_supervisor_ashas, get_all_asha_workers

    if supervisor_id:
        ashas = get_supervisor_ashas(supervisor_id)
    else:
        ashas = [a for a in get_all_asha_workers() if a.get("is_active")]

    metrics = [calc_asha_metrics(a["asha_id"], days) for a in ashas]
    return sorted(metrics, key=lambda m: m["composite_score"], reverse=True)


# ─────────────────────────────────────────────────────────────────
# SVG SPARKLINE  (server-side, no JS dependency)
# ─────────────────────────────────────────────────────────────────

def _mini_sparkline(values: list, color: str = "#0d8f72",
                    w: int = 80, h: int = 28) -> str:
    if not values or max(values, default=0) == 0:
        return f'<svg width="{w}" height="{h}"></svg>'
    mx  = max(values)
    n   = len(values)
    pts = []
    for i, v in enumerate(values):
        x = round(i / (n - 1) * w, 1) if n > 1 else w // 2
        y = round(h - (v / mx * (h - 4)) - 2, 1)
        pts.append(f"{x},{y}")
    path = "M " + " L ".join(pts)
    fill_pts = pts + [f"{w},{h}", f"0,{h}"]
    fp   = "M " + " L ".join(fill_pts) + " Z"
    last = pts[-1]
    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="{fp}" fill="{color}" fill-opacity="0.15"/>'
        f'<path d="{path}" stroke="{color}" stroke-width="1.8" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last.split(",")[0]}" cy="{last.split(",")[1]}" '
        f'r="2.5" fill="{color}"/>'
        f'</svg>'
    )


# ─────────────────────────────────────────────────────────────────
# HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────

PERFORMANCE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>MaaSakhi — Performance Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --green:      #054235;
            --green-mid:  #0d8f72;
            --green-b:    #1ec99a;
            --green-pale: #d4f5eb;
            --green-tint: #f0fdf9;
            --amber:      #f4a61a;
            --amber-pale: #fef6e4;
            --red:        #e53935;
            --red-pale:   #fdecea;
            --blue:       #1565c0;
            --blue-pale:  #e3eeff;
            --purple:     #7c3aed;
            --ink:        #0c1e35;
            --muted:      #5a7184;
            --pale:       #94aab8;
            --border:     #dde6ed;
            --bg:         #f4f7fa;
            --white:      #ffffff;
            --card:       0 2px 12px rgba(12,30,53,.07);
            --r:          14px;
            --r-sm:       9px;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--ink); }

        /* ── HEADER ─────────────────────────────── */
        .header {
            background: linear-gradient(135deg, var(--green) 0%, #0c3b30 100%);
            color:white; padding:22px 28px 0; overflow:hidden; position:relative;
        }
        .hbg { position:absolute; border-radius:50%; background:rgba(255,255,255,.04); }
        .hbg.a{width:220px;height:220px;top:-70px;right:-50px}
        .hbg.b{width:120px;height:120px;bottom:-40px;right:110px}
        .header-eye { font-size:10px; letter-spacing:.14em; text-transform:uppercase;
                      color:var(--green-b); margin-bottom:6px; font-weight:600; }
        .header-title { font-family:'Syne',sans-serif; font-size:22px; font-weight:800; }
        .header-sub { font-size:12px; opacity:.65; margin-top:5px;
                      display:flex; align-items:center; gap:8px; }
        .live { width:6px;height:6px;border-radius:50%;background:var(--green-b);
                display:inline-block;animation:blink 2s infinite; }
        @keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
        .hmeta { display:flex; gap:8px; margin-top:14px; flex-wrap:wrap; }
        .hpill { background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.16);
                 color:rgba(255,255,255,.8); padding:4px 12px; border-radius:20px;
                 font-size:11px; font-weight:500; }

        /* ── TABS ───────────────────────────────── */
        .tab-nav { display:flex; background:var(--green); padding:0 28px; gap:2px;
                   overflow-x:auto; scrollbar-width:none; border-bottom:1px solid rgba(255,255,255,.07); }
        .tab-nav::-webkit-scrollbar{display:none}
        .tab-btn { padding:10px 17px; border:none; background:transparent;
                   color:rgba(255,255,255,.45); font-family:'DM Sans',sans-serif;
                   font-size:12px; font-weight:600; cursor:pointer;
                   border-bottom:2px solid transparent; transition:all .2s; white-space:nowrap; }
        .tab-btn:hover { color:rgba(255,255,255,.8); }
        .tab-btn.active { color:white; border-bottom-color:var(--green-b); }
        .tab-panel { display:none; }
        .tab-panel.active { display:block; animation:rise .3s ease; }
        @keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

        /* ── LAYOUT ─────────────────────────────── */
        .wrap      { padding:20px 28px; }
        .two-col   { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
        .three-col { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; }
        @media(max-width:740px){ .two-col,.three-col { grid-template-columns:1fr; } }

        /* ── CARD ───────────────────────────────── */
        .card { background:var(--white); border-radius:var(--r);
                padding:18px 20px; border:1px solid var(--border);
                box-shadow:var(--card); animation:rise .4s ease both;
                transition:box-shadow .2s, transform .2s; }
        .card:hover { box-shadow:0 6px 22px rgba(12,30,53,.12); transform:translateY(-2px); }
        .card-title { font-family:'Syne',sans-serif; font-size:14px; font-weight:700; margin-bottom:4px; }
        .card-sub   { font-size:11.5px; color:var(--muted); margin-bottom:14px; }

        /* ── KPI ────────────────────────────────── */
        .kpi-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; padding:18px 28px 8px; }
        @media(max-width:600px){ .kpi-row { grid-template-columns:repeat(2,1fr); } }
        .kpi { background:var(--white); border-radius:var(--r); padding:16px 14px;
               border:1px solid var(--border); box-shadow:var(--card);
               animation:rise .4s ease both; transition:transform .2s; }
        .kpi:hover { transform:translateY(-2px); }
        .kpi-icon { font-size:18px; margin-bottom:6px; }
        .kpi-num  { font-family:'Syne',sans-serif; font-size:28px; font-weight:700; line-height:1; }
        .kpi-lbl  { font-size:10px; color:var(--muted); margin-top:4px;
                    font-weight:600; text-transform:uppercase; letter-spacing:.05em; }

        /* ── DISTRICT SUMMARY ───────────────────── */
        .district-band {
            background: var(--green-tint); border:1px solid var(--green-pale);
            border-radius:var(--r); padding:18px 20px; margin-bottom:16px;
        }
        .db-title { font-family:'Syne',sans-serif; font-size:15px; font-weight:700;
                    color:var(--green); margin-bottom:14px; }
        .db-grid  { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:12px; }
        .db-metric { text-align:center; }
        .db-num   { font-family:'Syne',sans-serif; font-size:26px; font-weight:700; }
        .db-lbl   { font-size:10px; color:var(--muted); margin-top:3px;
                    font-weight:600; text-transform:uppercase; letter-spacing:.04em; }

        /* ── RATING BADGE ───────────────────────── */
        .rating { display:inline-flex; align-items:center; gap:6px;
                  padding:6px 14px; border-radius:20px;
                  font-size:12px; font-weight:700; }
        .rating-GREEN   { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
        .rating-AMBER   { background:var(--amber-pale); color:#92400e; border:1px solid #fde68a; }
        .rating-RED     { background:var(--red-pale); color:#991b1b; border:1px solid #fecaca; }
        .rating-unknown { background:#f8fafc; color:var(--muted); border:1px solid var(--border); }

        /* ── ASHA PERF CARD ─────────────────────── */
        .asha-perf-card {
            background:var(--white); border-radius:var(--r);
            padding:18px 20px; border:1px solid var(--border);
            box-shadow:var(--card); animation:rise .4s ease both;
        }
        .apc-top    { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
        .apc-name   { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; }
        .apc-meta   { font-size:11.5px; color:var(--muted); margin-top:2px; }
        .apc-score  { font-family:'Syne',sans-serif; font-size:28px; font-weight:800;
                      text-align:center; line-height:1; }
        .apc-score-lbl { font-size:9px; color:var(--muted); text-align:center;
                         text-transform:uppercase; letter-spacing:.05em; }
        .metric-row { display:flex; justify-content:space-between;
                      align-items:center; padding:7px 0;
                      border-bottom:1px solid #f1f5f9; }
        .metric-row:last-child { border-bottom:none; }
        .mr-label { font-size:12px; color:var(--muted); }
        .mr-val   { font-size:13px; font-weight:600; }
        .bar-wrap { height:4px; background:#f1f5f9; border-radius:2px;
                    margin-top:3px; overflow:hidden; }
        .bar-fill { height:100%; border-radius:2px; transition:width 1.2s ease; }

        /* ── LEADERBOARD ────────────────────────── */
        .lb-row { display:flex; align-items:center; gap:12px; padding:11px 14px;
                  border-bottom:1px solid #f1f5f9; transition:background .15s; }
        .lb-row:hover { background:#f8fafc; }
        .lb-row:last-child { border-bottom:none; }
        .lb-rank { font-family:'Syne',sans-serif; font-size:16px; font-weight:700;
                   color:var(--border); min-width:26px; text-align:center; }
        .lb-name { font-weight:600; font-size:13px; }
        .lb-meta { font-size:10.5px; color:var(--muted); margin-top:2px; }
        .lb-bar  { flex:1; }
        .lb-bg   { height:4px; background:#f1f5f9; border-radius:2px; overflow:hidden; }
        .lb-fill { height:100%; border-radius:2px; background:var(--green-mid);
                   transition:width 1.2s ease; }
        .lb-score { font-family:'Syne',sans-serif; font-size:15px; font-weight:700;
                    color:var(--green-mid); min-width:32px; text-align:right; }

        /* ── TABLE ──────────────────────────────── */
        .tbl-wrap { overflow-x:auto; }
        table { width:100%; border-collapse:collapse; }
        thead th { padding:10px 13px; font-size:10.5px; font-weight:700;
                   text-align:left; color:var(--muted);
                   text-transform:uppercase; letter-spacing:.05em;
                   border-bottom:1px solid var(--border); background:#f8fafc; }
        tbody td { padding:11px 13px; font-size:12.5px; border-bottom:1px solid #f1f5f9; }
        tbody tr:last-child td { border-bottom:none; }
        tbody tr:hover { background:#f8fafc; }

        /* ── SECTION HEAD ───────────────────────── */
        .sec { padding:8px 28px 10px; font-size:11px; font-weight:700;
               color:var(--green-mid); text-transform:uppercase;
               letter-spacing:.08em; margin-top:8px;
               display:flex; align-items:center; gap:7px; }
        .sec-badge { background:var(--green-mid); color:white;
                     border-radius:20px; padding:1px 8px; font-size:10px; }

        /* ── FOOTER ─────────────────────────────── */
        .footer { text-align:center; font-size:11px; color:var(--pale);
                  padding:22px 28px; border-top:1px solid var(--border); }
        .footer a { color:var(--green-mid); text-decoration:none; }
        .btn { padding:9px 18px; border:none; border-radius:var(--r-sm);
               font-size:12px; font-weight:600; cursor:pointer;
               font-family:'DM Sans',sans-serif; transition:all .2s;
               text-decoration:none; display:inline-flex; align-items:center; gap:5px; }
        .btn:hover { transform:translateY(-1px); filter:brightness(1.06); }
        .btn-green { background:var(--green); color:white; }
        .btn-ghost { background:var(--bg); color:var(--ink); border:1px solid var(--border); }
        .fab { position:fixed; bottom:22px; right:22px; background:var(--green);
               color:white; border:none; border-radius:50%; width:42px; height:42px;
               font-size:16px; cursor:pointer;
               box-shadow:0 4px 16px rgba(5,66,53,.3);
               display:none; align-items:center; justify-content:center;
               transition:.2s; z-index:100; }
        .fab:hover { background:var(--green-mid); transform:scale(1.1); }

        .kpi:nth-child(1){animation-delay:.05s}
        .kpi:nth-child(2){animation-delay:.1s}
        .kpi:nth-child(3){animation-delay:.15s}
        .kpi:nth-child(4){animation-delay:.2s}
    </style>
</head>
<body>

<!-- HEADER -->
<div class="header">
    <div class="hbg a"></div><div class="hbg b"></div>
    <div class="header-eye">District Performance Report</div>
    <div class="header-title">ASHA Worker Performance Dashboard</div>
    <div class="header-sub">
        <span class="live"></span>
        Live &nbsp;•&nbsp; Last {{ days }} days &nbsp;•&nbsp; Generated {{ generated_at }}
    </div>
    <div class="hmeta">
        <span class="hpill">👩 {{ district.total_ashas }} Active ASHAs</span>
        <span class="hpill">📊 Avg Resolution: {{ district.avg_resolution_rate }}%</span>
        {% if district.avg_response_hrs %}
        <span class="hpill">⏱ Avg Response: {{ district.avg_response_hrs }}h</span>
        {% endif %}
        <span class="hpill">🏆 District Rating: {{ district.district_rating }}</span>
    </div>
</div>

<!-- TABS -->
<div class="tab-nav" role="tablist">
    <button class="tab-btn active" onclick="showTab('leaderboard',this)">🏆 Leaderboard</button>
    <button class="tab-btn" onclick="showTab('district',this)">🌍 District Overview</button>
    <button class="tab-btn" onclick="showTab('detail',this)">📋 All ASHA Details</button>
    <button class="tab-btn" onclick="showTab('support',this)">🆘 Needs Support</button>
</div>

<!-- DISTRICT KPI ROW -->
<div class="kpi-row">
    <div class="kpi">
        <div class="kpi-icon">✅</div>
        <div class="kpi-num" style="color:var(--green-mid)">{{ district.avg_resolution_rate }}%</div>
        <div class="kpi-lbl">Avg Resolution Rate</div>
    </div>
    <div class="kpi">
        <div class="kpi-icon">⏱</div>
        <div class="kpi-num" style="color:var(--amber)">
            {% if district.avg_response_hrs %}{{ district.avg_response_hrs }}h{% else %}—{% endif %}
        </div>
        <div class="kpi-lbl">Avg Response Time</div>
    </div>
    <div class="kpi">
        <div class="kpi-icon">⬆</div>
        <div class="kpi-num" style="color:var(--red)">{{ district.avg_escalation_rate }}%</div>
        <div class="kpi-lbl">Avg Escalation Rate</div>
    </div>
    <div class="kpi">
        <div class="kpi-icon">📋</div>
        <div class="kpi-num" style="color:var(--blue)">{{ district.total_visits }}</div>
        <div class="kpi-lbl">Total Visits Done</div>
    </div>
</div>


<!-- ═══ TAB 1: LEADERBOARD ═══ -->
<div class="tab-panel active" id="tab-leaderboard">
    <p class="sec">
        🏆 ASHA Leaderboard — Composite Score
        <span class="sec-badge">{{ leaderboard|length }}</span>
    </p>
    <div class="wrap" style="padding-top:0">
        <div class="card" style="padding:0 0 8px">
            {% for m in leaderboard %}
            {% set rc = 'color:#f4a61a' if loop.index==1 else ('color:#94aab8' if loop.index==2 else ('color:#b45309' if loop.index==3 else 'color:var(--border)')) %}
            <div class="lb-row">
                <div class="lb-rank" style="{{ rc }}">
                    {% if loop.index==1 %}🥇{% elif loop.index==2 %}🥈{% elif loop.index==3 %}🥉{% else %}{{ loop.index }}{% endif %}
                </div>
                <div style="min-width:150px">
                    <div class="lb-name">{{ m.name }}</div>
                    <div class="lb-meta">📍 {{ m.village }}
                        {% if m.total_patients %} · {{ m.total_patients }} patients{% endif %}
                    </div>
                </div>
                <div class="lb-bar">
                    <div style="display:flex;justify-content:space-between;
                                font-size:9.5px;color:var(--pale);margin-bottom:3px">
                        <span>Composite Score</span>
                        <span>{{ m.composite_score }}/100</span>
                    </div>
                    <div class="lb-bg">
                        <div class="lb-fill" style="width:{{ m.composite_score }}%"></div>
                    </div>
                    <div style="display:flex;gap:10px;margin-top:4px;flex-wrap:wrap">
                        <span style="font-size:10px;color:var(--green-mid)">✅ {{ m.resolution_rate }}% res.</span>
                        <span style="font-size:10px;color:var(--amber)">⬆ {{ m.escalation_rate }}% esc.</span>
                        {% if m.avg_response_hrs %}<span style="font-size:10px;color:var(--muted)">⏱ {{ m.avg_response_hrs }}h</span>{% endif %}
                    </div>
                </div>
                <div>
                    <div class="lb-score">{{ m.composite_score }}</div>
                    <div style="margin-top:4px">
                        <span class="rating rating-{{ m.performance_rating }}" style="font-size:9px;padding:3px 8px">
                            {{ m.performance_rating }}
                        </span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>


<!-- ═══ TAB 2: DISTRICT OVERVIEW ═══ -->
<div class="tab-panel" id="tab-district">
    <div class="wrap">
        <div class="district-band">
            <div class="db-title">📊 District-Wide Aggregates — Last {{ days }} Days</div>
            <div class="db-grid">
                <div class="db-metric">
                    <div class="db-num" style="color:var(--green-mid)">{{ district.avg_resolution_rate }}%</div>
                    <div class="db-lbl">Avg Resolution</div>
                </div>
                <div class="db-metric">
                    <div class="db-num" style="color:var(--amber)">
                        {% if district.avg_response_hrs %}{{ district.avg_response_hrs }}h{% else %}—{% endif %}
                    </div>
                    <div class="db-lbl">Avg Response</div>
                </div>
                <div class="db-metric">
                    <div class="db-num" style="color:var(--red)">{{ district.avg_escalation_rate }}%</div>
                    <div class="db-lbl">Avg Escalation</div>
                </div>
                <div class="db-metric">
                    <div class="db-num" style="color:var(--blue)">{{ district.total_alerts }}</div>
                    <div class="db-lbl">Total Alerts</div>
                </div>
                <div class="db-metric">
                    <div class="db-num" style="color:var(--green-mid)">{{ district.total_visits }}</div>
                    <div class="db-lbl">Total Visits</div>
                </div>
                <div class="db-metric">
                    <div class="db-num" style="color:var(--ink)">{{ district.total_patients }}</div>
                    <div class="db-lbl">Total Patients</div>
                </div>
            </div>
        </div>

        {% if district.top_performers %}
        <div class="card-title" style="margin-bottom:10px">🌟 Top Performers</div>
        <div class="three-col">
            {% for m in district.top_performers %}
            <div class="card">
                <div class="apc-top">
                    <div>
                        <div class="apc-name">{{ m.name }}</div>
                        <div class="apc-meta">📍 {{ m.village }}</div>
                    </div>
                    <div>
                        <div class="apc-score" style="color:var(--green-mid)">{{ m.composite_score }}</div>
                        <div class="apc-score-lbl">score</div>
                    </div>
                </div>
                <div style="margin-top:12px">
                    <span class="rating rating-{{ m.performance_rating }}">
                        {{ m.performance_rating }}
                    </span>
                </div>
                <div class="metric-row" style="margin-top:10px">
                    <span class="mr-label">Resolution</span>
                    <span class="mr-val" style="color:var(--green-mid)">{{ m.resolution_rate }}%</span>
                </div>
                <div class="metric-row">
                    <span class="mr-label">Response</span>
                    <span class="mr-val">{% if m.avg_response_hrs %}{{ m.avg_response_hrs }}h{% else %}—{% endif %}</span>
                </div>
                <div class="metric-row">
                    <span class="mr-label">Visits</span>
                    <span class="mr-val" style="color:var(--blue)">{{ m.visit_count }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</div>


<!-- ═══ TAB 3: ALL ASHA DETAILS ═══ -->
<div class="tab-panel" id="tab-detail">
    <p class="sec">📋 All ASHA Performance — Full Table</p>
    <div class="wrap" style="padding-top:0">
        <div class="card" style="padding:0">
            <div class="tbl-wrap">
                <table>
                    <thead><tr>
                        <th>ASHA Name</th><th>Village</th><th>Patients</th>
                        <th>Alerts</th><th>Resolved</th><th>Escalated</th>
                        <th>Visits</th><th>Res. %</th><th>Esc. %</th>
                        <th>Avg Resp.</th><th>Score</th><th>Rating</th>
                    </tr></thead>
                    <tbody>
                        {% for m in leaderboard %}
                        <tr>
                            <td>
                                <a href="/dashboard/{{ m.asha_id }}" target="_blank"
                                   style="color:var(--green-mid);font-weight:600;text-decoration:none">
                                    {{ m.name }}
                                </a>
                            </td>
                            <td style="color:var(--muted)">{{ m.village }}</td>
                            <td style="text-align:center;font-weight:600">{{ m.total_patients }}</td>
                            <td style="text-align:center">{{ m.total_alerts }}</td>
                            <td style="text-align:center;color:var(--green-mid);font-weight:600">{{ m.resolved_alerts }}</td>
                            <td style="text-align:center;color:{% if m.escalated_alerts > 0 %}var(--amber){% else %}var(--muted){% endif %}">{{ m.escalated_alerts }}</td>
                            <td style="text-align:center">{{ m.visit_count }}</td>
                            <td style="text-align:center">
                                <span style="font-weight:700;color:{% if m.resolution_rate >= 80 %}var(--green-mid){% elif m.resolution_rate >= 50 %}var(--amber){% else %}var(--red){% endif %}">
                                    {{ m.resolution_rate }}%
                                </span>
                            </td>
                            <td style="text-align:center;color:{% if m.escalation_rate > 30 %}var(--red){% elif m.escalation_rate > 10 %}var(--amber){% else %}var(--green-mid){% endif %}">
                                {{ m.escalation_rate }}%
                            </td>
                            <td style="text-align:center;color:var(--muted)">
                                {% if m.avg_response_hrs %}{{ m.avg_response_hrs }}h{% else %}—{% endif %}
                            </td>
                            <td style="text-align:center">
                                <span style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:var(--green-mid)">
                                    {{ m.composite_score }}
                                </span>
                            </td>
                            <td>
                                <span class="rating rating-{{ m.performance_rating }}" style="font-size:10px;padding:3px 9px">
                                    {{ m.performance_rating }}
                                </span>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>


<!-- ═══ TAB 4: NEEDS SUPPORT ═══ -->
<div class="tab-panel" id="tab-support">
    <p class="sec">
        🆘 ASHA Workers Needing Support
        <span class="sec-badge">{{ district.underperformers|length }}</span>
    </p>

    {% if district.underperformers %}
    <div class="wrap" style="padding-top:0">
        {% for m in district.underperformers %}
        <div class="asha-perf-card" style="margin-bottom:14px;animation-delay:{{ loop.index * 0.06 }}s">
            <div class="apc-top">
                <div>
                    <div class="apc-name">{{ m.name }}</div>
                    <div class="apc-meta">📍 {{ m.village }}
                        {% if m.supervisor_name %} · Supervisor: {{ m.supervisor_name }}{% endif %}
                    </div>
                    <div style="margin-top:8px">
                        <span class="rating rating-{{ m.performance_rating }}">
                            {{ m.performance_rating }}
                        </span>
                    </div>
                </div>
                <div style="text-align:center">
                    <div class="apc-score" style="color:var(--red)">{{ m.composite_score }}</div>
                    <div class="apc-score-lbl">/ 100</div>
                </div>
            </div>

            <div style="margin-top:14px">
                <!-- Resolution rate bar -->
                <div class="metric-row">
                    <span class="mr-label">Resolution Rate</span>
                    <span class="mr-val" style="color:{% if m.resolution_rate >= 50 %}var(--amber){% else %}var(--red){% endif %}">
                        {{ m.resolution_rate }}%
                    </span>
                </div>
                <div class="bar-wrap">
                    <div class="bar-fill" style="width:{{ m.resolution_rate }}%;
                         background:{% if m.resolution_rate >= 50 %}var(--amber){% else %}var(--red){% endif %}">
                    </div>
                </div>

                <!-- Escalation rate -->
                <div class="metric-row" style="margin-top:8px">
                    <span class="mr-label">Escalation Rate</span>
                    <span class="mr-val" style="color:{% if m.escalation_rate > 30 %}var(--red){% else %}var(--amber){% endif %}">
                        {{ m.escalation_rate }}%
                    </span>
                </div>

                <!-- Avg response -->
                <div class="metric-row">
                    <span class="mr-label">Avg Response Time</span>
                    <span class="mr-val">
                        {% if m.avg_response_hrs %}{{ m.avg_response_hrs }}h{% else %}No data{% endif %}
                    </span>
                </div>

                <!-- Visit count -->
                <div class="metric-row">
                    <span class="mr-label">Visits Logged ({{ days }}d)</span>
                    <span class="mr-val" style="color:var(--blue)">{{ m.visit_count }}</span>
                </div>

                <!-- Pending alerts -->
                {% if m.pending_alerts > 0 %}
                <div style="margin-top:10px;padding:10px 14px;background:var(--red-pale);
                            border:1px solid #fecaca;border-radius:8px;
                            font-size:12px;color:#991b1b;font-weight:500">
                    ⚠️ {{ m.pending_alerts }} alert(s) still pending — intervention needed
                </div>
                {% endif %}

                <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
                    <a href="/dashboard/{{ m.asha_id }}" target="_blank"
                       class="btn btn-green" style="font-size:11px">
                        View Dashboard →
                    </a>
                    <a href="tel:{{ m.phone }}" class="btn btn-ghost" style="font-size:11px">
                        📞 Call ASHA
                    </a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
        <div style="text-align:center;padding:50px;color:var(--pale)">
            <div style="font-size:36px;margin-bottom:10px">🌟</div>
            <div>All ASHA workers are performing well!</div>
            <div style="font-size:11px;margin-top:5px">No one below the support threshold (score &lt; 30)</div>
        </div>
    {% endif %}
</div>


<div style="padding:16px 28px 8px;display:flex;gap:10px;flex-wrap:wrap">
    <a href="/admin" class="btn btn-green" style="font-size:12px">← Admin Panel</a>
    <a href="/admin/export/nhm-csv" class="btn btn-ghost" style="font-size:12px">⬇ Export CSV</a>
</div>

<div class="footer">
    🌿 MaaSakhi Performance Engine &nbsp;•&nbsp;
    {{ generated_at }} &nbsp;•&nbsp;
    <a href="/admin">Admin Panel</a>
</div>

<button class="fab" id="fabBtn"
        onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>

<script>
    function showTab(name, btn) {
        document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el  => el.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        btn.classList.add('active');
        window.scrollTo({top:0, behavior:'smooth'});
    }
    window.addEventListener('scroll', () => {
        document.getElementById('fabBtn').style.display =
            window.scrollY > 300 ? 'flex' : 'none';
    });
    window.addEventListener('load', () => {
        document.querySelectorAll('.lb-fill,.bar-fill').forEach(el => {
            const w = el.style.width;
            el.style.width = '0%';
            setTimeout(() => { el.style.width = w; }, 350);
        });
    });
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────
# MAIN RENDER
# Called from admin.py: render_performance(days=30)
# ─────────────────────────────────────────────────────────────────

def render_performance(days: int = 30) -> str:
    """
    Render the full performance dashboard HTML.
    Fetches district metrics + full leaderboard.
    """
    district     = calc_district_metrics(days)
    leaderboard  = leaderboard_data(days=days)   # all ASHAs, sorted by score
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    return render_template_string(
        PERFORMANCE_HTML,
        district     = district,
        leaderboard  = leaderboard,
        days         = days,
        generated_at = generated_at,
    )