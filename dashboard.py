# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Worker Dashboard
# Full 4-Month Feature Set:
#   Month 1 — Visit outcome logging, scheme notifications, Maps
#   Month 2 — Supervisor view, escalation status, performance
#   Month 3 — Analytics tab, ANC records
#   Month 4 — Postpartum tab, child health, immunization, PNC
# ─────────────────────────────────────────────────────────────────

from flask import render_template_string

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <title>MaaSakhi — ASHA Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">

    <style>
        :root {
            --green-deep:   #054235;
            --green-mid:    #0a6b52;
            --green-bright: #10b981;
            --green-pale:   #d1fae5;
            --green-tint:   #f0faf5;
            --amber:        #f59e0b;
            --amber-pale:   #fffbeb;
            --red:          #ef4444;
            --red-pale:     #fef2f2;
            --blue:         #3b82f6;
            --purple:       #8b5cf6;
            --ink:          #111827;
            --muted:        #6b7280;
            --border:       #e5e7eb;
            --white:        #ffffff;
            --bg:           #f0faf5;
            --card-shadow:  0 4px 16px rgba(5,66,53,0.08);
            --radius:       16px;
            --radius-sm:    10px;
        }

        * { margin:0; padding:0; box-sizing:border-box; }

        body {
            font-family: 'DM Sans', sans-serif;
            background: var(--bg);
            color: var(--ink);
            min-height: 100vh;
        }

        /* ═══════════════════════════════════════════════════════
           HEADER
        ═══════════════════════════════════════════════════════ */
        .header {
            background: linear-gradient(135deg, var(--green-deep) 0%, var(--green-mid) 100%);
            color: white;
            padding: 22px 24px 0;
            position: relative;
            overflow: hidden;
        }
        .header-bg-circle {
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.05);
        }
        .header-bg-circle.c1 { width:200px; height:200px; top:-60px; right:-40px; }
        .header-bg-circle.c2 { width:120px; height:120px; bottom:-40px; right:80px; }
        .header-bg-circle.c3 { width:80px; height:80px; top:20px; right:160px; }
        .header-title {
            font-family: 'Syne', sans-serif;
            font-size: 20px;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 10px;
            position: relative;
        }
        .header-sub {
            font-size: 12px;
            opacity: 0.8;
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .live-pulse {
            width: 7px; height: 7px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 1.8s infinite;
            display: inline-block;
        }
        @keyframes pulse {
            0%,100% { opacity:1; transform:scale(1); box-shadow:0 0 0 0 rgba(74,222,128,0.5); }
            50%      { opacity:0.6; transform:scale(1.3); box-shadow:0 0 0 6px rgba(74,222,128,0); }
        }
        .header-meta {
            display: flex;
            gap: 8px;
            margin-top: 14px;
            flex-wrap: wrap;
        }
        .header-pill {
            background: rgba(255,255,255,0.13);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 500;
        }
        .header-pill.danger {
            background: rgba(239,68,68,0.2);
            border-color: rgba(239,68,68,0.35);
        }

        /* ═══════════════════════════════════════════════════════
           TAB NAV
        ═══════════════════════════════════════════════════════ */
        .tab-nav {
            display: flex;
            background: var(--green-deep);
            padding: 0 24px;
            gap: 2px;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .tab-nav::-webkit-scrollbar { display: none; }
        .tab-btn {
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: rgba(255,255,255,0.55);
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .tab-btn:hover { color: rgba(255,255,255,0.85); }
        .tab-btn.active {
            color: white;
            border-bottom-color: #4ade80;
        }
        .tab-badge {
            background: var(--red);
            color: white;
            border-radius: 20px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: 700;
        }

        /* ═══════════════════════════════════════════════════════
           TAB PANELS
        ═══════════════════════════════════════════════════════ */
        .tab-panel { display: none; }
        .tab-panel.active { display: block; animation: fadeUp 0.3s ease; }
        @keyframes fadeUp {
            from { opacity:0; transform:translateY(10px); }
            to   { opacity:1; transform:translateY(0); }
        }
        @keyframes slideIn {
            from { opacity:0; transform:translateX(-10px); }
            to   { opacity:1; transform:translateX(0); }
        }

        /* ═══════════════════════════════════════════════════════
           STATS ROW
        ═══════════════════════════════════════════════════════ */
        .stats-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            padding: 18px 20px 12px;
        }
        @media (max-width: 480px) { .stats-row { grid-template-columns: repeat(2,1fr); } }
        .stat-card {
            background: white;
            border-radius: var(--radius);
            padding: 16px 12px;
            text-align: center;
            border: 1px solid var(--green-pale);
            box-shadow: var(--card-shadow);
            animation: fadeUp 0.4s ease both;
            transition: transform 0.2s;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-icon { font-size: 18px; margin-bottom: 4px; }
        .stat-num  { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 700; line-height:1; }
        .stat-lbl  { font-size: 10px; color: var(--muted); margin-top: 4px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }

        /* ═══════════════════════════════════════════════════════
           SECTION HEADER
        ═══════════════════════════════════════════════════════ */
        .sec-head {
            padding: 6px 20px 10px;
            font-size: 11px;
            font-weight: 700;
            color: var(--green-mid);
            text-transform: uppercase;
            letter-spacing: .08em;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .sec-count {
            background: var(--green-mid);
            color: white;
            border-radius: 20px;
            padding: 1px 9px;
            font-size: 10px;
        }

        /* ═══════════════════════════════════════════════════════
           ALERT CARDS
        ═══════════════════════════════════════════════════════ */
        .alert-card {
            margin: 0 20px 14px;
            background: white;
            border-radius: var(--radius);
            padding: 18px;
            border-left: 4px solid var(--red);
            box-shadow: 0 4px 20px rgba(239,68,68,0.1);
            animation: slideIn 0.4s ease both;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .alert-card:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(239,68,68,0.15); }
        .alert-card.attended { border-left-color: var(--amber); box-shadow: 0 4px 20px rgba(245,158,11,0.1); }
        .alert-card.resolved { border-left-color: var(--green-bright); opacity: 0.72; }

        .alert-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
        .alert-name { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: var(--ink); }
        .alert-line {
            font-size: 12.5px; color: #4b5563; margin-top: 5px;
            display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
        }
        .alert-address {
            font-size: 11.5px; color: var(--muted); margin-top: 4px;
            display: flex; align-items: center; gap: 4px;
        }
        .alert-time { font-size: 11px; color: #9ca3af; margin-top: 5px; }

        /* ═══════════════════════════════════════════════════════
           BADGES
        ═══════════════════════════════════════════════════════ */
        .badge {
            display: inline-block;
            padding: 3px 11px;
            border-radius: 20px;
            font-size: 10.5px;
            font-weight: 600;
            white-space: nowrap;
        }
        .badge-red    { background: var(--red-pale);   color: #dc2626; border: 1px solid #fecaca; }
        .badge-amber  { background: var(--amber-pale);  color: #b45309; border: 1px solid #fde68a; }
        .badge-green  { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
        .badge-blue   { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .badge-purple { background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; }
        .badge-escl   { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; font-size: 10px; }

        /* ═══════════════════════════════════════════════════════
           STATUS FLOW
        ═══════════════════════════════════════════════════════ */
        .status-flow {
            display: flex; align-items: center; gap: 4px;
            margin-top: 12px; flex-wrap: wrap;
        }
        .step-node {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 10.5px;
            font-weight: 600;
            transition: 0.2s;
        }
        .step-done    { background: var(--green-deep); color: white; }
        .step-pending { background: #f3f4f6; color: #9ca3af; border: 1px solid var(--border); }
        .step-arr     { color: #d1d5db; font-size: 11px; }

        /* ═══════════════════════════════════════════════════════
           BUTTONS
        ═══════════════════════════════════════════════════════ */
        .btn-row { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: var(--radius-sm);
            font-size: 11.5px;
            font-weight: 600;
            cursor: pointer;
            font-family: 'DM Sans', sans-serif;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .btn:hover { transform: translateY(-1px); filter: brightness(1.08); }
        .btn-attend { background: var(--amber);        color: white; }
        .btn-maps   { background: var(--blue);         color: white; }
        .btn-call   { background: var(--purple);       color: white; }
        .btn-visit  { background: var(--green-bright); color: white; }
        .btn-dark   { background: var(--green-deep);   color: white; }
        .btn-ghost  { background: #f3f4f6; color: var(--ink); border: 1px solid var(--border); }

        /* ═══════════════════════════════════════════════════════
           VISIT LOG FORM (Month 1)
        ═══════════════════════════════════════════════════════ */
        .visit-form {
            background: #f8fffe;
            border: 1.5px solid var(--green-pale);
            border-radius: var(--radius-sm);
            padding: 16px;
            margin-top: 12px;
            display: none;
        }
        .visit-form.open { display: block; animation: fadeUp 0.3s ease; }
        .form-label {
            font-size: 11.5px; font-weight: 600;
            color: var(--green-deep); display: block; margin-bottom: 5px;
        }
        .form-ctrl {
            width: 100%;
            padding: 9px 12px;
            border: 1.5px solid var(--green-pale);
            border-radius: 8px;
            font-family: 'DM Sans', sans-serif;
            font-size: 12px;
            margin-bottom: 10px;
            background: white;
            color: var(--ink);
            transition: border-color 0.2s;
        }
        .form-ctrl:focus { outline: none; border-color: var(--green-mid); }

        /* ═══════════════════════════════════════════════════════
           PATIENT ROWS
        ═══════════════════════════════════════════════════════ */
        .patient-row {
            background: white;
            border-radius: var(--radius);
            padding: 14px 18px;
            margin: 0 20px 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--green-pale);
            box-shadow: var(--card-shadow);
            animation: fadeUp 0.4s ease both;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .patient-row:hover {
            transform: translateX(4px);
            box-shadow: 0 4px 20px rgba(8,80,65,0.1);
        }
        .patient-name   { font-family: 'Syne', sans-serif; font-size: 13.5px; font-weight: 700; color: var(--ink); }
        .patient-detail { font-size: 11.5px; color: var(--muted); margin-top: 3px; }
        .risk-bar {
            height: 4px; background: #f3f4f6;
            border-radius: 2px; margin-top: 8px; overflow: hidden; width: 100px;
        }
        .risk-fill {
            height: 100%; border-radius: 2px; transition: width 1.2s ease;
        }

        /* ═══════════════════════════════════════════════════════
           SCHEME CARDS (Month 1)
        ═══════════════════════════════════════════════════════ */
        .scheme-card {
            background: white;
            border-radius: var(--radius);
            padding: 16px 18px;
            margin: 0 20px 12px;
            border-left: 4px solid var(--blue);
            box-shadow: var(--card-shadow);
            animation: fadeUp 0.4s ease both;
        }
        .scheme-name { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: var(--ink); }
        .scheme-amount {
            display: inline-block;
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
            border-radius: 20px;
            padding: 2px 12px;
            font-size: 11px;
            font-weight: 700;
            margin-top: 6px;
        }
        .scheme-desc { font-size: 12px; color: var(--muted); margin-top: 6px; line-height: 1.6; }
        .scheme-eligibility {
            font-size: 11px; color: #4b5563;
            background: #f8fffe;
            border: 1px solid var(--green-pale);
            border-radius: 8px;
            padding: 8px 12px;
            margin-top: 10px;
            line-height: 1.7;
        }

        /* ═══════════════════════════════════════════════════════
           ANC RECORDS (Month 3)
        ═══════════════════════════════════════════════════════ */
        .anc-timeline {
            margin: 0 20px 16px;
            background: white;
            border-radius: var(--radius);
            padding: 18px;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--green-pale);
        }
        .anc-title { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; margin-bottom: 14px; }
        .anc-steps {
            display: flex;
            gap: 0;
            position: relative;
        }
        .anc-steps::before {
            content: '';
            position: absolute;
            top: 14px; left: 14px; right: 14px;
            height: 2px; background: #e5e7eb; z-index: 0;
        }
        .anc-step {
            flex: 1; text-align: center; position: relative; z-index: 1;
        }
        .anc-dot {
            width: 28px; height: 28px;
            border-radius: 50%;
            margin: 0 auto 6px;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; font-weight: 700;
        }
        .anc-dot.done  { background: var(--green-mid); color: white; }
        .anc-dot.next  { background: var(--amber); color: white; }
        .anc-dot.future{ background: #f3f4f6; color: #9ca3af; border: 2px solid var(--border); }
        .anc-label { font-size: 9px; color: var(--muted); font-weight: 600; }

        /* ═══════════════════════════════════════════════════════
           PERFORMANCE (Month 2)
        ═══════════════════════════════════════════════════════ */
        .perf-card {
            background: white;
            border-radius: var(--radius);
            padding: 18px;
            margin: 0 20px 14px;
            box-shadow: var(--card-shadow);
            border: 1px solid var(--green-pale);
        }
        .perf-title { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; margin-bottom: 14px; }
        .perf-grid { display: grid; grid-template-columns: repeat(2,1fr); gap: 12px; }
        .perf-metric {
            background: var(--bg);
            border-radius: 12px;
            padding: 14px;
            text-align: center;
        }
        .perf-num { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; }
        .perf-lbl { font-size: 10px; color: var(--muted); margin-top: 3px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
        .perf-rating {
            display: flex; align-items: center; justify-content: center;
            gap: 8px; margin-top: 16px;
            padding: 12px;
            border-radius: 10px;
            font-size: 13px; font-weight: 600;
        }
        .rating-GREEN  { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
        .rating-AMBER  { background: var(--amber-pale); color: #92400e; border: 1px solid #fde68a; }
        .rating-RED    { background: var(--red-pale); color: #991b1b; border: 1px solid #fecaca; }
        .rating-unknown{ background: #f9fafb; color: var(--muted); border: 1px solid var(--border); }

        /* ═══════════════════════════════════════════════════════
           POSTPARTUM TAB (Month 4)
        ═══════════════════════════════════════════════════════ */
        .pp-card {
            background: white;
            border-radius: var(--radius);
            padding: 18px;
            margin: 0 20px 14px;
            border-left: 4px solid var(--purple);
            box-shadow: var(--card-shadow);
            animation: slideIn 0.4s ease both;
        }
        .pp-name { font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; }
        .pp-delivery { font-size: 12px; color: var(--muted); margin-top: 4px; }
        .pp-days-badge {
            display: inline-block;
            background: #f5f3ff; color: #6d28d9;
            border: 1px solid #ddd6fe;
            border-radius: 20px; padding: 3px 12px;
            font-size: 11px; font-weight: 700; margin-top: 6px;
        }
        .pnc-schedule {
            display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap;
        }
        .pnc-day {
            padding: 5px 12px; border-radius: 20px;
            font-size: 11px; font-weight: 600;
        }
        .pnc-done   { background: var(--green-mid); color: white; }
        .pnc-today  { background: var(--amber); color: white; animation: bounce 1s infinite; }
        .pnc-future { background: #f3f4f6; color: #9ca3af; border: 1px solid var(--border); }
        @keyframes bounce {
            0%,100% { transform: translateY(0); }
            50%      { transform: translateY(-3px); }
        }

        /* ═══════════════════════════════════════════════════════
           CHILD HEALTH CARDS (Month 4)
        ═══════════════════════════════════════════════════════ */
        .child-card {
            background: white;
            border-radius: var(--radius);
            padding: 16px 18px;
            margin: 0 20px 12px;
            box-shadow: var(--card-shadow);
            border: 1px solid #ede9fe;
        }
        .child-name { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; }
        .child-age  { font-size: 11.5px; color: var(--muted); margin-top: 3px; }
        .immuno-row {
            display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;
        }
        .immuno-pill {
            padding: 4px 11px; border-radius: 20px;
            font-size: 10.5px; font-weight: 600;
        }
        .immuno-done { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
        .immuno-due  { background: var(--amber-pale); color: #92400e; border: 1px solid #fde68a; }
        .immuno-miss { background: var(--red-pale); color: #991b1b; border: 1px solid #fecaca; }

        /* Growth mini chart */
        .growth-bar-row { display: flex; align-items: flex-end; gap: 4px; height: 40px; margin-top: 10px; }
        .growth-bar-col { display: flex; flex-direction: column; align-items: center; flex: 1; }
        .growth-bar-fill {
            width: 100%; border-radius: 3px 3px 0 0;
            background: var(--green-mid);
            transition: height 1s ease;
            min-height: 4px;
        }
        .growth-bar-lbl { font-size: 8px; color: var(--muted); margin-top: 3px; }

        /* ═══════════════════════════════════════════════════════
           DANGER SIGNS ALERT (Month 4)
        ═══════════════════════════════════════════════════════ */
        .danger-banner {
            margin: 0 20px 12px;
            background: var(--red-pale);
            border: 1.5px solid #fecaca;
            border-radius: var(--radius-sm);
            padding: 12px 16px;
            display: flex; align-items: flex-start; gap: 10px;
            animation: fadeUp 0.3s ease;
        }
        .danger-icon { font-size: 20px; flex-shrink: 0; }
        .danger-text { font-size: 12px; color: #991b1b; font-weight: 500; line-height: 1.6; }

        /* ═══════════════════════════════════════════════════════
           EMPTY STATE
        ═══════════════════════════════════════════════════════ */
        .empty {
            text-align: center; padding: 40px 20px;
            color: #9ca3af; font-size: 13px;
        }
        .empty-icon { font-size: 36px; margin-bottom: 10px; }

        /* ═══════════════════════════════════════════════════════
           RECOVERY MSG
        ═══════════════════════════════════════════════════════ */
        .recovery-msg {
            margin-top: 10px; padding: 8px 14px;
            border-radius: 8px; font-size: 11.5px; font-weight: 500;
        }
        .recovery-waiting { background: var(--amber-pale); color: #92400e; border: 1px solid #fde68a; }
        .recovery-done    { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }

        /* ═══════════════════════════════════════════════════════
           FOOTER
        ═══════════════════════════════════════════════════════ */
        .footer {
            text-align: center;
            font-size: 11px;
            color: #9ca3af;
            padding: 24px 20px;
            margin-top: 8px;
            border-top: 1px solid var(--border);
        }
        .footer a { color: var(--green-mid); text-decoration: none; }

        /* ═══════════════════════════════════════════════════════
           FAB SCROLL-TO-TOP
        ═══════════════════════════════════════════════════════ */
        .fab {
            position: fixed; bottom: 24px; right: 24px;
            background: var(--green-deep); color: white;
            border: none; border-radius: 50%;
            width: 44px; height: 44px;
            font-size: 18px; cursor: pointer;
            box-shadow: 0 4px 16px rgba(5,66,53,0.35);
            display: none; align-items: center; justify-content: center;
            transition: 0.2s; z-index: 100;
        }
        .fab:hover { background: var(--green-mid); transform: scale(1.1); }

        /* ═══════════════════════════════════════════════════════
           STAT ANIMATIONS
        ═══════════════════════════════════════════════════════ */
        .stat-card:nth-child(1){ animation-delay:.05s; }
        .stat-card:nth-child(2){ animation-delay:.10s; }
        .stat-card:nth-child(3){ animation-delay:.15s; }
        .stat-card:nth-child(4){ animation-delay:.20s; }
    </style>
</head>
<body>

<!-- ════════════════════════════════════════════════════════════
     HEADER
═════════════════════════════════════════════════════════════ -->
<div class="header">
    <div class="header-bg-circle c1"></div>
    <div class="header-bg-circle c2"></div>
    <div class="header-bg-circle c3"></div>
    <div class="header-title">🌿 MaaSakhi — ASHA Dashboard</div>
    <div class="header-sub">
        <span class="live-pulse"></span>
        Live &nbsp;•&nbsp; Auto-refreshes every 30 s
    </div>
    <div class="header-meta">
        <span class="header-pill">👩 {{ asha_name }}</span>
        <span class="header-pill">📍 {{ asha_village }}</span>
        <span class="header-pill">👥 {{ total }} Patients</span>
        <span class="header-pill">📊 {{ total_reports }} Reports</span>
        {% if high_risk > 0 %}
        <span class="header-pill danger">🚨 {{ high_risk }} Alerts</span>
        {% endif %}
    </div>
</div>

<!-- ════════════════════════════════════════════════════════════
     TAB NAV
═════════════════════════════════════════════════════════════ -->
<div class="tab-nav" role="tablist">
    <button class="tab-btn active" onclick="showTab('alerts')" role="tab">
        🚨 Alerts
        {% if high_risk > 0 %}
        <span class="tab-badge">{{ high_risk }}</span>
        {% endif %}
    </button>
    <button class="tab-btn" onclick="showTab('patients')" role="tab">
        👩 Patients
    </button>
    <button class="tab-btn" onclick="showTab('postpartum')" role="tab">
        👶 Postpartum
        {% if pp_due_count > 0 %}
        <span class="tab-badge">{{ pp_due_count }}</span>
        {% endif %}
    </button>
    <button class="tab-btn" onclick="showTab('schemes')" role="tab">
        🏛️ Schemes
    </button>
    <button class="tab-btn" onclick="showTab('performance')" role="tab">
        📊 My Stats
    </button>
</div>

<!-- ════════════════════════════════════════════════════════════
     STATS ROW (always visible)
═════════════════════════════════════════════════════════════ -->
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-icon">🚨</div>
        <div class="stat-num" style="color:var(--red)" data-count="{{ high_risk }}">{{ high_risk }}</div>
        <div class="stat-lbl">Active Alerts</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">👩</div>
        <div class="stat-num" style="color:var(--green-mid)" data-count="{{ total }}">{{ total }}</div>
        <div class="stat-lbl">Registered</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-num" style="color:var(--green-bright)" data-count="{{ safe }}">{{ safe }}</div>
        <div class="stat-lbl">Safe</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">👶</div>
        <div class="stat-num" style="color:var(--purple)" data-count="{{ pp_due_count }}">{{ pp_due_count }}</div>
        <div class="stat-lbl">PNC Due</div>
    </div>
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 1: ALERTS
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel active" id="tab-alerts">

    <p class="sec-head">
        ⚠️ High Risk Alerts
        <span class="sec-count">{{ alerts|length }}</span>
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
                    <span class="badge badge-escl">⬆ Escalated — Level {{ a.get('level',0) }}</span>
                    {% endif %}
                </div>
                <span class="badge
                    {% if a.status=='Pending'  %}badge-red
                    {% elif a.status=='Attended' %}badge-amber
                    {% else %}badge-green{% endif %}">
                    {% if a.status=='Pending' %}🔴
                    {% elif a.status=='Attended' %}🟡
                    {% else %}🟢{% endif %}
                    {{ a.status }}
                </span>
            </div>

            <div class="alert-line">
                🤰 Week {{ a.week }} &nbsp;•&nbsp; ⚠️ {{ a.symptom[:80] }}{% if a.symptom|length > 80 %}…{% endif %}
            </div>
            <div class="alert-line">📞 {{ a.phone }}</div>

            {% if a.get('address') or a.get('village') %}
            <div class="alert-address">
                📍 {% if a.get('address') %}{{ a.address }}{% endif %}
                {% if a.get('village') %} · {{ a.village }}{% endif %}
            </div>
            {% endif %}

            <div class="alert-time">🕐 {{ a.time }}</div>

            <!-- Status flow -->
            <div class="status-flow">
                <span class="step-node step-done">Alerted</span>
                <span class="step-arr">→</span>
                <span class="step-node {% if a.status in ['Attended','Resolved'] %}step-done{% else %}step-pending{% endif %}">
                    Attended
                </span>
                <span class="step-arr">→</span>
                <span class="step-node {% if a.status in ['Attended','Resolved'] %}step-done{% else %}step-pending{% endif %}">
                    Visit Logged
                </span>
                <span class="step-arr">→</span>
                <span class="step-node {% if a.status == 'Resolved' %}step-done{% else %}step-pending{% endif %}">
                    Resolved
                </span>
            </div>

            <!-- Action buttons -->
            <div class="btn-row">
                {% if a.get('maps_link') %}
                <a href="{{ a.maps_link }}" target="_blank" class="btn btn-maps">📌 Navigate</a>
                {% endif %}
                <a href="tel:{{ a.phone }}" class="btn btn-call">📞 Call</a>

                {% if a.status == 'Pending' %}
                <form method="POST" action="/dashboard/{{ asha_id }}/attend/{{ a.id }}" style="display:inline">
                    <button type="submit" class="btn btn-attend">✅ Mark Attended</button>
                </form>
                {% endif %}

                {% if a.status == 'Attended' %}
                <button class="btn btn-visit" onclick="toggleForm('visit-{{ a.id }}')">
                    📋 Log Visit Outcome
                </button>
                {% endif %}
            </div>

            <!-- Recovery status -->
            {% if a.status == 'Attended' %}
            <div class="recovery-msg recovery-waiting">
                ⏳ Waiting for patient to confirm recovery on WhatsApp...
            </div>
            {% elif a.status == 'Resolved' %}
            <div class="recovery-msg recovery-done">
                ✅ Patient confirmed recovery — case closed.
                {% if a.get('resolved_notes') %}
                <br><span style="font-weight:400">{{ a.resolved_notes }}</span>
                {% endif %}
            </div>
            {% endif %}

            <!-- ── VISIT LOG FORM (Month 1) ──────────────────── -->
            {% if a.status == 'Attended' %}
            <div class="visit-form" id="visit-{{ a.id }}">
                <form method="POST" action="/dashboard/{{ asha_id }}/log-visit/{{ a.id }}">

                    <label class="form-label">📋 Visit Outcome *</label>
                    <select name="outcome" class="form-ctrl" required>
                        <option value="">-- Select outcome --</option>
                        <option value="stable">🟢 Patient stable — monitoring at home</option>
                        <option value="referred_phc">🏥 Referred to PHC / CHC</option>
                        <option value="referred_hospital">🏨 Referred to District Hospital</option>
                        <option value="called_108">🚑 Emergency — called 108 ambulance</option>
                        <option value="not_found">❌ Patient not found at address</option>
                    </select>

                    <label class="form-label">📍 Referred to (if applicable)</label>
                    <input name="referred_to" class="form-ctrl"
                           placeholder="e.g. PHC Rampur, District Hospital Jaipur" type="text">

                    <label class="form-label">📝 Notes (optional)</label>
                    <textarea name="notes" class="form-ctrl" rows="2"
                              placeholder="Any observations about patient condition..."></textarea>

                    <button type="submit" class="btn btn-dark">💾 Save Visit Record</button>
                </form>
            </div>
            {% endif %}

        </div>
        {% endfor %}

    {% else %}
        <div class="empty">
            <div class="empty-icon">✅</div>
            <div>No active alerts right now</div>
            <div style="font-size:11px;margin-top:5px;color:#d1d5db">All your patients are safe</div>
        </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 2: PATIENTS
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-patients">
    <p class="sec-head">
        👩 Registered Patients
        <span class="sec-count">{{ total }}</span>
    </p>

    {% if patients %}
        {% for phone, p in patients.items() %}
        {% if p.step == 'registered' %}
        {% set risk = patient_risks.get(phone, {}) %}
        {% set rl = risk.get('level', 'LOW') %}
        {% set rs = risk.get('score', 0) %}

        <div class="patient-row">
            <div style="flex:1">
                <div class="patient-name">{{ p.name }}</div>
                <div class="patient-detail">
                    🤰 Week {{ p.week }}
                    {% if p.get('village') %} · 📍 {{ p.village }}{% endif %}
                    {% if p.get('status') == 'postpartum' %} · <span style="color:var(--purple);font-weight:600">Postpartum</span>{% endif %}
                </div>
                {% if p.get('address') %}
                <div class="patient-detail" style="font-size:11px">🏠 {{ p.address }}</div>
                {% endif %}
                <!-- ANC progress -->
                {% set anc = anc_data.get(phone, []) %}
                <div class="patient-detail" style="margin-top:5px">
                    ANC: {{ anc|length }}/4 visits
                </div>
                <div class="risk-bar">
                    <div class="risk-fill" style="
                        width:{% if rl=='HIGH' %}85%{% elif rl=='MODERATE' %}52%{% else %}18%{% endif %};
                        background:{% if rl=='HIGH' %}var(--red){% elif rl=='MODERATE' %}var(--amber){% else %}var(--green-bright){% endif %}">
                    </div>
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;margin-left:12px">
                <span class="badge
                    {% if rl=='HIGH' %}badge-red
                    {% elif rl=='MODERATE' %}badge-amber
                    {% else %}badge-green{% endif %}">
                    {{ rl }}
                </span>
                <div style="font-size:10px;color:#9ca3af;margin-top:4px">{{ rs }}/100</div>
                <a href="tel:{{ phone }}" class="btn btn-call" style="margin-top:8px;padding:5px 10px;font-size:10px">📞</a>
            </div>
        </div>
        {% endif %}
        {% endfor %}
    {% else %}
        <div class="empty">
            <div class="empty-icon">👩</div>
            <div>No patients registered yet</div>
            <div style="font-size:11px;margin-top:5px;color:#d1d5db">Share the WhatsApp number in your village</div>
        </div>
    {% endif %}


    <!-- ANC Visit Quick Log -->
    <p class="sec-head" style="margin-top:14px">📋 Log ANC Visit</p>
    <div style="margin:0 20px 16px">
        <div style="background:white;border-radius:var(--radius);padding:18px;box-shadow:var(--card-shadow);border:1px solid var(--green-pale)">
            <form method="POST" action="/dashboard/{{ asha_id }}/log-anc">
                <label class="form-label">Patient Phone</label>
                <select name="patient_phone" class="form-ctrl">
                    <option value="">-- Select patient --</option>
                    {% for phone, p in patients.items() %}
                    {% if p.step == 'registered' %}
                    <option value="{{ phone }}">{{ p.name }} (Wk {{ p.week }})</option>
                    {% endif %}
                    {% endfor %}
                </select>
                <label class="form-label">ANC Visit Number</label>
                <select name="visit_number" class="form-ctrl">
                    <option value="1">ANC 1 (Before 12 weeks)</option>
                    <option value="2">ANC 2 (14–16 weeks)</option>
                    <option value="3">ANC 3 (28–32 weeks)</option>
                    <option value="4">ANC 4 (36 weeks)</option>
                </select>
                <label class="form-label">Visit Date</label>
                <input name="visit_date" type="date" class="form-ctrl">
                <label class="form-label">Notes</label>
                <input name="notes" type="text" class="form-ctrl" placeholder="Any observations...">
                <button type="submit" class="btn btn-dark">💾 Save ANC Record</button>
            </form>
        </div>
    </div>
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 3: POSTPARTUM + CHILD HEALTH (Month 4)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-postpartum">

    <!-- Newborn danger signs banner -->
    <div class="danger-banner">
        <div class="danger-icon">⚠️</div>
        <div class="danger-text">
            <strong>Newborn Danger Signs to watch:</strong><br>
            Not feeding • Jaundice beyond 3 days • Hypothermia (cold to touch) •
            Fast/slow breathing • Lethargy • Umbilical redness or pus
        </div>
    </div>

    <p class="sec-head">
        🤱 PNC Check-in Due Today
        <span class="sec-count">{{ pp_due_count }}</span>
    </p>

    {% if pp_due_patients %}
        {% for pp in pp_due_patients %}
        <div class="pp-card">
            <div class="pp-name">{{ pp.name }}</div>
            <div class="pp-delivery">
                📅 Delivered: {{ pp.delivery_date }}
                {% if pp.get('birth_weight') %} · Baby: {{ pp.birth_weight }} kg{% endif %}
            </div>
            <span class="pp-days-badge">Day {{ pp.days_since }} PNC Visit Due</span>

            <!-- PNC schedule -->
            <div class="pnc-schedule">
                {% for day in [1,3,7,14,42] %}
                <span class="pnc-day
                    {% if pp.days_since > day %}pnc-done
                    {% elif pp.days_since == day %}pnc-today
                    {% else %}pnc-future{% endif %}">
                    Day {{ day }}
                </span>
                {% endfor %}
            </div>

            <div class="btn-row">
                <a href="tel:{{ pp.phone }}" class="btn btn-call">📞 Call</a>
                <form method="POST" action="/dashboard/{{ asha_id }}/log-pnc/{{ pp.phone }}" style="display:inline">
                    <button type="submit" class="btn btn-dark">✅ Mark PNC Done</button>
                </form>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty">
            <div class="empty-icon">🤱</div>
            <div>No PNC visits due today</div>
        </div>
    {% endif %}


    <!-- Register Delivery -->
    <p class="sec-head" style="margin-top:14px">🍼 Register New Delivery</p>
    <div style="margin:0 20px 16px">
        <div style="background:white;border-radius:var(--radius);padding:18px;box-shadow:var(--card-shadow);border:1px solid #ede9fe">
            <form method="POST" action="/dashboard/{{ asha_id }}/register-delivery">
                <label class="form-label">Patient</label>
                <select name="patient_phone" class="form-ctrl">
                    <option value="">-- Select patient --</option>
                    {% for phone, p in patients.items() %}
                    {% if p.step == 'registered' and p.get('status') != 'postpartum' %}
                    <option value="{{ phone }}">{{ p.name }} (Wk {{ p.week }})</option>
                    {% endif %}
                    {% endfor %}
                </select>
                <label class="form-label">Delivery Date</label>
                <input name="delivery_date" type="date" class="form-ctrl" required>
                <label class="form-label">Birth Weight (kg)</label>
                <input name="birth_weight" type="text" class="form-ctrl" placeholder="e.g. 2.9">
                <label class="form-label">Mode of Delivery</label>
                <select name="delivery_mode" class="form-ctrl">
                    <option value="normal">Normal / Vaginal</option>
                    <option value="cesarean">Caesarean (C-Section)</option>
                    <option value="instrumental">Instrumental (Forceps/Vacuum)</option>
                </select>
                <label class="form-label">Facility</label>
                <input name="facility" type="text" class="form-ctrl" placeholder="e.g. PHC Rampur, Home delivery">
                <button type="submit" class="btn btn-dark">💾 Register Delivery</button>
            </form>
        </div>
    </div>


    <!-- Children cards -->
    {% if children_data %}
    <p class="sec-head" style="margin-top:14px">👶 Child Health Records</p>
    {% for child in children_data %}
    <div class="child-card">
        <div class="child-name">{{ child.child_name }}</div>
        <div class="child-age">
            📅 DOB: {{ child.dob }} · {{ child.gender }}
            {% if child.get('birth_weight') %} · Birth weight: {{ child.birth_weight }} kg{% endif %}
        </div>

        <!-- Immunization status -->
        {% set imm = child.get('immunizations', []) %}
        {% if imm %}
        <div class="immuno-row">
            {% for v in imm %}
            <span class="immuno-pill immuno-done">✓ {{ v.vaccine_name }}</span>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Due vaccines -->
        {% if child.get('due_vaccines') %}
        <div class="immuno-row" style="margin-top:6px">
            {% for v in child.due_vaccines %}
            <span class="immuno-pill immuno-due">⏰ {{ v }} due</span>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Growth mini chart -->
        {% set growth = child.get('growth_logs', []) %}
        {% if growth %}
        <div style="font-size:10px;color:var(--muted);margin-top:10px;font-weight:600">WEIGHT TREND</div>
        <div class="growth-bar-row">
            {% for g in growth[-6:] %}
            {% set h = ((g.weight_kg / 10) * 40)|int %}
            <div class="growth-bar-col">
                <div class="growth-bar-fill" style="height:{{ [h,4]|max }}px"></div>
                <div class="growth-bar-lbl">{{ g.age_months }}m</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="btn-row">
            <button class="btn btn-ghost" onclick="toggleForm('growth-{{ child.id }}')">📏 Log Growth</button>
            <button class="btn btn-ghost" onclick="toggleForm('imm-{{ child.id }}')">💉 Log Vaccine</button>
        </div>

        <!-- Growth log form -->
        <div class="visit-form" id="growth-{{ child.id }}">
            <form method="POST" action="/dashboard/{{ asha_id }}/log-growth/{{ child.id }}">
                <input name="mother_phone" type="hidden" value="{{ child.mother_phone }}">
                <label class="form-label">Weight (kg)</label>
                <input name="weight_kg" type="number" step="0.01" class="form-ctrl" placeholder="e.g. 3.2">
                <label class="form-label">Height (cm)</label>
                <input name="height_cm" type="number" step="0.1" class="form-ctrl" placeholder="e.g. 52.5">
                <label class="form-label">Age (months)</label>
                <input name="age_months" type="number" class="form-ctrl" placeholder="e.g. 3">
                <button type="submit" class="btn btn-dark">💾 Save Growth</button>
            </form>
        </div>

        <!-- Immunization log form -->
        <div class="visit-form" id="imm-{{ child.id }}">
            <form method="POST" action="/dashboard/{{ asha_id }}/log-vaccine/{{ child.id }}">
                <input name="mother_phone" type="hidden" value="{{ child.mother_phone }}">
                <label class="form-label">Vaccine</label>
                <select name="vaccine_name" class="form-ctrl">
                    <option value="BCG">BCG (Birth)</option>
                    <option value="OPV-0">OPV-0 (Birth)</option>
                    <option value="Hepatitis B-1">Hepatitis B (Birth)</option>
                    <option value="OPV-1">OPV-1 (6 weeks)</option>
                    <option value="Pentavalent-1">Pentavalent-1 (6 weeks)</option>
                    <option value="OPV-2">OPV-2 (10 weeks)</option>
                    <option value="Pentavalent-2">Pentavalent-2 (10 weeks)</option>
                    <option value="OPV-3">OPV-3 (14 weeks)</option>
                    <option value="Pentavalent-3">Pentavalent-3 (14 weeks)</option>
                    <option value="IPV">IPV (14 weeks)</option>
                    <option value="Measles-Rubella-1">MR-1 (9 months)</option>
                    <option value="JE-1">JE-1 (9 months)</option>
                    <option value="Measles-Rubella-2">MR-2 (16 months)</option>
                    <option value="DPT-Booster">DPT Booster (16–24 months)</option>
                    <option value="Vitamin-A">Vitamin A</option>
                </select>
                <label class="form-label">Date Given</label>
                <input name="given_date" type="date" class="form-ctrl">
                <label class="form-label">Given By</label>
                <input name="given_by" type="text" class="form-ctrl" placeholder="ANM name / facility">
                <button type="submit" class="btn btn-dark">💉 Save Vaccine</button>
            </form>
        </div>
    </div>
    {% endfor %}
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 4: GOVT SCHEMES (Month 1)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-schemes">

    <p class="sec-head">🏛️ Government Schemes for Mothers</p>

    {% for scheme in schemes %}
    <div class="scheme-card">
        <div class="scheme-name">{{ scheme.name }}</div>
        <span class="scheme-amount">{{ scheme.amount }}</span>
        <div class="scheme-desc">{{ scheme.description }}</div>
        <div class="scheme-eligibility">
            <strong>✅ Eligibility:</strong> {{ scheme.eligibility }}<br>
            <strong>📝 How to apply:</strong> {{ scheme.how_to_apply }}
        </div>
        <!-- Mark delivered button -->
        <div style="margin-top:12px">
            <button class="btn btn-ghost" onclick="toggleForm('scheme-{{ loop.index }}')">
                ✅ Mark as Delivered to Patient
            </button>
        </div>
        <div class="visit-form" id="scheme-{{ loop.index }}">
            <form method="POST" action="/dashboard/{{ asha_id }}/log-scheme">
                <input name="scheme_name" type="hidden" value="{{ scheme.name }}">
                <input name="amount" type="hidden" value="{{ scheme.amount }}">
                <label class="form-label">Select Patient</label>
                <select name="patient_phone" class="form-ctrl">
                    <option value="">-- Select patient --</option>
                    {% for phone, p in patients.items() %}
                    {% if p.step == 'registered' %}
                    <option value="{{ phone }}">{{ p.name }}</option>
                    {% endif %}
                    {% endfor %}
                </select>
                <button type="submit" class="btn btn-dark">💾 Save Record</button>
            </form>
        </div>
    </div>
    {% endfor %}
</div>


<!-- ════════════════════════════════════════════════════════════
     TAB 5: MY PERFORMANCE (Month 2)
═════════════════════════════════════════════════════════════ -->
<div class="tab-panel" id="tab-performance">
    <p class="sec-head">📊 My Performance — Last 30 Days</p>

    {% if performance %}
    <div class="perf-card">
        <div class="perf-title">📈 Key Metrics</div>
        <div class="perf-grid">
            <div class="perf-metric">
                <div class="perf-num" style="color:var(--green-mid)">
                    {{ performance.get('visit_count', 0) }}
                </div>
                <div class="perf-lbl">Visits Done</div>
            </div>
            <div class="perf-metric">
                <div class="perf-num" style="color:var(--green-bright)">
                    {{ performance.get('resolution_rate', 0) }}%
                </div>
                <div class="perf-lbl">Resolution Rate</div>
            </div>
            <div class="perf-metric">
                <div class="perf-num" style="color:var(--amber)">
                    {% if performance.get('avg_response_hrs') %}
                    {{ performance.avg_response_hrs }}h
                    {% else %}—{% endif %}
                </div>
                <div class="perf-lbl">Avg Response</div>
            </div>
            <div class="perf-metric">
                <div class="perf-num" style="color:var(--red)">
                    {{ performance.get('escalation_rate', 0) }}%
                </div>
                <div class="perf-lbl">Escalation Rate</div>
            </div>
        </div>

        {% set rating = performance.get('performance_rating', 'unknown') %}
        <div class="perf-rating rating-{{ rating }}">
            {% if rating == 'GREEN' %}🌟 Excellent performance — keep it up!
            {% elif rating == 'AMBER' %}⚠️ Good — reduce response time to improve
            {% elif rating == 'RED' %}🔴 Needs improvement — respond faster to alerts
            {% else %}📊 Not enough data yet{% endif %}
        </div>
    </div>

    <!-- Recent visits -->
    {% if recent_visits %}
    <p class="sec-head">📋 Recent Visit Records</p>
    {% for v in recent_visits %}
    <div class="patient-row" style="animation-delay:{{ loop.index * 0.05 }}s">
        <div style="flex:1">
            <div class="patient-name">{{ v.patient_name }}</div>
            <div class="patient-detail">
                🕐 {{ v.visit_time }} &nbsp;•&nbsp;
                <span class="badge
                    {% if v.outcome=='stable' %}badge-green
                    {% elif 'referred' in v.outcome %}badge-amber
                    {% elif 'called_108' in v.outcome %}badge-red
                    {% else %}badge-blue{% endif %}">
                    {{ v.outcome|replace('_',' ')|title }}
                </span>
            </div>
            {% if v.get('notes') %}
            <div class="patient-detail" style="font-size:11px;margin-top:3px;font-style:italic">{{ v.notes }}</div>
            {% endif %}
        </div>
    </div>
    {% endfor %}
    {% endif %}

    {% else %}
    <div class="empty">
        <div class="empty-icon">📊</div>
        <div>No performance data yet</div>
        <div style="font-size:11px;margin-top:5px;color:#d1d5db">Start logging visit outcomes to see stats</div>
    </div>
    {% endif %}
</div>


<!-- ════════════════════════════════════════════════════════════
     BACK + FOOTER
═════════════════════════════════════════════════════════════ -->
<div style="padding:20px 20px 8px">
    <a href="/" class="btn btn-dark">← Back to Home</a>
</div>

<div class="footer">
    🌿 MaaSakhi &nbsp;•&nbsp; WHO + NHM + FOGSI Guidelines &nbsp;•&nbsp;
    <a href="/login">Logout</a>
</div>

<button class="fab" id="fabBtn" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>

<script>
    // ── Tab switching ──────────────────────────────────────────
    function showTab(name) {
        document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        event.currentTarget.classList.add('active');
        window.scrollTo({top:0, behavior:'smooth'});
    }

    // ── Toggle inline forms ────────────────────────────────────
    function toggleForm(id) {
        const el = document.getElementById(id);
        el.classList.toggle('open');
        if (el.classList.contains('open')) {
            el.scrollIntoView({behavior:'smooth', block:'nearest'});
        }
    }

    // ── Scroll-to-top FAB ─────────────────────────────────────
    window.addEventListener('scroll', () => {
        document.getElementById('fabBtn').style.display =
            window.scrollY > 300 ? 'flex' : 'none';
    });

    // ── Animate stat counters ──────────────────────────────────
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count) || 0;
        if (!target) return;
        let cur = 0;
        const step = Math.ceil(target / 18);
        const t = setInterval(() => {
            cur = Math.min(cur + step, target);
            el.textContent = cur;
            if (cur >= target) clearInterval(t);
        }, 35);
    });

    // ── Animate risk bars ──────────────────────────────────────
    window.addEventListener('load', () => {
        document.querySelectorAll('.risk-fill').forEach(bar => {
            const w = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => { bar.style.width = w; }, 400);
        });
    });
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────
# Government Schemes Data (Month 1)
# ─────────────────────────────────────────────────────────────────
GOVT_SCHEMES = [
    {
        "name":         "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "amount":       "₹5,000 in 3 instalments",
        "description":  "Direct cash benefit for first live birth to compensate for wage loss during pregnancy and promote proper nutrition.",
        "eligibility":  "All pregnant women for first living child. Must register before 150 days of pregnancy.",
        "how_to_apply": "Register with ASHA/ANM. Fill Form 1-A at Anganwadi or Health Centre with bank account + Aadhaar + MCP card."
    },
    {
        "name":         "Janani Suraksha Yojana (JSY)",
        "amount":       "₹1,400 (rural) · ₹1,000 (urban)",
        "description":  "Cash incentive to promote institutional delivery and reduce maternal and neonatal mortality.",
        "eligibility":  "All BPL pregnant women for institutional delivery. No age or birth order limit in LPS states.",
        "how_to_apply": "Delivered in government facility. Cash given at discharge. ASHA gets ₹600 for facilitating."
    },
    {
        "name":         "Janani Shishu Suraksha Karyakram (JSSK)",
        "amount":       "Free services (no cash)",
        "description":  "Completely free and cashless maternity care — delivery, C-section, medicines, diagnostics, diet, blood, transport.",
        "eligibility":  "All pregnant women and sick newborns (up to 30 days) in government hospitals. No BPL requirement.",
        "how_to_apply": "Automatically entitled at any government facility. Demand services from facility in-charge."
    },
    {
        "name":         "Mukhyamantri Rajshri Yojana (Rajasthan)",
        "amount":       "₹50,000 in 6 instalments for girl child",
        "description":  "State scheme to promote birth and education of girl children, reduce sex-selective practices.",
        "eligibility":  "Girl children born in government hospitals on or after 1 June 2016. Rajasthan residents only.",
        "how_to_apply": "Apply at hospital at time of delivery. Subsequent instalments linked to school enrolment milestones."
    },
    {
        "name":         "Ayushman Bharat — PMJAY",
        "amount":       "₹5 lakh per family per year",
        "description":  "Health insurance for secondary and tertiary hospitalisation. Covers maternity, C-section, newborn care.",
        "eligibility":  "Bottom 40% of population per SECC 2011 data. Beneficiary check on pmjay.gov.in.",
        "how_to_apply": "Show Ayushman card or Aadhaar at empanelled hospital. ASHA can help verify beneficiary status."
    }
]


# ─────────────────────────────────────────────────────────────────
# Render function
# ─────────────────────────────────────────────────────────────────
def render_dashboard(patients, high_risk, total, safe, asha_id):
    from database import (
        get_all_asha_alerts,
        get_symptom_logs,
        get_risk_score_from_db,
        get_asha_visits,
        get_asha_performance,
        get_anc_records,
        get_postpartum_patients_due,
        get_children,
        get_growth_logs,
        get_immunization_records,
        get_asha_by_phone
    )

    # Basic data
    alerts        = get_all_asha_alerts(asha_id)
    total_reports = sum(len(get_symptom_logs(phone)) for phone in patients)

    # Risk scores
    patient_risks = {}
    for phone in patients:
        score, level, _ = get_risk_score_from_db(phone)
        patient_risks[phone] = {"score": score, "level": level}

    # ANC data
    anc_data = {}
    for phone in patients:
        anc_data[phone] = get_anc_records(phone)

    # Performance (Month 2)
    performance   = get_asha_performance(asha_id, days=30)
    recent_visits = get_asha_visits(asha_id, limit=10)

    # Postpartum (Month 4)
    pp_due_patients = get_postpartum_patients_due(asha_id)
    pp_due_count    = len(pp_due_patients)

    # Children + growth + immunization (Month 4)
    children_data = []
    for phone in patients:
        kids = get_children(phone)
        for kid in kids:
            kid["mother_phone"]   = phone
            kid["growth_logs"]    = get_growth_logs(kid["id"])
            kid["immunizations"]  = get_immunization_records(kid["id"])
            # Compute due vaccines (simple NHM schedule logic)
            given = {v["vaccine_name"] for v in kid["immunizations"]}
            all_vaccines = [
                "BCG","OPV-0","Hepatitis B-1","OPV-1","Pentavalent-1",
                "OPV-2","Pentavalent-2","OPV-3","Pentavalent-3","IPV",
                "Measles-Rubella-1","JE-1","Measles-Rubella-2","DPT-Booster"
            ]
            kid["due_vaccines"] = [v for v in all_vaccines if v not in given][:3]
            children_data.append(kid)

    # ASHA name/village
    asha_info    = get_asha_by_phone(asha_id) or {}
    asha_name    = asha_info.get("name",    asha_id)
    asha_village = asha_info.get("village", "")

    return render_template_string(
        DASHBOARD_HTML,
        alerts          = alerts,
        patients        = patients,
        high_risk       = high_risk,
        total           = total,
        safe            = safe,
        total_reports   = total_reports,
        patient_risks   = patient_risks,
        asha_id         = asha_id,
        asha_name       = asha_name,
        asha_village    = asha_village,
        anc_data        = anc_data,
        performance     = performance,
        recent_visits   = recent_visits,
        pp_due_patients = pp_due_patients,
        pp_due_count    = pp_due_count,
        children_data   = children_data,
        schemes         = GOVT_SCHEMES
    )