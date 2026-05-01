# -----------------------------------------------------------------
# MaaSakhi Admin Panel
# Full 5-Tier Hierarchy + All 4-Month Features
# -----------------------------------------------------------------

from flask import render_template_string, request, redirect, session


# =================================================================
# HTML BUILDERS — return strings, no triple quotes
# =================================================================

def _base_styles():
    lines = [
        "<style>",
        "* { margin:0; padding:0; box-sizing:border-box; }",
        "body { font-family:'Segoe UI',Arial,sans-serif; background:#0f0f1a; color:#e0e0f0; }",
        ".topbar { background:#1a0a3a; padding:16px 24px; display:flex;",
        "          justify-content:space-between; align-items:center;",
        "          border-bottom:2px solid #5B2FBF; }",
        ".topbar h1 { font-size:20px; color:#A78BFA; }",
        ".logout { color:#ff6b6b; font-size:12px; text-decoration:none; }",
        ".stats { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; padding:20px; }",
        ".stat { background:#1a1a2e; border-radius:12px; padding:16px; text-align:center;",
        "        border:1px solid #2a2a4a; transition:.2s; }",
        ".stat:hover { border-color:#5B2FBF; transform:translateY(-2px); }",
        ".stat-number { font-size:30px; font-weight:bold; }",
        ".stat-label  { font-size:10px; color:#888; margin-top:4px; text-transform:uppercase; letter-spacing:.04em; }",
        ".section-title { padding:8px 20px; font-size:11px; font-weight:bold; color:#A78BFA;",
        "                 text-transform:uppercase; letter-spacing:.06em; margin-top:8px; }",
        ".card { margin:0 20px 12px; background:#1a1a2e; border-radius:12px;",
        "        padding:20px; border:1px solid #2a2a4a; }",
        ".form-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr));",
        "            gap:10px; margin-bottom:12px; }",
        "input,select { width:100%; padding:10px 12px; background:#0f0f1a;",
        "               border:1px solid #3a3a5a; border-radius:8px;",
        "               color:#e0e0f0; font-size:13px; }",
        "input::placeholder { color:#555; }",
        ".btn { padding:10px 20px; border:none; border-radius:8px;",
        "       font-size:13px; cursor:pointer; font-weight:bold; transition:.15s; }",
        ".btn:hover { opacity:.88; transform:translateY(-1px); }",
        ".btn-primary { background:#5B2FBF; color:white; }",
        ".btn-danger  { background:#991b1b; color:white; }",
        ".btn-success { background:#065f46; color:white; }",
        ".btn-blue    { background:#1565c0; color:white; }",
        ".btn-amber   { background:#92400e; color:white; }",
        ".btn-sm { padding:5px 11px; font-size:11px; }",
        "table { width:100%; border-collapse:collapse; font-size:13px; }",
        "th { text-align:left; padding:10px 12px; background:#12122a; color:#A78BFA;",
        "     font-size:11px; text-transform:uppercase; letter-spacing:.04em; }",
        "td { padding:10px 12px; border-bottom:1px solid #1e1e3a; color:#c0c0d8; }",
        "tr:hover td { background:#1e1e38; }",
        ".badge { display:inline-block; padding:3px 10px; border-radius:20px;",
        "         font-size:10px; font-weight:bold; }",
        ".badge-active   { background:#064e3b; color:#6ee7b7; }",
        ".badge-inactive { background:#7f1d1d; color:#fca5a5; }",
        ".badge-red      { background:#7f1d1d; color:#fca5a5; }",
        ".badge-amber    { background:#78350f; color:#fcd34d; }",
        ".badge-green    { background:#064e3b; color:#6ee7b7; }",
        ".badge-purple   { background:#2e1065; color:#c4b5fd; }",
        ".badge-blue     { background:#1e3a5f; color:#93c5fd; }",
        ".msg { padding:10px 16px; border-radius:8px; margin:0 20px 12px; font-size:13px; }",
        ".msg-success { background:#064e3b; color:#6ee7b7; }",
        ".msg-error   { background:#7f1d1d; color:#fca5a5; }",
        ".tab-bar { display:flex; gap:2px; padding:12px 20px 0;",
        "           border-bottom:1px solid #2a2a4a; overflow-x:auto; }",
        ".tab { padding:8px 16px; border-radius:8px 8px 0 0; font-size:12px; font-weight:bold;",
        "       cursor:pointer; text-decoration:none; color:#888; background:#12122a; white-space:nowrap; }",
        ".tab.active { background:#1a1a2e; color:#A78BFA; border-bottom:2px solid #5B2FBF; }",
        ".village-group { background:#12122a; border-radius:8px; padding:12px 16px;",
        "                 margin-bottom:8px; border-left:3px solid #5B2FBF; }",
        ".village-name  { font-size:13px; color:#A78BFA; font-weight:bold; margin-bottom:6px; }",
        ".asha-chip { display:inline-block; background:#1e1e3a; border:1px solid #3a3a5a;",
        "             border-radius:20px; padding:4px 12px; font-size:11px; margin:3px; color:#c0c0d8; }",
        ".kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; }",
        ".kpi { background:#12122a; border-radius:10px; padding:14px; text-align:center; border:1px solid #2a2a4a; }",
        ".kpi-num { font-size:26px; font-weight:bold; }",
        ".kpi-lbl { font-size:10px; color:#888; margin-top:3px; text-transform:uppercase; letter-spacing:.04em; }",
        ".perf-bar { height:5px; background:#1e1e3a; border-radius:3px; overflow:hidden; margin-top:4px; }",
        ".perf-fill { height:100%; border-radius:3px; background:#5B2FBF; transition:width 1s ease; }",
        ".export-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; }",
        ".export-card { background:#12122a; border-radius:10px; padding:18px;",
        "               border:1px solid #2a2a4a; }",
        ".export-card h4 { color:#A78BFA; font-size:13px; margin-bottom:6px; }",
        ".export-card p  { font-size:12px; color:#888; margin-bottom:14px; line-height:1.6; }",
        ".footer { text-align:center; font-size:11px; color:#333; padding:20px; }",
        "@media(max-width:768px) { .stats { grid-template-columns:repeat(2,1fr); }",
        "    .form-row { grid-template-columns:1fr; } }",
        "</style>",
    ]
    return "\n".join(lines)


