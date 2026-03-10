import os

import dash
from dash import html, dcc, callback, Input, Output, State, no_update

from dashboard.roles import ROLES
from dashboard.services.api import get_firms

# Admin password -- set via ADMIN_PASSWORD env var on Render.
# Falls back to a default for local dev convenience.
_ADMIN_PW = os.environ.get("ADMIN_PASSWORD", "WT$msba2026")

dash.register_page(__name__, path="/", title="Wealthtender Dashboard")


# ---------------------------------------------------------------------------
# Team credits
# ---------------------------------------------------------------------------
MSBA = [
    "Alisha Surabhi",
    "Joseph Bailey",
    "Chris Breton",
    "Manny Escalante",
    "Zan Merrill",
    "Carolina Rios",
]

UNDERGRAD = [
    "Saif Ansari",
    "Isabelle Demengeon",
    "Abhinav Yarlagadda",
    "Julianna Tijerina",
    "Katelyn Semien",
]


def _last_name(full_name: str) -> str:
    parts = full_name.split()
    return parts[-1] if parts else full_name


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def layout():
    return html.Div(children=[
        html.Div(className="splash-hero", children=[
            html.A(
                href="https://wealthtender.com", target="_blank",
                children=[html.Img(
                    src="/assets/brand/logo-wordmark.svg",
                    className="brand-wordmark",
                    style={"height": "32px", "marginBottom": "16px"},
                    alt="Wealthtender",
                )],
            ),
            html.H2("Advisor Review Analytics"),
            html.Div("UT Austin MSBA Capstone 2026",
                      className="splash-subtitle", style={"marginBottom": "8px"}),
            html.Div("Select a portal to continue.",
                      id="splash-prompt", className="splash-subtitle"),
        ]),

        # Role selection cards
        html.Div(id="splash-role-selection", children=[
            html.Div(className="splash-nav-grid", style={"maxWidth": "520px"}, children=[
                # Admin card
                html.Div(
                    id="role-card-admin",
                    className="splash-role-card",
                    children=[
                        html.Div("Wealthtender Admin", className="splash-role-title"),
                        html.Div(ROLES["admin"]["desc"], className="splash-role-desc"),
                        # Password gate (hidden until card is clicked)
                        html.Div(
                            id="admin-pw-section",
                            style={"display": "none", "marginTop": "12px"},
                            children=[
                                html.Div("Enter admin password:", style={
                                    "fontSize": "12px", "color": "#6b7280",
                                    "marginBottom": "4px"}),
                                dcc.Input(
                                    id="admin-pw-input",
                                    type="password",
                                    placeholder="Password",
                                    debounce=True,
                                    style={"width": "100%", "fontSize": "13px",
                                           "padding": "6px 10px",
                                           "borderRadius": "6px",
                                           "border": "1px solid #d1d5db"}),
                                html.Button(
                                    "Sign In", id="admin-pw-submit",
                                    className="splash-enter-btn",
                                    style={"marginTop": "8px"}),
                                html.Div(
                                    id="admin-pw-error",
                                    style={"fontSize": "11px", "color": "#dc2626",
                                           "marginTop": "4px"}),
                            ],
                        ),
                    ],
                ),
                # Firm card
                html.Div(
                    id="role-card-firm",
                    className="splash-role-card",
                    children=[
                        html.Div("Firm Portal", className="splash-role-title"),
                        html.Div(ROLES["firm"]["desc"], className="splash-role-desc"),
                        html.Div(
                            id="splash-firm-picker",
                            style={"display": "none", "marginTop": "12px"},
                            children=[
                                html.Div("Select your firm:", style={
                                    "fontSize": "12px", "color": "#6b7280",
                                    "marginBottom": "4px"}),
                                dcc.Dropdown(
                                    id="splash-firm-dropdown",
                                    placeholder="Choose a firm...",
                                    searchable=True, style={"fontSize": "13px"}),
                                html.Button("Enter", id="splash-firm-enter",
                                            className="splash-enter-btn",
                                            style={"marginTop": "8px"},
                                            disabled=True),
                            ],
                        ),
                    ],
                ),
            ]),
        ]),

        # Confirmed state (shown after role is set)
        html.Div(id="splash-confirmed", style={"display": "none"}, children=[
            html.Div(style={"textAlign": "center", "padding": "20px"}, children=[
                html.Div("Role set. Use the navigation above to explore.",
                         style={"color": "#6b7280", "fontSize": "14px"}),
            ]),
        ]),

        # Team credits
        html.Div(className="splash-team", children=[
            html.H3("MSBA Team"),
            html.Div(
                " \u2022 ".join(sorted(MSBA, key=_last_name)),
                style={"fontSize": "13px", "color": "#374151",
                       "lineHeight": "1.6"}),
            html.H3("Undergraduate Contributors",
                     style={"marginTop": "16px"}),
            html.Div(
                " \u2022 ".join(sorted(UNDERGRAD, key=_last_name)),
                style={"fontSize": "13px", "color": "#374151",
                       "lineHeight": "1.6"}),
        ]),

        html.Div(
            style={"textAlign": "center", "marginTop": "32px", "marginBottom": "16px"},
            children=[html.Div(
                "Admin access is password-protected. Contact the team for credentials.",
                style={"fontSize": "11px", "color": "#9ca3af", "fontStyle": "italic"},
            )],
        ),
    ])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("splash-firm-picker", "style"),
    Output("splash-firm-dropdown", "options"),
    Input("role-card-firm", "n_clicks"),
    prevent_initial_call=True,
)
def show_firm_picker(n_clicks):
    firms = get_firms()
    options = [{"label": f["firm_id"], "value": f["firm_id"]} for f in firms]
    if not options:
        options = [{"label": "No firms available", "value": "__none__", "disabled": True}]
    return {"display": "block", "marginTop": "12px"}, options


