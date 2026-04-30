# ─────────────────────────────────────────────────────────────────
# MaaSakhi — analytics.py
# District Analytics Dashboard (Month 3)
# Standalone render module — called from admin.py / app.py
#
# Features:
#   • District overview KPIs
#   • 30-day alert trend chart (SVG sparklines)
#   • Village-level risk heatmap table
#   • ANC compliance rates
#   • ASHA performance leaderboard
#   • Symptom frequency breakdown
#   • Postpartum + child health summary
#   • NHM export buttons
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────
# DATA LAYER — all SQL queries isolated here
# ─────────────────────────────────────────────────────────────────

def get_analytics_data(days: int = 30) -> dict:
    """
    Pulls all analytics data from the DB in one call.
    Returns a structured dict consumed by render_analytics().
    Falls back to empty structures if DB is unavailable.
    """
    from database import engine
    if not engine:
        return _empty_data()

    from sqlalchemy import text
    data = _empty_data()

    try:
        with engine.connect() as conn:

            # ── District KPIs ─────────────────────────────────────
            data["total_patients"] = conn.execute(text(
                "SELECT COUNT(*) FROM patients WHERE step = 'registered'"
            )).scalar() or 0

            data["total_ashas"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_workers WHERE is_active = TRUE"
            )).scalar() or 0

            data["total_supervisors"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_supervisors WHERE is_active = TRUE"
            )).scalar() or 0

            data["total_bmos"] = conn.execute(text(
                "SELECT COUNT(*) FROM block_officers WHERE is_active = TRUE"
            )).scalar() or 0

            data["total_alerts"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts"
            )).scalar() or 0

            data["pending_alerts"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE status = 'Pending'"
            )).scalar() or 0

            data["resolved_alerts"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE status = 'Resolved'"
            )).scalar() or 0

            data["escalated_alerts"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE escalation_level > 0"
            )).scalar() or 0

            data["postpartum_patients"] = conn.execute(text(
                "SELECT COUNT(*) FROM patients WHERE status = 'postpartum'"
            )).scalar() or 0

            data["total_deliveries"] = conn.execute(text(
                "SELECT COUNT(*) FROM deliveries"
            )).scalar() or 0

            data["total_children"] = conn.execute(text(
                "SELECT COUNT(*) FROM children"
            )).scalar() or 0

            data["total_anc_visits"] = conn.execute(text(
                "SELECT COUNT(*) FROM anc_records"
            )).scalar() or 0

            data["alerts_today"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE DATE(created_at) = CURRENT_DATE"
            )).scalar() or 0

            data["resolved_today"] = conn.execute(text(
                "SELECT COUNT(*) FROM asha_alerts WHERE status='Resolved' AND DATE(created_at)=CURRENT_DATE"
            )).scalar() or 0

            # Resolution rate
            if data["total_alerts"] > 0:
                data["resolution_rate"] = round(
                    data["resolved_alerts"] / data["total_alerts"] * 100, 1
                )

            # ── Daily trend (last N days) ─────────────────────────
            rows = conn.execute(text(f"""
                SELECT
                    DATE(created_at)                              AS day,
                    COUNT(*)                                      AS total,
                    SUM(CASE WHEN symptom_level='RED'   THEN 1 ELSE 0 END)   AS red,
                    SUM(CASE WHEN symptom_level='AMBER' THEN 1 ELSE 0 END)   AS amber,
                    SUM(CASE WHEN symptom_level='GREEN' THEN 1 ELSE 0 END)   AS green
                FROM (
                    SELECT created_at,
                           CASE
                             WHEN level='RED'   THEN 'RED'
                             WHEN level='AMBER' THEN 'AMBER'
                             ELSE 'GREEN'
                           END AS symptom_level
                    FROM symptom_logs
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                ) sub
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """)).fetchall()

            data["daily_trend"] = [{
                "day":   str(r.day),
                "total": int(r.total),
                "red":   int(r.red   or 0),
                "amber": int(r.amber or 0),
                "green": int(r.green or 0),
            } for r in rows]

            # Fill missing days with zeros
            data["daily_trend"] = _fill_date_gaps(data["daily_trend"], days)

            # ── Symptom level breakdown ───────────────────────────
            sym_rows = conn.execute(text("""
                SELECT level, COUNT(*) AS cnt
                FROM symptom_logs
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY level
            """)).fetchall()
            data["symptom_breakdown"] = {r.level: int(r.cnt) for r in sym_rows}

            # ── Top symptoms (text frequency) ─────────────────────
            top_sym = conn.execute(text("""
                SELECT
                    LOWER(TRIM(message)) AS msg,
                    COUNT(*) AS cnt
                FROM symptom_logs
                WHERE level IN ('RED','AMBER')
                  AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY LOWER(TRIM(message))
                ORDER BY cnt DESC
                LIMIT 8
            """)).fetchall()
            data["top_symptoms"] = [
                {"msg": r.msg[:55], "cnt": int(r.cnt)} for r in top_sym
            ]

            # ── Village risk scores ───────────────────────────────
            vil_rows = conn.execute(text("""
                SELECT
                    p.village,
                    COUNT(DISTINCT p.phone)                              AS total_patients,
                    COUNT(DISTINCT aa.id)                                AS active_alerts,
                    COUNT(DISTINCT CASE WHEN aa.status='Resolved'
                          THEN aa.id END)                                AS resolved_alerts,
                    AVG(CASE WHEN sl.level='RED'   THEN 40
                             WHEN sl.level='AMBER' THEN 15
                             WHEN sl.level='GREEN' THEN 2
                             ELSE 0 END)                                 AS avg_risk
                FROM patients p
                LEFT JOIN asha_alerts  aa ON aa.phone = p.phone AND aa.status != 'Resolved'
                LEFT JOIN symptom_logs sl ON sl.phone = p.phone
                WHERE p.step = 'registered'
                GROUP BY p.village
                ORDER BY avg_risk DESC NULLS LAST
                LIMIT 20
            """)).fetchall()

            data["village_risks"] = [{
                "village":          r.village or "Unknown",
                "total_patients":   int(r.total_patients),
                "active_alerts":    int(r.active_alerts  or 0),
                "resolved_alerts":  int(r.resolved_alerts or 0),
                "avg_risk":         round(float(r.avg_risk), 1) if r.avg_risk else 0,
            } for r in vil_rows]

            # ── ASHA performance leaderboard ──────────────────────
            perf_rows = conn.execute(text("""
                SELECT
                    aw.asha_id,
                    aw.name,
                    aw.village,
                    COUNT(DISTINCT p.phone)                              AS patients,
                    COUNT(DISTINCT aa.id)                                AS total_alerts,
                    COUNT(DISTINCT CASE WHEN aa.status='Resolved'
                          THEN aa.id END)                                AS resolved,
                    COUNT(DISTINCT CASE WHEN aa.escalation_level > 0
                          THEN aa.id END)                                AS escalated,
                    COUNT(DISTINCT av.id)                                AS visits,
                    AVG(CASE WHEN aa.status='Resolved'
                        THEN EXTRACT(EPOCH FROM (aa.escalated_at - aa.created_at))/3600.0
                        END)                                             AS avg_resp_hrs
                FROM asha_workers aw
                LEFT JOIN patients   p  ON p.asha_id  = aw.asha_id AND p.step='registered'
                LEFT JOIN asha_alerts aa ON aa.asha_id = aw.asha_id
                LEFT JOIN asha_visits av ON av.asha_id = aw.asha_id
                WHERE aw.is_active = TRUE
                GROUP BY aw.asha_id, aw.name, aw.village
                ORDER BY resolved DESC, avg_resp_hrs ASC NULLS LAST
                LIMIT 15
            """)).fetchall()

            data["asha_leaderboard"] = [{
                "asha_id":       r.asha_id,
                "name":          r.name,
                "village":       r.village or "—",
                "patients":      int(r.patients),
                "total_alerts":  int(r.total_alerts),
                "resolved":      int(r.resolved),
                "escalated":     int(r.escalated),
                "visits":        int(r.visits),
                "avg_resp_hrs":  round(float(r.avg_resp_hrs), 1) if r.avg_resp_hrs else None,
                "resolution_rate": (
                    round(int(r.resolved) / int(r.total_alerts) * 100, 1)
                    if int(r.total_alerts) > 0 else 0
                ),
            } for r in perf_rows]

            # ── ANC compliance ────────────────────────────────────
            anc_rows = conn.execute(text("""
                SELECT
                    visit_number,
                    COUNT(DISTINCT phone) AS patients_with_visit
                FROM anc_records
                GROUP BY visit_number
                ORDER BY visit_number
            """)).fetchall()
            anc_map = {int(r.visit_number): int(r.patients_with_visit) for r in anc_rows}
            total_p = data["total_patients"] or 1
            data["anc_compliance"] = [
                {
                    "visit":    i,
                    "label":    ["ANC 1\n<12wk", "ANC 2\n14–16wk",
                                 "ANC 3\n28–32wk", "ANC 4\n36wk"][i - 1],
                    "count":    anc_map.get(i, 0),
                    "pct":      round(anc_map.get(i, 0) / total_p * 100, 1)
                }
                for i in range(1, 5)
            ]

            # ── Scheme delivery totals ────────────────────────────
            scheme_rows = conn.execute(text("""
                SELECT scheme_name, COUNT(*) AS cnt
                FROM scheme_deliveries
                GROUP BY scheme_name
                ORDER BY cnt DESC
            """)).fetchall()
            data["scheme_deliveries"] = [
                {"name": r.scheme_name, "cnt": int(r.cnt)} for r in scheme_rows
            ]

            # ── Escalation breakdown by level ─────────────────────
            esc_rows = conn.execute(text("""
                SELECT escalation_level, COUNT(*) AS cnt
                FROM asha_alerts
                GROUP BY escalation_level
                ORDER BY escalation_level
            """)).fetchall()
            data["escalation_breakdown"] = {
                int(r.escalation_level): int(r.cnt) for r in esc_rows
            }

            # ── Visit outcomes breakdown ──────────────────────────
            outcome_rows = conn.execute(text("""
                SELECT outcome, COUNT(*) AS cnt
                FROM asha_visits
                GROUP BY outcome
                ORDER BY cnt DESC
            """)).fetchall()
            data["visit_outcomes"] = [
                {"outcome": r.outcome, "cnt": int(r.cnt)} for r in outcome_rows
            ]

            # ── Weekly new registrations (last 12 weeks) ──────────
            reg_rows = conn.execute(text("""
                SELECT
                    DATE_TRUNC('week', created_at) AS week_start,
                    COUNT(*) AS new_patients
                FROM patients
                WHERE step = 'registered'
                  AND created_at >= NOW() - INTERVAL '12 weeks'
                GROUP BY DATE_TRUNC('week', created_at)
                ORDER BY week_start ASC
            """)).fetchall()
            data["weekly_registrations"] = [
                {
                    "week":    r.week_start.strftime("%d %b") if r.week_start else "",
                    "count":   int(r.new_patients)
                }
                for r in reg_rows
            ]

    except Exception as e:
        print(f"analytics.py get_analytics_data error: {e}")

    return data


