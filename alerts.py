# ─────────────────────────────────────────────────────────────────
# MaaSakhi ASHA Alert System
# Stores and manages high risk alerts
# ─────────────────────────────────────────────────────────────────

from datetime import datetime

# In-memory alert storage
# In production this would be a database
asha_alerts = []


def save_alert(name, week, symptom, phone):
    """Save a new high risk alert."""
    alert = {
        "name": name,
        "week": week,
        "symptom": symptom,
        "phone": phone,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "status": "Pending"
    }
    asha_alerts.append(alert)

    # Print to terminal so ASHA worker can see it
    print(f"""
╔══════════════════════════════════════╗
  ⚠️  HIGH RISK ALERT — MaaSakhi
╠══════════════════════════════════════╣
  Patient : {name}
  Week    : {week}
  Symptom : {symptom}
  Phone   : {phone}
  Time    : {alert['time']}
  Action  : Contact immediately!
╚══════════════════════════════════════╝
""")
    return alert


def get_all_alerts():
    """Return all alerts."""
    return asha_alerts


def get_alert_count():
    """Return total number of alerts."""
    return len(asha_alerts)