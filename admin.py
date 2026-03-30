# ─────────────────────────────────────────────────────────────────
# MaaSakhi Admin Panel
# 3-Tier: Admin → ASHA Workers → Patients
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string, request, redirect, session

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi — Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:Arial,sans-serif; background:#0f0f1a; color:#e0e0f0; }

        .topbar {
            background:#1a0a3a;
            padding:16px 24px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            border-bottom:2px solid #5B2FBF;
        }
        .topbar h1 { font-size:20px; color:#A78BFA; }
        .topbar span { font-size:12px; color:#888; }
        .logout { color:#ff6b6b; font-size:12px; text-decoration:none; }

        .stats {
            display:grid;
            grid-template-columns:repeat(4,1fr);
            gap:12px;
            padding:20px;
        }
        .stat {
            background:#1a1a2e;
            border-radius:12px;
            padding:16px;
            text-align:center;
            border:1px solid #2a2a4a;
        }
        .stat-number { font-size:32px; font-weight:bold; }
        .stat-label  { font-size:11px; color:#888; margin-top:4px; }

        .section-title {
            padding:8px 20px;
            font-size:11px;
            font-weight:bold;
            color:#A78BFA;
            text-transform:uppercase;
            letter-spacing:.06em;
            margin-top:8px;
        }

        .card {
            margin:0 20px 12px;
            background:#1a1a2e;
            border-radius:12px;
            padding:20px;
            border:1px solid #2a2a4a;
        }

        .form-row {
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
            gap:10px;
            margin-bottom:12px;
        }
        input, select {
            width:100%;
            padding:10px 12px;
            background:#0f0f1a;
            border:1px solid #3a3a5a;
            border-radius:8px;
            color:#e0e0f0;
            font-size:13px;
        }
        input::placeholder { color:#555; }
        .btn {
            padding:10px 20px;
            border:none;
            border-radius:8px;
            font-size:13px;
            cursor:pointer;
            font-weight:bold;
        }
        .btn-primary { background:#5B2FBF; color:white; }
        .btn-primary:hover { background:#7C52D4; }
        .btn-danger  { background:#991b1b; color:white; }
        .btn-danger:hover { background:#dc2626; }
        .btn-success { background:#065f46; color:white; }
        .btn-success:hover { background:#059669; }
        .btn-sm { padding:6px 12px; font-size:11px; }

        table {
            width:100%;
            border-collapse:collapse;
            font-size:13px;
        }
        th {
            text-align:left;
            padding:10px 12px;
            background:#12122a;
            color:#A78BFA;
            font-size:11px;
            text-transform:uppercase;
            letter-spacing:.04em;
        }
        td {
            padding:10px 12px;
            border-bottom:1px solid #1e1e3a;
            color:#c0c0d8;
        }
        tr:hover td { background:#1e1e38; }

        .badge {
            display:inline-block;
            padding:3px 10px;
            border-radius:20px;
            font-size:10px;
            font-weight:bold;
        }
        .badge-active   { background:#064e3b; color:#6ee7b7; }
        .badge-inactive { background:#7f1d1d; color:#fca5a5; }
        .badge-red      { background:#7f1d1d; color:#fca5a5; }
        .badge-amber    { background:#78350f; color:#fcd34d; }
        .badge-green    { background:#064e3b; color:#6ee7b7; }
        .badge-purple   { background:#2e1065; color:#c4b5fd; }

        .village-group {
            background:#12122a;
            border-radius:8px;
            padding:12px 16px;
            margin-bottom:8px;
            border-left:3px solid #5B2FBF;
        }
        .village-name { font-size:13px; color:#A78BFA; font-weight:bold; margin-bottom:6px; }
        .asha-chip {
            display:inline-block;
            background:#1e1e3a;
            border:1px solid #3a3a5a;
            border-radius:20px;
            padding:4px 12px;
            font-size:11px;
            margin:3px;
            color:#c0c0d8;
        }
        .asha-chip .count {
            background:#5B2FBF;
            border-radius:10px;
            padding:1px 6px;
            font-size:10px;
            margin-left:4px;
            color:white;
        }

        .alert-row { border-left:3px solid #dc2626; }

        .msg { padding:10px 16px; border-radius:8px; margin:0 20px 12px; font-size:13px; }
        .msg-success { background:#064e3b; color:#6ee7b7; }
        .msg-error   { background:#7f1d1d; color:#fca5a5; }

        .tab-bar {
            display:flex;
            gap:4px;
            padding:12px 20px 0;
            border-bottom:1px solid #2a2a4a;
        }
        .tab {
            padding:8px 18px;
            border-radius:8px 8px 0 0;
            font-size:12px;
            font-weight:bold;
            cursor:pointer;
            text-decoration:none;
            color:#888;
            background:#12122a;
        }
        .tab.active { background:#1a1a2e; color:#A78BFA; border-bottom:2px solid #5B2FBF; }

        .footer { text-align:center; font-size:11px; color:#333; padding:20px; }

        @media(max-width:768px) {
            .stats { grid-template-columns:repeat(2,1fr); }
            .form-row { grid-template-columns:1fr; }
        }
    </style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar">
    <h1>🌿 MaaSakhi — Admin Panel</h1>
    <div>
        <span>Logged in as {{ admin_name }}</span> &nbsp;
        <a href="/admin/logout" class="logout">Logout</a>
    </div>
</div>

<!-- FLASH MESSAGE -->
{% if message %}
<div class="msg {{ 'msg-success' if success else 'msg-error' }}">
    {{ message }}
</div>
{% endif %}

<!-- STATS ROW -->
<div class="stats">
    <div class="stat">
        <div class="stat-number" style="color:#A78BFA">{{ total_asha }}</div>
        <div class="stat-label">ASHA Workers</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color:#48CAE4">{{ total_patients }}</div>
        <div class="stat-label">Total Patients</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color:#ff6b6b">{{ total_alerts }}</div>
        <div class="stat-label">High Risk Alerts</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color:#6ee7b7">{{ total_villages }}</div>
        <div class="stat-label">Villages Covered</div>
    </div>
</div>

<!-- TABS -->
<div class="tab-bar">
    <a href="/admin?tab=asha" class="tab {{ 'active' if tab == 'asha' }}">👩 ASHA Workers</a>
    <a href="/admin?tab=map"  class="tab {{ 'active' if tab == 'map'  }}">🗺️ Village Map</a>
    <a href="/admin?tab=patients" class="tab {{ 'active' if tab == 'patients' }}">🤰 All Patients</a>
    <a href="/admin?tab=alerts" class="tab {{ 'active' if tab == 'alerts' }}">🚨 All Alerts</a>
</div>

<!-- ── TAB 1: ASHA WORKERS ── -->
{% if tab == 'asha' %}

<div class="card" style="margin-top:16px">
    <p style="font-size:13px;color:#A78BFA;font-weight:bold;margin-bottom:14px">
        ➕ Add New ASHA Worker
    </p>
    <form method="POST" action="/admin/add-asha">
        <div class="form-row">
            <input name="asha_id"  placeholder="ASHA ID (e.g. asha_001)" required />
            <input name="name"     placeholder="Full Name" required />
            <input name="phone"    placeholder="WhatsApp number (whatsapp:+91...)" required />
            <input name="village"  placeholder="Village Name" required />
            <input name="district" placeholder="District (optional)" />
            <button type="submit" class="btn btn-primary">Add ASHA Worker</button>
        </div>
    </form>
</div>

<p class="section-title">All ASHA Workers ({{ total_asha }})</p>
<div class="card">
    {% if asha_workers %}
    <table>
        <tr>
            <th>ASHA ID</th>
            <th>Name</th>
            <th>Phone</th>
            <th>Village</th>
            <th>District</th>
            <th>Patients</th>
            <th>Alerts</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
        {% for a in asha_workers %}
        <tr>
            <td><code style="color:#A78BFA">{{ a.asha_id }}</code></td>
            <td><strong>{{ a.name }}</strong></td>
            <td style="font-size:11px">{{ a.phone }}</td>
            <td>{{ a.village }}</td>
            <td style="color:#888">{{ a.district or '—' }}</td>
            <td>
                <span class="badge badge-purple">
                    {{ asha_stats.get(a.asha_id, {}).get('total_patients', 0) }} patients
                </span>
            </td>
            <td>
                <span class="badge badge-red">
                    {{ asha_stats.get(a.asha_id, {}).get('high_risk_alerts', 0) }} alerts
                </span>
            </td>
            <td>
                <span class="badge {{ 'badge-active' if a.is_active else 'badge-inactive' }}">
                    {{ 'Active' if a.is_active else 'Inactive' }}
                </span>
            </td>
            <td>
                <form method="POST" action="/admin/toggle-asha" style="display:inline">
                    <input type="hidden" name="asha_id" value="{{ a.asha_id }}">
                    <button class="btn btn-success btn-sm" type="submit">
                        {{ 'Deactivate' if a.is_active else 'Activate' }}
                    </button>
                </form>
                <form method="POST" action="/admin/delete-asha" style="display:inline;margin-left:4px"
                      onsubmit="return confirm('Delete {{ a.name }}?')">
                    <input type="hidden" name="asha_id" value="{{ a.asha_id }}">
                    <button class="btn btn-danger btn-sm" type="submit">Delete</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="color:#555;text-align:center;padding:20px">
        No ASHA workers added yet. Add your first ASHA worker above!
    </p>
    {% endif %}
</div>

<!-- ── TAB 2: VILLAGE MAP ── -->
{% elif tab == 'map' %}

<p class="section-title" style="margin-top:16px">Village → ASHA Worker Mapping</p>
<div class="card">
    {% if village_map %}
        {% for village, workers in village_map.items() %}
        <div class="village-group">
            <div class="village-name">📍 {{ village }}</div>
            {% for w in workers %}
            <span class="asha-chip">
                {{ w.name }}
                <span class="count">{{ w.patient_count }} patients</span>
            </span>
            {% endfor %}
        </div>
        {% endfor %}
    {% else %}
    <p style="color:#555;text-align:center;padding:20px">
        No villages mapped yet. Add ASHA workers first!
    </p>
    {% endif %}
</div>

<!-- ── TAB 3: ALL PATIENTS ── -->
{% elif tab == 'patients' %}

<p class="section-title" style="margin-top:16px">All Registered Patients ({{ total_patients }})</p>
<div class="card">
    {% if all_patients %}
    <table>
        <tr>
            <th>Name</th>
            <th>Week</th>
            <th>Village</th>
            <th>ASHA Worker</th>
            <th>Phone</th>
            <th>Risk</th>
        </tr>
        {% for phone, p in all_patients.items() %}
        <tr>
            <td><strong>{{ p.name }}</strong></td>
            <td>Week {{ p.week }}</td>
            <td>{{ p.village or '—' }}</td>
            <td style="font-size:11px;color:#A78BFA">{{ p.asha_id }}</td>
            <td style="font-size:11px">{{ phone }}</td>
            <td>
                {% set score = patient_risks.get(phone, {}) %}
                <span class="badge
                    {{ 'badge-red' if score.get('level') == 'HIGH'
                    else 'badge-amber' if score.get('level') == 'MODERATE'
                    else 'badge-green' }}">
                    {{ score.get('level', 'LOW') }}
                </span>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="color:#555;text-align:center;padding:20px">No patients registered yet.</p>
    {% endif %}
</div>

<!-- ── TAB 4: ALL ALERTS ── -->
{% elif tab == 'alerts' %}

<p class="section-title" style="margin-top:16px">All High Risk Alerts ({{ total_alerts }})</p>
<div class="card">
    {% if all_alerts %}
    <table>
        <tr>
            <th>Patient</th>
            <th>Week</th>
            <th>Symptom</th>
            <th>Village</th>
            <th>ASHA Worker</th>
            <th>Time</th>
            <th>Status</th>
        </tr>
        {% for a in all_alerts %}
        <tr class="alert-row">
            <td><strong>{{ a.name }}</strong></td>
            <td>Week {{ a.week }}</td>
            <td style="font-size:11px">{{ a.symptom[:50] }}...</td>
            <td>{{ a.village or '—' }}</td>
            <td style="font-size:11px;color:#A78BFA">
                {{ a.asha_name or a.asha_id }}
            </td>
            <td style="font-size:11px;color:#888">{{ a.time }}</td>
            <td>
                <span class="badge badge-red">{{ a.status }}</span>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="color:#555;text-align:center;padding:20px">No alerts yet. ✅</p>
    {% endif %}
</div>
{% endif %}

<div class="footer">
    MaaSakhi Admin  • WHO + NHM + FOGSI Guidelines
</div>

</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi Admin Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family:Arial,sans-serif;
            background:#0f0f1a;
            display:flex;
            justify-content:center;
            align-items:center;
            min-height:100vh;
        }
        .box {
            background:#1a1a2e;
            padding:36px;
            border-radius:16px;
            border:1px solid #3a3a5a;
            width:90%;
            max-width:380px;
            text-align:center;
        }
        h2 { font-size:22px; color:#A78BFA; margin-bottom:6px; }
        p  { font-size:13px; color:#888; margin-bottom:24px; }
        input {
            width:100%;
            padding:12px;
            margin-bottom:12px;
            background:#0f0f1a;
            border:1px solid #3a3a5a;
            border-radius:8px;
            color:#e0e0f0;
            font-size:13px;
        }
        button {
            width:100%;
            padding:13px;
            background:#5B2FBF;
            color:white;
            border:none;
            border-radius:8px;
            font-size:14px;
            font-weight:bold;
            cursor:pointer;
        }
        button:hover { background:#7C52D4; }
        .error { color:#ff6b6b; font-size:12px; margin-top:10px; }
        .back { display:block; margin-top:16px; font-size:12px; color:#555; text-decoration:none; }
        .back:hover { color:#A78BFA; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🌿 MaaSakhi</h2>
        <p>Admin Panel Login</p>
        <form method="POST">
            <input name="username" placeholder="Username" required />
            <input name="password" type="password" placeholder="Password" required />
            <button type="submit">Login to Admin Panel</button>
        </form>
        {% if error %}
        <p class="error">❌ {{ error }}</p>
        {% endif %}
        <a href="/login" class="back">← ASHA Worker Login</a>
    </div>
</body>
</html>
"""


def render_admin_login(error=None):
    return render_template_string(ADMIN_LOGIN_HTML, error=error)


def render_admin_panel(admin_name, tab, message=None, success=True):
    from database import (
        get_all_asha_workers, get_all_patients_admin,
        get_all_alerts_admin, get_asha_stats,
        get_risk_score_from_db
    )

    asha_workers  = get_all_asha_workers()
    all_patients  = get_all_patients_admin()
    all_alerts    = get_all_alerts_admin()

    # Stats
    total_asha     = len(asha_workers)
    total_patients = len(all_patients)
    total_alerts   = len([a for a in all_alerts if a["status"] != "Resolved"])
    total_villages = len(set(a["village"] for a in asha_workers))

    # Per-ASHA stats
    asha_stats = {}
    for a in asha_workers:
        asha_stats[a["asha_id"]] = get_asha_stats(a["asha_id"])

    # Village map — group workers by village with patient counts
    village_map = {}
    for a in asha_workers:
        v = a["village"]
        if v not in village_map:
            village_map[v] = []
        stats = asha_stats.get(a["asha_id"], {})
        village_map[v].append({
            "name":          a["name"],
            "asha_id":       a["asha_id"],
            "patient_count": stats.get("total_patients", 0)
        })

    # Patient risk scores
    patient_risks = {}
    for phone in all_patients:
        score, risk_level, _ = get_risk_score_from_db(phone)
        patient_risks[phone] = {"score": score, "level": risk_level}

    return render_template_string(
        ADMIN_DASHBOARD_HTML,
        admin_name=admin_name,
        tab=tab,
        message=message,
        success=success,
        asha_workers=asha_workers,
        asha_stats=asha_stats,
        all_patients=all_patients,
        all_alerts=all_alerts,
        village_map=village_map,
        patient_risks=patient_risks,
        total_asha=total_asha,
        total_patients=total_patients,
        total_alerts=total_alerts,
        total_villages=total_villages
    )
