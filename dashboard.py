# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Worker Dashboard
# Beautiful UI — Animations, Maps, Visit Logging, Care Loop
# Pending → Attended → Visit Logged → Resolved
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>MaaSakhi — ASHA Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        * { margin:0; padding:0; box-sizing:border-box; }

        body {
            font-family:'Poppins',sans-serif;
            background:#f0faf5;
            color:#1f2937;
        }

        /* ── HEADER ─────────────────────────────────────────── */
        .header {
            background:linear-gradient(135deg,#085041,#0a6b52);
            color:white;
            padding:24px;
            position:relative;
            overflow:hidden;
        }
        .header::before {
            content:'';
            position:absolute;
            top:-40px; right:-40px;
            width:180px; height:180px;
            background:rgba(255,255,255,0.06);
            border-radius:50%;
        }
        .header::after {
            content:'';
            position:absolute;
            bottom:-60px; right:60px;
            width:120px; height:120px;
            background:rgba(255,255,255,0.04);
            border-radius:50%;
        }
        .header h1 {
            font-size:22px;
            font-weight:700;
            display:flex;
            align-items:center;
            gap:10px;
        }
        .header p { font-size:13px; opacity:0.85; margin-top:5px; }
        .header-meta {
            display:flex;
            gap:16px;
            margin-top:14px;
            flex-wrap:wrap;
        }
        .header-badge {
            background:rgba(255,255,255,0.15);
            border:1px solid rgba(255,255,255,0.25);
            padding:5px 14px;
            border-radius:20px;
            font-size:12px;
            font-weight:500;
        }

        /* ── LIVE DOT ────────────────────────────────────────── */
        .live-dot {
            display:inline-block;
            width:8px; height:8px;
            background:#4ade80;
            border-radius:50%;
            margin-right:6px;
            animation:pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%,100% { opacity:1; transform:scale(1); }
            50%      { opacity:0.5; transform:scale(1.4); }
        }

        /* ── STATS ───────────────────────────────────────────── */
        .stats {
            display:grid;
            grid-template-columns:repeat(3,1fr);
            gap:14px;
            padding:20px;
        }
        .stat {
            background:white;
            border-radius:16px;
            padding:18px 12px;
            text-align:center;
            border:1px solid #d1fae5;
            box-shadow:0 4px 12px rgba(0,0,0,0.05);
            animation:fadeUp 0.5s ease both;
            transition:transform 0.2s;
        }
        .stat:hover { transform:translateY(-4px); }
        .stat:nth-child(1) { animation-delay:0.1s; }
        .stat:nth-child(2) { animation-delay:0.2s; }
        .stat:nth-child(3) { animation-delay:0.3s; }
        .stat-number {
            font-size:34px;
            font-weight:700;
            line-height:1;
        }
        .stat-label {
            font-size:11px;
            color:#6b7280;
            margin-top:6px;
            font-weight:500;
        }
        .stat-icon { font-size:20px; margin-bottom:6px; }

        /* ── SECTION LABELS ──────────────────────────────────── */
        .section {
            padding:4px 20px 10px;
            font-size:11px;
            font-weight:700;
            color:#085041;
            text-transform:uppercase;
            letter-spacing:.1em;
            margin-top:8px;
            display:flex;
            align-items:center;
            gap:8px;
        }
        .section-count {
            background:#085041;
            color:white;
            border-radius:20px;
            padding:1px 10px;
            font-size:11px;
        }

        /* ── ALERT CARDS ─────────────────────────────────────── */
        .alert-card {
            margin:0 20px 14px;
            background:white;
            border-radius:16px;
            padding:18px;
            border-left:5px solid #ef4444;
            box-shadow:0 6px 20px rgba(239,68,68,0.1);
            animation:slideIn 0.4s ease both;
            transition:transform 0.2s, box-shadow 0.2s;
        }
        .alert-card:hover {
            transform:translateY(-2px);
            box-shadow:0 10px 28px rgba(239,68,68,0.15);
        }
        .alert-card.attended {
            border-left-color:#f59e0b;
            box-shadow:0 6px 20px rgba(245,158,11,0.1);
        }
        .alert-card.attended:hover {
            box-shadow:0 10px 28px rgba(245,158,11,0.15);
        }
        .alert-card.resolved {
            border-left-color:#10b981;
            box-shadow:0 4px 12px rgba(16,185,129,0.08);
            opacity:0.75;
        }

        @keyframes slideIn {
            from { opacity:0; transform:translateX(-12px); }
            to   { opacity:1; transform:translateX(0); }
        }
        @keyframes fadeUp {
            from { opacity:0; transform:translateY(16px); }
            to   { opacity:1; transform:translateY(0); }
        }

        .alert-top {
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:8px;
        }
        .alert-name {
            font-weight:700;
            font-size:16px;
            color:#111827;
        }
        .alert-detail {
            font-size:13px;
            color:#4b5563;
            margin-top:5px;
            display:flex;
            align-items:center;
            gap:6px;
        }
        .alert-address {
            font-size:12px;
            color:#6b7280;
            margin-top:4px;
            display:flex;
            align-items:center;
            gap:5px;
        }
        .alert-time {
            font-size:11px;
            color:#9ca3af;
            margin-top:6px;
        }

        /* ── BADGES ──────────────────────────────────────────── */
        .badge {
            display:inline-block;
            padding:3px 12px;
            border-radius:20px;
            font-size:11px;
            font-weight:600;
            white-space:nowrap;
        }
        .badge-red    { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; }
        .badge-amber  { background:#fffbeb; color:#b45309; border:1px solid #fde68a; }
        .badge-green  { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
        .badge-ok     { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }

        /* ── STATUS FLOW ─────────────────────────────────────── */
        .status-flow {
            display:flex;
            align-items:center;
            gap:4px;
            margin-top:12px;
            flex-wrap:wrap;
        }
        .step {
            padding:4px 12px;
            border-radius:20px;
            font-size:11px;
            font-weight:600;
            transition:0.2s;
        }
        .step-done    { background:#085041; color:white; }
        .step-pending { background:#f3f4f6; color:#9ca3af; border:1px solid #e5e7eb; }
        .step-arrow   { color:#d1d5db; font-size:12px; }

        /* ── ACTION BUTTONS ──────────────────────────────────── */
        .action-row {
            display:flex;
            gap:10px;
            margin-top:14px;
            flex-wrap:wrap;
        }
        .btn {
            padding:9px 18px;
            border:none;
            border-radius:10px;
            font-size:12px;
            font-weight:600;
            cursor:pointer;
            font-family:'Poppins',sans-serif;
            transition:all 0.2s;
            text-decoration:none;
            display:inline-flex;
            align-items:center;
            gap:6px;
        }
        .btn:hover { transform:translateY(-1px); }
        .btn-attend  { background:#f59e0b; color:white; }
        .btn-attend:hover  { background:#d97706; }
        .btn-maps    { background:#3b82f6; color:white; }
        .btn-maps:hover    { background:#2563eb; }
        .btn-call    { background:#8b5cf6; color:white; }
        .btn-call:hover    { background:#7c3aed; }
        .btn-visit   { background:#10b981; color:white; }
        .btn-visit:hover   { background:#059669; }

        /* ── VISIT LOG MODAL ─────────────────────────────────── */
        .visit-form {
            background:#f8fffe;
            border:1px solid #d1fae5;
            border-radius:12px;
            padding:16px;
            margin-top:12px;
            display:none;
        }
        .visit-form.open { display:block; animation:fadeUp 0.3s ease; }
        .visit-form label {
            font-size:12px;
            font-weight:600;
            color:#085041;
            display:block;
            margin-bottom:5px;
        }
        .visit-form select,
        .visit-form input,
        .visit-form textarea {
            width:100%;
            padding:9px 12px;
            border:1.5px solid #d1fae5;
            border-radius:8px;
            font-family:'Poppins',sans-serif;
            font-size:12px;
            margin-bottom:10px;
            background:white;
            color:#1f2937;
        }
        .visit-form select:focus,
        .visit-form input:focus,
        .visit-form textarea:focus {
            outline:none;
            border-color:#085041;
        }
        .btn-submit-visit {
            background:#085041;
            color:white;
            padding:9px 20px;
            border:none;
            border-radius:8px;
            font-size:12px;
            font-weight:600;
            cursor:pointer;
            font-family:'Poppins',sans-serif;
        }

        /* ── ESCALATION LEVEL ────────────────────────────────── */
        .escalation-badge {
            background:#fef3c7;
            border:1px solid #fcd34d;
            color:#92400e;
            padding:3px 10px;
            border-radius:20px;
            font-size:10px;
            font-weight:600;
        }

        /* ── PATIENT ROWS ────────────────────────────────────── */
        .patient-row {
            background:white;
            border-radius:14px;
            padding:14px 18px;
            margin:0 20px 10px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            border:1px solid #d1fae5;
            box-shadow:0 2px 8px rgba(0,0,0,0.04);
            animation:fadeUp 0.4s ease both;
            transition:transform 0.2s, box-shadow 0.2s;
        }
        .patient-row:hover {
            transform:translateX(4px);
            box-shadow:0 4px 16px rgba(8,80,65,0.1);
        }
        .patient-name   { font-weight:600; font-size:14px; color:#111827; }
        .patient-detail { font-size:12px; color:#6b7280; margin-top:3px; }
        .patient-address{ font-size:11px; color:#9ca3af; margin-top:2px; }

        .risk-bar-wrap {
            height:5px;
            background:#f3f4f6;
            border-radius:3px;
            margin-top:8px;
            overflow:hidden;
            width:120px;
        }
        .risk-bar-fill {
            height:100%;
            border-radius:3px;
            transition:width 1s ease;
        }

        /* ── EMPTY STATE ─────────────────────────────────────── */
        .empty {
            text-align:center;
            padding:40px 20px;
            color:#9ca3af;
            font-size:14px;
        }
        .empty-icon { font-size:40px; margin-bottom:10px; }

        /* ── RECOVERY STATUS ─────────────────────────────────── */
        .recovery-msg {
            margin-top:10px;
            padding:8px 14px;
            border-radius:8px;
            font-size:12px;
            font-weight:500;
        }
        .recovery-waiting {
            background:#fffbeb;
            color:#92400e;
            border:1px solid #fde68a;
        }
        .recovery-done {
            background:#f0fdf4;
            color:#166534;
            border:1px solid #bbf7d0;
        }

        /* ── FOOTER ──────────────────────────────────────────── */
        .footer {
            text-align:center;
            font-size:11px;
            color:#9ca3af;
            padding:24px 20px;
            margin-top:10px;
            border-top:1px solid #e5e7eb;
        }
        .footer a { color:#085041; text-decoration:none; }

        /* ── SCROLL TO TOP ───────────────────────────────────── */
        .scroll-top {
            position:fixed;
            bottom:24px; right:24px;
            background:#085041;
            color:white;
            border:none;
            border-radius:50%;
            width:44px; height:44px;
            font-size:18px;
            cursor:pointer;
            box-shadow:0 4px 14px rgba(8,80,65,0.35);
            display:none;
            align-items:center;
            justify-content:center;
            transition:0.2s;
            z-index:100;
        }
        .scroll-top:hover { background:#0a6b52; transform:scale(1.1); }

        @media(max-width:480px){
            .stats { grid-template-columns:repeat(3,1fr); gap:8px; }
            .stat-number { font-size:26px; }
            .header h1 { font-size:18px; }
        }
    </style>
</head>
<body>

<!-- ── HEADER ──────────────────────────────────────────────────── -->
<div class="header">
    <h1>
        <span>🌿</span>
        MaaSakhi — ASHA Dashboard
    </h1>
    <p>
        <span class="live-dot"></span>
        Live • Auto-refreshes every 30 seconds
    </p>
    <div class="header-meta">
        <span class="header-badge">👩 ASHA: {{ asha_id }}</span>
        <span class="header-badge">📋 {{ total }} Patients</span>
        <span class="header-badge">📊 {{ total_reports }} Reports</span>
        <span class="header-badge" style="background:rgba(239,68,68,0.25);
               border-color:rgba(239,68,68,0.4)">
            🚨 {{ high_risk }} Active Alerts
        </span>
    </div>
</div>

<!-- ── STATS ────────────────────────────────────────────────────── -->
<div class="stats">
    <div class="stat">
        <div class="stat-icon">🚨</div>
        <div class="stat-number" style="color:#ef4444">{{ high_risk }}</div>
        <div class="stat-label">Active Alerts</div>
    </div>
    <div class="stat">
        <div class="stat-icon">👩</div>
        <div class="stat-number" style="color:#0a6b52">{{ total }}</div>
        <div class="stat-label">Registered</div>
    </div>
    <div class="stat">
        <div class="stat-icon">✅</div>
        <div class="stat-number" style="color:#10b981">{{ safe }}</div>
        <div class="stat-label">Safe</div>
    </div>
</div>

<!-- ── ALERTS ───────────────────────────────────────────────────── -->
<p class="section">
    ⚠️ High Risk Alerts
    <span class="section-count">{{ alerts|length }}</span>
</p>

{% if alerts %}
    {% for a in alerts %}
    <div class="alert-card
        {% if a.status == 'Attended' %}attended
        {% elif a.status == 'Resolved' %}resolved{% endif %}">

        <!-- Top row -->
        <div class="alert-top">
            <div>
                <div class="alert-name">{{ a.name }}</div>
                {% if a.get('level', 0) > 0 %}
                <span class="escalation-badge">
                    ⬆ Escalated — Level {{ a.get('level', 0) }}
                </span>
                {% endif %}
            </div>
            <span class="badge
                {% if a.status == 'Pending' %}badge-red
                {% elif a.status == 'Attended' %}badge-amber
                {% else %}badge-green{% endif %}">
                {% if a.status == 'Pending' %}🔴
                {% elif a.status == 'Attended' %}🟡
                {% else %}🟢{% endif %}
                {{ a.status }}
            </span>
        </div>

        <!-- Details -->
        <div class="alert-detail">
            🤰 Week {{ a.week }} &nbsp;•&nbsp;
            ⚠️ {{ a.symptom[:80] }}{% if a.symptom|length > 80 %}...{% endif %}
        </div>
        <div class="alert-detail">📞 {{ a.phone }}</div>

        <!-- Address + Maps -->
        {% if a.get('address') or a.get('village') %}
        <div class="alert-address">
            📍
            {% if a.get('address') %}{{ a.address }}{% endif %}
            {% if a.get('village') %} • {{ a.village }}{% endif %}
        </div>
        {% endif %}

        <div class="alert-time">🕐 {{ a.time }}</div>

        <!-- Status flow -->
        <div class="status-flow">
            <span class="step step-done">Alerted</span>
            <span class="step-arrow">→</span>
            <span class="step
                {% if a.status in ['Attended','Resolved'] %}step-done
                {% else %}step-pending{% endif %}">
                Attended
            </span>
            <span class="step-arrow">→</span>
            <span class="step
                {% if a.status == 'Resolved' %}step-done
                {% else %}step-pending{% endif %}">
                Resolved
            </span>
        </div>

        <!-- Action buttons -->
        <div class="action-row">

            {% if a.get('maps_link') %}
            <a href="{{ a.maps_link }}" target="_blank" class="btn btn-maps">
                📌 Navigate
            </a>
            {% endif %}

            <a href="tel:{{ a.phone }}" class="btn btn-call">
                📞 Call
            </a>

            {% if a.status == 'Pending' %}
            <form method="POST"
                  action="/dashboard/{{ asha_id }}/attend/{{ a.id }}"
                  style="display:inline">
                <button type="submit" class="btn btn-attend">
                    ✅ Mark Attended
                </button>
            </form>
            {% endif %}

            {% if a.status == 'Attended' %}
            <button class="btn btn-visit"
                    onclick="toggleVisit('visit-{{ a.id }}')">
                📋 Log Visit Outcome
            </button>
            {% endif %}

        </div>

        <!-- Recovery waiting / done message -->
        {% if a.status == 'Attended' %}
        <div class="recovery-msg recovery-waiting">
            ⏳ Waiting for patient to confirm recovery on WhatsApp...
        </div>
        {% elif a.status == 'Resolved' %}
        <div class="recovery-msg recovery-done">
            ✅ Patient confirmed recovery — case closed.
        </div>
        {% endif %}

        <!-- Visit outcome form (hidden by default) -->
        {% if a.status == 'Attended' %}
        <div class="visit-form" id="visit-{{ a.id }}">
            <form method="POST"
                  action="/dashboard/{{ asha_id }}/log-visit/{{ a.id }}">

                <label>What was the outcome of your visit?</label>
                <select name="outcome" required>
                    <option value="">-- Select outcome --</option>
                    <option value="stable">
                        🟢 Patient is stable — monitoring at home
                    </option>
                    <option value="referred_phc">
                        🏥 Referred to PHC / CHC
                    </option>
                    <option value="referred_hospital">
                        🏨 Referred to District Hospital
                    </option>
                    <option value="called_108">
                        🚑 Emergency — called 108 ambulance
                    </option>
                    <option value="not_found">
                        ❌ Patient not found at address
                    </option>
                </select>

                <label>Referred to (if applicable)</label>
                <input name="referred_to"
                       placeholder="e.g. PHC Rampur, District Hospital Jaipur"
                       type="text"/>

                <label>Notes (optional)</label>
                <textarea name="notes"
                          rows="2"
                          placeholder="Any additional observations..."></textarea>

                <button type="submit" class="btn-submit-visit">
                    💾 Save Visit Record
                </button>
            </form>
        </div>
        {% endif %}

    </div>
    {% endfor %}

{% else %}
    <div class="empty">
        <div class="empty-icon">✅</div>
        <div>No active alerts right now</div>
        <div style="font-size:12px;margin-top:6px;color:#d1d5db">
            All your patients are safe
        </div>
    </div>
{% endif %}


<!-- ── PATIENTS ─────────────────────────────────────────────────── -->
<p class="section" style="margin-top:16px">
    👩 Registered Patients
    <span class="section-count">{{ total }}</span>
</p>

{% if patients %}
    {% for phone, p in patients.items() %}
    {% if p.step == 'registered' %}

    {% set risk = patient_risks.get(phone, {}) %}
    {% set risk_level = risk.get('level', 'LOW') %}
    {% set risk_score = risk.get('score', 0) %}

    <div class="patient-row">
        <div style="flex:1">
            <div class="patient-name">{{ p.name }}</div>
            <div class="patient-detail">
                🤰 Week {{ p.week }}
                {% if p.village %} &nbsp;•&nbsp; 📍 {{ p.village }}{% endif %}
            </div>
            {% if p.get('address') %}
            <div class="patient-address">🏠 {{ p.address }}</div>
            {% endif %}
            <div class="risk-bar-wrap">
                <div class="risk-bar-fill" style="
                    width:{% if risk_level == 'HIGH' %}90%
                           {% elif risk_level == 'MODERATE' %}55%
                           {% else %}20%{% endif %};
                    background:{% if risk_level == 'HIGH' %}#ef4444
                                {% elif risk_level == 'MODERATE' %}#f59e0b
                                {% else %}#10b981{% endif %}">
                </div>
            </div>
        </div>

        <div style="text-align:right;flex-shrink:0;margin-left:12px">
            <span class="badge
                {% if risk_level == 'HIGH' %}badge-red
                {% elif risk_level == 'MODERATE' %}badge-amber
                {% else %}badge-ok{% endif %}">
                {{ risk_level }}
            </span>
            <div style="font-size:11px;color:#9ca3af;margin-top:5px">
                Score: {{ risk_score }}/100
            </div>
        </div>
    </div>

    {% endif %}
    {% endfor %}

{% else %}
    <div class="empty">
        <div class="empty-icon">👩</div>
        <div>No patients registered yet</div>
        <div style="font-size:12px;margin-top:6px;color:#d1d5db">
            Share the WhatsApp number with women in your village
        </div>
    </div>
{% endif %}


<!-- ── FOOTER ───────────────────────────────────────────────────── -->
<div style="padding:0 20px 20px">
    <a href="/" style="
        display:inline-block;
        padding:10px 20px;
        background:#085041;
        color:white;
        border-radius:10px;
        text-decoration:none;
        font-size:13px;
        font-weight:600">
        ← Back to Home
    </a>
</div>

<div class="footer">
    🌿 MaaSakhi &nbsp;•&nbsp;
    Powered by WHO + NHM + FOGSI Guidelines &nbsp;•&nbsp;
    <a href="/login">Logout</a>
</div>

<!-- ── SCROLL TO TOP ────────────────────────────────────────────── -->
<button class="scroll-top" id="scrollBtn" onclick="window.scrollTo({top:0,behavior:'smooth'})">
    ↑
</button>

<script>
    // Toggle visit outcome form
    function toggleVisit(id) {
        const el = document.getElementById(id);
        el.classList.toggle('open');
    }

    // Scroll to top button
    window.addEventListener('scroll', () => {
        const btn = document.getElementById('scrollBtn');
        btn.style.display = window.scrollY > 300 ? 'flex' : 'none';
    });

    // Animate risk bars on load
    window.addEventListener('load', () => {
        document.querySelectorAll('.risk-bar-fill').forEach(bar => {
            const target = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => { bar.style.width = target; }, 300);
        });
    });

    // Animate stat numbers counting up
    document.querySelectorAll('.stat-number').forEach(el => {
        const target = parseInt(el.textContent) || 0;
        if (target === 0) return;
        let current = 0;
        const step  = Math.ceil(target / 20);
        const timer = setInterval(() => {
            current = Math.min(current + step, target);
            el.textContent = current;
            if (current >= target) clearInterval(timer);
        }, 40);
    });
</script>

</body>
</html>
"""


def render_dashboard(patients, high_risk, total, safe, asha_id):
    from database import (
        get_all_asha_alerts,
        get_symptom_logs,
        get_risk_score_from_db
    )

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
        alerts        = alerts,
        patients      = patients,
        high_risk     = high_risk,
        total         = total,
        safe          = safe,
        total_reports = total_reports,
        patient_risks = patient_risks,
        asha_id       = asha_id
    )