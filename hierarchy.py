# ─────────────────────────────────────────────────────────────────
# MaaSakhi Hierarchy Utility
# Role-based permission checker and routing helper
#
# Roles (highest → lowest):
# admin      → District Health Officer — sees everything
# bmo        → Block Medical Officer — sees their block
# supervisor → ASHA Supervisor (ANM) — sees her ASHAs
# asha       → ASHA Worker — sees her patients
# ─────────────────────────────────────────────────────────────────

from functools import wraps
from flask import session, redirect


# ─────────────────────────────────────────────────────────────────
# ROLE HIERARCHY
# Higher number = more access
# ─────────────────────────────────────────────────────────────────

ROLE_LEVELS = {
    "asha":       1,
    "supervisor": 2,
    "bmo":        3,
    "admin":      4,
}

ROLE_NAMES = {
    "asha":       "ASHA Worker",
    "supervisor": "ASHA Supervisor (ANM)",
    "bmo":        "Block Medical Officer",
    "admin":      "District Health Officer",
}

ROLE_DASHBOARDS = {
    "asha":       "/dashboard/{id}",
    "supervisor": "/supervisor/{id}",
    "bmo":        "/bmo/{id}",
    "admin":      "/admin",
}

ROLE_COLORS = {
    "asha":       "#085041",
    "supervisor": "#0369A1",
    "bmo":        "#B45309",
    "admin":      "#7C3AED",
}

ROLE_ICONS = {
    "asha":       "👩",
    "supervisor": "👩‍💼",
    "bmo":        "🏥",
    "admin":      "🏛",
}


# ─────────────────────────────────────────────────────────────────
# PERMISSION CHECKERS
# ─────────────────────────────────────────────────────────────────

def get_role_level(role):
    """Returns numeric level for a role. Higher = more access."""
    return ROLE_LEVELS.get(role, 0)


def can_access(user_role, required_role):
    """
    Returns True if user_role has enough access for required_role.
    Example: admin can access supervisor pages, but not vice versa.
    """
    return get_role_level(user_role) >= get_role_level(required_role)


def can_view_patient(user, patient):
    """
    Checks if a user can view a specific patient's data.
    Respects the hierarchy — each role only sees their own chain.
    """
    role = user.get("role", "")

    if role == "admin":
        return True   # Admin sees everyone

    if role == "bmo":
        return user.get("bmo_id") == patient.get("bmo_id")

    if role == "supervisor":
        return user.get("supervisor_id") == patient.get("supervisor_id")

    if role == "asha":
        return user.get("asha_id") == patient.get("asha_id")

    return False


def can_view_alert(user, alert):
    """
    Checks if a user can view a specific alert.
    """
    role = user.get("role", "")

    if role == "admin":
        return True

    if role == "bmo":
        return user.get("bmo_id") == alert.get("bmo_id")

    if role == "supervisor":
        # Supervisor sees all alerts from her ASHAs
        # or escalated to her
        return (
            user.get("supervisor_id") == alert.get("supervisor_id")
            or alert.get("escalation_level", 0) >= 1
        )

    if role == "asha":
        return user.get("asha_id") == alert.get("asha_id")

    return False


def can_escalate(user, alert):
    """
    Checks if user can escalate this alert further.
    Can only escalate if alert is in your chain AND not already at top.
    """
    if not can_view_alert(user, alert):
        return False
    return alert.get("escalation_level", 0) < 3


def can_resolve(user, alert):
    """
    Any level can resolve an alert in their chain.
    """
    return can_view_alert(user, alert)


def can_manage_asha(user):
    """Only admin and supervisors can manage ASHA workers."""
    return user.get("role") in ["admin", "supervisor"]


def can_manage_supervisor(user):
    """Only admin and BMOs can manage supervisors."""
    return user.get("role") in ["admin", "bmo"]


def can_manage_bmo(user):
    """Only admin can manage BMOs."""
    return user.get("role") == "admin"


def can_view_district_analytics(user):
    """Only admin and BMO can see district-wide analytics."""
    return user.get("role") in ["admin", "bmo"]


# ─────────────────────────────────────────────────────────────────
# ROUTE DECORATORS
# Use these on Flask routes to protect them
# ─────────────────────────────────────────────────────────────────