def _head(title="MaaSakhi Admin"):
    lines = [
        "<!DOCTYPE html><html>",
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>" + title + "</title>",
        '<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700&display=swap" rel="stylesheet">',
        _base_styles(),
        "</head><body>",
    ]
    return "\n".join(lines)


def _topbar(admin_name):
    return (
        '<div class="topbar">'
        '<h1 style="font-family:Syne,sans-serif">🌿 MaaSakhi — Admin Panel</h1>'
        '<div><span style="font-size:12px;color:#888">Logged in as ' + admin_name + '</span>'
        ' &nbsp; <a href="/admin/logout" class="logout">Logout</a></div>'
        '</div>'
    )


def _flash(message, success):
    if not message:
        return ""
    cls = "msg-success" if success else "msg-error"
    return '<div class="msg ' + cls + '">' + message + '</div>'


def _tab_bar(tab):
    tabs = [
        ("asha",         "👩 ASHA Workers"),
        ("supervisors",  "👩‍💼 Supervisors"),
        ("bmo",          "🏥 BMOs"),
        ("map",          "🗺️ Village Map"),
        ("patients",     "🤰 Patients"),
        ("alerts",       "🚨 Alerts"),
        ("analytics",    "📊 Analytics"),
        ("performance",  "🏆 Performance"),
        ("export",       "📤 Export"),
    ]
    parts = ['<div class="tab-bar">']
    for key, label in tabs:
        active = " active" if tab == key else ""
        parts.append(
            '<a href="/admin?tab=' + key + '" class="tab' + active + '">' + label + '</a>'
        )
    parts.append("</div>")
    return "\n".join(parts)


# =================================================================
# TAB CONTENT BUILDERS
# =================================================================