def _empty_data() -> dict:
    return {
        "total_patients":       0,
        "total_ashas":          0,
        "total_supervisors":    0,
        "total_bmos":           0,
        "total_alerts":         0,
        "pending_alerts":       0,
        "resolved_alerts":      0,
        "escalated_alerts":     0,
        "postpartum_patients":  0,
        "total_deliveries":     0,
        "total_children":       0,
        "total_anc_visits":     0,
        "alerts_today":         0,
        "resolved_today":       0,
        "resolution_rate":      0.0,
        "daily_trend":          [],
        "symptom_breakdown":    {},
        "top_symptoms":         [],
        "village_risks":        [],
        "asha_leaderboard":     [],
        "anc_compliance":       [],
        "scheme_deliveries":    [],
        "escalation_breakdown": {},
        "visit_outcomes":       [],
        "weekly_registrations": [],
    }


def _fill_date_gaps(trend: list, days: int) -> list:
    """Ensure every day in the last N days has an entry (fill missing with zeros)."""
    existing = {d["day"]: d for d in trend}
    result   = []
    today    = datetime.now().date()
    for i in range(days - 1, -1, -1):
        d = str(today - timedelta(days=i))
        result.append(existing.get(d, {
            "day": d, "total": 0, "red": 0, "amber": 0, "green": 0
        }))
    return result


# ─────────────────────────────────────────────────────────────────
# SVG CHART BUILDERS (server-side, no JS library needed)
# ─────────────────────────────────────────────────────────────────

def _sparkline_svg(values: list[int], color: str = "#10b981",
                   width: int = 200, height: int = 48) -> str:
    """Minimal SVG sparkline for trend indicators."""
    if not values or max(values) == 0:
        return f'<svg width="{width}" height="{height}"></svg>'
    mx  = max(values)
    n   = len(values)
    pts = []
    for i, v in enumerate(values):
        x = round(i / (n - 1) * width, 1) if n > 1 else width // 2
        y = round(height - (v / mx * (height - 4)) - 2, 1)
        pts.append(f"{x},{y}")
    path = "M " + " L ".join(pts)
    # Filled area
    fill_pts = pts + [f"{width},{height}", f"0,{height}"]
    fill_path = "M " + " L ".join(fill_pts) + " Z"
    return (
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="{fill_path}" fill="{color}" fill-opacity="0.12"/>'
        f'<path d="{path}" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{pts[-1].split(",")[0]}" cy="{pts[-1].split(",")[1]}" r="3" fill="{color}"/>'
        f'</svg>'
    )


