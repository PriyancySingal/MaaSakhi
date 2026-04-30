# ─────────────────────────────────────────────────────────────────
# MaaSakhi — reports.py
# Monthly PDF Report Generator (Month 3)
#
# Generates NHM-ready monthly summary PDF reports with:
#   • Cover page with district branding
#   • Executive summary KPIs
#   • Patient registration & ANC compliance
#   • Alert & escalation statistics
#   • ASHA worker performance table
#   • Village-level risk summary
#   • Postpartum & child health summary
#   • Govt scheme delivery tracking
#   • Signature / submission block
#
# Entry point: generate_monthly_pdf(month, year, district)
# Returns: bytes (PDF file content) — stream directly to browser
# ─────────────────────────────────────────────────────────────────

import io
from datetime import datetime, date, timedelta
from fpdf import FPDF

# ─────────────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────

# (R, G, B)
C_GREEN_DEEP   = (5,   66,  53)
C_GREEN_MID    = (13, 143, 114)
C_GREEN_LIGHT  = (212, 245, 235)
C_GREEN_PALE   = (240, 250, 246)
C_AMBER        = (244, 166,  26)
C_AMBER_PALE   = (254, 246, 228)
C_RED          = (229,  57,  53)
C_RED_PALE     = (253, 236, 234)
C_BLUE         = (21, 101, 192)
C_BLUE_PALE    = (227, 238, 255)
C_PURPLE       = (124,  58, 237)
C_INK          = (12,  30,  53)
C_MUTED        = (90, 113, 132)
C_PALE         = (148, 170, 184)
C_BORDER       = (221, 230, 237)
C_BG           = (244, 247, 250)
C_WHITE        = (255, 255, 255)


# ─────────────────────────────────────────────────────────────────
# DATA FETCHER
# ─────────────────────────────────────────────────────────────────