def _tab_asha(asha_workers, asha_stats, all_supervisors, total_asha):
    lines = []

    # Add form
    lines.append('<div class="card" style="margin-top:16px">')
    lines.append('<p style="font-size:13px;color:#A78BFA;font-weight:bold;margin-bottom:14px">➕ Add New ASHA Worker</p>')
    lines.append('<form method="POST" action="/admin/add-asha">')
    lines.append('<div class="form-row">')
    lines.append('<input name="asha_id"       placeholder="ASHA ID (e.g. ASHA_001)" required />')
    lines.append('<input name="name"          placeholder="Full Name" required />')
    lines.append('<input name="phone"         placeholder="WhatsApp: whatsapp:+91..." required />')
    lines.append('<input name="village"       placeholder="Village Name" required />')
    lines.append('<input name="block_name"    placeholder="Block Name" />')
    lines.append('<input name="district"      placeholder="District" />')

    # Supervisor dropdown
    lines.append('<select name="supervisor_id">')
    lines.append('<option value="">-- Assign Supervisor (optional) --</option>')
    for s in all_supervisors:
        lines.append(
            '<option value="' + s["supervisor_id"] + '">'
            + s["name"] + ' — ' + s["block_name"] +
            '</option>'
        )
    lines.append('</select>')
    lines.append('<button type="submit" class="btn btn-primary">Add ASHA Worker</button>')
    lines.append('</div></form></div>')

    # Table
    lines.append('<p class="section-title">All ASHA Workers (' + str(total_asha) + ')</p>')
    lines.append('<div class="card"><table>')
    lines.append(
        '<tr><th>ASHA ID</th><th>Name</th><th>Phone</th><th>Village</th>'
        '<th>Block</th><th>Supervisor</th><th>Patients</th><th>Alerts</th>'
        '<th>Status</th><th>Actions</th></tr>'
    )
    if asha_workers:
        for a in asha_workers:
            stats       = asha_stats.get(a["asha_id"], {})
            patients    = stats.get("total_patients",   0)
            alerts      = stats.get("high_risk_alerts", 0)
            status_lbl  = "Active" if a["is_active"] else "Inactive"
            status_cls  = "badge-active" if a["is_active"] else "badge-inactive"
            toggle_lbl  = "Deactivate" if a["is_active"] else "Activate"
            sup_name    = a.get("supervisor_name", "—") or "—"
            lines.append(
                "<tr>"
                '<td><code style="color:#A78BFA">' + str(a["asha_id"]) + "</code></td>"
                "<td><strong>" + str(a["name"]) + "</strong></td>"
                '<td style="font-size:11px">' + str(a["phone"]) + "</td>"
                "<td>" + str(a["village"]) + "</td>"
                '<td style="color:#888">' + str(a.get("block_name") or "—") + "</td>"
                '<td style="font-size:11px;color:#A78BFA">' + sup_name + "</td>"
                '<td><span class="badge badge-purple">' + str(patients) + " patients</span></td>"
                '<td><span class="badge badge-red">' + str(alerts) + " alerts</span></td>"
                '<td><span class="badge ' + status_cls + '">' + status_lbl + "</span></td>"
                "<td>"
                '<form method="POST" action="/admin/toggle-asha" style="display:inline">'
                '<input type="hidden" name="asha_id" value="' + str(a["asha_id"]) + '">'
                '<button class="btn btn-success btn-sm" type="submit">' + toggle_lbl + "</button></form>"
                '<form method="POST" action="/admin/delete-asha" style="display:inline;margin-left:4px"'
                ' onsubmit="return confirm(\'Delete ' + str(a["name"]) + '?\')">'
                '<input type="hidden" name="asha_id" value="' + str(a["asha_id"]) + '">'
                '<button class="btn btn-danger btn-sm" type="submit">Delete</button></form>'
                "</td></tr>"
            )
    else:
        lines.append('<tr><td colspan="10" style="text-align:center;color:#555;padding:20px">No ASHA workers yet.</td></tr>')
    lines.append("</table></div>")
    return "\n".join(lines)


def _tab_supervisors(all_supervisors, all_bmos):
    lines = []
    lines.append('<div class="card" style="margin-top:16px">')
    lines.append('<p style="font-size:13px;color:#A78BFA;font-weight:bold;margin-bottom:14px">➕ Add Supervisor (ANM)</p>')
    lines.append('<form method="POST" action="/admin/add-supervisor">')
    lines.append('<div class="form-row">')
    lines.append('<input name="supervisor_id" placeholder="Supervisor ID (e.g. SUP_001)" required />')
    lines.append('<input name="name"          placeholder="Full Name" required />')
    lines.append('<input name="phone"         placeholder="WhatsApp: whatsapp:+91..." required />')
    lines.append('<input name="block_name"    placeholder="Block Name" required />')
    lines.append('<input name="district"      placeholder="District" required />')
    lines.append('<select name="bmo_id">')
    lines.append('<option value="">-- Assign BMO (optional) --</option>')
    for b in all_bmos:
        lines.append(
            '<option value="' + b["bmo_id"] + '">'
            + b["name"] + ' — ' + b["block_name"] +
            '</option>'
        )
    lines.append('</select>')
    lines.append('<button type="submit" class="btn btn-primary">Add Supervisor</button>')
    lines.append('</div></form></div>')

    # Table
    lines.append('<p class="section-title">All Supervisors (' + str(len(all_supervisors)) + ')</p>')
    lines.append('<div class="card"><table>')
    lines.append(
        '<tr><th>ID</th><th>Name</th><th>Phone</th>'
        '<th>Block</th><th>District</th><th>BMO</th>'
        '<th>Status</th><th>Actions</th></tr>'
    )
    if all_supervisors:
        for s in all_supervisors:
            status_lbl = "Active" if s["is_active"] else "Inactive"
            status_cls = "badge-active" if s["is_active"] else "badge-inactive"
            toggle_lbl = "Deactivate" if s["is_active"] else "Activate"
            lines.append(
                "<tr>"
                '<td><code style="color:#A78BFA">' + str(s["supervisor_id"]) + "</code></td>"
                "<td><strong>" + str(s["name"]) + "</strong></td>"
                '<td style="font-size:11px">' + str(s["phone"]) + "</td>"
                "<td>" + str(s["block_name"]) + "</td>"
                "<td>" + str(s["district"]) + "</td>"
                '<td style="font-size:11px;color:#888">' + str(s.get("bmo_id") or "—") + "</td>"
                '<td><span class="badge ' + status_cls + '">' + status_lbl + "</span></td>"
                "<td>"
                '<form method="POST" action="/admin/toggle-supervisor" style="display:inline">'
                '<input type="hidden" name="supervisor_id" value="' + str(s["supervisor_id"]) + '">'
                '<button class="btn btn-success btn-sm">' + toggle_lbl + "</button></form>"
                '<form method="POST" action="/admin/delete-supervisor"'
                ' style="display:inline;margin-left:4px"'
                ' onsubmit="return confirm(\'Delete?\');">'
                '<input type="hidden" name="supervisor_id" value="' + str(s["supervisor_id"]) + '">'
                '<button class="btn btn-danger btn-sm">Delete</button></form>'
                "</td></tr>"
            )
    else:
        lines.append('<tr><td colspan="8" style="text-align:center;color:#555;padding:20px">No supervisors yet.</td></tr>')
    lines.append("</table></div>")
    return "\n".join(lines)