def _bar_chart_svg(items: list[dict], key_label: str, key_value: str,
                   color: str = "#0369a1",
                   width: int = 560, height: int = 180) -> str:
    """Horizontal bar chart SVG for ANC compliance, top symptoms, etc."""
    if not items:
        return ""
    max_val = max(d[key_value] for d in items) or 1
    bar_h   = min(22, (height - 20) // len(items))
    gap     = 4
    label_w = 130
    svg     = [f'<svg width="{width}" height="{len(items)*(bar_h+gap)+20}" '
               f'xmlns="http://www.w3.org/2000/svg" style="overflow:visible">']
    for i, d in enumerate(items):
        y       = i * (bar_h + gap)
        bar_w   = max(4, round((d[key_value] / max_val) * (width - label_w - 50)))
        label   = str(d[key_label])[:22]
        val_str = str(d[key_value])
        # Label
        svg.append(
            f'<text x="{label_w - 6}" y="{y + bar_h - 6}" '
            f'text-anchor="end" font-size="11" fill="#64748b" '
            f'font-family="DM Sans,sans-serif">{label}</text>'
        )
        # Bar background
        svg.append(
            f'<rect x="{label_w}" y="{y}" width="{width - label_w - 50}" '
            f'height="{bar_h}" rx="4" fill="#f1f5f9"/>'
        )
        # Bar fill
        svg.append(
            f'<rect x="{label_w}" y="{y}" width="{bar_w}" '
            f'height="{bar_h}" rx="4" fill="{color}" opacity="0.85"/>'
        )
        # Value label
        svg.append(
            f'<text x="{label_w + bar_w + 6}" y="{y + bar_h - 6}" '
            f'font-size="11" fill="{color}" font-weight="600" '
            f'font-family="DM Sans,sans-serif">{val_str}</text>'
        )
    svg.append("</svg>")
    return "".join(svg)


def _stacked_area_svg(daily: list[dict],
                      width: int = 640, height: int = 140) -> str:
    """
    Stacked area chart: RED / AMBER / GREEN layers over time.
    Returns raw SVG string.
    """
    if not daily:
        return ""

    n      = len(daily)
    pad_l  = 32
    pad_r  = 10
    pad_t  = 10
    pad_b  = 24
    cw     = width  - pad_l - pad_r
    ch     = height - pad_t - pad_b
    max_v  = max((d["total"] for d in daily), default=1) or 1

    def xp(i):
        return pad_l + round(i / (n - 1) * cw, 1) if n > 1 else pad_l + cw // 2

    def yp(v):
        return pad_t + ch - round(v / max_v * ch, 1)

    # Layers: green bottom, amber middle, red top
    layers = [
        ("green", "#10b981", "#d1fae5"),
        ("amber", "#f59e0b", "#fef3c7"),
        ("red",   "#ef4444", "#fee2e2"),
    ]

    svg = [
        f'<svg width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]

    # Y-axis gridlines
    for g in range(0, 5):
        gy = pad_t + round(g / 4 * ch)
        svg.append(
            f'<line x1="{pad_l}" y1="{gy}" x2="{pad_l+cw}" y2="{gy}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
        )
        lbl = round(max_v * (1 - g / 4))
        svg.append(
            f'<text x="{pad_l - 4}" y="{gy + 4}" text-anchor="end" '
            f'font-size="9" fill="#94a3b8" font-family="DM Sans,sans-serif">{lbl}</text>'
        )

    # Running cumulative for stacking
    def area_path(key, base_key=None):
        top_pts = []
        bot_pts = []
        for i, d in enumerate(daily):
            base = d.get(base_key, 0) if base_key else 0
            top  = base + d.get(key, 0)
            top_pts.append((xp(i), yp(top)))
            bot_pts.append((xp(i), yp(base)))
        path_fwd = " L ".join(f"{x},{y}" for x, y in top_pts)
        path_rev = " L ".join(f"{x},{y}" for x, y in reversed(bot_pts))
        return f"M {path_fwd} L {path_rev} Z"

    # Build cumulative stacks
    def add_layer(key, base_key, stroke_col, fill_col):
        fill_d = area_path(key, base_key)
        # Top line only
        top_pts = []
        for i, d in enumerate(daily):
            base = d.get(base_key, 0) if base_key else 0
            top  = base + d.get(key, 0)
            top_pts.append(f"{xp(i)},{yp(top)}")
        line_d = "M " + " L ".join(top_pts)
        svg.append(f'<path d="{fill_d}" fill="{fill_col}" fill-opacity="0.7"/>')
        svg.append(
            f'<path d="{line_d}" stroke="{stroke_col}" stroke-width="1.5" '
            f'fill="none" stroke-linejoin="round"/>'
        )

    add_layer("green", None,    "#10b981", "#d1fae5")
    add_layer("amber", "green", "#f59e0b", "#fef3c7")
    add_layer("red",   "amber", "#ef4444", "#fee2e2")  # amber+green as base

    # X-axis date labels (show every ~7th)
    step = max(1, n // 7)
    for i, d in enumerate(daily):
        if i % step == 0:
            label = d["day"][5:]   # MM-DD
            svg.append(
                f'<text x="{xp(i)}" y="{height - 4}" text-anchor="middle" '
                f'font-size="9" fill="#94a3b8" font-family="DM Sans,sans-serif">{label}</text>'
            )

    svg.append("</svg>")
    return "".join(svg)


# ─────────────────────────────────────────────────────────────────
# RISK COLOUR HELPER
# ─────────────────────────────────────────────────────────────────

def _risk_color(score: float) -> tuple[str, str, str]:
    """Returns (bg_color, text_color, label) based on avg_risk score."""
    if score >= 30:
        return "#fef2f2", "#dc2626", "HIGH"
    if score >= 12:
        return "#fffbeb", "#b45309", "MOD"
    return "#f0fdf4", "#16a34a", "LOW"


# ─────────────────────────────────────────────────────────────────
# ANALYTICS HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────

ANALYTICS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>MaaSakhi — District Analytics</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {
            --ink:          #0c1e35;
            --muted:        #5a7184;
            --pale:         #94aab8;
            --border:       #dde6ed;
            --bg:           #f4f7fa;
            --white:        #ffffff;
            --teal:         #0a6e58;
            --teal-mid:     #0d8f72;
            --teal-bright:  #1ec99a;
            --teal-pale:    #d4f5eb;
            --teal-tint:    #f0faf6;
            --red:          #e53935;
            --red-pale:     #fdecea;
            --amber:        #f4a61a;
            --amber-pale:   #fef6e4;
            --blue:         #1565c0;
            --blue-pale:    #e3eeff;
            --purple:       #7c3aed;
            --card:         0 2px 12px rgba(12,30,53,.07);
            --card-hover:   0 6px 24px rgba(12,30,53,.13);
            --r:            14px;
            --r-sm:         9px;
        }

        * { margin:0; padding:0; box-sizing:border-box; }

        body {
            font-family: 'DM Sans', sans-serif;
            background: var(--bg);
            color: var(--ink);
        }

        /* ── HEADER ───────────────────────────────────────────── */
        .header {
            background: var(--ink);
            padding: 26px 32px 0;
            position: relative;
            overflow: hidden;
        }
        .header::after {
            content: '';
            position: absolute;
            inset: 0;
            background: repeating-linear-gradient(
                -45deg,
                transparent 0px, transparent 18px,
                rgba(255,255,255,.018) 18px, rgba(255,255,255,.018) 19px
            );
            pointer-events: none;
        }
        .header-eyebrow {
            font-size: 10px; letter-spacing: .14em;
            text-transform: uppercase;
            color: var(--teal-bright); margin-bottom: 7px;
            font-weight: 600;
        }
        .header-title {
            font-family: 'Fraunces', serif;
            font-size: 26px; font-weight: 600;
            color: white; line-height: 1.2;
        }
        .header-sub {
            font-size: 12px; color: rgba(255,255,255,.5);
            margin-top: 6px;
            display: flex; align-items: center; gap: 10px;
        }
        .live-dot {
            width: 6px; height: 6px; border-radius: 50%;
            background: var(--teal-bright);
            display: inline-block; animation: blink 2s infinite;
        }
        @keyframes blink {
            0%,100% { opacity:1; } 50% { opacity:.3; }
        }
        .header-meta { display:flex; gap:8px; margin-top:16px; flex-wrap:wrap; }
        .hpill {
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.13);
            color: rgba(255,255,255,.75);
            padding: 4px 13px; border-radius: 20px;
            font-size: 11px; font-weight: 500;
        }
        .hpill.hl { background:rgba(30,201,154,.12); border-color:rgba(30,201,154,.25); color:var(--teal-bright); }
        .hpill.danger { background:rgba(229,57,53,.15); border-color:rgba(229,57,53,.3); color:#ff8a80; }

        /* ── TAB NAV ──────────────────────────────────────────── */
        .tab-nav {
            display: flex; background: var(--ink);
            padding: 0 32px; gap: 2px;
            overflow-x: auto; scrollbar-width: none;
            border-bottom: 1px solid rgba(255,255,255,.07);
        }
        .tab-nav::-webkit-scrollbar { display:none; }
        .tab-btn {
            padding: 10px 18px; border: none; background: transparent;
            color: rgba(255,255,255,.45);
            font-family: 'DM Sans', sans-serif;
            font-size: 12px; font-weight: 600; cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all .2s; white-space: nowrap;
        }
        .tab-btn:hover  { color: rgba(255,255,255,.8); }
        .tab-btn.active { color: white; border-bottom-color: var(--teal-bright); }

        /* ── PANELS ───────────────────────────────────────────── */
        .tab-panel { display:none; }
        .tab-panel.active { display:block; animation: rise .3s ease; }
        @keyframes rise {
            from { opacity:0; transform:translateY(10px); }
            to   { opacity:1; transform:translateY(0); }
        }

        /* ── KPI GRID ─────────────────────────────────────────── */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px; padding: 22px 32px 10px;
        }
        @media(max-width:700px){ .kpi-grid { grid-template-columns:repeat(2,1fr); } }
        .kpi {
            background: var(--white); border-radius: var(--r);
            padding: 18px 16px;
            border: 1px solid var(--border);
            box-shadow: var(--card);
            transition: box-shadow .2s, transform .2s;
            animation: rise .4s ease both;
        }
        .kpi:hover { box-shadow: var(--card-hover); transform: translateY(-2px); }
        .kpi-top { display:flex; justify-content:space-between; align-items:flex-start; }
        .kpi-icon {
            width:38px; height:38px; border-radius:10px;
            display:flex; align-items:center; justify-content:center;
            font-size:18px; flex-shrink:0;
        }
        .kpi-spark { margin-top:6px; }
        .kpi-num {
            font-family: 'Fraunces', serif;
            font-size: 32px; font-weight: 700;
            line-height: 1; margin-top: 10px;
        }
        .kpi-lbl {
            font-size: 11px; color: var(--muted); margin-top: 5px;
            font-weight: 500; text-transform: uppercase; letter-spacing: .05em;
        }
        .kpi-delta {
            font-size: 11px; font-weight: 600; margin-top: 4px;
        }

        /* ── SECTION HEAD ─────────────────────────────────────── */
        .sec {
            padding: 8px 32px 12px;
            font-size: 11px; font-weight: 700;
            color: var(--teal); text-transform: uppercase;
            letter-spacing: .08em; margin-top: 8px;
            display: flex; align-items: center; gap: 8px;
        }
        .sec-badge {
            background: var(--teal); color: white;
            border-radius: 20px; padding: 1px 8px; font-size: 10px;
        }

        /* ── CHART CARD ───────────────────────────────────────── */
        .chart-card {
            background: var(--white); border-radius: var(--r);
            padding: 20px 22px;
            border: 1px solid var(--border);
            box-shadow: var(--card);
            animation: rise .4s ease both;
        }
        .chart-card-title {
            font-family: 'Fraunces', serif;
            font-size: 15px; font-weight: 600; margin-bottom: 4px;
        }
        .chart-card-sub { font-size: 11.5px; color: var(--muted); margin-bottom: 16px; }
        .chart-legend { display:flex; gap:14px; margin-bottom:12px; flex-wrap:wrap; }
        .legend-item { display:flex; align-items:center; gap:5px; font-size:11px; color:var(--muted); }
        .legend-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

        /* ── TWO COL LAYOUT ───────────────────────────────────── */
        .two-col {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            padding: 0 32px 20px;
        }
        @media(max-width:760px){ .two-col { grid-template-columns:1fr; } }

        /* ── VILLAGE TABLE ────────────────────────────────────── */
        .tbl-wrap { overflow-x:auto; }
        table {
            width:100%; border-collapse:collapse;
        }
        thead th {
            padding: 10px 14px; font-size:10.5px; font-weight:700;
            text-align:left; color:var(--muted);
            text-transform:uppercase; letter-spacing:.05em;
            border-bottom: 1px solid var(--border);
            background: #f8fafc;
        }
        tbody td { padding: 11px 14px; font-size: 12.5px; border-bottom:1px solid #f1f5f9; }
        tbody tr:last-child td { border-bottom:none; }
        tbody tr:hover { background:#f8fafc; }

        /* ── RISK PILL ────────────────────────────────────────── */
        .rpill {
            display:inline-block; padding:2px 9px;
            border-radius:20px; font-size:10px; font-weight:700;
        }

        /* ── LEADERBOARD ──────────────────────────────────────── */
        .lb-row {
            display:flex; align-items:center; gap:12px;
            padding:12px 14px; border-bottom:1px solid #f1f5f9;
            transition: background .15s;
        }
        .lb-row:hover { background:#f8fafc; }
        .lb-row:last-child { border-bottom:none; }
        .lb-rank {
            font-family: 'Fraunces', serif;
            font-size:18px; font-weight:700;
            color:var(--border); min-width:26px; text-align:center;
        }
        .lb-rank.gold   { color:#f4a61a; }
        .lb-rank.silver { color:#94aab8; }
        .lb-rank.bronze { color:#b45309; }
        .lb-name  { font-weight:600; font-size:13px; }
        .lb-meta  { font-size:11px; color:var(--muted); margin-top:2px; }
        .lb-bar   { flex:1; }
        .lb-bar-bg { height:4px; background:#f1f5f9; border-radius:2px; overflow:hidden; }
        .lb-bar-fill { height:100%; border-radius:2px; background:var(--teal-mid); transition:width 1.2s ease; }
        .lb-val   { font-family:'Fraunces',serif; font-size:15px; font-weight:700;
                    color:var(--teal); min-width:36px; text-align:right; }

        /* ── ANC FUNNEL ───────────────────────────────────────── */
        .anc-funnel { display:flex; gap:10px; align-items:flex-end; padding:10px 0; }
        .anc-col    { flex:1; text-align:center; }
        .anc-bar-wrap { height:80px; display:flex; align-items:flex-end; justify-content:center; }
        .anc-bar {
            width:48px; border-radius:6px 6px 0 0;
            transition: height 1.2s ease;
            min-height:4px;
        }
        .anc-pct  { font-family:'Fraunces',serif; font-size:18px; font-weight:700; margin-top:6px; }
        .anc-lbl  { font-size:10px; color:var(--muted); margin-top:2px; font-weight:600; }
        .anc-cnt  { font-size:11px; color:var(--pale); margin-top:1px; }

        /* ── DONUT CHART (CSS only) ────────────────────────────── */
        .donut-wrap { display:flex; align-items:center; gap:20px; }
        .donut { position:relative; width:100px; height:100px; flex-shrink:0; }
        .donut svg { transform:rotate(-90deg); }
        .donut-center {
            position:absolute; inset:0;
            display:flex; flex-direction:column;
            align-items:center; justify-content:center;
        }
        .donut-num  { font-family:'Fraunces',serif; font-size:20px; font-weight:700; color:var(--ink); }
        .donut-sub  { font-size:9px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
        .donut-legend { display:flex; flex-direction:column; gap:7px; }
        .dl-row { display:flex; align-items:center; gap:7px; font-size:12px; }
        .dl-swatch { width:10px; height:10px; border-radius:3px; flex-shrink:0; }

        /* ── OUTCOME PILLS ────────────────────────────────────── */
        .outcome-grid { display:flex; flex-wrap:wrap; gap:8px; padding:6px 0; }
        .outcome-pill {
            padding:6px 14px; border-radius:20px; font-size:11.5px; font-weight:600;
            display:flex; align-items:center; gap:6px;
        }

        /* ── EXPORT BUTTONS ───────────────────────────────────── */
        .export-row {
            display:flex; gap:10px; padding:0 32px 28px; flex-wrap:wrap; margin-top:8px;
        }
        .btn {
            padding:10px 20px; border:none; border-radius:var(--r-sm);
            font-size:12px; font-weight:600; cursor:pointer;
            font-family:'DM Sans',sans-serif;
            transition:all .2s; text-decoration:none;
            display:inline-flex; align-items:center; gap:6px;
        }
        .btn:hover { transform:translateY(-1px); filter:brightness(1.06); }
        .btn-teal   { background:var(--teal); color:white; }
        .btn-blue   { background:var(--blue); color:white; }
        .btn-dark   { background:var(--ink);  color:white; }
        .btn-ghost  { background:var(--bg); color:var(--ink); border:1px solid var(--border); }

        /* ── FOOTER ───────────────────────────────────────────── */
        .footer {
            text-align:center; font-size:11px; color:var(--pale);
            padding:20px 32px; border-top:1px solid var(--border);
        }
        .footer a { color:var(--teal); text-decoration:none; }

        /* ── FAB ──────────────────────────────────────────────── */
        .fab {
            position:fixed; bottom:22px; right:22px;
            background:var(--ink); color:white; border:none;
            border-radius:50%; width:42px; height:42px;
            font-size:16px; cursor:pointer;
            box-shadow:0 4px 16px rgba(12,30,53,.3);
            display:none; align-items:center; justify-content:center;
            transition:.2s; z-index:100;
        }
        .fab:hover { background:var(--teal); transform:scale(1.1); }

        .kpi:nth-child(1){animation-delay:.05s}
        .kpi:nth-child(2){animation-delay:.10s}
        .kpi:nth-child(3){animation-delay:.15s}
        .kpi:nth-child(4){animation-delay:.20s}
    </style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════
     HEADER
══════════════════════════════════════════════════════════════ -->
<div class="header">
    <div class="header-eyebrow">District Health Analytics</div>
    <div class="header-title">MaaSakhi Intelligence Dashboard</div>
    <div class="header-sub">
        <span class="live-dot"></span>
        Live data &nbsp;•&nbsp; Generated {{ generated_at }}
        &nbsp;•&nbsp; Last {{ days }} days
    </div>
    <div class="header-meta">
        <span class="hpill hl">🤰 {{ d.total_patients }} Patients</span>
        <span class="hpill">👩 {{ d.total_ashas }} ASHAs</span>
        <span class="hpill">👩‍💼 {{ d.total_supervisors }} Supervisors</span>
        <span class="hpill">🏥 {{ d.total_bmos }} BMOs</span>
        {% if d.pending_alerts > 0 %}
        <span class="hpill danger">🚨 {{ d.pending_alerts }} Pending</span>
        {% endif %}
    </div>
</div>

<!-- ═══════════════════════════════════════════════════════════
     TAB NAV
══════════════════════════════════════════════════════════════ -->
<div class="tab-nav" role="tablist">
    <button class="tab-btn active" onclick="showTab('overview',this)">📊 Overview</button>
    <button class="tab-btn" onclick="showTab('trends',this)">📈 Trends</button>
    <button class="tab-btn" onclick="showTab('villages',this)">🗺️ Villages</button>
    <button class="tab-btn" onclick="showTab('ashas',this)">👩 ASHA Performance</button>
    <button class="tab-btn" onclick="showTab('health',this)">🏥 Health Metrics</button>
    <button class="tab-btn" onclick="showTab('export',this)">📤 Export</button>
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 1 — OVERVIEW
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel active" id="tab-overview">

    <!-- KPI Row 1 -->
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-top">
                <div class="kpi-icon" style="background:var(--teal-pale)">🤰</div>
                <div class="kpi-spark">{{ sparklines.patients }}</div>
            </div>
            <div class="kpi-num" style="color:var(--teal)">{{ d.total_patients }}</div>
            <div class="kpi-lbl">Registered Patients</div>
        </div>
        <div class="kpi">
            <div class="kpi-top">
                <div class="kpi-icon" style="background:#fee2e2">🚨</div>
                <div class="kpi-spark">{{ sparklines.alerts }}</div>
            </div>
            <div class="kpi-num" style="color:var(--red)">{{ d.pending_alerts }}</div>
            <div class="kpi-lbl">Pending Alerts</div>
            <div class="kpi-delta" style="color:var(--muted)">
                {{ d.alerts_today }} today
            </div>
        </div>
        <div class="kpi">
            <div class="kpi-top">
                <div class="kpi-icon" style="background:var(--teal-pale)">✅</div>
            </div>
            <div class="kpi-num" style="color:var(--teal-mid)">{{ d.resolution_rate }}%</div>
            <div class="kpi-lbl">Resolution Rate</div>
            <div class="kpi-delta" style="color:var(--muted)">
                {{ d.resolved_alerts }} / {{ d.total_alerts }} resolved
            </div>
        </div>
        <div class="kpi">
            <div class="kpi-top">
                <div class="kpi-icon" style="background:#fef6e4">⬆</div>
            </div>
            <div class="kpi-num" style="color:var(--amber)">{{ d.escalated_alerts }}</div>
            <div class="kpi-lbl">Escalated Alerts</div>
        </div>
    </div>

    <!-- KPI Row 2 -->
    <div class="kpi-grid" style="padding-top:0">
        <div class="kpi">
            <div class="kpi-icon" style="background:#f5f3ff;font-size:18px">👶</div>
            <div class="kpi-num" style="color:var(--purple)">{{ d.total_deliveries }}</div>
            <div class="kpi-lbl">Deliveries Registered</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:var(--teal-pale);font-size:18px">📋</div>
            <div class="kpi-num" style="color:var(--teal)">{{ d.total_anc_visits }}</div>
            <div class="kpi-lbl">ANC Visits Done</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:var(--blue-pale);font-size:18px">👩</div>
            <div class="kpi-num" style="color:var(--blue)">{{ d.total_ashas }}</div>
            <div class="kpi-lbl">Active ASHA Workers</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:#fef6e4;font-size:18px">🏛️</div>
            <div class="kpi-num" style="color:var(--amber)">{{ d.scheme_deliveries|sum(attribute='cnt') }}</div>
            <div class="kpi-lbl">Scheme Deliveries</div>
        </div>
    </div>

    <!-- Symptom breakdown donut + visit outcomes -->
    <div class="two-col" style="padding-top:0">

        <!-- Symptom risk donut -->
        <div class="chart-card">
            <div class="chart-card-title">Alert Risk Distribution</div>
            <div class="chart-card-sub">Last 30 days — RED / AMBER / GREEN</div>
            {% set red_c   = d.symptom_breakdown.get('RED',   0) %}
            {% set amb_c   = d.symptom_breakdown.get('AMBER', 0) %}
            {% set grn_c   = d.symptom_breakdown.get('GREEN', 0) %}
            {% set sym_tot = red_c + amb_c + grn_c or 1 %}
            {% set red_pct = (red_c   / sym_tot * 100)|round(1) %}
            {% set amb_pct = (amb_c   / sym_tot * 100)|round(1) %}
            {% set grn_pct = (grn_c   / sym_tot * 100)|round(1) %}
            {% set r = 40 %}
            {% set circ = 2 * 3.14159 * r %}
            {% set red_dash   = (red_pct   / 100 * circ)|round(2) %}
            {% set amb_dash   = (amb_pct   / 100 * circ)|round(2) %}
            {% set grn_dash   = (grn_pct   / 100 * circ)|round(2) %}
            {% set amb_offset = (100 - red_pct) / 100 * circ %}
            {% set grn_offset = (100 - red_pct - amb_pct) / 100 * circ %}
            <div class="donut-wrap">
                <div class="donut">
                    <svg viewBox="0 0 100 100" width="100" height="100">
                        <circle cx="50" cy="50" r="{{ r }}" fill="none"
                                stroke="#f1f5f9" stroke-width="16"/>
                        <circle cx="50" cy="50" r="{{ r }}" fill="none"
                                stroke="#10b981" stroke-width="16"
                                stroke-dasharray="{{ grn_dash }} {{ circ - grn_dash }}"
                                stroke-dashoffset="{{ grn_offset }}"/>
                        <circle cx="50" cy="50" r="{{ r }}" fill="none"
                                stroke="#f4a61a" stroke-width="16"
                                stroke-dasharray="{{ amb_dash }} {{ circ - amb_dash }}"
                                stroke-dashoffset="{{ amb_offset }}"/>
                        <circle cx="50" cy="50" r="{{ r }}" fill="none"
                                stroke="#e53935" stroke-width="16"
                                stroke-dasharray="{{ red_dash }} {{ circ - red_dash }}"
                                stroke-dashoffset="{{ circ }}"/>
                    </svg>
                    <div class="donut-center">
                        <div class="donut-num">{{ sym_tot }}</div>
                        <div class="donut-sub">total</div>
                    </div>
                </div>
                <div class="donut-legend">
                    <div class="dl-row">
                        <div class="dl-swatch" style="background:#e53935"></div>
                        <div><strong style="color:#e53935">{{ red_c }}</strong>
                            <span style="color:var(--muted);font-size:11px"> RED ({{ red_pct }}%)</span>
                        </div>
                    </div>
                    <div class="dl-row">
                        <div class="dl-swatch" style="background:#f4a61a"></div>
                        <div><strong style="color:#f4a61a">{{ amb_c }}</strong>
                            <span style="color:var(--muted);font-size:11px"> AMBER ({{ amb_pct }}%)</span>
                        </div>
                    </div>
                    <div class="dl-row">
                        <div class="dl-swatch" style="background:#10b981"></div>
                        <div><strong style="color:#10b981">{{ grn_c }}</strong>
                            <span style="color:var(--muted);font-size:11px"> GREEN ({{ grn_pct }}%)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Visit outcomes -->
        <div class="chart-card">
            <div class="chart-card-title">Visit Outcomes</div>
            <div class="chart-card-sub">What happened when ASHA visited patients</div>
            {% if d.visit_outcomes %}
            <div class="outcome-grid">
                {% for vo in d.visit_outcomes %}
                {% set oc = vo.outcome %}
                {% if oc == 'stable' %}
                    {% set bg,fg,icon = '#f0fdf4','#16a34a','🟢' %}
                {% elif 'referred' in oc %}
                    {% set bg,fg,icon = '#fef6e4','#b45309','🏥' %}
                {% elif 'called_108' in oc %}
                    {% set bg,fg,icon = '#fdecea','#dc2626','🚑' %}
                {% elif 'not_found' in oc %}
                    {% set bg,fg,icon = '#f1f5f9','#64748b','❓' %}
                {% else %}
                    {% set bg,fg,icon = '#f1f5f9','#475569','📋' %}
                {% endif %}
                <div class="outcome-pill" style="background:{{ bg }};color:{{ fg }}">
                    {{ icon }} {{ oc|replace('_',' ')|title }}
                    <span style="font-size:13px;font-family:'Fraunces',serif">{{ vo.cnt }}</span>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p style="color:var(--pale);font-size:12px;padding:20px 0">No visit outcome data yet.</p>
            {% endif %}
        </div>
    </div>
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 2 — TRENDS
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-trends">

    <div style="padding:20px 32px">
        <div class="chart-card">
            <div class="chart-card-title">Daily Symptom Activity — Last {{ days }} Days</div>
            <div class="chart-card-sub">Stacked by severity: RED · AMBER · GREEN</div>
            <div class="chart-legend">
                <div class="legend-item"><div class="legend-dot" style="background:#e53935"></div>Danger (RED)</div>
                <div class="legend-item"><div class="legend-dot" style="background:#f4a61a"></div>Warning (AMBER)</div>
                <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>Normal (GREEN)</div>
            </div>
            <div style="overflow-x:auto">
                {{ stacked_area_chart }}
            </div>
        </div>
    </div>

    <div class="two-col" style="padding-top:0">
        <!-- Top symptoms -->
        <div class="chart-card">
            <div class="chart-card-title">Most Reported Symptoms</div>
            <div class="chart-card-sub">RED + AMBER reports — last 30 days</div>
            {% if d.top_symptoms %}
            <div style="overflow-x:auto">
                {{ top_symptoms_chart }}
            </div>
            {% else %}
            <p style="color:var(--pale);font-size:12px;padding:20px 0">No symptom data yet.</p>
            {% endif %}
        </div>

        <!-- Weekly registrations -->
        <div class="chart-card">
            <div class="chart-card-title">Weekly New Registrations</div>
            <div class="chart-card-sub">New patients joining MaaSakhi per week</div>
            {% if d.weekly_registrations %}
            <div style="overflow-x:auto">
                {{ weekly_reg_chart }}
            </div>
            {% else %}
            <p style="color:var(--pale);font-size:12px;padding:20px 0">No registration data yet.</p>
            {% endif %}
        </div>
    </div>

    <!-- Escalation breakdown -->
    <div style="padding:0 32px 20px">
        <div class="chart-card">
            <div class="chart-card-title">Escalation Breakdown</div>
            <div class="chart-card-sub">How many alerts reached each tier</div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;padding:10px 0">
                {% set esc_labels = {0:'Level 0 (ASHA only)', 1:'Level 1 (→ Supervisor)', 2:'Level 2 (→ BMO)', 3:'Level 3 (→ DHO)'} %}
                {% set esc_colors = {0:'var(--teal)',1:'var(--amber)',2:'var(--red)',3:'var(--purple)'} %}
                {% for lvl in range(4) %}
                {% set cnt = d.escalation_breakdown.get(lvl, 0) %}
                <div style="flex:1;min-width:120px;background:var(--bg);
                            border-radius:10px;padding:14px;text-align:center;
                            border:1px solid var(--border)">
                    <div style="font-family:'Fraunces',serif;font-size:28px;
                                font-weight:700;color:{{ esc_colors[lvl] }}">{{ cnt }}</div>
                    <div style="font-size:11px;color:var(--muted);margin-top:4px">
                        {{ esc_labels[lvl] }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 3 — VILLAGES
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-villages">

    <p class="sec">
        🗺️ Village Risk Rankings
        <span class="sec-badge">{{ d.village_risks|length }}</span>
    </p>

    {% if d.village_risks %}
    <div style="padding:0 32px 20px">
        <div class="chart-card" style="padding:0">
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Village</th>
                            <th>Patients</th>
                            <th>Active Alerts</th>
                            <th>Resolved</th>
                            <th>Avg Risk Score</th>
                            <th>Risk Level</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in d.village_risks %}
                        {% set bg, fg, lbl = risk_color(v.avg_risk) %}
                        <tr>
                            <td style="color:var(--pale);font-weight:600">{{ loop.index }}</td>
                            <td>
                                <div style="font-weight:600">{{ v.village }}</div>
                            </td>
                            <td style="text-align:center;font-weight:600">{{ v.total_patients }}</td>
                            <td style="text-align:center">
                                {% if v.active_alerts > 0 %}
                                <span style="color:var(--red);font-weight:700">{{ v.active_alerts }}</span>
                                {% else %}<span style="color:var(--teal)">0</span>{% endif %}
                            </td>
                            <td style="text-align:center;color:var(--teal-mid)">{{ v.resolved_alerts }}</td>
                            <td>
                                <div style="display:flex;align-items:center;gap:8px">
                                    <div style="flex:1;background:#f1f5f9;height:5px;border-radius:3px;overflow:hidden;min-width:60px">
                                        <div style="height:100%;border-radius:3px;background:{{ fg }};
                                                    width:{{ [v.avg_risk * 2, 100]|min }}%"></div>
                                    </div>
                                    <span style="font-size:11px;font-weight:600;color:{{ fg }}">
                                        {{ v.avg_risk }}
                                    </span>
                                </div>
                            </td>
                            <td>
                                <span class="rpill" style="background:{{ bg }};color:{{ fg }}">
                                    {{ lbl }}
                                </span>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% else %}
        <div style="text-align:center;padding:50px;color:var(--pale)">
            <div style="font-size:36px;margin-bottom:10px">🗺️</div>
            No village data available yet.
        </div>
    {% endif %}
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 4 — ASHA PERFORMANCE
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-ashas">

    <p class="sec">
        🏆 ASHA Leaderboard — Resolution Rate
        <span class="sec-badge">{{ d.asha_leaderboard|length }}</span>
    </p>

    {% if d.asha_leaderboard %}
    <div style="padding:0 32px 20px">
        <div class="chart-card" style="padding:0 0 8px">
            {% for a in d.asha_leaderboard %}
            {% set rank_cls = 'gold' if loop.index==1 else ('silver' if loop.index==2 else ('bronze' if loop.index==3 else '')) %}
            <div class="lb-row">
                <div class="lb-rank {{ rank_cls }}">
                    {% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}{{ loop.index }}{% endif %}
                </div>
                <div style="min-width:140px">
                    <div class="lb-name">{{ a.name }}</div>
                    <div class="lb-meta">📍 {{ a.village }} · {{ a.patients }} patients</div>
                </div>
                <div class="lb-bar">
                    <div style="display:flex;justify-content:space-between;
                                font-size:10px;color:var(--pale);margin-bottom:3px">
                        <span>Resolution</span>
                        <span>{{ a.resolution_rate }}%</span>
                    </div>
                    <div class="lb-bar-bg">
                        <div class="lb-bar-fill" style="width:{{ a.resolution_rate }}%"></div>
                    </div>
                    <div style="display:flex;gap:10px;margin-top:5px;flex-wrap:wrap">
                        <span style="font-size:10px;color:var(--teal)">
                            ✅ {{ a.resolved }} resolved
                        </span>
                        <span style="font-size:10px;color:var(--amber)">
                            ⬆ {{ a.escalated }} escalated
                        </span>
                        {% if a.avg_resp_hrs %}
                        <span style="font-size:10px;color:var(--muted)">
                            ⏱ {{ a.avg_resp_hrs }}h avg
                        </span>
                        {% endif %}
                    </div>
                </div>
                <div class="lb-val">{{ a.resolution_rate }}%</div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% else %}
        <div style="text-align:center;padding:50px;color:var(--pale)">
            <div style="font-size:36px;margin-bottom:10px">👩</div>
            No ASHA performance data yet.
        </div>
    {% endif %}

    <!-- Full table view -->
    {% if d.asha_leaderboard %}
    <p class="sec" style="margin-top:4px">📋 Full Performance Table</p>
    <div style="padding:0 32px 28px">
        <div class="chart-card" style="padding:0">
            <div class="tbl-wrap">
                <table>
                    <thead><tr>
                        <th>ASHA Name</th><th>Village</th><th>Patients</th>
                        <th>Alerts</th><th>Resolved</th><th>Escalated</th>
                        <th>Visits</th><th>Res. Rate</th><th>Avg Resp.</th>
                    </tr></thead>
                    <tbody>
                        {% for a in d.asha_leaderboard %}
                        <tr>
                            <td>
                                <a href="/dashboard/{{ a.asha_id }}" target="_blank"
                                   style="color:var(--teal);font-weight:600;text-decoration:none">
                                    {{ a.name }}
                                </a>
                            </td>
                            <td style="color:var(--muted)">{{ a.village }}</td>
                            <td style="text-align:center;font-weight:600">{{ a.patients }}</td>
                            <td style="text-align:center">{{ a.total_alerts }}</td>
                            <td style="text-align:center;color:var(--teal-mid);font-weight:600">{{ a.resolved }}</td>
                            <td style="text-align:center;color:{% if a.escalated > 0 %}var(--amber){% else %}var(--muted){% endif %}">
                                {{ a.escalated }}
                            </td>
                            <td style="text-align:center">{{ a.visits }}</td>
                            <td style="text-align:center">
                                <span style="font-weight:700;color:{% if a.resolution_rate >= 80 %}var(--teal){% elif a.resolution_rate >= 50 %}var(--amber){% else %}var(--red){% endif %}">
                                    {{ a.resolution_rate }}%
                                </span>
                            </td>
                            <td style="text-align:center;color:var(--muted)">
                                {% if a.avg_resp_hrs %}{{ a.avg_resp_hrs }}h{% else %}—{% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endif %}
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 5 — HEALTH METRICS
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-health">

    <!-- ANC Compliance Funnel -->
    <p class="sec">📋 ANC Compliance Funnel</p>
    <div style="padding:0 32px 20px">
        <div class="chart-card">
            <div class="chart-card-title">Antenatal Care Visit Coverage</div>
            <div class="chart-card-sub">
                % of registered patients who have completed each ANC visit
            </div>
            {% if d.anc_compliance %}
            <div class="anc-funnel">
                {% set anc_colors = ['#1ec99a','#0d8f72','#0a6e58','#054235'] %}
                {% for a in d.anc_compliance %}
                {% set bar_h = (a.pct / 100 * 76)|round|int %}
                <div class="anc-col">
                    <div class="anc-bar-wrap">
                        <div class="anc-bar"
                             style="height:{{ [bar_h, 4]|max }}px;
                                    background:{{ anc_colors[loop.index0] }}">
                        </div>
                    </div>
                    <div class="anc-pct" style="color:{{ anc_colors[loop.index0] }}">
                        {{ a.pct }}%
                    </div>
                    <div class="anc-lbl">ANC {{ a.visit }}</div>
                    <div class="anc-cnt">{{ a.count }} patients</div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p style="color:var(--pale);font-size:12px;padding:20px 0">No ANC data yet.</p>
            {% endif %}
        </div>
    </div>

    <!-- Postpartum + Child health KPIs -->
    <p class="sec">👶 Postpartum & Child Health</p>
    <div class="kpi-grid" style="padding-top:0">
        <div class="kpi">
            <div class="kpi-icon" style="background:#f5f3ff">🤱</div>
            <div class="kpi-num" style="color:var(--purple)">{{ d.postpartum_patients }}</div>
            <div class="kpi-lbl">Postpartum Mothers</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:var(--teal-pale)">🍼</div>
            <div class="kpi-num" style="color:var(--teal)">{{ d.total_deliveries }}</div>
            <div class="kpi-lbl">Deliveries Registered</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:var(--blue-pale)">👶</div>
            <div class="kpi-num" style="color:var(--blue)">{{ d.total_children }}</div>
            <div class="kpi-lbl">Children Tracked</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon" style="background:#fef6e4">💉</div>
            <div class="kpi-num" style="color:var(--amber)">—</div>
            <div class="kpi-lbl">Vaccines Given</div>
        </div>
    </div>

    <!-- Scheme deliveries -->
    {% if d.scheme_deliveries %}
    <p class="sec" style="margin-top:4px">🏛️ Government Scheme Deliveries</p>
    <div style="padding:0 32px 28px">
        <div class="chart-card">
            <div class="chart-card-title">Scheme Benefit Distribution</div>
            <div class="chart-card-sub">How many patients received each scheme</div>
            <div style="overflow-x:auto">
                {{ scheme_chart }}
            </div>
        </div>
    </div>
    {% endif %}
</div>


<!-- ═══════════════════════════════════════════════════════════
     TAB 6 — EXPORT
══════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-export">

    <p class="sec" style="margin-top:16px">📤 Data Exports</p>

    <div style="padding:0 32px">
        <div class="chart-card">
            <div class="chart-card-title">NHM-Compatible Exports</div>
            <div class="chart-card-sub">
                Download patient and health worker data in formats
                accepted by the National Health Mission HMIS portal.
            </div>

            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
                        gap:14px;margin-top:20px">

                <div style="background:var(--bg);border-radius:var(--r-sm);
                            padding:18px;border:1px solid var(--border)">
                    <div style="font-size:20px;margin-bottom:8px">📄</div>
                    <div style="font-weight:600;font-size:13px;margin-bottom:4px">
                        NHM Patient CSV
                    </div>
                    <div style="font-size:11.5px;color:var(--muted);margin-bottom:14px;line-height:1.6">
                        All registered patients with village, block, district,
                        ANC visits, alert history, delivery data.
                        HMIS-compatible column format.
                    </div>
                    <a href="/admin/export/nhm-csv" class="btn btn-teal">
                        ⬇ Download CSV
                    </a>
                </div>

                <div style="background:var(--bg);border-radius:var(--r-sm);
                            padding:18px;border:1px solid var(--border)">
                    <div style="font-size:20px;margin-bottom:8px">📑</div>
                    <div style="font-weight:600;font-size:13px;margin-bottom:4px">
                        Monthly PDF Report
                    </div>
                    <div style="font-size:11.5px;color:var(--muted);margin-bottom:14px;line-height:1.6">
                        Formatted monthly summary: patient count, ANC rates,
                        high-risk count, escalations, ASHA performance.
                        Ready to submit to NHM.
                    </div>
                    <a href="/admin/export/monthly-pdf" class="btn btn-blue">
                        ⬇ Download PDF
                    </a>
                </div>

                <div style="background:var(--bg);border-radius:var(--r-sm);
                            padding:18px;border:1px solid var(--border)">
                    <div style="font-size:20px;margin-bottom:8px">📊</div>
                    <div style="font-weight:600;font-size:13px;margin-bottom:4px">
                        Analytics JSON API
                    </div>
                    <div style="font-size:11.5px;color:var(--muted);margin-bottom:14px;line-height:1.6">
                        Raw analytics data as JSON for integration with
                        external dashboards or NHM district systems.
                    </div>
                    <div style="display:flex;gap:8px;flex-wrap:wrap">
                        <a href="/admin/api/trends" target="_blank" class="btn btn-ghost">
                            📈 Trends JSON
                        </a>
                        <a href="/admin/api/village-risks" target="_blank" class="btn btn-ghost">
                            🗺️ Village JSON
                        </a>
                    </div>
                </div>

            </div>

            <!-- Quick stats for NHM report -->
            <div style="margin-top:24px;padding:16px;background:var(--teal-tint);
                        border:1px solid var(--teal-pale);border-radius:var(--r-sm)">
                <div style="font-weight:600;font-size:13px;color:var(--teal);margin-bottom:12px">
                    📋 Current Month Summary (for NHM submission)
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px">
                    {% set nhm_items = [
                        ('Total Mothers Registered', d.total_patients),
                        ('ANC 1 Coverage',           d.anc_compliance[0].count if d.anc_compliance else 0),
                        ('ANC 4 (Full) Coverage',    d.anc_compliance[3].count if d.anc_compliance else 0),
                        ('Institutional Deliveries', d.total_deliveries),
                        ('High Risk Identified',     d.escalated_alerts),
                        ('Cases Resolved',           d.resolved_alerts),
                    ] %}
                    {% for label, val in nhm_items %}
                    <div>
                        <div style="font-size:11px;color:var(--muted)">{{ label }}</div>
                        <div style="font-family:'Fraunces',serif;font-size:20px;
                                    font-weight:700;color:var(--teal)">{{ val }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>


<!-- FOOTER -->
<div style="padding:16px 32px 6px;display:flex;gap:10px;flex-wrap:wrap">
    <a href="/admin" class="btn btn-dark" style="font-size:12px">← Admin Panel</a>
    <a href="/admin?tab=analytics" class="btn btn-ghost" style="font-size:12px">Refresh</a>
</div>

<div class="footer">
    🌿 MaaSakhi Analytics &nbsp;•&nbsp; Data as of {{ generated_at }} &nbsp;•&nbsp;
    WHO + NHM + FOGSI Guidelines &nbsp;•&nbsp;
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

    // Animate leaderboard bars on load
    window.addEventListener('load', () => {
        document.querySelectorAll('.lb-bar-fill').forEach(bar => {
            const w = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => { bar.style.width = w; }, 400);
        });
        document.querySelectorAll('.anc-bar').forEach(bar => {
            const h = bar.style.height;
            bar.style.height = '0px';
            setTimeout(() => { bar.style.height = h; }, 400);
        });
    });
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
# Called from admin.py: render_analytics()
# ─────────────────────────────────────────────────────────────────

def render_analytics(days: int = 30) -> str:
    """
    Fetches all analytics data and renders the full dashboard HTML.
    `days` controls the trend window (default 30).
    """
    data = get_analytics_data(days)

    # Pre-build all SVG charts server-side
    daily_totals = [d["total"] for d in data["daily_trend"]]
    alert_totals = [
        d.get("red", 0) for d in data["daily_trend"]
    ]

    sparklines = {
        "patients": _sparkline_svg(
            [data["total_patients"]] * 10, "#0d8f72", 80, 36
        ),
        "alerts": _sparkline_svg(alert_totals[-14:], "#e53935", 80, 36),
    }

    stacked_area_chart = _stacked_area_svg(data["daily_trend"], 640, 160)

    top_symptoms_chart = _bar_chart_svg(
        data["top_symptoms"], "msg", "cnt", "#e53935", 480, 200
    ) if data["top_symptoms"] else ""

    weekly_reg_chart = _bar_chart_svg(
        data["weekly_registrations"], "week", "count", "#0d8f72", 480, 180
    ) if data["weekly_registrations"] else ""

    scheme_chart = _bar_chart_svg(
        data["scheme_deliveries"], "name", "cnt", "#1565c0", 480, 140
    ) if data["scheme_deliveries"] else ""

    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    return render_template_string(
        ANALYTICS_HTML,
        d                  = data,
        days               = days,
        generated_at       = generated_at,
        sparklines         = sparklines,
        stacked_area_chart = stacked_area_chart,
        top_symptoms_chart = top_symptoms_chart,
        weekly_reg_chart   = weekly_reg_chart,
        scheme_chart       = scheme_chart,
        risk_color         = _risk_color,
    )