def _fetch_report_data(month: int, year: int) -> dict:
    """
    Pull all data needed for the monthly report from the DB.
    Returns a structured dict; falls back to zeros on any DB error.
    """
    from database import engine
    if not engine:
        return _empty_report_data(month, year)

    from sqlalchemy import text

    # Date range for this month
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    d = _empty_report_data(month, year)

    try:
        with engine.connect() as conn:

            # ── Patient counts ─────────────────────────────────
            d["total_patients"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients WHERE step='registered'
            """)).scalar() or 0

            d["new_patients_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients
                WHERE step='registered'
                  AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            d["postpartum_patients"] = conn.execute(text("""
                SELECT COUNT(*) FROM patients WHERE status='postpartum'
            """)).scalar() or 0

            d["total_deliveries"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
            """)).scalar() or 0

            d["deliveries_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM deliveries
                WHERE created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            # ── ANC compliance ─────────────────────────────────
            for v in range(1, 5):
                d[f"anc{v}_count"] = conn.execute(text("""
                    SELECT COUNT(DISTINCT phone) FROM anc_records
                    WHERE visit_number = :v
                """), {"v": v}).scalar() or 0

            d["anc_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM anc_records
                WHERE created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            # ── Alert statistics ───────────────────────────────
            d["total_alerts"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
            """)).scalar() or 0

            d["alerts_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            d["resolved_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE status='Resolved'
                  AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            d["pending_alerts"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts WHERE status='Pending'
            """)).scalar() or 0

            d["escalated_month"] = conn.execute(text("""
                SELECT COUNT(*) FROM asha_alerts
                WHERE escalation_level > 0
                  AND created_at >= :s AND created_at < :e
            """), {"s": start, "e": end}).scalar() or 0

            # ── ASHA workforce ─────────────────────────────────
            d["total_ashas"]       = conn.execute(text("SELECT COUNT(*) FROM asha_workers WHERE is_active=TRUE")).scalar() or 0
            d["total_supervisors"] = conn.execute(text("SELECT COUNT(*) FROM asha_supervisors WHERE is_active=TRUE")).scalar() or 0
            d["total_bmos"]        = conn.execute(text("SELECT COUNT(*) FROM block_officers WHERE is_active=TRUE")).scalar() or 0

            # ── ASHA performance rows ──────────────────────────
            perf_rows = conn.execute(text("""
                SELECT
                    aw.name,
                    aw.village,
                    COUNT(DISTINCT p.phone)                                   AS patients,
                    COUNT(DISTINCT aa.id)                                     AS alerts,
                    COUNT(DISTINCT CASE WHEN aa.status='Resolved' THEN aa.id END) AS resolved,
                    COUNT(DISTINCT CASE WHEN aa.escalation_level>0 THEN aa.id END) AS escalated,
                    COUNT(DISTINCT av.id)                                     AS visits
                FROM asha_workers aw
                LEFT JOIN patients    p  ON p.asha_id  = aw.asha_id AND p.step='registered'
                LEFT JOIN asha_alerts aa ON aa.asha_id = aw.asha_id
                    AND aa.created_at >= :s AND aa.created_at < :e
                LEFT JOIN asha_visits av ON av.asha_id = aw.asha_id
                    AND av.created_at >= :s AND av.created_at < :e
                WHERE aw.is_active = TRUE
                GROUP BY aw.asha_id, aw.name, aw.village
                ORDER BY resolved DESC, patients DESC
                LIMIT 20
            """), {"s": start, "e": end}).fetchall()

            d["asha_perf"] = [{
                "name":      r.name[:22],
                "village":   (r.village or "—")[:18],
                "patients":  int(r.patients),
                "alerts":    int(r.alerts),
                "resolved":  int(r.resolved),
                "escalated": int(r.escalated),
                "visits":    int(r.visits),
                "res_rate":  round(int(r.resolved) / int(r.alerts) * 100, 0)
                             if int(r.alerts) > 0 else 0,
            } for r in perf_rows]

            # ── Village risk summary ───────────────────────────
            vil_rows = conn.execute(text("""
                SELECT
                    p.village,
                    COUNT(DISTINCT p.phone)                                  AS patients,
                    COUNT(DISTINCT aa.id)                                    AS active_alerts,
                    AVG(CASE WHEN sl.level='RED' THEN 40
                             WHEN sl.level='AMBER' THEN 15
                             ELSE 2 END)                                     AS avg_risk
                FROM patients p
                LEFT JOIN asha_alerts  aa ON aa.phone=p.phone AND aa.status!='Resolved'
                LEFT JOIN symptom_logs sl ON sl.phone=p.phone
                WHERE p.step='registered'
                GROUP BY p.village
                ORDER BY avg_risk DESC NULLS LAST
                LIMIT 12
            """)).fetchall()

            d["village_risks"] = [{
                "village":       (r.village or "Unknown")[:20],
                "patients":      int(r.patients),
                "active_alerts": int(r.active_alerts or 0),
                "avg_risk":      round(float(r.avg_risk), 1) if r.avg_risk else 0,
            } for r in vil_rows]

            # ── Scheme deliveries ──────────────────────────────
            scheme_rows = conn.execute(text("""
                SELECT scheme_name, COUNT(*) AS cnt
                FROM scheme_deliveries
                WHERE created_at >= :s AND created_at < :e
                GROUP BY scheme_name ORDER BY cnt DESC
            """), {"s": start, "e": end}).fetchall()
            d["scheme_rows"] = [{"name": r.scheme_name[:35], "cnt": int(r.cnt)}
                                 for r in scheme_rows]
            d["total_scheme_deliveries"] = sum(r["cnt"] for r in d["scheme_rows"])

            # ── Child health ───────────────────────────────────
            d["total_children"] = conn.execute(text(
                "SELECT COUNT(*) FROM children"
            )).scalar() or 0
            d["total_vaccines"]  = conn.execute(text(
                "SELECT COUNT(*) FROM immunization_records"
            )).scalar() or 0
            d["total_growth_logs"] = conn.execute(text(
                "SELECT COUNT(*) FROM child_growth_logs"
            )).scalar() or 0

            # ── Visit outcomes ─────────────────────────────────
            out_rows = conn.execute(text("""
                SELECT outcome, COUNT(*) AS cnt
                FROM asha_visits
                WHERE created_at >= :s AND created_at < :e
                GROUP BY outcome ORDER BY cnt DESC
            """), {"s": start, "e": end}).fetchall()
            d["visit_outcomes"] = [{"outcome": r.outcome, "cnt": int(r.cnt)}
                                    for r in out_rows]
            d["total_visits_month"] = sum(r["cnt"] for r in d["visit_outcomes"])

    except Exception as e:
        print(f"reports.py _fetch_report_data error: {e}")

    # Derived
    if d["alerts_month"] > 0:
        d["resolution_rate_month"] = round(
            d["resolved_month"] / d["alerts_month"] * 100, 1
        )
    total_p = d["total_patients"] or 1
    for v in range(1, 5):
        d[f"anc{v}_pct"] = round(d[f"anc{v}_count"] / total_p * 100, 1)

    return d


def _empty_report_data(month: int, year: int) -> dict:
    return {
        "month": month, "year": year,
        "total_patients": 0, "new_patients_month": 0,
        "postpartum_patients": 0, "total_deliveries": 0, "deliveries_month": 0,
        "anc1_count": 0, "anc2_count": 0, "anc3_count": 0, "anc4_count": 0,
        "anc1_pct": 0, "anc2_pct": 0, "anc3_pct": 0, "anc4_pct": 0,
        "anc_month": 0,
        "total_alerts": 0, "alerts_month": 0, "resolved_month": 0,
        "pending_alerts": 0, "escalated_month": 0,
        "resolution_rate_month": 0.0,
        "total_ashas": 0, "total_supervisors": 0, "total_bmos": 0,
        "asha_perf": [], "village_risks": [],
        "scheme_rows": [], "total_scheme_deliveries": 0,
        "total_children": 0, "total_vaccines": 0, "total_growth_logs": 0,
        "visit_outcomes": [], "total_visits_month": 0,
    }


# ─────────────────────────────────────────────────────────────────
# PDF CLASS
# ─────────────────────────────────────────────────────────────────

class MaaSakhiReport(FPDF):
    """
    Custom FPDF subclass with MaaSakhi branding helpers.
    Uses only core fonts (Helvetica, Times) — no external font files needed.
    """

    def __init__(self, month_label: str, district: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.month_label = month_label
        self.district    = district
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 15, 18)

    # ── Header (called automatically on every page) ───────────────
    def header(self):
        if self.page_no() == 1:
            return   # cover page has its own full header

        # Thin green top bar
        self.set_fill_color(*C_GREEN_DEEP)
        self.rect(0, 0, 210, 7, "F")

        # Logo text
        self.set_xy(18, 10)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_GREEN_DEEP)
        self.cell(0, 5, "MaaSakhi — Monthly Health Report", ln=False)

        # Right-aligned month
        self.set_xy(0, 10)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_MUTED)
        self.cell(192, 5, f"{self.month_label}  |  {self.district}", align="R", ln=True)

        # Horizontal rule
        self.set_draw_color(*C_BORDER)
        self.line(18, 18, 192, 18)
        self.ln(6)

    # ── Footer ────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*C_BORDER)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*C_PALE)
        self.cell(0, 4,
                  f"MaaSakhi  |  Confidential — For NHM Official Use Only  |  Page {self.page_no()}",
                  align="C")

    # ── Helpers ───────────────────────────────────────────────────
    def _rgb(self, t):
        self.set_fill_color(*t)
        self.set_text_color(*t)

    def section_title(self, icon: str, title: str):
        """Coloured section heading with left accent bar."""
        self.ln(3)
        self.set_fill_color(*C_GREEN_DEEP)
        self.rect(self.get_x() - 18, self.get_y(), 4, 7, "F")
        self.set_x(self.get_x() - 14)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*C_GREEN_DEEP)
        self.cell(0, 7, f"  {icon}  {title}", ln=True)
        self.ln(2)

    def kpi_box(self, x, y, w, h, value, label, color=C_GREEN_MID, bg=C_GREEN_PALE):
        """Draw a single KPI tile."""
        self.set_fill_color(*bg)
        self.set_draw_color(*color)
        self.set_line_width(0.4)
        self.rect(x, y, w, h, "FD")
        # Value
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*color)
        self.set_xy(x, y + 2)
        self.cell(w, 10, str(value), align="C")
        # Label
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*C_MUTED)
        self.set_xy(x, y + 12)
        self.cell(w, 5, label, align="C")
        self.set_line_width(0.2)

    def table_header(self, cols: list[tuple[str, float, str]]):
        """
        cols: list of (label, width_mm, align)
        Draws a shaded header row.
        """
        self.set_fill_color(*C_GREEN_DEEP)
        self.set_text_color(*C_WHITE)
        self.set_font("Helvetica", "B", 8)
        for label, w, align in cols:
            self.cell(w, 6, label, border=0, fill=True, align=align)
        self.ln()

    def table_row(self, cells: list[tuple[str, float, str]],
                  even: bool = True, bold: bool = False):
        """Draws one data row with alternating background."""
        bg = C_GREEN_PALE if even else C_WHITE
        self.set_fill_color(*bg)
        self.set_text_color(*C_INK)
        self.set_font("Helvetica", "B" if bold else "", 8)
        for val, w, align in cells:
            self.cell(w, 5.5, str(val), border=0, fill=True, align=align)
        self.ln()

    def progress_bar(self, x, y, w, h, pct: float, color=C_GREEN_MID):
        """Mini horizontal progress bar."""
        self.set_fill_color(*C_BORDER)
        self.rect(x, y, w, h, "F")
        if pct > 0:
            fill_w = min(w * pct / 100, w)
            self.set_fill_color(*color)
            self.rect(x, y, fill_w, h, "F")

    def colored_badge(self, x, y, w, label: str, bg, fg):
        """Small rounded-corner badge."""
        self.set_fill_color(*bg)
        self.set_text_color(*fg)
        self.set_font("Helvetica", "B", 7.5)
        self.set_xy(x, y)
        self.cell(w, 4.5, label, align="C", fill=True)

    def divider(self):
        self.set_draw_color(*C_BORDER)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(4)