def _tab_bmo(all_bmos):
    lines = []
    lines.append('<div class="card" style="margin-top:16px">')
    lines.append('<p style="font-size:13px;color:#A78BFA;font-weight:bold;margin-bottom:14px">➕ Add Block Medical Officer (BMO)</p>')
    lines.append('<form method="POST" action="/admin/add-bmo">')
    lines.append('<div class="form-row">')
    lines.append('<input name="bmo_id"     placeholder="BMO ID (e.g. BMO_001)" required />')
    lines.append('<input name="name"       placeholder="Full Name" required />')
    lines.append('<input name="phone"      placeholder="WhatsApp: whatsapp:+91..." required />')
    lines.append('<input name="block_name" placeholder="Block Name" required />')
    lines.append('<input name="district"   placeholder="District" required />')
    lines.append('<button type="submit" class="btn btn-primary">Add BMO</button>')
    lines.append('</div></form></div>')

    lines.append('<p class="section-title">All Block Medical Officers (' + str(len(all_bmos)) + ')</p>')
    lines.append('<div class="card"><table>')
    lines.append('<tr><th>BMO ID</th><th>Name</th><th>Phone</th><th>Block</th><th>District</th><th>Status</th><th>Actions</th></tr>')
    if all_bmos:
        for b in all_bmos:
            status_lbl = "Active" if b["is_active"] else "Inactive"
            status_cls = "badge-active" if b["is_active"] else "badge-inactive"
            toggle_lbl = "Deactivate" if b["is_active"] else "Activate"
            lines.append(
                "<tr>"
                '<td><code style="color:#A78BFA">' + str(b["bmo_id"]) + "</code></td>"
                "<td><strong>" + str(b["name"]) + "</strong></td>"
                '<td style="font-size:11px">' + str(b["phone"]) + "</td>"
                "<td>" + str(b["block_name"]) + "</td>"
                "<td>" + str(b["district"]) + "</td>"
                '<td><span class="badge ' + status_cls + '">' + status_lbl + "</span></td>"
                "<td>"
                '<form method="POST" action="/admin/toggle-bmo" style="display:inline">'
                '<input type="hidden" name="bmo_id" value="' + str(b["bmo_id"]) + '">'
                '<button class="btn btn-success btn-sm">' + toggle_lbl + "</button></form>"
                '<form method="POST" action="/admin/delete-bmo"'
                ' style="display:inline;margin-left:4px"'
                ' onsubmit="return confirm(\'Delete?\');">'
                '<input type="hidden" name="bmo_id" value="' + str(b["bmo_id"]) + '">'
                '<button class="btn btn-danger btn-sm">Delete</button></form>'
                "</td></tr>"
            )
    else:
        lines.append('<tr><td colspan="7" style="text-align:center;color:#555;padding:20px">No BMOs yet.</td></tr>')
    lines.append("</table></div>")
    return "\n".join(lines)


