# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Worker Dashboard
# Accessible at: your-url/dashboard
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string



DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi — ASHA Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: Arial, sans-serif; background:#f0faf5; color:#2c2c2a; }

        .header { background:#085041; color:white; padding:20px 24px; }
        .header h1 { font-size:22px; }
        .header p  { font-size:13px; opacity:0.8; margin-top:4px; }

        .stats { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; padding:20px; }
        .stat  { background:white; border-radius:12px; padding:16px; text-align:center; border:1px solid #e1f5ee; }
        .stat-number { font-size:36px; font-weight:bold; }
        .stat-label  { font-size:12px; color:#888; margin-top:4px; }

        .section { padding:0 20px 10px; font-size:12px; font-weight:bold;
                   color:#085041; text-transform:uppercase; letter-spacing:.06em; margin-top:8px; }

        .alert-card { margin:0 20px 12px; background:white; border-radius:12px;
                      padding:16px; border-left:4px solid #e24b4a; }
        .alert-name   { font-weight:bold; font-size:15px; }
        .alert-detail { font-size:13px; color:#666; margin-top:4px; }
        .alert-time   { font-size:12px; color:#aaa; margin-top:6px; }

        .badge     { display:inline-block; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:bold; }
        .badge-red { background:#fcebeb; color:#a32d2d; }
        .badge-ok  { background:#eaf3de; color:#3b6d11; }

        .patient-row { background:white; border-radius:10px; padding:14px 16px;
                       margin:0 20px 8px; display:flex; justify-content:space-between;
                       align-items:center; border:1px solid #e1f5ee; }
        .patient-name   { font-weight:500; font-size:14px; }
        .patient-detail { font-size:12px; color:#888; margin-top:2px; }

        .empty { text-align:center; padding:30px; color:#aaa; font-size:14px; }

        .footer { text-align:center; font-size:12px; color:#aaa; padding:20px; }
    </style>
</head>
<body>

<div class="header">
    <h1>🌿 MaaSakhi — ASHA Dashboard</h1>
    <p>Auto-refreshes every 30 seconds • Powered by WHO + NHM Guidelines</p>
</div>

<div class="header">
    <h1>🌸 MaaSakhi Dashboard</h1>
    <p>ASHA ID: {{ asha_id }}</p>
</div>

<div class="stats">
    <div class="stat">
        <div class="stat-number" style="color:#e24b4a">{{ high_risk }}</div>
        <div class="stat-label">High Risk Alerts</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color:#ba7517">{{ total }}</div>
        <div class="stat-label">Total Registered</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color:#085041">{{ safe }}</div>
        <div class="stat-label">Safe Patients</div>
    </div>
</div>

<p class="section">⚠️ High Risk Alerts</p>
{% if alerts %}
    {% for a in alerts %}
    <div class="alert-card">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="alert-name">{{ a.name }}</div>
            <span class="badge badge-red">HIGH RISK</span>
        </div>
        <div class="alert-detail">Week {{ a.week }} • {{ a.symptom }}</div>
        <div class="alert-detail">📞 {{ a.phone }}</div>
        <div class="alert-time">🕐 {{ a.time }}</div>
    </div>
    {% endfor %}
{% else %}
    <div class="empty">✅ No high risk alerts right now</div>
{% endif %}

<p class="section" style="margin-top:12px">👩 Registered Patients</p>
{% if patients %}
    {% for phone, p in patients.items() %}
    {% if p.step == 'registered' %}


    
    <div class="patient-row">
        <div>
            <div class="patient-name">{{ p.name }}</div>
            <div class="patient-detail">Week {{ p.week }} • {{ phone }}</div>
        </div>
        <span class="badge badge-ok">Active</span>
    </div>
    
    {% endif %}
    {% endfor %}
{% else %}
    <div class="empty">No patients registered yet</div>
{% endif %}

<div class="footer">
    MaaSakhi • Built for WitchHunt 2026 • Powered by WHO + NHM + FOGSI Guidelines
</div>

</body>
</html>
"""


def render_dashboard(patients, high_risk, total, safe,asha_id):
    from database import get_all_asha_alerts, get_symptom_logs, get_risk_score_from_db
    alerts        = get_all_asha_alerts(asha_id)
    total_reports = sum(
        len(get_symptom_logs(phone)) for phone in patients
    )

    patient_risks = {}
    for phone in patients:
        score, risk_level, summary = get_risk_score_from_db(phone)
        patient_risks[phone] = {
            "score": score,
            "level": risk_level
        }

    return render_template_string(
        DASHBOARD_HTML,
        alerts=alerts,
        patients=patients,
        high_risk=high_risk,
        total=total,
        safe=safe,
        total_reports=total_reports,
        patient_risks=patient_risks,
        asha_id=asha_id
    )