# ─────────────────────────────────────────────────────────────────
# PAGE BUILDERS
# ─────────────────────────────────────────────────────────────────

def _page_cover(pdf: MaaSakhiReport, d: dict, month_label: str, district: str,
                generated_at: str):
    """Full-bleed cover page."""
    pdf.add_page()

    # Deep green top band
    pdf.set_fill_color(*C_GREEN_DEEP)
    pdf.rect(0, 0, 210, 80, "F")

    # Decorative circle top-right
    pdf.set_fill_color(13, 143, 114)
    pdf.ellipse(160, -20, 80, 80, "F")
    pdf.set_fill_color(30, 201, 154)
    pdf.ellipse(170, -10, 50, 50, "F")

    # Logo / brand
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*C_WHITE)
    pdf.set_xy(18, 22)
    pdf.cell(0, 12, "MaaSakhi", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(148, 235, 200)
    pdf.set_x(18)
    pdf.cell(0, 6, "AI-Powered Maternal Health Monitoring System", ln=True)

    # Report title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*C_WHITE)
    pdf.set_xy(18, 50)
    pdf.cell(0, 8, "Monthly Health Report", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(200, 235, 220)
    pdf.set_x(18)
    pdf.cell(0, 6, f"{month_label}  —  {district}", ln=True)

    # White body area
    pdf.set_fill_color(*C_WHITE)
    pdf.rect(0, 80, 210, 217, "F")

    # ── Cover KPIs ────────────────────────────────────────────────
    pdf.set_xy(18, 90)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*C_GREEN_DEEP)
    pdf.cell(0, 7, "Key Highlights This Month", ln=True)
    pdf.ln(2)

    kpis = [
        (d["new_patients_month"],    "New\nRegistrations", C_GREEN_MID,    C_GREEN_PALE),
        (d["alerts_month"],          "Alerts\nRaised",     C_RED,          C_RED_PALE),
        (d["resolved_month"],        "Alerts\nResolved",   C_GREEN_MID,    C_GREEN_PALE),
        (d["deliveries_month"],      "Deliveries\nRecorded",C_PURPLE,      (245,240,255)),
        (d["anc_month"],             "ANC Visits\nLogged", C_BLUE,         C_BLUE_PALE),
        (d["total_scheme_deliveries"],"Scheme\nDeliveries", C_AMBER,       C_AMBER_PALE),
    ]
    kw, kh, kx, ky = 28, 22, 18, 103
    for i, (val, lbl, fg, bg) in enumerate(kpis):
        pdf.kpi_box(kx + i * 30, ky, kw, kh, val, lbl.replace("\n"," "), fg, bg)

    # ── Resolution rate big callout ───────────────────────────────
    rr = d["resolution_rate_month"]
    ry = 135
    pdf.set_fill_color(*C_GREEN_PALE)
    pdf.set_draw_color(*C_GREEN_MID)
    pdf.set_line_width(0.5)
    pdf.rect(18, ry, 174, 24, "FD")
    pdf.set_line_width(0.2)

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_GREEN_DEEP)
    pdf.set_xy(18, ry + 3)
    pdf.cell(40, 14, f"{rr}%", align="C")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_GREEN_DEEP)
    pdf.set_xy(60, ry + 4)
    pdf.cell(0, 6, "Monthly Alert Resolution Rate", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.set_xy(60, ry + 11)
    pdf.cell(0, 5, f"{d['resolved_month']} resolved out of {d['alerts_month']} alerts raised this month")

    # ── Workforce callout ─────────────────────────────────────────
    wy = 168
    pdf.set_fill_color(*C_BG)
    pdf.rect(18, wy, 174, 16, "F")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_INK)
    pdf.set_xy(18, wy + 3)
    pdf.cell(58, 5, f"  Active ASHA Workers: {d['total_ashas']}", ln=False)
    pdf.cell(58, 5, f"Supervisors: {d['total_supervisors']}", align="C", ln=False)
    pdf.cell(58, 5, f"Block Medical Officers: {d['total_bmos']}", align="R", ln=True)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.set_x(18)
    pdf.cell(0, 5, f"  Total Registered Patients: {d['total_patients']}  |  Cumulative Deliveries: {d['total_deliveries']}")

    # ── Footer metadata ───────────────────────────────────────────
    pdf.set_xy(18, 240)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_PALE)
    pdf.cell(0, 5, f"Generated: {generated_at}  |  Confidential — For NHM Official Use Only", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 5, "MaaSakhi  |  AI-Powered Maternal Health System  |  WHO + NHM + FOGSI Guidelines")

    # ── Bottom green bar ──────────────────────────────────────────
    pdf.set_fill_color(*C_GREEN_DEEP)
    pdf.rect(0, 280, 210, 17, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_WHITE)
    pdf.set_xy(0, 284)
    pdf.cell(210, 5, "MaaSakhi — Empowering Every Mother in Rural India", align="C")


