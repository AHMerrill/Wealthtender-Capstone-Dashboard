"""
Role-based access configuration.

This file is the single source of truth for what each role can see.
When Wealthtender plugs in real authentication, they only need to:
  1. Inject `role` and `firm_id` from their auth session into the dcc.Store
  2. Optionally edit the ROLES dict below to adjust visibility

No page code needs to change.
"""

# -------------------------------------------------------------------------
# Role definitions
# -------------------------------------------------------------------------
# pages  : list of URL paths the role can navigate to (beyond "/")
# label  : display name shown in the UI
# desc   : short description for the splash page
# show_firm_picker : whether the firm dropdown is visible
# firm_locked      : if True, firm_id comes from auth (not a dropdown)

ROLES = {
    "admin": {
        "label": "Wealthtender Admin",
        "desc": "Full access to all firms, advisors, EDA, and methodology.",
        "pages": [
            "/eda",
            "/advisor-dna",
            "/benchmarks",
            "/leaderboard",
            "/comparisons",
            "/methodology",
        ],
        "show_firm_picker": True,
        "firm_locked": False,
    },
    "firm": {
        "label": "Firm Portal",
        "desc": "View your firm's advisors, scores, and industry benchmarks.",
        "pages": [
            "/advisor-dna",
            "/benchmarks",
            "/leaderboard",
            "/comparisons",
        ],
        "show_firm_picker": False,   # firm comes from auth context
        "firm_locked": True,
    },
}

# Default role when no selection has been made (shows splash page only)
DEFAULT_ROLE = None


def get_role_config(role: str) -> dict:
    """Return config for a role, or empty-dict for unknown roles."""
    return ROLES.get(role, {})


def pages_for_role(role: str) -> list[str]:
    """Return the list of allowed page paths for a role."""
    cfg = get_role_config(role)
    return cfg.get("pages", [])


def nav_links_for_role(role: str) -> list[tuple[str, str]]:
    """Return (label, href) pairs for the nav bar, filtered by role.

    The label is derived from the path (e.g. "/firm-overview" -> "Firm Overview").
    Home ("/") is always included.
    """
    allowed = set(pages_for_role(role))
    links = [("Home", "/")]
    for path in pages_for_role(role):
        label = path.strip("/").replace("-", " ").title()
        # Special-case short labels
        if path == "/eda":
            label = "EDA"
        elif path == "/advisor-dna":
            label = "Advisor DNA"
        links.append((label, path))
    return links
