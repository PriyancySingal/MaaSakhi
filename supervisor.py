# ─────────────────────────────────────────────────────────────────
# MaaSakhi — supervisor.py
# ASHA Supervisor (ANM) Dashboard
# Standalone render module — called from app.py
#
# Features (all months):
#   Month 1 — Alert view with Maps, visit log access
#   Month 2 — Performance tracking, escalation controls
#   Month 3 — ANC summary, district trends per block
#   Month 4 — Postpartum + PNC due per ASHA
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string

# ─────────────────────────────────────────────────────────────────
# CSS + HTML TEMPLATE
# ─────────────────────────────────────────────────────────────────

SUPERVISOR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>MaaSakhi — Supervisor Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
        /* ── TOKENS ──────────────────────────────────────────── */
        :root {
            --blue-deep:   #0a2540;
            --blue-mid:    #0369a1;
            --blue-bright: #38bdf8;
            --blue-pale:   #e0f2fe;
            --blue-tint:   #f0f9ff;
            --amber:       #f59e0b;
            --amber-pale:  #fffbeb;
            --red:         #ef4444;
            --red-pale:    #fef2f2;
            --green:       #10b981;
            --green-pale:  #d1fae5;
            --purple:      #8b5cf6;
            --ink:         #0f172a;
            --muted:       #64748b;
            --border:      #e2e8f0;
            --bg:          #f1f5f9;
            --white:       #ffffff;
            --card-shadow: 0 4px 16px rgba(10,37,64,0.08);
            --r:           16px;
            --r-sm:        10px;
        }

        * { margin:0; padding:0; box-sizing:border-box; }

        body {
            font-family: 'Instrument Sans', sans-serif;
            background: var(--bg);
            color: var(--ink);
            min-height: 100vh;
        }

        /* ── HEADER ──────────────────────────────────────────── */
        .header {
            background: linear-gradient(135deg, var(--blue-deep) 0%, #0c3560 100%);
            color: white;
            padding: 22px 28px 0;
            position: relative;
            overflow: hidden;
        }
        .hbg { position:absolute; border-radius:50%; background:rgba(255,255,255,0.04); }
        .hbg.a { width:240px;height:240px; top:-80px; right:-60px; }
        .hbg.b { width:140px;height:140px; bottom:-50px; right:100px; }
        .hbg.c { width:80px; height:80px;  top:30px;   right:200px; }
        .header-role {
            font-size:10px; font-weight:600; letter-spacing:.12em;
            text-transform:uppercase; color:var(--blue-bright);
            margin-bottom:6px;
        }
        .header-title {
            font-family: 'Syne', sans-serif;
            font-size: 22px; font-weight: 800;
            display: flex; align-items: center; gap: 10px;
        }
        .header-sub {
            font-size: 12px; opacity: 0.7; margin-top: 5px;
            display: flex; align-items: center; gap: 10px;
        }
        .live {
            width:7px; height:7px; background:#4ade80;
            border-radius:50%; animation:livepulse 2s infinite; display:inline-block;
        }
        @keyframes livepulse {
            0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(74,222,128,.5); }
            50%      { opacity:.6; box-shadow:0 0 0 6px rgba(74,222,128,0); }
        }
        .header-meta {
            display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap;
        }
        .hpill {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.18);
            padding: 4px 13px; border-radius:20px;
            font-size: 11px; font-weight: 500;
        }
        .hpill.danger { background:rgba(239,68,68,.18); border-color:rgba(239,68,68,.3); }
        .hpill.warn   { background:rgba(245,158,11,.18); border-color:rgba(245,158,11,.3); }

        /* ── TAB NAV ─────────────────────────────────────────── */
        .tab-nav {
            display: flex; background: var(--blue-deep);
            padding: 0 28px; gap:2px; overflow-x:auto; scrollbar-width:none;
        }
        .tab-nav::-webkit-scrollbar { display:none; }
        .tab-btn {
            padding: 10px 18px; border:none; background:transparent;
            color: rgba(255,255,255,.5);
            font-family:'Instrument Sans',sans-serif;
            font-size:12px; font-weight:600;
            cursor:pointer; border-bottom:2px solid transparent;
            transition:all .2s; white-space:nowrap;
            display:flex; align-items:center; gap:5px;
        }
        .tab-btn:hover { color:rgba(255,255,255,.85); }
        .tab-btn.active { color:white; border-bottom-color:#4ade80; }
        .tab-badge {
            background:var(--red); color:white;
            border-radius:20px; padding:1px 6px;
            font-size:10px; font-weight:700;
        }

        /* ── TAB PANELS ──────────────────────────────────────── */
        .tab-panel { display:none; }
        .tab-panel.active { display:block; animation:fadeUp .3s ease; }
        @keyframes fadeUp {
            from { opacity:0; transform:translateY(8px); }
            to   { opacity:1; transform:translateY(0); }
        }
        @keyframes slideIn {
            from { opacity:0; transform:translateX(-8px); }
            to   { opacity:1; transform:translateX(0); }
        }

        /* ── STATS ROW ───────────────────────────────────────── */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(5,1fr);
            gap: 12px; padding: 18px 28px 10px;
        }
        @media(max-width:640px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
        .stat {
            background: white; border-radius:var(--r);
            padding: 16px 12px; text-align:center;
            border:1px solid var(--border);
            box-shadow: var(--card-shadow);
            animation: fadeUp .4s ease both;
            transition: transform .2s;
        }
        .stat:hover { transform:translateY(-3px); }
        .stat-icon { font-size:18px; margin-bottom:4px; }
        .stat-num  { font-family:'Syne',sans-serif; font-size:26px; font-weight:700; line-height:1; }
        .stat-lbl  { font-size:10px; color:var(--muted); margin-top:4px;
                     font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
        .stat:nth-child(1){animation-delay:.05s}
        .stat:nth-child(2){animation-delay:.10s}
        .stat:nth-child(3){animation-delay:.15s}
        .stat:nth-child(4){animation-delay:.20s}
        .stat:nth-child(5){animation-delay:.25s}

        /* ── SECTION HEAD ────────────────────────────────────── */
        .sec-head {
            padding: 8px 28px 10px;
            font-size:11px; font-weight:700; color:var(--blue-mid);
            text-transform:uppercase; letter-spacing:.08em;
            margin-top:8px;
            display:flex; align-items:center; gap:8px;
        }
        .sec-count {
            background:var(--blue-mid); color:white;
            border-radius:20px; padding:1px 9px; font-size:10px;
        }

        /* ── ALERT CARDS ─────────────────────────────────────── */
        .alert-card {
            margin: 0 28px 14px;
            background: white; border-radius:var(--r);
            padding: 18px;
            border-left: 4px solid var(--red);
            box-shadow: 0 4px 20px rgba(239,68,68,.1);
            animation: slideIn .35s ease both;
            transition: transform .2s, box-shadow .2s;
        }
        .alert-card:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(239,68,68,.15); }
        .alert-card.attended { border-left-color:var(--amber); box-shadow:0 4px 20px rgba(245,158,11,.1); }
        .alert-card.resolved { border-left-color:var(--green); opacity:.72; }
        .alert-card.escalated { border-left-color:var(--purple); box-shadow:0 4px 20px rgba(139,92,246,.1); }

        .alert-top { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
        .alert-name { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; }
        .alert-line {
            font-size:12.5px; color:#475569; margin-top:5px;
            display:flex; align-items:center; gap:6px; flex-wrap:wrap;
        }
        .alert-meta { font-size:11.5px; color:var(--muted); margin-top:3px; }
        .alert-time { font-size:11px; color:#94a3b8; margin-top:5px; }

        /* ── BADGES ──────────────────────────────────────────── */
        .badge {
            display:inline-block; padding:3px 11px;
            border-radius:20px; font-size:10.5px; font-weight:600; white-space:nowrap;
        }
        .badge-red    { background:var(--red-pale);   color:#dc2626; border:1px solid #fecaca; }
        .badge-amber  { background:var(--amber-pale);  color:#b45309; border:1px solid #fde68a; }
        .badge-green  { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
        .badge-blue   { background:var(--blue-pale);  color:#0369a1; border:1px solid #bae6fd; }
        .badge-purple { background:#f5f3ff; color:#6d28d9; border:1px solid #ddd6fe; }
        .badge-escl   { background:#fef3c7; color:#92400e; border:1px solid #fcd34d; font-size:10px; }

        /* ── BUTTONS ─────────────────────────────────────────── */
        .btn-row { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
        .btn {
            padding:7px 15px; border:none; border-radius:var(--r-sm);
            font-size:11.5px; font-weight:600; cursor:pointer;
            font-family:'Instrument Sans',sans-serif;
            transition:all .2s; text-decoration:none;
            display:inline-flex; align-items:center; gap:5px;
        }
        .btn:hover { transform:translateY(-1px); filter:brightness(1.08); }
        .btn-blue   { background:var(--blue-mid);  color:white; }
        .btn-red    { background:var(--red);        color:white; }
        .btn-green  { background:var(--green);      color:white; }
        .btn-amber  { background:var(--amber);      color:white; }
        .btn-purple { background:var(--purple);     color:white; }
        .btn-dark   { background:var(--blue-deep);  color:white; }
        .btn-ghost  { background:#f1f5f9; color:var(--ink); border:1px solid var(--border); }

        /* ── STATUS FLOW ─────────────────────────────────────── */
        .status-flow { display:flex; align-items:center; gap:4px; margin-top:10px; flex-wrap:wrap; }
        .step { padding:4px 11px; border-radius:20px; font-size:10.5px; font-weight:600; transition:.2s; }
        .step-done { background:var(--blue-deep); color:white; }
        .step-pend { background:#f1f5f9; color:#94a3b8; border:1px solid var(--border); }
        .step-arr  { color:#cbd5e1; font-size:11px; }

        /* ── ASHA WORKER TABLE ───────────────────────────────── */
        .table-wrap { margin:0 28px 20px; overflow-x:auto; }
        table {
            width:100%; border-collapse:collapse;
            background:white; border-radius:var(--r);
            overflow:hidden; box-shadow:var(--card-shadow);
        }
        thead th {
            background:#f8fafc; padding:11px 14px;
            font-size:11px; font-weight:700; text-align:left;
            color:var(--muted); text-transform:uppercase; letter-spacing:.05em;
            border-bottom:1px solid var(--border);
        }
        tbody td { padding:12px 14px; font-size:13px; border-bottom:1px solid #f1f5f9; }
        tbody tr:last-child td { border-bottom:none; }
        tbody tr:hover { background:#f8fafc; }
        .rating-GREEN  { color:#16a34a; font-weight:600; }
        .rating-AMBER  { color:#b45309; font-weight:600; }
        .rating-RED    { color:#dc2626; font-weight:600; }
        .rating-unknown{ color:#94a3b8; }

        /* ── PERFORMANCE CARDS ───────────────────────────────── */
        .perf-grid {
            display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
            gap:14px; padding:0 28px 20px;
        }
        .perf-card {
            background:white; border-radius:var(--r);
            padding:18px; box-shadow:var(--card-shadow);
            border:1px solid var(--border);
            animation:fadeUp .4s ease both;
        }
        .perf-card-name {
            font-family:'Syne',sans-serif; font-size:14px; font-weight:700;
            margin-bottom:4px;
        }
        .perf-card-meta { font-size:11.5px; color:var(--muted); margin-bottom:14px; }
        .metric-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
        .metric-label { font-size:12px; color:var(--muted); }
        .metric-val { font-family:'Syne',sans-serif; font-size:16px; font-weight:700; }
        .perf-bar { height:5px; background:#f1f5f9; border-radius:3px; margin-top:3px; overflow:hidden; }
        .perf-bar-fill { height:100%; border-radius:3px; transition:width 1.2s ease; }
        .rating-pill {
            display:flex; align-items:center; justify-content:center;
            gap:6px; margin-top:12px; padding:9px;
            border-radius:8px; font-size:12px; font-weight:600;
        }
        .rp-GREEN  { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; }
        .rp-AMBER  { background:var(--amber-pale); color:#92400e; border:1px solid #fde68a; }
        .rp-RED    { background:var(--red-pale); color:#991b1b; border:1px solid #fecaca; }
        .rp-unknown{ background:#f8fafc; color:var(--muted); border:1px solid var(--border); }

        /* ── POSTPARTUM DUE ──────────────────────────────────── */
        .pp-card {
            background:white; border-radius:var(--r);
            padding:16px 18px; margin:0 28px 12px;
            border-left:4px solid var(--purple);
            box-shadow:var(--card-shadow);
            animation:slideIn .35s ease both;
        }
        .pp-name { font-family:'Syne',sans-serif; font-size:14px; font-weight:700; }
        .pp-meta { font-size:12px; color:var(--muted); margin-top:3px; }
        .pnc-row { display:flex; gap:5px; margin-top:10px; flex-wrap:wrap; }
        .pnc-pip {
            padding:4px 11px; border-radius:20px;
            font-size:11px; font-weight:600;
        }
        .pnc-done   { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; }
        .pnc-today  { background:#fef3c7; color:#92400e; border:1px solid #fcd34d;
                      animation:bounce .9s infinite; }
        .pnc-future { background:#f1f5f9; color:#94a3b8; border:1px solid var(--border); }
        @keyframes bounce {
            0%,100% { transform:translateY(0); }
            50%      { transform:translateY(-3px); }
        }

        /* ── ANC SUMMARY ─────────────────────────────────────── */
        .anc-card {
            background:white; border-radius:var(--r);
            padding:18px; margin:0 28px 14px;
            box-shadow:var(--card-shadow); border:1px solid var(--border);
        }
        .anc-title { font-family:'Syne',sans-serif; font-size:14px; font-weight:700; margin-bottom:14px; }
        .anc-steps { display:flex; gap:0; position:relative; }
        .anc-steps::before {
            content:''; position:absolute;
            top:13px; left:14px; right:14px;
            height:2px; background:var(--border); z-index:0;
        }
        .anc-step  { flex:1; text-align:center; position:relative; z-index:1; }
        .anc-dot {
            width:26px; height:26px; border-radius:50%;
            margin:0 auto 6px;
            display:flex; align-items:center; justify-content:center;
            font-size:11px; font-weight:700;
        }
        .anc-dot.done   { background:var(--blue-mid); color:white; }
        .anc-dot.next   { background:var(--amber); color:white; }
        .anc-dot.future { background:#f1f5f9; color:#94a3b8; border:2px solid var(--border); }
        .anc-lbl { font-size:9px; color:var(--muted); font-weight:600; }

        /* ── ESCALATION FORM ─────────────────────────────────── */
        .esc-form {
            background:var(--red-pale); border:1px solid #fecaca;
            border-radius:var(--r-sm); padding:14px;
            margin-top:10px; display:none;
        }
        .esc-form.open { display:block; animation:fadeUp .3s ease; }
        .form-label { font-size:11.5px; font-weight:600; color:var(--blue-deep); display:block; margin-bottom:5px; }
        .form-ctrl {
            width:100%; padding:9px 12px;
            border:1.5px solid #fecaca; border-radius:8px;
            font-family:'Instrument Sans',sans-serif; font-size:12px;
            margin-bottom:10px; background:white; color:var(--ink);
        }
        .form-ctrl:focus { outline:none; border-color:var(--blue-mid); }

        /* ── EMPTY ───────────────────────────────────────────── */
        .empty { text-align:center; padding:44px 20px; color:#94a3b8; font-size:13px; }
        .empty-icon { font-size:36px; margin-bottom:10px; }

        /* ── FOOTER ──────────────────────────────────────────── */
        .footer {
            text-align:center; font-size:11px; color:#94a3b8;
            padding:24px 28px; border-top:1px solid var(--border); margin-top:8px;
        }
        .footer a { color:var(--blue-mid); text-decoration:none; }

        /* ── FAB ─────────────────────────────────────────────── */
        .fab {
            position:fixed; bottom:22px; right:22px;
            background:var(--blue-deep); color:white;
            border:none; border-radius:50%;
            width:44px; height:44px; font-size:18px; cursor:pointer;
            box-shadow:0 4px 16px rgba(10,37,64,.35);
            display:none; align-items:center; justify-content:center;
            transition:.2s; z-index:100;
        }
        .fab:hover { background:var(--blue-mid); transform:scale(1.1); }
    </style>
</head>
<body>

<!-- ════════════════════════════════════════════════════════════
     HEADER
═════════════════════════════════════════════════════════════ -->
<div class="header">
    <div class="hbg a"></div><div class="hbg b"></div><div class="hbg c"></div>
    <div class="header-role">Supervisor (ANM) · Block Level</div>
    <div class="header-title">👩‍💼 {{ supervisor_name }}</div>
    <div class="header-sub">
        <span class="live"></span>
        Live · Auto-refreshes every 30 s &nbsp;•&nbsp; {{ block_name }} · {{ district }}
    </div>
    <div class="header-meta">
        <span class="hpill">🏘️ {{ block_name }}</span>
        <span class="hpill">👩 {{ stats.total_ashas }} ASHA Workers</span>
        <span class="hpill">🤰 {{ stats.total_patients }} Patients</span>
        {% if stats.pending_alerts > 0 %}
        <span class="hpill danger">🚨 {{ stats.pending_alerts }} Pending</span>
        {% endif %}
        {% if stats.escalated_to_me > 0 %}
        <span class="hpill warn">⬆ {{ stats.escalated_to_me }} Escalated to Me</span>
        {% endif %}
    </div>
</div>

<!-- ════════════════════════════════════════════════════════════
     TAB NAV
═════════════════════════════════════════════════════════════ -->
<div class="tab-nav" role="tablist">
    <button class="tab-btn active" onclick="showTab('alerts',this)" role="tab">
        🚨 Alerts
        {% if stats.pending_alerts > 0 %}
        <span class="tab-badge">{{ stats.pending_alerts }}</span>
        {% endif %}
    </button>
    <button class="tab-btn" onclick="showTab('ashas',this)" role="tab">
        👩 ASHA Workers
    </button>
    <button class="tab-btn" onclick="showTab('performance',this)" role="tab">
        📊 Performance
    </button>
    <button class="tab-btn" onclick="showTab('postpartum',this)" role="tab">
        👶 Postpartum
        {% if pp_due_count > 0 %}
        <span class="tab-badge">{{ pp_due_count }}</span>
        {% endif %}
    </button>
    <button class="tab-btn" onclick="showTab('anc',this)" role="tab">
        📋 ANC Summary
    </button>
</div>

<!-- ════════════════════════════════════════════════════════════
     STATS ROW
═════════════════════════════════════════════════════════════ -->
<div class="stats-row">
    <div class="stat">
        <div class="stat-icon">👩</div>
        <div class="stat-num" style="color:var(--blue-mid)" data-count="{{ stats.total_ashas }}">{{ stats.total_ashas }}</div>
        <div class="stat-lbl">ASHA Workers</div>
    </div>
    <div class="stat">
        <div class="stat-icon">🤰</div>
        <div class="stat-num" style="color:var(--green)" data-count="{{ stats.total_patients }}">{{ stats.total_patients }}</div>
        <div class="stat-lbl">Patients</div>
    </div>
    <div class="stat">
        <div class="stat-icon">🚨</div>
        <div class="stat-num" style="color:var(--red)" data-count="{{ stats.pending_alerts }}">{{ stats.pending_alerts }}</div>
        <div class="stat-lbl">Pending</div>
    </div>
    <div class="stat">
        <div class="stat-icon">⬆</div>
        <div class="stat-num" style="color:var(--amber)" data-count="{{ stats.escalated_to_me }}">{{ stats.escalated_to_me }}</div>
        <div class="stat-lbl">Escalated to Me</div>
    </div>
    <div class="stat">
        <div class="stat-icon">✅</div>
        <div class="stat-num" style="color:var(--green)" data-count="{{ stats.resolved_this_week }}">{{ stats.resolved_this_week }}</div>
        <div class="stat-lbl">Resolved (7d)</div>
    </div>
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 1 — ALERTS
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel active" id="tab-alerts">

    <p class="sec-head">
        ⚠️ All Alerts — My ASHA Workers
        <span class="sec-count">{{ alerts|length }}</span>
    </p>

    {% if alerts %}
        {% for a in alerts %}
        <div class="alert-card
            {% if a.status=='Attended' %}attended
            {% elif a.status=='Resolved' %}resolved
            {% elif a.get('level',0) >= 1 %}escalated{% endif %}">

            <!-- Top row -->
            <div class="alert-top">
                <div>
                    <div class="alert-name">{{ a.name }}</div>
                    {% if a.get('level',0) > 0 %}
                    <span class="badge badge-escl">⬆ Escalated · Level {{ a.level }}</span>
                    {% endif %}
                </div>
                <span class="badge
                    {% if a.status=='Pending'  %}badge-red
                    {% elif a.status=='Attended'%}badge-amber
                    {% else %}badge-green{% endif %}">
                    {% if a.status=='Pending' %}🔴{% elif a.status=='Attended' %}🟡{% else %}🟢{% endif %}
                    {{ a.status }}
                </span>
            </div>

            <div class="alert-line">
                🤰 Week {{ a.week }} &nbsp;•&nbsp; ⚠️ {{ a.symptom[:70] }}{% if a.symptom|length > 70 %}…{% endif %}
            </div>
            <div class="alert-meta">📞 {{ a.phone }}
                {% if a.get('village') %} &nbsp;•&nbsp; 📍 {{ a.village }}{% endif %}
                {% if a.get('address') %} &nbsp;•&nbsp; 🏠 {{ a.address }}{% endif %}
            </div>
            <div class="alert-meta">
                👩 ASHA: {{ a.get('asha_name','—') }}
                {% if a.get('asha_id') %}
                &nbsp;(<a href="/dashboard/{{ a.asha_id }}" target="_blank"
                          style="color:var(--blue-mid);font-size:11px">View dashboard →</a>)
                {% endif %}
            </div>
            <div class="alert-time">🕐 {{ a.time }}</div>

            <!-- Status flow -->
            <div class="status-flow">
                <span class="step step-done">Alerted</span>
                <span class="step-arr">→</span>
                <span class="step {% if a.status in ['Attended','Resolved'] %}step-done{% else %}step-pend{% endif %}">
                    Attended
                </span>
                <span class="step-arr">→</span>
                <span class="step {% if a.status=='Resolved' %}step-done{% else %}step-pend{% endif %}">
                    Resolved
                </span>
            </div>

            <!-- Action buttons -->
            <div class="btn-row">
                {% if a.get('maps_link') %}
                <a href="{{ a.maps_link }}" target="_blank" class="btn btn-blue">📌 Navigate</a>
                {% endif %}
                <a href="tel:{{ a.phone }}" class="btn btn-purple">📞 Call Patient</a>
                {% if a.get('asha_id') %}
                <a href="tel:{{ a.get('asha_phone','') }}" class="btn btn-ghost">📞 Call ASHA</a>
                {% endif %}

                {% if a.status == 'Pending' and a.get('level',0) < 2 %}
                <button class="btn btn-amber"
                        onclick="toggleEsc('esc-{{ a.id }}')">
                    ⬆ Escalate to BMO
                </button>
                {% endif %}

                {% if a.status in ['Pending','Attended'] %}
                <form method="POST"
                      action="/supervisor/{{ supervisor_id }}/resolve/{{ a.id }}"
                      style="display:inline">
                    <button type="submit" class="btn btn-green">✅ Mark Resolved</button>
                </form>
                {% endif %}
            </div>

            <!-- Escalation reason form -->
            {% if a.status == 'Pending' and a.get('level',0) < 2 %}
            <div class="esc-form" id="esc-{{ a.id }}">
                <form method="POST"
                      action="/supervisor/{{ supervisor_id }}/escalate/{{ a.id }}">
                    <label class="form-label">Reason for escalation to BMO</label>
                    <select name="reason" class="form-ctrl">
                        <option value="no_response">ASHA not responding for 2+ hours</option>
                        <option value="critical_condition">Patient in critical condition</option>
                        <option value="transport_needed">Emergency transport needed</option>
                        <option value="blood_needed">Blood / transfusion needed</option>
                        <option value="hospital_referral">Immediate hospital admission required</option>
                        <option value="other">Other</option>
                    </select>
                    <label class="form-label">Additional notes (optional)</label>
                    <textarea name="notes" class="form-ctrl" rows="2"
                              placeholder="Any details for BMO..."></textarea>
                    <button type="submit" class="btn btn-red">⬆ Confirm Escalate to BMO</button>
                </form>
            </div>
            {% endif %}

        </div>
        {% endfor %}
    {% else %}
        <div class="empty">
            <div class="empty-icon">✅</div>
            <div>No active alerts across your ASHA workers</div>
            <div style="font-size:11px;margin-top:5px;color:#cbd5e1">
                All patients are currently safe
            </div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 2 — ASHA WORKERS
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-ashas">
    <p class="sec-head">
        👩 My ASHA Workers
        <span class="sec-count">{{ ashas|length }}</span>
    </p>

    {% if ashas %}
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Village</th>
                    <th>Patients</th>
                    <th>Pending</th>
                    <th>Resolved</th>
                    <th>Escalated</th>
                    <th>Avg Response</th>
                    <th>Status</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {% for a in ashas %}
                {% set hrs = a.get('avg_response_hrs') %}
                {% if hrs is none %}
                    {% set rating = 'unknown' %}
                {% elif hrs <= 1 %}
                    {% set rating = 'GREEN' %}
                {% elif hrs <= 3 %}
                    {% set rating = 'AMBER' %}
                {% else %}
                    {% set rating = 'RED' %}
                {% endif %}
                <tr>
                    <td>
                        <div style="font-weight:600">{{ a.name }}</div>
                        <div style="font-size:11px;color:var(--muted)">{{ a.phone }}</div>
                    </td>
                    <td>{{ a.village }}</td>
                    <td style="text-align:center;font-weight:600">{{ a.patient_count }}</td>
                    <td style="text-align:center">
                        {% if a.pending_alerts > 0 %}
                        <span style="color:var(--red);font-weight:700">{{ a.pending_alerts }}</span>
                        {% else %}<span style="color:var(--green)">0</span>{% endif %}
                    </td>
                    <td style="text-align:center;color:var(--green);font-weight:600">
                        {{ a.resolved_alerts }}
                    </td>
                    <td style="text-align:center">
                        {% if a.escalated_alerts > 0 %}
                        <span style="color:var(--amber);font-weight:600">{{ a.escalated_alerts }}</span>
                        {% else %}<span style="color:var(--muted)">0</span>{% endif %}
                    </td>
                    <td>
                        <span class="rating-{{ rating }}">
                            {% if rating=='GREEN'  %}🟢 ≤1 hr
                            {% elif rating=='AMBER' %}🟡 {{ hrs }}h
                            {% elif rating=='RED'   %}🔴 {{ hrs }}h
                            {% else %}—{% endif %}
                        </span>
                    </td>
                    <td>
                        <span class="badge {% if a.is_active %}badge-green{% else %}badge-red{% endif %}">
                            {% if a.is_active %}Active{% else %}Inactive{% endif %}
                        </span>
                    </td>
                    <td>
                        <a href="/dashboard/{{ a.asha_id }}" target="_blank"
                           style="color:var(--blue-mid);font-size:12px;font-weight:600">
                            View →
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
        <div class="empty">
            <div class="empty-icon">👩</div>
            <div>No ASHA workers assigned to you yet</div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 3 — PERFORMANCE (Month 2)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-performance">
    <p class="sec-head">📊 Individual ASHA Performance — Last 30 Days</p>

    {% if performances %}
    <div class="perf-grid">
        {% for p in performances %}
        {% set rating = p.get('performance_rating','unknown') %}
        <div class="perf-card" style="animation-delay:{{ loop.index * 0.06 }}s">
            <div class="perf-card-name">{{ p.name }}</div>
            <div class="perf-card-meta">📍 {{ p.village }}</div>

            <div class="metric-row">
                <span class="metric-label">Visit Count</span>
                <span class="metric-val" style="color:var(--blue-mid)">
                    {{ p.get('visit_count',0) }}
                </span>
            </div>

            <div class="metric-row">
                <span class="metric-label">Resolution Rate</span>
                <span class="metric-val" style="color:var(--green)">
                    {{ p.get('resolution_rate',0) }}%
                </span>
            </div>
            <div class="perf-bar">
                <div class="perf-bar-fill"
                     style="width:{{ p.get('resolution_rate',0) }}%;background:var(--green)">
                </div>
            </div>

            <div class="metric-row" style="margin-top:8px">
                <span class="metric-label">Escalation Rate</span>
                <span class="metric-val" style="color:var(--red)">
                    {{ p.get('escalation_rate',0) }}%
                </span>
            </div>
            <div class="perf-bar">
                <div class="perf-bar-fill"
                     style="width:{{ p.get('escalation_rate',0) }}%;background:var(--red)">
                </div>
            </div>

            <div class="metric-row" style="margin-top:8px">
                <span class="metric-label">Avg Response Time</span>
                <span class="metric-val" style="color:var(--amber)">
                    {% if p.get('avg_response_hrs') %}{{ p.avg_response_hrs }}h{% else %}—{% endif %}
                </span>
            </div>

            <div class="rating-pill rp-{{ rating }}">
                {% if rating=='GREEN'  %}🌟 Excellent — keep it up!
                {% elif rating=='AMBER' %}⚠️ Good — reduce response time
                {% elif rating=='RED'   %}🔴 Needs improvement
                {% else %}📊 Not enough data yet{% endif %}
            </div>

            <div style="margin-top:12px">
                <a href="/dashboard/{{ p.asha_id }}" target="_blank"
                   class="btn btn-ghost" style="font-size:11px">
                    View Full Dashboard →
                </a>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Block-level summary -->
    <p class="sec-head" style="margin-top:8px">📈 Block Summary</p>
    <div style="margin:0 28px 20px;background:white;border-radius:var(--r);
                padding:20px;box-shadow:var(--card-shadow);border:1px solid var(--border)">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px">
            <div style="text-align:center">
                <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                            color:var(--green)">
                    {{ block_avg_resolution }}%
                </div>
                <div style="font-size:11px;color:var(--muted);margin-top:3px">
                    Avg Resolution Rate
                </div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                            color:var(--amber)">
                    {{ block_avg_response }}h
                </div>
                <div style="font-size:11px;color:var(--muted);margin-top:3px">
                    Avg Response Time
                </div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                            color:var(--red)">
                    {{ top_escalation_asha }}
                </div>
                <div style="font-size:11px;color:var(--muted);margin-top:3px">
                    Most Escalations (ASHA)
                </div>
            </div>
            <div style="text-align:center">
                <div style="font-family:'Syne',sans-serif;font-size:24px;font-weight:700;
                            color:var(--blue-mid)">
                    {{ top_performer_asha }}
                </div>
                <div style="font-size:11px;color:var(--muted);margin-top:3px">
                    Top Performer
                </div>
            </div>
        </div>
    </div>

    {% else %}
        <div class="empty">
            <div class="empty-icon">📊</div>
            <div>No performance data yet</div>
            <div style="font-size:11px;margin-top:5px;color:#cbd5e1">
                Data appears after ASHA workers log visit outcomes
            </div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 4 — POSTPARTUM DUE (Month 4)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-postpartum">

    <div style="margin:14px 28px 10px;background:#f5f3ff;border:1.5px solid #ddd6fe;
                border-radius:var(--r-sm);padding:12px 16px;
                display:flex;align-items:flex-start;gap:10px">
        <div style="font-size:18px;flex-shrink:0">🤱</div>
        <div style="font-size:12px;color:#6d28d9;line-height:1.7;font-weight:500">
            <strong>Postpartum danger signs — counsel mothers to watch for:</strong><br>
            Excessive bleeding · Fever >38°C · Chest pain · Wound discharge ·
            Mastitis · Severe headache · Swollen legs
        </div>
    </div>

    <p class="sec-head">
        👶 PNC Check-ins Due Today
        <span class="sec-count">{{ pp_due_count }}</span>
    </p>

    {% if all_pp_due %}
        {% for pp in all_pp_due %}
        <div class="pp-card">
            <div class="pp-name">{{ pp.name }}</div>
            <div class="pp-meta">
                📅 Delivered: {{ pp.delivery_date }}
                {% if pp.get('birth_weight') %} · Baby: {{ pp.birth_weight }} kg{% endif %}
                &nbsp;•&nbsp; ASHA: {{ pp.get('asha_name','—') }}
                (<a href="/dashboard/{{ pp.get('asha_id','') }}" target="_blank"
                   style="color:var(--blue-mid);font-size:11px">dashboard →</a>)
            </div>
            <div class="pp-meta">📞 {{ pp.phone }}</div>

            <div class="pnc-row">
                {% for day in [1,3,7,14,42] %}
                <span class="pnc-pip
                    {% if pp.days_since > day %}pnc-done
                    {% elif pp.days_since == day %}pnc-today
                    {% else %}pnc-future{% endif %}">
                    Day {{ day }}
                </span>
                {% endfor %}
            </div>

            <div class="btn-row">
                <a href="tel:{{ pp.phone }}" class="btn btn-purple">📞 Call Patient</a>
                <a href="tel:{{ pp.get('asha_phone','') }}" class="btn btn-ghost">📞 Call ASHA</a>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty">
            <div class="empty-icon">👶</div>
            <div>No PNC visits due today across your block</div>
        </div>
    {% endif %}

    <!-- Postpartum patients full list -->
    <p class="sec-head" style="margin-top:10px">
        🤱 All Postpartum Patients
        <span class="sec-count">{{ postpartum_patients|length }}</span>
    </p>

    {% if postpartum_patients %}
    <div class="table-wrap">
        <table>
            <thead><tr>
                <th>Name</th><th>Delivery Date</th>
                <th>Birth Weight</th><th>Facility</th>
                <th>ASHA</th><th>Village</th>
            </tr></thead>
            <tbody>
                {% for pp in postpartum_patients %}
                <tr>
                    <td>
                        <div style="font-weight:600">{{ pp.name }}</div>
                        <div style="font-size:11px;color:var(--muted)">{{ pp.phone }}</div>
                    </td>
                    <td>{{ pp.delivery_date or '—' }}</td>
                    <td>{{ pp.birth_weight or '—' }}</td>
                    <td>{{ pp.facility or '—' }}</td>
                    <td>{{ pp.asha_name or '—' }}</td>
                    <td>{{ pp.village or '—' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
        <div class="empty" style="padding:20px">
            <div style="color:var(--muted);font-size:12px">
                No postpartum patients registered yet
            </div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 5 — ANC SUMMARY (Month 3)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-anc">
    <p class="sec-head">📋 ANC Compliance Across My ASHA Workers</p>

    {% if anc_summary %}
    <div class="table-wrap">
        <table>
            <thead><tr>
                <th>ASHA Name</th><th>Village</th>
                <th>Patients</th>
                <th>ANC 1 ✓</th><th>ANC 2 ✓</th>
                <th>ANC 3 ✓</th><th>ANC 4 ✓</th>
                <th>Full Coverage</th>
            </tr></thead>
            <tbody>
                {% for row in anc_summary %}
                {% set full = row.anc1 > 0 and row.anc2 > 0 and row.anc3 > 0 and row.anc4 > 0 %}
                <tr>
                    <td style="font-weight:600">{{ row.asha_name }}</td>
                    <td>{{ row.village }}</td>
                    <td style="text-align:center;font-weight:600">{{ row.total_patients }}</td>
                    <td style="text-align:center">
                        <span class="badge {% if row.anc1 > 0 %}badge-green{% else %}badge-red{% endif %}">
                            {{ row.anc1 }}
                        </span>
                    </td>
                    <td style="text-align:center">
                        <span class="badge {% if row.anc2 > 0 %}badge-green{% else %}badge-amber{% endif %}">
                            {{ row.anc2 }}
                        </span>
                    </td>
                    <td style="text-align:center">
                        <span class="badge {% if row.anc3 > 0 %}badge-green{% else %}badge-amber{% endif %}">
                            {{ row.anc3 }}
                        </span>
                    </td>
                    <td style="text-align:center">
                        <span class="badge {% if row.anc4 > 0 %}badge-green{% else %}badge-red{% endif %}">
                            {{ row.anc4 }}
                        </span>
                    </td>
                    <td style="text-align:center">
                        <span class="badge {% if full %}badge-green{% else %}badge-amber{% endif %}">
                            {% if full %}✓ Complete{% else %}⚠ Incomplete{% endif %}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <!-- Missing ANC alerts -->
    {% if missing_anc %}
    <p class="sec-head" style="margin-top:16px;color:var(--red)">
        ⚠️ Patients with Missing ANC Visits
        <span class="sec-count" style="background:var(--red)">{{ missing_anc|length }}</span>
    </p>
    {% for m in missing_anc %}
    <div style="margin:0 28px 10px;background:var(--red-pale);border-radius:var(--r-sm);
                padding:12px 16px;border:1px solid #fecaca;display:flex;
                justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div>
            <div style="font-weight:600;font-size:13px">{{ m.name }}</div>
            <div style="font-size:11.5px;color:#991b1b">
                Week {{ m.week }} · {{ m.village }} · ASHA: {{ m.asha_name }}
            </div>
            <div style="font-size:11px;color:#b91c1c;margin-top:2px">
                Missing: ANC visits {{ m.missing_visits|join(', ') }}
            </div>
        </div>
        <a href="tel:{{ m.phone }}" class="btn btn-ghost" style="font-size:11px">📞 Call</a>
    </div>
    {% endfor %}
    {% endif %}

    {% else %}
        <div class="empty">
            <div class="empty-icon">📋</div>
            <div>No ANC data recorded yet</div>
            <div style="font-size:11px;margin-top:5px;color:#cbd5e1">
                Ask ASHA workers to log ANC visits from their dashboard
            </div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     FOOTER
═════════════════════════════════════════════════════════════ -->
<div style="padding:20px 28px 8px">
    <a href="/" class="btn btn-dark" style="font-size:12px">← Home</a>
    &nbsp;
    <a href="/login" class="btn btn-ghost" style="font-size:12px">Logout</a>
</div>

<div class="footer">
    🌿 MaaSakhi &nbsp;•&nbsp; Supervisor Dashboard &nbsp;•&nbsp;
    WHO + NHM + FOGSI Guidelines &nbsp;•&nbsp;
    <a href="/login">Logout</a>
</div>

<button class="fab" id="fabBtn" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>

<script>
    // ── Tab switching ─────────────────────────────────────────
    function showTab(name, btn) {
        document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el  => el.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        btn.classList.add('active');
        window.scrollTo({top:0, behavior:'smooth'});
    }

    // ── Toggle escalation form ─────────────────────────────────
    function toggleEsc(id) {
        const el = document.getElementById(id);
        el.classList.toggle('open');
        if (el.classList.contains('open'))
            el.scrollIntoView({behavior:'smooth', block:'nearest'});
    }

    // ── Scroll-to-top FAB ─────────────────────────────────────
    window.addEventListener('scroll', () => {
        document.getElementById('fabBtn').style.display =
            window.scrollY > 300 ? 'flex' : 'none';
    });

    // ── Count-up animation for stat numbers ───────────────────
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count) || 0;
        if (!target) return;
        let cur = 0;
        const step = Math.ceil(target / 20);
        const t = setInterval(() => {
            cur = Math.min(cur + step, target);
            el.textContent = cur;
            if (cur >= target) clearInterval(t);
        }, 40);
    });

    // ── Animate performance bars ──────────────────────────────
    window.addEventListener('load', () => {
        document.querySelectorAll('.perf-bar-fill').forEach(bar => {
            const w = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => { bar.style.width = w; }, 500);
        });
    });
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────
# DATA HELPERS
# ─────────────────────────────────────────────────────────────────

def _compute_anc_summary(ashas: list) -> tuple[list, list]:
    """
    For every ASHA under this supervisor, count how many of their
    patients have completed each ANC visit (1-4).
    Also returns a list of patients with missing visits.
    """
    from database import engine
    if not engine:
        return [], []

    from sqlalchemy import text as sqlt
    summary      = []
    missing_anc  = []

    try:
        with engine.connect() as conn:
            for a in ashas:
                # ANC counts per visit number for this ASHA
                rows = conn.execute(sqlt("""
                    SELECT ar.visit_number, COUNT(DISTINCT ar.phone) AS cnt
                    FROM anc_records ar
                    JOIN patients p ON p.phone = ar.phone
                    WHERE p.asha_id = :asha_id
                    GROUP BY ar.visit_number
                """), {"asha_id": a["asha_id"]}).fetchall()

                counts = {r.visit_number: r.cnt for r in rows}
                total_patients = a.get("patient_count", 0)

                summary.append({
                    "asha_name":     a["name"],
                    "village":       a["village"],
                    "total_patients":total_patients,
                    "anc1":          counts.get(1, 0),
                    "anc2":          counts.get(2, 0),
                    "anc3":          counts.get(3, 0),
                    "anc4":          counts.get(4, 0),
                })

                # Patients missing >= 1 ANC visit (week-appropriate)
                patients = conn.execute(sqlt("""
                    SELECT p.phone, p.name, p.week, p.village,
                           ARRAY_AGG(DISTINCT ar.visit_number) AS done_visits
                    FROM patients p
                    LEFT JOIN anc_records ar ON ar.phone = p.phone
                    WHERE p.asha_id = :asha_id AND p.step = 'registered'
                    GROUP BY p.phone, p.name, p.week, p.village
                """), {"asha_id": a["asha_id"]}).fetchall()

                for p in patients:
                    done = set(p.done_visits or [])
                    # Which visits should be done by this week?
                    expected = []
                    if p.week and p.week >= 12: expected.append(1)
                    if p.week and p.week >= 16: expected.append(2)
                    if p.week and p.week >= 32: expected.append(3)
                    if p.week and p.week >= 36: expected.append(4)
                    missing = [v for v in expected if v not in done]
                    if missing:
                        missing_anc.append({
                            "name":          p.name,
                            "phone":         p.phone,
                            "week":          p.week,
                            "village":       p.village or a["village"],
                            "asha_name":     a["name"],
                            "missing_visits":missing
                        })
    except Exception as e:
        print(f"supervisor.py _compute_anc_summary error: {e}")

    return summary, missing_anc


def _get_all_pp_due(ashas: list) -> tuple[list, list]:
    """
    Collect all postpartum patients due for PNC today across
    all ASHA workers under this supervisor.
    Also returns the full list of postpartum patients.
    """
    from database import get_postpartum_patients_due, engine
    from sqlalchemy import text as sqlt

    all_due  = []
    all_pp   = []

    for a in ashas:
        due = get_postpartum_patients_due(a["asha_id"])
        for d in due:
            d["asha_name"]  = a["name"]
            d["asha_id"]    = a["asha_id"]
            d["asha_phone"] = a["phone"]
        all_due.extend(due)

    # Full postpartum list (status = 'postpartum')
    if engine:
        try:
            with engine.connect() as conn:
                rows = conn.execute(sqlt("""
                    SELECT p.name, p.phone, p.village,
                           d.delivery_date, d.birth_weight, d.delivery_mode,
                           d.facility,
                           aw.name AS asha_name
                    FROM patients p
                    JOIN deliveries d ON d.phone = p.phone
                    JOIN asha_workers aw ON aw.asha_id = p.asha_id
                    WHERE p.status = 'postpartum'
                    AND aw.supervisor_id = :sup_id
                    ORDER BY d.delivery_date DESC
                """), {"sup_id": ashas[0].get("supervisor_id") if ashas else ""}).fetchall()
                all_pp = [{
                    "name":          r.name,
                    "phone":         r.phone,
                    "village":       r.village or "",
                    "delivery_date": r.delivery_date or "—",
                    "birth_weight":  r.birth_weight  or "—",
                    "facility":      r.facility      or "—",
                    "asha_name":     r.asha_name      or "—"
                } for r in rows]
        except Exception as e:
            print(f"supervisor.py _get_all_pp_due error: {e}")

    return all_due, all_pp


def _block_perf_summary(performances: list) -> tuple[str, str, str, str]:
    """Compute block-level aggregate metrics from individual perf dicts."""
    if not performances:
        return "—", "—", "—", "—"

    res_rates = [p.get("resolution_rate", 0)  for p in performances]
    resp_hrs  = [p.get("avg_response_hrs")     for p in performances
                 if p.get("avg_response_hrs") is not None]
    esc_counts = [(p.get("escalated_alerts", 0), p.get("name","")) for p in performances]

    block_avg_resolution = (
        f"{round(sum(res_rates)/len(res_rates),1)}%"
        if res_rates else "—"
    )
    block_avg_response   = (
        f"{round(sum(resp_hrs)/len(resp_hrs),1)}"
        if resp_hrs else "—"
    )
    top_escalation_asha  = (
        max(esc_counts, key=lambda x: x[0])[1]
        if esc_counts else "—"
    )
    # Top performer = highest resolution rate & lowest response time
    best = max(performances,
               key=lambda p: (p.get("resolution_rate",0),
                               -(p.get("avg_response_hrs") or 99)),
               default=None)
    top_performer_asha = best["name"] if best else "—"

    return (block_avg_resolution, block_avg_response,
            top_escalation_asha, top_performer_asha)


# ─────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
# Called from app.py: render_supervisor(supervisor_id, supervisor_info)
# ─────────────────────────────────────────────────────────────────

def render_supervisor(supervisor_id: str, supervisor_info: dict) -> str:
    """
    Build and return the full supervisor dashboard HTML.

    supervisor_info — dict returned by verify_supervisor() or unified_login():
        { supervisor_id, name, phone, block_name, district, bmo_id, role }
    """
    from database import (
        get_supervisor_stats,
        get_supervisor_ashas,
        get_supervisor_alerts,
        get_asha_performance,
    )

    stats  = get_supervisor_stats(supervisor_id)
    ashas  = get_supervisor_ashas(supervisor_id)   # list of ASHA dicts with metrics
    alerts = get_supervisor_alerts(supervisor_id)

    # ── Performance data per ASHA (Month 2) ───────────────────────
    performances = []
    for a in ashas:
        perf = get_asha_performance(a["asha_id"], days=30)
        perf["name"]    = a["name"]
        perf["village"] = a["village"]
        perf["asha_id"] = a["asha_id"]
        performances.append(perf)

    # Add supervisor_id to each asha dict for the SQL in _get_all_pp_due
    for a in ashas:
        a["supervisor_id"] = supervisor_id

    # ── ANC summary (Month 3) ─────────────────────────────────────
    anc_summary, missing_anc = _compute_anc_summary(ashas)

    # ── Postpartum data (Month 4) ─────────────────────────────────
    all_pp_due, postpartum_patients = _get_all_pp_due(ashas)
    pp_due_count = len(all_pp_due)

    # ── Block-level perf aggregates ───────────────────────────────
    (block_avg_resolution, block_avg_response,
     top_escalation_asha, top_performer_asha) = _block_perf_summary(performances)

    # ── Enrich alerts with asha_phone for calling ─────────────────
    asha_phone_map = {a["asha_id"]: a["phone"] for a in ashas}
    for alert in alerts:
        alert["asha_phone"] = asha_phone_map.get(alert.get("asha_id",""), "")

    return render_template_string(
        SUPERVISOR_HTML,
        supervisor_id       = supervisor_id,
        supervisor_name     = supervisor_info.get("name",       "Supervisor"),
        block_name          = supervisor_info.get("block_name", ""),
        district            = supervisor_info.get("district",   ""),
        stats               = stats,
        ashas               = ashas,
        alerts              = alerts,
        performances        = performances,
        anc_summary         = anc_summary,
        missing_anc         = missing_anc,
        all_pp_due          = all_pp_due,
        pp_due_count        = pp_due_count,
        postpartum_patients = postpartum_patients,
        block_avg_resolution= block_avg_resolution,
        block_avg_response  = block_avg_response,
        top_escalation_asha = top_escalation_asha,
        top_performer_asha  = top_performer_asha,
    )