def _page_patient_anc(pdf: MaaSakhiReport, d: dict):
    """Page 2: Patient Registration + ANC Compliance."""
    pdf.add_page()
    pdf.section_title("1.", "Patient Registration & ANC Compliance")

    # ── Registration summary boxes ────────────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5, "Patient Registration Overview", ln=True)
    pdf.ln(1)

    boxes = [
        (d["total_patients"],        "Total Registered",    C_GREEN_MID, C_GREEN_PALE),
        (d["new_patients_month"],    "New This Month",      C_BLUE,      C_BLUE_PALE),
        (d["postpartum_patients"],   "Postpartum",          C_PURPLE,    (245,240,255)),
        (d["total_deliveries"],      "Total Deliveries",    C_AMBER,     C_AMBER_PALE),
    ]
    bx, by, bw, bh = 18, pdf.get_y(), 40, 20
    for i, (val, lbl, fg, bg) in enumerate(boxes):
        pdf.kpi_box(bx + i * 44, by, bw, bh, val, lbl, fg, bg)
    pdf.set_y(by + bh + 6)

    # ── ANC Compliance funnel ─────────────────────────────────────
    pdf.section_title("", "ANC Visit Coverage")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5,
             "Percentage of registered patients who have completed each ANC visit "
             "(cumulative, not month-specific).", ln=True)
    pdf.ln(2)

    anc_items = [
        (1, "ANC 1", "Before 12 weeks",    d["anc1_count"], d["anc1_pct"]),
        (2, "ANC 2", "14–16 weeks",         d["anc2_count"], d["anc2_pct"]),
        (3, "ANC 3", "28–32 weeks",          d["anc3_count"], d["anc3_pct"]),
        (4, "ANC 4", "36 weeks",             d["anc4_count"], d["anc4_pct"]),
    ]
    anc_colors = [C_GREEN_MID, C_GREEN_DEEP, C_GREEN_MID, C_GREEN_DEEP]

    for i, (v, label, timing, count, pct) in enumerate(anc_items):
        y = pdf.get_y()

        # Left: label
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_INK)
        pdf.set_xy(18, y)
        pdf.cell(30, 7, label, align="L")

        # Timing
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*C_MUTED)
        pdf.set_xy(48, y + 1)
        pdf.cell(35, 5, timing)

        # Progress bar
        bar_x, bar_w = 88, 80
        pdf.progress_bar(bar_x, y + 2, bar_w, 4, pct, anc_colors[i])

        # Pct label
        pdf.set_font("Helvetica", "B", 9)
        color = C_GREEN_MID if pct >= 70 else (C_AMBER if pct >= 40 else C_RED)
        pdf.set_text_color(*color)
        pdf.set_xy(bar_x + bar_w + 3, y)
        pdf.cell(18, 7, f"{pct}%", align="L")

        # Count
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*C_MUTED)
        pdf.set_xy(bar_x + bar_w + 22, y)
        pdf.cell(25, 7, f"({count} patients)")

        pdf.ln(8)

    pdf.divider()

    # ── ANC compliance target comparison ─────────────────────────
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*C_INK)
    pdf.cell(0, 5, "NHM Target vs Achieved", ln=True)
    pdf.ln(1)

    nhm_targets = [(1, 95), (2, 90), (3, 85), (4, 75)]
    cols = [
        ("ANC Visit", 30, "L"),
        ("NHM Target", 30, "C"),
        ("Achieved", 30, "C"),
        ("Gap", 30, "C"),
        ("Status", 30, "C"),
    ]
    pdf.table_header(cols)
    for i, (v, target) in enumerate(nhm_targets):
        achieved = d[f"anc{v}_pct"]
        gap      = round(achieved - target, 1)
        status   = "✓ Met" if achieved >= target else "✗ Below"
        bg       = C_GREEN_PALE if achieved >= target else C_RED_PALE
        fg       = C_GREEN_DEEP  if achieved >= target else C_RED
        even     = (i % 2 == 0)
        pdf.table_row([
            (f"ANC {v}", 30, "L"),
            (f"{target}%", 30, "C"),
            (f"{achieved}%", 30, "C"),
            (f"{gap:+.1f}%", 30, "C"),
            (status, 30, "C"),
        ], even=even)