@callback(
    Output("splash-firm-enter", "disabled"),
    Input("splash-firm-dropdown", "value"),
)
def enable_enter_btn(value):
    return not bool(value)


# --- Role setters: ONLY write to user-role, NEVER to url ---

@callback(
    Output("admin-pw-section", "style"),
    Input("role-card-admin", "n_clicks"),
    prevent_initial_call=True,
)
def show_admin_pw(n_clicks):
    """Reveal password input when the admin card is clicked."""
    if not n_clicks:
        return no_update
    return {"display": "block", "marginTop": "12px"}


@callback(
    Output("user-role", "data", allow_duplicate=True),
    Output("admin-pw-error", "children"),
    Input("admin-pw-submit", "n_clicks"),
    Input("admin-pw-input", "n_submit"),
    State("admin-pw-input", "value"),
    prevent_initial_call=True,
)
def set_admin_role(btn_clicks, input_submit, password):
    """Verify password server-side and set admin role if correct."""
    if not (btn_clicks or input_submit):
        return no_update, no_update
    if not password:
        return no_update, "Please enter a password."
    if password == _ADMIN_PW:
        return {"role": "admin", "firm_id": None}, ""
    return no_update, "Incorrect password."


@callback(
    Output("user-role", "data", allow_duplicate=True),
    Input("splash-firm-enter", "n_clicks"),
    State("splash-firm-dropdown", "value"),
    prevent_initial_call=True,
)
def set_firm_role(n_clicks, firm_id):
    if not n_clicks or not firm_id:
        return no_update
    return {"role": "firm", "firm_id": firm_id}


# --- Splash view updates when role changes ---

@callback(
    Output("splash-role-selection", "style"),
    Output("splash-confirmed", "style"),
    Output("splash-prompt", "children"),
    Input("user-role", "data"),
)
def update_splash_view(user_role_data):
    if user_role_data and isinstance(user_role_data, dict) and user_role_data.get("role") in ROLES:
        role_label = ROLES[user_role_data["role"]]["label"]
        return {"display": "none"}, {"display": "block"}, f"Signed in as {role_label}."
    return {"display": "block"}, {"display": "none"}, "Select a portal to continue."