def _tab_map(village_map):
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">Village → ASHA Worker Mapping</p>')
    lines.append('<div class="card">')
    if village_map:
        for village, workers in village_map.items():
            lines.append('<div class="village-group">')
            lines.append('<div class="village-name">📍 ' + str(village) + '</div>')
            for w in workers:
                lines.append(
                    '<span class="asha-chip">' + str(w["name"]) +
                    ' <span style="background:#5B2FBF;border-radius:10px;'
                    'padding:1px 6px;font-size:10px;margin-left:4px;color:white">'
                    + str(w["patient_count"]) + ' patients</span></span>'
                )
            lines.append('</div>')
    else:
        lines.append('<p style="color:#555;text-align:center;padding:20px">No villages mapped yet.</p>')
    lines.append('</div>')
    return "\n".join(lines)


def _tab_patients(all_patients, patient_risks, total_patients):
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">All Registered Patients (' + str(total_patients) + ')</p>')
    lines.append('<div class="card"><table>')
    lines.append('<tr><th>Name</th><th>Week</th><th>Village</th><th>District</th><th>ASHA</th><th>Status</th><th>Phone</th><th>Risk</th></tr>')
    if all_patients:
        for phone, p in all_patients.items():
            risk  = patient_risks.get(phone, {})
            rl    = risk.get("level", "LOW")
            rs    = risk.get("score", 0)
            rcls  = "badge-red" if rl == "HIGH" else ("badge-amber" if rl == "MODERATE" else "badge-green")
            status_color = "#f59e0b" if p.get("status") == "postpartum" else "#6ee7b7"
            lines.append(
                "<tr>"
                "<td><strong>" + str(p.get("name","")) + "</strong></td>"
                "<td>Wk " + str(p.get("week","")) + "</td>"
                "<td>" + str(p.get("village","—")) + "</td>"
                '<td style="color:#888">' + str(p.get("district","—")) + "</td>"
                '<td style="font-size:11px;color:#A78BFA">' + str(p.get("asha_name", p.get("asha_id",""))) + "</td>"
                '<td><span style="font-size:10px;font-weight:600;color:' + status_color + '">'
                + str(p.get("status","active")).title() + "</span></td>"
                '<td style="font-size:11px">' + str(phone) + "</td>"
                '<td><span class="badge ' + rcls + '">' + rl + " (" + str(rs) + ")</span></td>"
                "</tr>"
            )
    else:
        lines.append('<tr><td colspan="8" style="text-align:center;color:#555;padding:20px">No patients yet.</td></tr>')
    lines.append("</table></div>")
    return "\n".join(lines)


def _tab_alerts(all_alerts, total_alerts):
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">All Alerts (' + str(total_alerts) + ' active)</p>')
    lines.append('<div class="card"><table>')
    lines.append(
        '<tr><th>Patient</th><th>Week</th><th>Symptom</th>'
        '<th>Village</th><th>Address</th><th>ASHA</th>'
        '<th>Escalation</th><th>Time</th><th>Status</th><th>Maps</th></tr>'
    )
    if all_alerts:
        for a in all_alerts:
            status    = str(a.get("status",""))
            scls      = ("badge-red" if status == "Pending"
                         else "badge-amber" if status == "Attended"
                         else "badge-green")
            lvl       = a.get("level", 0)
            esc_badge = ""
            if lvl and lvl > 0:
                esc_badge = ' <span class="badge badge-amber">Esc L' + str(lvl) + "</span>"
            maps_btn  = ""
            if a.get("maps_link"):
                maps_btn = '<a href="' + str(a["maps_link"]) + '" target="_blank" style="color:#60a5fa;font-size:11px">📌 Map</a>'
            symptom_short = str(a.get("symptom",""))[:45] + ("..." if len(str(a.get("symptom",""))) > 45 else "")
            lines.append(
                "<tr>"
                "<td><strong>" + str(a.get("name","")) + "</strong></td>"
                "<td>Wk " + str(a.get("week","")) + "</td>"
                '<td style="font-size:11px">' + symptom_short + "</td>"
                "<td>" + str(a.get("village","—")) + "</td>"
                '<td style="font-size:11px;color:#888">' + str(a.get("address","—")) + "</td>"
                '<td style="font-size:11px;color:#A78BFA">' + str(a.get("asha_name","—")) + "</td>"
                '<td style="font-size:11px">' + esc_badge + "</td>"
                '<td style="font-size:11px;color:#888">' + str(a.get("time","")) + "</td>"
                '<td><span class="badge ' + scls + '">' + status + "</span></td>"
                "<td>" + maps_btn + "</td>"
                "</tr>"
            )
    else:
        lines.append('<tr><td colspan="10" style="text-align:center;color:#555;padding:20px">No alerts yet. ✅</td></tr>')
    lines.append("</table></div>")
    return "\n".join(lines)