def _page_alerts(pdf: MaaSakhiReport, d: dict):
    """Page 3: Alert & Escalation Statistics."""
    pdf.add_page()
    pdf.section_title("2.", "Alert & Escalation Statistics")

    # KPI boxes
    alert_boxes = [
        (d["alerts_month"],   "Alerts This Month", C_RED,      C_RED_PALE),
        (d["resolved_month"], "Resolved",          C_GREEN_MID, C_GREEN_PALE),
        (d["escalated_month"],"Escalated",         C_AMBER,    C_AMBER_PALE),
        (d["pending_alerts"], "Still Pending",     C_RED,      C_RED_PALE),
    ]
    bx, by, bw, bh = 18, pdf.get_y(), 40, 20
    for i, (val, lbl, fg, bg) in enumerate(alert_boxes):
        pdf.kpi_box(bx + i * 44, by, bw, bh, val, lbl, fg, bg)
    pdf.set_y(by + bh + 6)

    # Resolution rate bar
    rr = d["resolution_rate_month"]
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_INK)
    pdf.cell(60, 6, "Monthly Resolution Rate:", ln=False)
    pdf.set_font("Helvetica", "B", 12)
    color = C_GREEN_MID if rr >= 80 else (C_AMBER if rr >= 50 else C_RED)
    pdf.set_text_color(*color)
    pdf.cell(25, 6, f"{rr}%", ln=False)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 6, f"  ({d['resolved_month']} of {d['alerts_month']} alerts resolved)", ln=True)
    pdf.ln(1)
    pdf.progress_bar(18, pdf.get_y(), 174, 5, rr, color)
    pdf.ln(8)

    # Visit outcomes
    if d["visit_outcomes"]:
        pdf.section_title("", "Visit Outcome Breakdown")
        cols = [("Outcome", 80, "L"), ("Count", 30, "C"), ("% of Visits", 40, "C")]
        pdf.table_header(cols)
        total_v = d["total_visits_month"] or 1
        for i, vo in enumerate(d["visit_outcomes"]):
            pct = round(vo["cnt"] / total_v * 100, 1)
            label = vo["outcome"].replace("_", " ").title()
            pdf.table_row([
                (label, 80, "L"),
                (str(vo["cnt"]), 30, "C"),
                (f"{pct}%", 40, "C"),
            ], even=(i % 2 == 0))
        pdf.ln(4)

    # Escalation breakdown
    pdf.section_title("", "Escalation Level Breakdown")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5,
             "Number of alerts that reached each tier of the 5-level hierarchy.", ln=True)
    pdf.ln(2)

    from database import engine
    esc_map = {0: 0, 1: 0, 2: 0, 3: 0}
    if engine:
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                rows = conn.execute(text("""
                    SELECT escalation_level, COUNT(*) AS cnt
                    FROM asha_alerts GROUP BY escalation_level
                """)).fetchall()
                for r in rows:
                    esc_map[int(r.escalation_level)] = int(r.cnt)
        except Exception:
            pass

    esc_labels = {
        0: "Level 0 — ASHA Only (resolved without escalating)",
        1: "Level 1 — Escalated to Supervisor (ANM)",
        2: "Level 2 — Escalated to BMO",
        3: "Level 3 — Escalated to DHO",
    }
    esc_colors = {0: C_GREEN_MID, 1: C_AMBER, 2: C_RED, 3: C_PURPLE}
    total_esc  = sum(esc_map.values()) or 1

    for lvl in range(4):
        cnt  = esc_map[lvl]
        pct  = round(cnt / total_esc * 100, 1)
        y    = pdf.get_y()
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*C_INK)
        pdf.set_xy(18, y)
        pdf.cell(95, 6, esc_labels[lvl])
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*esc_colors[lvl])
        pdf.cell(18, 6, str(cnt), align="C")
        pdf.set_text_color(*C_MUTED)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(20, 6, f"({pct}%)", align="C")
        pdf.ln(7)
        pdf.progress_bar(18, pdf.get_y() - 3, 174, 3, pct, esc_colors[lvl])
        pdf.ln(2)


