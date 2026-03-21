# ─────────────────────────────────────────────────────────────────
# MaaSakhi Health Log — Database Version
# All data now persisted in PostgreSQL
# ─────────────────────────────────────────────────────────────────

from database import (
    get_symptom_logs, get_risk_score_from_db
)


def get_health_log(phone):
    """Get health log from database."""
    return get_symptom_logs(phone)


def get_risk_score(phone):
    """Get risk score from database."""
    return get_risk_score_from_db(phone)


def get_symptom_pattern(phone):
    """Get symptom pattern summary for AI."""
    logs = get_symptom_logs(phone)

    if not logs:
        return "No previous symptoms reported."

    recent  = logs[-5:] if len(logs) >= 5 else logs
    pattern = "Recent symptom history:\n"

    for entry in recent:
        pattern += (
            f"• Week {entry['week']} — "
            f"{entry['message'][:50]} — "
            f"{entry['level']} — "
            f"{entry['time']}\n"
        )

    return pattern