def _tab_analytics(district_stats):
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">District Analytics</p>')

    # KPI overview
    lines.append('<div class="card">')
    lines.append('<p style="font-size:13px;font-weight:bold;color:#A78BFA;margin-bottom:14px">📊 District Overview</p>')
    lines.append('<div class="kpi-grid">')
    kpis = [
        (district_stats.get("total_patients",0),     "Total Patients",      "#A78BFA"),
        (district_stats.get("total_ashas",0),         "ASHA Workers",        "#48CAE4"),
        (district_stats.get("total_supervisors",0),   "Supervisors",         "#6ee7b7"),
        (district_stats.get("total_bmos",0),          "BMOs",                "#fbbf24"),
        (district_stats.get("high_risk",0),           "Active Alerts",       "#ff6b6b"),
        (district_stats.get("escalated_alerts",0),    "Escalated",           "#f97316"),
        (district_stats.get("resolved_today",0),      "Resolved Today",      "#6ee7b7"),
        (district_stats.get("alerts_today",0),        "Alerts Today",        "#ff6b6b"),
        (district_stats.get("total_deliveries",0),    "Deliveries",          "#c4b5fd"),
        (district_stats.get("total_children",0),      "Children Tracked",    "#93c5fd"),
    ]
    for val, lbl, color in kpis:
        lines.append(
            '<div class="kpi">'
            '<div class="kpi-num" style="color:' + color + '">' + str(val) + '</div>'
            '<div class="kpi-lbl">' + lbl + '</div>'
            '</div>'
        )
    lines.append('</div></div>')

    # Quick links to full pages
    lines.append('<div class="card">')
    lines.append('<p style="font-size:13px;font-weight:bold;color:#A78BFA;margin-bottom:14px">📈 Full Analytics Dashboards</p>')
    lines.append('<div style="display:flex;gap:12px;flex-wrap:wrap">')
    lines.append('<a href="/admin/analytics" class="btn btn-blue">📊 Open Analytics Dashboard</a>')
    lines.append('<a href="/admin/performance" class="btn btn-primary">🏆 Open Performance Dashboard</a>')
    lines.append('</div></div>')

    return "\n".join(lines)


def _tab_performance(asha_workers, asha_stats):
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">ASHA Performance Summary</p>')
    lines.append('<div class="card"><table>')
    lines.append(
        '<tr><th>ASHA Name</th><th>Village</th><th>Patients</th>'
        '<th>Total Alerts</th><th>Resolved</th><th>Escalated</th>'
        '<th>Resolution %</th><th>Avg Response</th><th>Rating</th></tr>'
    )
    if asha_workers:
        for a in asha_workers:
            st  = asha_stats.get(a["asha_id"], {})
            tot = st.get("total_alerts",    0)
            res = st.get("resolved_alerts", 0)
            esc = st.get("escalated_alerts",0)
            vis = st.get("visit_count",     0)
            rr  = round(res / tot * 100, 1) if tot > 0 else 0
            rh  = st.get("avg_response_hrs")
            rt  = (str(rh) + "h") if rh else "—"
            rating = st.get("performance_rating", "unknown")
            rcol = ("#6ee7b7" if rating == "GREEN"
                    else "#fcd34d" if rating == "AMBER"
                    else "#ff6b6b" if rating == "RED"
                    else "#888")
            rr_color = ("#6ee7b7" if rr >= 80 else "#fcd34d" if rr >= 50 else "#ff6b6b")
            lines.append(
                "<tr>"
                "<td><strong>" + str(a["name"]) + "</strong></td>"
                "<td>" + str(a["village"]) + "</td>"
                '<td style="text-align:center">' + str(st.get("total_patients",0)) + "</td>"
                '<td style="text-align:center">' + str(tot) + "</td>"
                '<td style="text-align:center;color:#6ee7b7">' + str(res) + "</td>"
                '<td style="text-align:center;color:#fcd34d">' + str(esc) + "</td>"
                '<td style="text-align:center;font-weight:bold;color:' + rr_color + '">'
                + str(rr) + "%</td>"
                '<td style="text-align:center">' + rt + "</td>"
                '<td><span style="font-weight:bold;color:' + rcol + '">'
                + str(rating) + "</span></td>"
                "</tr>"
            )
    else:
        lines.append('<tr><td colspan="9" style="text-align:center;color:#555;padding:20px">No data yet.</td></tr>')
    lines.append("</table></div>")
    lines.append('<div class="card">')
    lines.append('<a href="/admin/performance" class="btn btn-primary">🏆 Open Full Performance Dashboard →</a>')
    lines.append("</div>")
    return "\n".join(lines)