def _page_asha_performance(pdf: MaaSakhiReport, d: dict):
    """Page 4: ASHA Worker Performance Table."""
    pdf.add_page()
    pdf.section_title("3.", "ASHA Worker Performance")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5,
             "Performance data for this reporting period. "
             "Resolution Rate = Resolved Alerts / Total Alerts × 100.", ln=True)
    pdf.ln(2)

    if not d["asha_perf"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 8, "No ASHA performance data available for this period.", ln=True)
        return

    cols = [
        ("ASHA Name",   40, "L"),
        ("Village",     34, "L"),
        ("Patients",    18, "C"),
        ("Alerts",      18, "C"),
        ("Resolved",    18, "C"),
        ("Escalated",   18, "C"),
        ("Visits",      15, "C"),
        ("Res. %",      13, "C"),
    ]
    pdf.table_header(cols)

    for i, a in enumerate(d["asha_perf"]):
        rr = a["res_rate"]
        # Colour resolution rate
        rr_color = (
            C_GREEN_MID if rr >= 80
            else C_AMBER if rr >= 50
            else C_RED
        )
        even = (i % 2 == 0)
        bg = C_GREEN_PALE if even else C_WHITE
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*C_INK)
        pdf.set_font("Helvetica", "", 8)

        # Draw cells manually so we can colour the last one
        for val, w, align in [
            (a["name"],          40, "L"),
            (a["village"],       34, "L"),
            (a["patients"],      18, "C"),
            (a["alerts"],        18, "C"),
            (a["resolved"],      18, "C"),
            (a["escalated"],     18, "C"),
            (a["visits"],        15, "C"),
        ]:
            pdf.cell(w, 5.5, str(val), border=0, fill=True, align=align)

        # Resolution rate with colour
        pdf.set_text_color(*rr_color)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(13, 5.5, f"{rr:.0f}%", border=0, fill=True, align="C")
        pdf.ln()

    # Summary row
    total_a   = sum(a["alerts"]   for a in d["asha_perf"])
    total_r   = sum(a["resolved"] for a in d["asha_perf"])
    total_esc = sum(a["escalated"] for a in d["asha_perf"])
    total_v   = sum(a["visits"]   for a in d["asha_perf"])
    agg_rr    = round(total_r / total_a * 100, 1) if total_a else 0

    pdf.set_fill_color(*C_GREEN_DEEP)
    pdf.set_text_color(*C_WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for val, w, align in [
        ("TOTAL", 74, "L"),
        (total_a, 18, "C"),
        (total_r, 18, "C"),
        (total_esc, 18, "C"),
        (total_v, 15, "C"),
        (f"{agg_rr}%", 13, "C"),
    ]:
        pdf.cell(w, 5.5, str(val), border=0, fill=True, align=align)
    pdf.ln(8)

    # Top performer callout
    if d["asha_perf"]:
        best = max(d["asha_perf"], key=lambda a: a["res_rate"])
        pdf.set_fill_color(*C_GREEN_PALE)
        pdf.set_draw_color(*C_GREEN_MID)
        pdf.set_line_width(0.4)
        pdf.rect(18, pdf.get_y(), 174, 12, "FD")
        pdf.set_line_width(0.2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_GREEN_DEEP)
        pdf.set_xy(22, pdf.get_y() + 1.5)
        pdf.cell(0, 5,
                 f"🌟 Top Performer: {best['name']} ({best['village']}) "
                 f"— Resolution Rate {best['res_rate']:.0f}%  |  "
                 f"{best['resolved']} alerts resolved", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*C_MUTED)
        pdf.set_x(22)
        pdf.cell(0, 4.5,
                 f"Patients: {best['patients']}  |  "
                 f"Visits: {best['visits']}  |  "
                 f"Escalations: {best['escalated']}")


def _page_village_risk(pdf: MaaSakhiReport, d: dict):
    """Page 5: Village-Level Risk Summary."""
    pdf.add_page()
    pdf.section_title("4.", "Village-Level Risk Summary")

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5,
             "Villages ranked by average patient risk score. "
             "Score: RED=40pts, AMBER=15pts, GREEN=2pts per report.", ln=True)
    pdf.ln(2)

    if not d["village_risks"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 8, "No village data available.", ln=True)
        return

    cols = [
        ("#",           8,  "C"),
        ("Village",    42,  "L"),
        ("Patients",   22,  "C"),
        ("Active Alerts", 28, "C"),
        ("Avg Risk Score", 30, "C"),
        ("Risk Level", 28,  "C"),
        ("Bar",        16,  "L"),
    ]
    pdf.table_header(cols)

    max_risk = max((v["avg_risk"] for v in d["village_risks"]), default=1) or 1
    for i, v in enumerate(d["village_risks"]):
        score = v["avg_risk"]
        if score >= 30:
            level, bg, fg = "HIGH",   C_RED_PALE,   C_RED
        elif score >= 12:
            level, bg, fg = "MEDIUM", C_AMBER_PALE, C_AMBER
        else:
            level, bg, fg = "LOW",    C_GREEN_PALE, C_GREEN_MID

        even = (i % 2 == 0)
        row_bg = (240, 250, 246) if even else C_WHITE
        pdf.set_fill_color(*row_bg)
        pdf.set_text_color(*C_INK)
        pdf.set_font("Helvetica", "", 8)

        y = pdf.get_y()
        for val, w, align in [
            (i + 1,             8,  "C"),
            (v["village"],     42,  "L"),
            (v["patients"],    22,  "C"),
            (v["active_alerts"],28, "C"),
            (f"{score:.1f}",   30,  "C"),
        ]:
            pdf.cell(w, 6, str(val), border=0, fill=True, align=align)

        # Risk level badge
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*fg)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(28, 6, level, border=0, fill=True, align="C")

        # Mini bar
        bar_x = pdf.get_x() + 1
        bar_y = y + 2
        bar_w = min(14 * score / max_risk, 14)
        pdf.set_fill_color(*row_bg)
        pdf.cell(16, 6, "", border=0, fill=True)
        if bar_w > 0:
            pdf.set_fill_color(*fg)
            pdf.rect(bar_x, bar_y, bar_w, 2.5, "F")

        pdf.ln()

    # Risk distribution summary
    high   = sum(1 for v in d["village_risks"] if v["avg_risk"] >= 30)
    medium = sum(1 for v in d["village_risks"] if 12 <= v["avg_risk"] < 30)
    low    = sum(1 for v in d["village_risks"] if v["avg_risk"] < 12)

    pdf.ln(4)
    pdf.set_fill_color(*C_BG)
    pdf.rect(18, pdf.get_y(), 174, 10, "F")
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_xy(22, pdf.get_y() + 2.5)
    pdf.set_text_color(*C_RED)
    pdf.cell(55, 5, f"High Risk Villages: {high}", ln=False)
    pdf.set_text_color(*C_AMBER)
    pdf.cell(60, 5, f"Medium Risk: {medium}", ln=False)
    pdf.set_text_color(*C_GREEN_MID)
    pdf.cell(55, 5, f"Low Risk: {low}", ln=True)


