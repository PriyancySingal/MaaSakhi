# ─────────────────────────────────────────────────────────────────
# MaaSakhi Personal Health Log
# Tracks every woman's real symptom history
# Used to generate personalized updates and risk scores
# ─────────────────────────────────────────────────────────────────

from datetime import datetime

# In-memory health logs per user
# Structure: { phone: [ {week, message, level, time}, ... ] }
health_logs = {}


def log_symptom(phone, week, message, level):
    """Save every symptom report to the woman's personal log."""
    if phone not in health_logs:
        health_logs[phone] = []

    entry = {
        "week": week,
        "message": message,
        "level": level,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p")
    }
    health_logs[phone].append(entry)
    return entry


def get_health_log(phone):
    """Get full health history for a woman."""
    return health_logs.get(phone, [])


def get_risk_score(phone):
    """
    Calculate real risk score based on actual symptom history.
    Returns: score (0-100), risk_level, summary
    """
    log = health_logs.get(phone, [])

    if not log:
        return 0, "Unknown", "No reports yet"

    # Count by severity
    red_count   = sum(1 for e in log if e["level"] == "RED")
    amber_count = sum(1 for e in log if e["level"] == "AMBER")
    green_count = sum(1 for e in log if e["level"] == "GREEN")
    total       = len(log)

    # Calculate score
    score = min(100, (red_count * 40) + (amber_count * 15) + (green_count * 2))

    # Recent reports matter more
    recent = log[-3:] if len(log) >= 3 else log
    recent_reds = sum(1 for e in recent if e["level"] == "RED")
    if recent_reds >= 2:
        score = min(100, score + 20)

    # Determine risk level
    if score >= 60 or red_count >= 2:
        risk_level = "HIGH"
    elif score >= 30 or red_count >= 1:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    # Build summary
    summary = (
        f"Total reports: {total} | "
        f"Danger signs: {red_count} | "
        f"Warnings: {amber_count} | "
        f"Normal: {green_count}"
    )

    return score, risk_level, summary


def get_recent_symptoms(phone, count=5):
    """Get last N symptom reports."""
    log = health_logs.get(phone, [])
    return log[-count:] if len(log) >= count else log


def get_symptom_pattern(phone):
    """
    Analyze symptom patterns for AI to use.
    Returns a summary string for the AI prompt.
    """
    log = health_logs.get(phone, [])

    if not log:
        return "No previous symptoms reported."

    recent = log[-5:] if len(log) >= 5 else log

    pattern = "Recent symptom history:\n"
    for entry in recent:
        pattern += (
            f"• Week {entry['week']} — "
            f"{entry['message'][:50]} — "
            f"{entry['level']} — "
            f"{entry['time']}\n"
        )

    return pattern