def require_admin(f):
    """
    Flask route decorator — requires admin session.
    Usage: @require_admin
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin" not in session:
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated


def require_login(f):
    """
    Flask route decorator — requires any logged-in role.
    Checks session for admin, supervisor, bmo, or asha.
    Usage: @require_login
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def require_role(minimum_role):
    """
    Flask route decorator — requires minimum role level.
    Usage: @require_role("supervisor")
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect("/login")
            if not can_access(user.get("role", ""), minimum_role):
                return get_access_denied_page(user)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ─────────────────────────────────────────────────────────────────
# SESSION HELPERS
# ─────────────────────────────────────────────────────────────────

def get_current_user():
    """
    Returns current logged-in user from session.
    Checks all role session keys.
    Returns None if not logged in.
    """
    # Admin session (username/password login)
    if "admin" in session:
        user = dict(session["admin"])
        user["role"] = "admin"
        return user

    # Role-based phone login
    for role in ["supervisor", "bmo", "asha"]:
        key = f"{role}_user"
        if key in session:
            user = dict(session[key])
            user["role"] = role
            return user

    return None


def login_user(role, user_data):
    """
    Saves user to session after successful login.
    Call this after verifying credentials.
    """
    if role == "admin":
        session["admin"] = user_data
    else:
        session[f"{role}_user"] = user_data


def logout_user():
    """Clears all session data."""
    for key in ["admin", "supervisor_user", "bmo_user", "asha_user"]:
        session.pop(key, None)


# ─────────────────────────────────────────────────────────────────
# DASHBOARD ROUTER
# Given a user, returns the correct dashboard URL
# ─────────────────────────────────────────────────────────────────

def get_dashboard_url(user):
    """
    Returns the correct dashboard URL for a logged-in user.
    """
    role = user.get("role", "")

    if role == "admin":
        return "/admin"

    elif role == "bmo":
        bmo_id = user.get("bmo_id", "")
        return f"/bmo/{bmo_id}"

    elif role == "supervisor":
        supervisor_id = user.get("supervisor_id", "")
        return f"/supervisor/{supervisor_id}"

    elif role == "asha":
        asha_id = user.get("asha_id", "")
        return f"/dashboard/{asha_id}"

    return "/"


# ─────────────────────────────────────────────────────────────────
# ACCESS DENIED PAGE
# ─────────────────────────────────────────────────────────────────

def get_access_denied_page(user):
    """Returns a styled access denied HTML page."""
    role      = user.get("role", "unknown")
    role_name = ROLE_NAMES.get(role, "User")
    color     = ROLE_COLORS.get(role, "#085041")
    dashboard = get_dashboard_url(user)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Access Denied — MaaSakhi</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{
                font-family:Arial,sans-serif;
                background:#f9fafb;
                display:flex;
                justify-content:center;
                align-items:center;
                min-height:100vh;
            }}
            .box {{
                background:white;
                padding:40px;
                border-radius:16px;
                box-shadow:0 8px 30px rgba(0,0,0,0.1);
                text-align:center;
                max-width:400px;
                width:90%;
            }}
            .icon {{ font-size:48px; margin-bottom:16px; }}
            h2 {{ color:#1f2937; font-size:22px; }}
            p  {{ color:#6b7280; margin-top:10px; font-size:14px; }}
            .role-badge {{
                display:inline-block;
                background:{color}20;
                color:{color};
                border:1px solid {color}40;
                padding:4px 16px;
                border-radius:20px;
                font-size:13px;
                font-weight:600;
                margin-top:14px;
            }}
            .btn {{
                display:inline-block;
                margin-top:24px;
                padding:12px 28px;
                background:{color};
                color:white;
                border-radius:10px;
                text-decoration:none;
                font-size:14px;
                font-weight:600;
            }}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="icon">🔒</div>
            <h2>Access Denied</h2>
            <p>You don't have permission to view this page.</p>
            <div class="role-badge">
                {ROLE_ICONS.get(role, '👤')} {role_name}
            </div>
            <br>
            <a href="{dashboard}" class="btn">
                Go to My Dashboard
            </a>
        </div>
    </body>
    </html>
    """


# ─────────────────────────────────────────────────────────────────
# BREADCRUMB HELPER
# Generates hierarchy breadcrumb for dashboards
# ─────────────────────────────────────────────────────────────────

def get_breadcrumb(role, name, location=""):
    """
    Returns HTML breadcrumb showing where user sits in hierarchy.
    Example: District → Block Rampur → Supervisor Meena → ASHA Priya
    """
    levels = {
        "admin":      [("🏛 District", "#7C3AED")],
        "bmo":        [("🏛 District", "#7C3AED"),
                       (f"🏥 {location}", "#B45309")],
        "supervisor": [("🏛 District", "#7C3AED"),
                       ("🏥 Block", "#B45309"),
                       (f"👩‍💼 {name}", "#0369A1")],
        "asha":       [("🏛 District", "#7C3AED"),
                       ("🏥 Block", "#B45309"),
                       ("👩‍💼 Supervisor", "#0369A1"),
                       (f"👩 {name}", "#085041")],
    }

    items = levels.get(role, [])
    if not items:
        return ""

    parts = []
    for i, (label, color) in enumerate(items):
        is_last = (i == len(items) - 1)
        style = (
            f"color:{color};font-weight:{'700' if is_last else '400'};"
            f"font-size:12px;"
        )
        parts.append(f'<span style="{style}">{label}</span>')

    return (
        f'<div style="display:flex;align-items:center;gap:6px;'
        f'flex-wrap:wrap;padding:8px 0;">'
        + ' <span style="color:#d1d5db;font-size:12px">›</span> '.join(parts)
        + '</div>'
    )