def _page_child_health(pdf: MaaSakhiReport, d: dict):
    """Page 6: Postpartum, Child Health & Govt Schemes."""
    pdf.add_page()
    pdf.section_title("5.", "Postpartum & Child Health")

    # KPIs
    boxes = [
        (d["postpartum_patients"], "Postpartum Mothers", C_PURPLE,    (245, 240, 255)),
        (d["total_deliveries"],    "Deliveries Registered", C_GREEN_MID, C_GREEN_PALE),
        (d["total_children"],      "Children Tracked",   C_BLUE,      C_BLUE_PALE),
        (d["total_vaccines"],      "Vaccines Given",     C_AMBER,     C_AMBER_PALE),
    ]
    bx, by, bw, bh = 18, pdf.get_y(), 40, 20
    for i, (val, lbl, fg, bg) in enumerate(boxes):
        pdf.kpi_box(bx + i * 44, by, bw, bh, val, lbl, fg, bg)
    pdf.set_y(by + bh + 6)

    # Growth logs
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)
    pdf.cell(0, 5,
             f"Child growth measurements recorded: {d['total_growth_logs']}  |  "
             f"PNC check-ins this month: Tracked via ASHA visit logs.", ln=True)
    pdf.ln(4)

    pdf.divider()

    # ── Govt Scheme Deliveries ────────────────────────────────────
    pdf.section_title("6.", "Government Scheme Deliveries")

    if not d["scheme_rows"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 8, "No scheme delivery records for this period.", ln=True)
    else:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 5,
                 f"Total scheme deliveries recorded this month: "
                 f"{d['total_scheme_deliveries']}", ln=True)
        pdf.ln(2)

        cols = [("Scheme Name", 120, "L"), ("Beneficiaries", 40, "C"), ("Share %", 14, "C")]
        pdf.table_header(cols)
        total_s = d["total_scheme_deliveries"] or 1
        for i, s in enumerate(d["scheme_rows"]):
            pct = round(s["cnt"] / total_s * 100, 1)
            pdf.table_row([
                (s["name"], 120, "L"),
                (s["cnt"],   40, "C"),
                (f"{pct}%", 14, "C"),
            ], even=(i % 2 == 0))
        pdf.ln(4)


def _page_signature(pdf: MaaSakhiReport, d: dict, month_label: str,
                    district: str, generated_at: str):
    """Final page: Observations, Recommendations & Signature Block."""
    pdf.add_page()
    pdf.section_title("7.", "Observations & Recommendations")

    # Auto-generated observations based on data
    observations = _generate_observations(d)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_INK)
    for obs in observations:
        pdf.set_x(18)
        pdf.multi_cell(174, 5.5, f"  {obs}", ln=True)
        pdf.ln(1)

    pdf.ln(4)
    pdf.divider()

    # ── NHM Submission Details ────────────────────────────────────
    pdf.section_title("", "NHM Report Submission Details")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*C_MUTED)

    meta_items = [
        ("Reporting Period:",     month_label),
        ("District:",              district),
        ("Report Generated:",      generated_at),
        ("Total ASHA Workers:",    str(d["total_ashas"])),
        ("Total Registered Patients:", str(d["total_patients"])),
        ("Overall Resolution Rate:",   f"{d['resolution_rate_month']}%"),
        ("System Version:",        "MaaSakhi v2.0"),
        ("Guidelines:",            "WHO ANC Guidelines 2016  |  NHM RMNCH+A  |  FOGSI"),
    ]
    for label, val in meta_items:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*C_INK)
        pdf.set_x(18)
        pdf.cell(68, 6, label, ln=False)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*C_MUTED)
        pdf.cell(0, 6, val, ln=True)

    pdf.ln(6)
    pdf.divider()

    # ── Signature block ───────────────────────────────────────────
    pdf.section_title("", "Verification & Submission")
    pdf.ln(2)

    sig_boxes = [
        ("Prepared by\n(ASHA Supervisor / ANM)", "Name: ___________________\nSignature: ______________\nDate: ___________________"),
        ("Reviewed by\n(Block Medical Officer)",  "Name: ___________________\nSignature: ______________\nDate: ___________________"),
        ("Approved by\n(District Health Officer)","Name: ___________________\nSignature: ______________\nDate: ___________________"),
    ]
    sx = 18
    for title, lines in sig_boxes:
        sy = pdf.get_y()
        pdf.set_fill_color(*C_BG)
        pdf.set_draw_color(*C_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(sx, sy, 56, 32, "FD")
        pdf.set_line_width(0.2)

        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*C_GREEN_DEEP)
        pdf.set_xy(sx + 2, sy + 2)
        for t in title.split("\n"):
            pdf.cell(52, 4.5, t, ln=True)
            pdf.set_x(sx + 2)

        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(*C_MUTED)
        pdf.set_xy(sx + 2, sy + 12)
        for line in lines.split("\n"):
            pdf.cell(52, 5, line, ln=True)
            pdf.set_x(sx + 2)
        pdf.set_y(sy)
        sx += 60

    pdf.set_y(pdf.get_y() + 36)
    pdf.ln(4)

    # Official stamp box
    pdf.set_fill_color(*C_BG)
    pdf.set_draw_color(*C_BORDER)
    pdf.set_line_width(0.3)
    pdf.rect(18, pdf.get_y(), 174, 16, "FD")
    pdf.set_line_width(0.2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*C_MUTED)
    pdf.set_xy(22, pdf.get_y() + 2)
    pdf.cell(0, 5, "Official Stamp / Seal:", ln=True)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_x(22)
    pdf.cell(0, 5,
             "This report is generated by MaaSakhi — an AI-powered maternal health "
             "monitoring system operating under NHM guidelines.")