def _tab_export():
    lines = []
    lines.append('<p class="section-title" style="margin-top:16px">NHM Data Exports</p>')
    lines.append('<div class="card">')
    lines.append('<p style="font-size:13px;font-weight:bold;color:#A78BFA;margin-bottom:4px">📤 Export Formats</p>')
    lines.append('<p style="font-size:12px;color:#888;margin-bottom:16px">All files are UTF-8 / BOM encoded — open directly in Excel.</p>')
    lines.append('<div class="export-grid">')

    exports = [
        ("/admin/export/nhm-csv",     "📄 NHM Patient CSV",
         "All registered patients — HMIS Form 3 compatible. Village, block, district, ANC, alerts, delivery data.", "btn-blue"),
        ("/admin/export/nhm-zip",     "📦 Full NHM ZIP",
         "All 10 registers in one ZIP: patients, ANC, deliveries, children, ASHA performance, alerts, schemes, symptoms, villages, escalation log.", "btn-primary"),
        ("/admin/export/monthly-pdf", "📑 Monthly PDF Report",
         "Formatted NHM submission report: KPIs, resolution rate, village risks, ASHA performance table, observations and signature block.", "btn-amber"),
    ]
    for url, title, desc, btn_cls in exports:
        lines.append('<div class="export-card">')
        lines.append('<h4>' + title + '</h4>')
        lines.append('<p>' + desc + '</p>')
        lines.append('<a href="' + url + '" class="btn ' + btn_cls + '">⬇ Download</a>')
        lines.append('</div>')

    lines.append('</div></div>')

    # JSON APIs
    lines.append('<div class="card" style="margin-top:0">')
    lines.append('<p style="font-size:13px;font-weight:bold;color:#A78BFA;margin-bottom:12px">🔗 JSON API Endpoints</p>')
    lines.append('<div style="display:flex;gap:10px;flex-wrap:wrap">')
    apis = [
        ("/admin/api/trends",       "📈 Trend Data"),
        ("/admin/api/village-risks","🗺️ Village Risks"),
        ("/admin/api/nhm-summary",  "📋 NHM Summary"),
    ]
    for url, label in apis:
        lines.append(
            '<a href="' + url + '" target="_blank"'
            ' style="padding:8px 16px;background:#12122a;border:1px solid #3a3a5a;'
            'border-radius:8px;color:#A78BFA;font-size:12px;text-decoration:none">'
            + label + '</a>'
        )
    lines.append('</div></div>')
    return "\n".join(lines)


# =================================================================
# STATS ROW
# =================================================================

def _stats_row(district_stats, total_asha, total_supervisors, total_bmos, total_villages):
    stats = [
        (str(total_asha),                                              "ASHA Workers",      "#A78BFA"),
        (str(total_supervisors),                                       "Supervisors",        "#48CAE4"),
        (str(total_bmos),                                              "BMOs",               "#fbbf24"),
        (str(district_stats.get("total_patients", 0)),                 "Patients",           "#6ee7b7"),
        (str(district_stats.get("high_risk", 0)),                      "Active Alerts",      "#ff6b6b"),
    ]
    parts = ['<div class="stats">']
    for val, lbl, color in stats:
        parts.append(
            '<div class="stat">'
            '<div class="stat-number" style="color:' + color + '">' + val + '</div>'
            '<div class="stat-label">' + lbl + '</div>'
            '</div>'
        )
    parts.append('</div>')
    return "\n".join(parts)


# =================================================================
# PUBLIC API
# =================================================================

def render_admin_login(error=None):
    err_html = ('<p class="error">❌ ' + error + '</p>') if error else ""
    parts = [
        "<!DOCTYPE html><html><head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>MaaSakhi Admin Login</title>",
        "<style>",
        "* { margin:0; padding:0; box-sizing:border-box; }",
        "body { font-family:Arial,sans-serif; background:#0f0f1a;",
        "       display:flex; justify-content:center; align-items:center; min-height:100vh; }",
        ".box { background:#1a1a2e; padding:36px; border-radius:16px;",
        "       border:1px solid #3a3a5a; width:90%; max-width:380px; text-align:center; }",
        "h2 { font-size:22px; color:#A78BFA; margin-bottom:6px; }",
        "p  { font-size:13px; color:#888; margin-bottom:24px; }",
        "input { width:100%; padding:12px; margin-bottom:12px; background:#0f0f1a;",
        "        border:1px solid #3a3a5a; border-radius:8px; color:#e0e0f0; font-size:13px; }",
        "button { width:100%; padding:13px; background:#5B2FBF; color:white;",
        "         border:none; border-radius:8px; font-size:14px; font-weight:bold; cursor:pointer; }",
        "button:hover { background:#7C52D4; }",
        ".error { color:#ff6b6b; font-size:12px; margin-top:10px; }",
        ".back { display:block; margin-top:16px; font-size:12px; color:#555; text-decoration:none; }",
        ".back:hover { color:#A78BFA; }",
        "</style></head><body>",
        '<div class="box">',
        "<h2>🌿 MaaSakhi</h2>",
        "<p>Admin Panel Login</p>",
        '<form method="POST">',
        '<input name="username" placeholder="Username" required />',
        '<input name="password" type="password" placeholder="Password" required />',
        '<button type="submit">Login to Admin Panel</button>',
        "</form>",
        err_html,
        '<a href="/login" class="back">← ASHA Worker Login</a>',
        "</div></body></html>",
    ]
    return "\n".join(parts)


def render_admin_panel(admin_name, tab, message=None, success=True):
    from database import (
        get_all_asha_workers, get_all_patients_admin,
        get_all_alerts_admin, get_asha_stats,
        get_risk_score_from_db, get_district_stats,
        get_all_supervisors, get_all_block_officers,
        get_asha_performance,
    )

    # ── Fetch all data ────────────────────────────────────────────
    asha_workers    = get_all_asha_workers()
    all_supervisors = get_all_supervisors()
    all_bmos        = get_all_block_officers()
    all_patients    = get_all_patients_admin()
    all_alerts      = get_all_alerts_admin()
    district_stats  = get_district_stats()

    # ── Aggregate counts ──────────────────────────────────────────
    total_asha        = len(asha_workers)
    total_supervisors = len(all_supervisors)
    total_bmos        = len(all_bmos)
    total_patients    = len(all_patients)
    total_active_alerts = len([a for a in all_alerts if a["status"] != "Resolved"])
    total_villages    = len(set(a["village"] for a in asha_workers if a.get("village")))

    # ── Per-ASHA stats + performance ─────────────────────────────
    asha_stats = {}
    for a in asha_workers:
        base = get_asha_stats(a["asha_id"])
        try:
            perf = get_asha_performance(a["asha_id"], days=30)
            base.update(perf)
        except Exception:
            pass
        asha_stats[a["asha_id"]] = base

    # ── Village map ───────────────────────────────────────────────
    village_map = {}
    for a in asha_workers:
        v = a.get("village", "Unknown")
        if v not in village_map:
            village_map[v] = []
        st = asha_stats.get(a["asha_id"], {})
        village_map[v].append({
            "name":          a["name"],
            "asha_id":       a["asha_id"],
            "patient_count": st.get("total_patients", 0),
        })

    # ── Patient risk scores ───────────────────────────────────────
    patient_risks = {}
    for phone in all_patients:
        score, level, _ = get_risk_score_from_db(phone)
        patient_risks[phone] = {"score": score, "level": level}

    # Add delivery / child counts to district_stats if missing
    district_stats.setdefault("total_deliveries", 0)
    district_stats.setdefault("total_children",   0)
    try:
        from database import engine
        from sqlalchemy import text as sqlt
        with engine.connect() as conn:
            district_stats["total_deliveries"] = conn.execute(
                sqlt("SELECT COUNT(*) FROM deliveries")
            ).scalar() or 0
            district_stats["total_children"] = conn.execute(
                sqlt("SELECT COUNT(*) FROM children")
            ).scalar() or 0
    except Exception:
        pass

    # ── Build page ────────────────────────────────────────────────
    parts = [
        _head("MaaSakhi Admin Panel"),
        _topbar(admin_name),
        _flash(message, success),
        _stats_row(district_stats, total_asha, total_supervisors, total_bmos, total_villages),
        _tab_bar(tab),
    ]

    if tab == "asha":
        parts.append(_tab_asha(asha_workers, asha_stats, all_supervisors, total_asha))
    elif tab == "supervisors":
        parts.append(_tab_supervisors(all_supervisors, all_bmos))
    elif tab == "bmo":
        parts.append(_tab_bmo(all_bmos))
    elif tab == "map":
        parts.append(_tab_map(village_map))
    elif tab == "patients":
        parts.append(_tab_patients(all_patients, patient_risks, total_patients))
    elif tab == "alerts":
        parts.append(_tab_alerts(all_alerts, total_active_alerts))
    elif tab == "analytics":
        parts.append(_tab_analytics(district_stats))
    elif tab == "performance":
        parts.append(_tab_performance(asha_workers, asha_stats))
    elif tab == "export":
        parts.append(_tab_export())
    else:
        parts.append(_tab_asha(asha_workers, asha_stats, all_supervisors, total_asha))

    parts.append('<div class="footer">MaaSakhi Admin &nbsp;•&nbsp; WHO + NHM + FOGSI Guidelines</div>')
    parts.append("</body></html>")

    return "\n".join(parts)