def _generate_observations(d: dict) -> list:
    """
    Auto-generate plain-language observations from the data.
    Returns a list of bullet-point strings.
    """
    obs = []
    rr = d["resolution_rate_month"]

    if rr >= 80:
        obs.append(
            f"✓ Strong performance: {rr}% alert resolution rate this month exceeds "
            "the NHM target of 80%."
        )
    elif rr >= 50:
        obs.append(
            f"⚠ Alert resolution rate of {rr}% is below the NHM target of 80%. "
            "Supervisor follow-up is recommended."
        )
    else:
        obs.append(
            f"✗ Critical: Alert resolution rate of {rr}% is significantly below target. "
            "Immediate district-level review required."
        )

    if d["escalated_month"] > 0:
        esc_pct = round(d["escalated_month"] / (d["alerts_month"] or 1) * 100, 1)
        if esc_pct > 30:
            obs.append(
                f"✗ High escalation rate: {esc_pct}% of alerts escalated beyond ASHA level. "
                "Capacity building and supervision may be needed."
            )
        else:
            obs.append(
                f"✓ Escalation rate of {esc_pct}% is within acceptable range."
            )

    # ANC compliance
    if d["anc4_pct"] < 50:
        obs.append(
            f"⚠ Only {d['anc4_pct']}% of registered patients have completed all 4 ANC visits. "
            "ASHA workers should be counselled to improve ANC follow-up."
        )
    elif d["anc4_pct"] >= 75:
        obs.append(
            f"✓ ANC 4 coverage of {d['anc4_pct']}% meets the NHM target of 75%. "
            "Strong antenatal follow-up by ASHA workers."
        )

    # High risk villages
    high_risk_villages = [v for v in d["village_risks"] if v["avg_risk"] >= 30]
    if high_risk_villages:
        names = ", ".join(v["village"] for v in high_risk_villages[:3])
        obs.append(
            f"⚠ {len(high_risk_villages)} high-risk village(s) identified: {names}. "
            "Priority outreach and increased ASHA supervision recommended."
        )

    # Pending alerts
    if d["pending_alerts"] > 5:
        obs.append(
            f"✗ {d['pending_alerts']} alert(s) remain pending as of report generation. "
            "Immediate follow-up required by respective ASHA workers and supervisors."
        )
    elif d["pending_alerts"] == 0:
        obs.append("✓ No pending alerts at time of report generation.")

    # Scheme delivery
    if d["total_scheme_deliveries"] > 0:
        obs.append(
            f"✓ {d['total_scheme_deliveries']} government scheme benefit(s) delivered "
            "to patients this month."
        )

    return obs


# ─────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────

def generate_monthly_pdf(
    month:    int = None,
    year:     int = None,
    district: str = "District"
) -> bytes:
    """
    Generate the full monthly PDF report and return it as bytes.

    Usage in app.py:
        from reports import generate_monthly_pdf
        pdf_bytes = generate_monthly_pdf()
        return Response(pdf_bytes, mimetype='application/pdf',
                        headers={'Content-Disposition':
                                 'attachment; filename=Report.pdf'})

    Defaults to the current month/year if not specified.
    """
    now   = datetime.now()
    month = month or now.month
    year  = year  or now.year

    month_label  = datetime(year, month, 1).strftime("%B %Y")
    generated_at = now.strftime("%d %b %Y, %I:%M %p")

    # Fetch data
    d = _fetch_report_data(month, year)

    # Build PDF
    pdf = MaaSakhiReport(month_label=month_label, district=district)

    _page_cover(pdf, d, month_label, district, generated_at)
    _page_patient_anc(pdf, d)
    _page_alerts(pdf, d)
    _page_asha_performance(pdf, d)
    _page_village_risk(pdf, d)
    _page_child_health(pdf, d)
    _page_signature(pdf, d, month_label, district, generated_at)

    # Return as bytes
    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────────
# QUICK SELF-TEST  (python reports.py)
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating test PDF report...")
    pdf_bytes = generate_monthly_pdf(district="Jaipur District")
    with open("/tmp/maasakhi_test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"Done — {len(pdf_bytes):,} bytes written to /tmp/maasakhi_test_report.pdf")