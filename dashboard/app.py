from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import dash
import logging
import threading
from pathlib import Path

from dashboard.services.api import get_firms, get_stopwords, warm_api, is_api_ready
from dashboard.components.eda_content import eda_content
from dashboard.branding import ensure_theme_css
from dashboard.roles import ROLES, nav_links_for_role, pages_for_role, get_role_config

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger(__name__)

# In local debug mode (python -m dashboard.app) this thread warms the API.
# Under Gunicorn, this thread runs in the master and dies at fork -- the
# gunicorn.conf.py post_fork hook starts a fresh thread in each worker.
threading.Thread(target=warm_api, daemon=True).start()

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    assets_folder=str(ROOT / "assets"),
)

server = app.server
app.title = "Wealthtender Dashboard"
ensure_theme_css()
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/png" href="/assets/favicon.png">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# ---------------------------------------------------------------------------
# Helpers (must be defined BEFORE the layout that uses them)
# ---------------------------------------------------------------------------
def _filter(label, control):
    return html.Div(className="filter-group", style={"marginTop": "12px"}, children=[
        html.Div(label, className="filter-label"), control,
    ])


def _get_role_and_firm(data):
    if not data or not isinstance(data, dict):
        return None, None
    role = data.get("role")
    if role not in ROLES:
        return None, None
    firm_id = data.get("firm_id")
    if firm_id is not None and not isinstance(firm_id, str):
        firm_id = str(firm_id)
    return role, firm_id


def _norm(pathname):
    """Normalise pathname so double-slashes don't break routing."""
    if not pathname:
        return "/"
    return "/" + pathname.strip("/")


# ---------------------------------------------------------------------------
# Layout
#
# Everything is declared statically.  Callbacks ONLY toggle visibility (style)
# and property values -- they never create or destroy components.
#
# ALL page content is rendered by dash.page_container.  There is no separate
# "eda-shell".  The sidebar filters live here in app.py; the EDA callback in
# eda_content.py reads them by ID.
# ---------------------------------------------------------------------------
app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Location(id="url"),
        dcc.Store(id="user-role", storage_type="session"),
        dcc.Store(id="firm-options-loaded", data=False),
        dcc.Store(id="eda-sliders-initialized", data=False),
        dcc.Interval(id="api-poll", interval=3_000, max_intervals=40),

        # -- Top nav bar --
        html.Div(
            className="top-nav",
            children=[
                html.A(
                    href="https://wealthtender.com",
                    className="brand-block",
                    children=[
                        html.Img(src=app.get_asset_url("brand/logo-mark.svg"),
                                 className="brand-mark", alt="Wealthtender mark"),
                        html.Img(src=app.get_asset_url("brand/logo-wordmark.svg"),
                                 className="brand-wordmark", alt="Wealthtender"),
                    ],
                ),
                html.Div(
                    className="top-nav-links",
                    children=[
                        html.Div(id="nav-links",
                                 style={"display": "contents"}),
                        html.Button("Sign Out", id="sign-out-btn",
                                    style={"display": "none"}),
                    ],
                ),
            ],
        ),

        # -- Body (sidebar + main) --
        html.Div(
            id="content-shell",
            className="content-shell",
            children=[
                # ---- Sidebar (always in DOM, visibility toggled) ----
                html.Aside(
                    id="sidebar",
                    className="sidebar",
                    style={"display": "none"},
                    children=[
                        html.Div(className="sidebar-header", children=[
                            html.Div("Filters", className="sidebar-title"),
                        ]),
                        html.Div(id="sidebar-role-badge",
                                 style={"marginBottom": "8px"}),

                        # Firm dropdown (admin) or locked name (firm user)
                        html.Div(id="firm-selector-group",
                                 className="filter-group",
                                 style={"display": "none", "marginTop": "8px"},
                                 children=[
                            html.Div("Firm Selector", className="filter-label"),
                            dcc.Dropdown(id="firm-dropdown",
                                         placeholder="Select firm",
                                         searchable=False),
                        ]),
                        html.Div(id="firm-locked-display",
                                 style={"display": "none", "marginTop": "8px"},
                                 children=[
                            html.Div("Firm", className="filter-label"),
                            html.Div(id="firm-locked-name", style={
                                "fontWeight": "600", "color": "#004C8C",
                                "fontSize": "14px", "padding": "6px 0"}),
                        ]),

                        # EDA-specific filters
                        html.Div(
                            id="eda-filters-section",
                            className="sidebar-section",
                            style={"display": "none"},
                            children=[
                                html.Div(className="filter-group", children=[
                                    html.Div("Scope", className="filter-label"),
                                    dcc.RadioItems(
                                        id="eda-scope",
                                        options=[
                                            {"label": "Global", "value": "global"},
                                            {"label": "Firm", "value": "firm"},
                                        ],
                                        value="global", inline=False),
                                ]),
                                _filter("Rating", dcc.Dropdown(
                                    id="eda-rating-filter",
                                    options=[{"label": "All", "value": "all"}]
                                    + [{"label": str(i), "value": float(i)}
                                       for i in range(1, 6)],
                                    value="all", clearable=False)),
                                _filter("Reviews per Advisor", dcc.RangeSlider(
                                    id="eda-review-range",
                                    min=0, max=50, step=1, value=[0, 50],  # updated by API
                                    tooltip={"placement": "bottom",
                                             "always_visible": False})),
                                _filter("Date Range", dcc.DatePickerRange(
                                    id="eda-date-range",
                                    start_date=None, end_date=None,
                                    display_format="YYYY-MM-DD",
                                    start_date_placeholder_text="Start",
                                    end_date_placeholder_text="End",
                                    style={"width": "100%"})),
                                _filter("Token Count", dcc.RangeSlider(
                                    id="eda-token-range",
                                    min=0, max=1000, step=10, value=[0, 1000],
                                    tooltip={"placement": "bottom",
                                             "always_visible": False})),
                                _filter("N-gram Size", dcc.Dropdown(
                                    id="eda-ngram-size",
                                    options=[{"label": f"{i}-gram", "value": i}
                                             for i in range(1, 4)],
                                    value=1, clearable=False)),
                                _filter("Top N", dcc.Slider(
                                    id="eda-ngram-topn",
                                    min=10, max=50, step=5, value=20,
                                    marks={10: "10", 20: "20", 30: "30",
                                           40: "40", 50: "50"})),
                                _filter("Exclude Stopwords", dcc.Checklist(
                                    id="eda-exclude-stopwords",
                                    options=[{"label": "Exclude common words",
                                              "value": "exclude"}],
                                    value=["exclude"])),

                                # --- Stopword customization panel ---
                                html.Div(
                                    id="eda-stopword-picker-wrap",
                                    style={"marginTop": "8px",
                                           "display": "block"},
                                    children=[
                                        html.Div(
                                            "NLTK default stopwords active.",
                                            style={"fontSize": "11px",
                                                   "color": "#6b7280",
                                                   "marginBottom": "8px",
                                                   "fontStyle": "italic"}),

                                        # 1) Extra words (tag-style chips)
                                        html.Div(
                                            "Add extra words to exclude:",
                                            style={"fontSize": "11px",
                                                   "color": "#374151",
                                                   "fontWeight": "600",
                                                   "marginBottom": "4px"}),
                                        dcc.Dropdown(
                                            id="eda-extra-stopwords",
                                            multi=True,
                                            options=[],
                                            value=[],
                                            placeholder="Type a word, press Enter...",
                                            searchable=True,
                                            style={"fontSize": "12px",
                                                   "marginBottom": "4px"}),
                                        html.Div(
                                            "Type any word and press Enter "
                                            "to add it. Click \u00d7 to remove.",
                                            style={"fontSize": "10px",
                                                   "color": "#9ca3af",
                                                   "marginBottom": "10px"}),

                                        # 2) Collapsible default list
                                        html.Button(
                                            "Show default list",
                                            id="eda-sw-toggle-btn",
                                            n_clicks=0,
                                            style={
                                                "fontSize": "11px",
                                                "color": "#004C8C",
                                                "background": "none",
                                                "border": "none",
                                                "cursor": "pointer",
                                                "padding": "0",
                                                "textDecoration": "underline",
                                                "fontFamily": "inherit"}),
                                        html.Div(
                                            id="eda-sw-default-list-wrap",
                                            style={"display": "none",
                                                   "marginTop": "6px"},
                                            children=[
                                                html.Div(
                                                    "Uncheck words to keep "
                                                    "them in results:",
                                                    style={
                                                        "fontSize": "10px",
                                                        "color": "#6b7280",
                                                        "marginBottom":
                                                            "4px"}),
                                                html.Div(
                                                    style={
                                                        "maxHeight": "300px",
                                                        "overflowY": "auto",
                                                        "border":
                                                            "1px solid "
                                                            "#e5e7eb",
                                                        "borderRadius": "6px",
                                                        "padding": "8px",
                                                        "background":
                                                            "#fafafa"},
                                                    children=[
                                                        dcc.Checklist(
                                                            id="eda-sw-defaults",
                                                            options=[],
                                                            value=[],
                                                            inline=True,
                                                            labelStyle={
                                                                "display":
                                                                    "inline-block",
                                                                "marginRight":
                                                                    "6px",
                                                                "marginBottom":
                                                                    "4px",
                                                                "fontSize":
                                                                    "11px"}),
                                                    ],
                                                ),
                                            ],
                                        ),

                                        # Hidden dropdown the EDA callback
                                        # reads (merged value)
                                        dcc.Dropdown(
                                            id="eda-custom-stopwords",
                                            multi=True,
                                            style={"display": "none"}),
                                    ],
                                ),
                            ],
                        ),

                        # Placeholder for non-EDA pages
                        html.Div(id="sidebar-page-note",
                                 style={"display": "none", "marginTop": "12px"},
                                 children=[
                            html.Div("(Page-specific filters coming soon)",
                                     className="sidebar-note"),
                        ]),
                    ],
                ),

                # ---- Main content ----
                html.Main(
                    className="page-container",
                    children=[
                        html.Div(id="api-status-banner"),
                        html.Div(id="access-denied",
                                 style={"display": "none"}),
                        # EDA content is always in the DOM (hidden when
                        # not on /eda).  This avoids "nonexistent Output"
                        # errors from the EDA callback.
                        html.Div(id="eda-shell",
                                 style={"display": "none"},
                                 children=eda_content()),
                        # All other pages render via page_container:
                        html.Div(id="page-shell",
                                 children=[dash.page_container]),
                    ],
                ),
            ],
        ),
    ],
)


# =========================================================================
# CALLBACKS
#
# Rules:
#   1. Only navigate_on_role_change writes to url.pathname
#   2. Only splash + sign_out write to user-role.data
#   3. Everything else toggles visibility or updates props
# =========================================================================


# ---------- Nav links ----------

@callback(
    Output("nav-links", "children"),
    Output("sign-out-btn", "style"),
    Input("url", "pathname"),
    Input("user-role", "data"),
)
def render_nav(pathname, user_role_data):
    pathname = _norm(pathname)
    role, _ = _get_role_and_firm(user_role_data)
    if not role:
        return (
            [dcc.Link("Home", href="/",
                      className="active" if pathname == "/" else "")],
            {"display": "none"},
        )
    links = []
    for label, href in nav_links_for_role(role):
        cls = "active" if pathname == href else ""
        links.append(dcc.Link(label, href=href, className=cls))
    return links, {
        "marginLeft": "12px", "fontSize": "12px", "opacity": "0.7",
        "background": "none", "border": "none", "cursor": "pointer",
        "color": "#6b7280", "fontFamily": "inherit",
        "textDecoration": "underline",
    }


# ---------- Navigate on role change ----------

@callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("user-role", "data"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def navigate_on_role_change(user_role_data, current_path):
    current_path = _norm(current_path)
    role, _ = _get_role_and_firm(user_role_data)
    log.info("navigate_on_role_change: role=%s  path=%s", role, current_path)
    if not role:
        return "/" if current_path != "/" else no_update
    if current_path == "/":
        dest = "/eda" if role == "admin" else "/firm-overview"
        log.info("navigate_on_role_change -> %s", dest)
        return dest
    return no_update


# ---------- Sign out ----------

@callback(
    Output("user-role", "data", allow_duplicate=True),
    Input("sign-out-btn", "n_clicks"),
    prevent_initial_call=True,
)
def sign_out(n_clicks):
    if not n_clicks:
        return no_update
    log.info("sign_out: clearing role")
    return None


# ---------- API status ----------

@callback(
    Output("api-status-banner", "children"),
    Output("api-status-banner", "style"),
    Output("api-poll", "disabled"),
    Input("api-poll", "n_intervals"),
)
def check_api_status(_n):
    if is_api_ready():
        return None, {"display": "none"}, True
    return (
        html.Div(className="api-status-banner", children=[
            html.Span(className="spinner"),
            "Connecting to data service\u2026 this may take a moment.",
        ]),
        {"display": "block"},
        False,
    )


# ---------- Firm dropdown (loads once) ----------

@callback(
    Output("firm-dropdown", "options"),
    Output("firm-dropdown", "value"),
    Output("firm-options-loaded", "data"),
    Input("user-role", "data"),
    State("firm-options-loaded", "data"),
    State("firm-dropdown", "value"),
)
def load_firm_options(user_role_data, already_loaded, cur_value):
    role, firm_id = _get_role_and_firm(user_role_data)
    if not role or already_loaded:
        return no_update, no_update, no_update
    firms = get_firms()
    opts = [{"label": f["firm_id"], "value": f["firm_id"]} for f in firms]
    if not opts:
        # API unreachable or no firms -- allow retry on next role change
        opts = [{"label": "No firms available",
                 "value": "__none__", "disabled": True}]
        log.info("load_firm_options: no firms (API down?), will retry")
        return opts, no_update, False
    if firm_id and any(o["value"] == firm_id for o in opts):
        default = firm_id
    else:
        default = cur_value or (opts[0]["value"] if opts else None)
    log.info("load_firm_options: %d opts, default=%s", len(opts), default)
    return opts, default, True


# ---------- Sidebar visibility ----------

@callback(
    Output("sidebar", "style"),
    Output("sidebar-role-badge", "children"),
    Output("firm-selector-group", "style"),
    Output("firm-locked-display", "style"),
    Output("firm-locked-name", "children"),
    Output("eda-filters-section", "style"),
    Output("sidebar-page-note", "style"),
    Input("url", "pathname"),
    Input("user-role", "data"),
)
def update_sidebar(pathname, user_role_data):
    pathname = _norm(pathname)
    role, firm_id = _get_role_and_firm(user_role_data)
    hide = {"display": "none"}

    if not role or pathname == "/":
        return hide, "", hide, hide, "", hide, hide

    cfg = get_role_config(role)
    badge = html.Span(
        cfg.get("label", role.title()),
        style={"fontSize": "11px", "color": "#6b7280", "fontStyle": "italic"})

    # Firm picker vs locked
    if cfg.get("show_firm_picker"):
        fg = {"display": "block", "marginTop": "8px"}
        fl = hide
        fn = ""
    elif cfg.get("firm_locked") and firm_id:
        fg = hide
        fl = {"display": "block", "marginTop": "8px"}
        fn = firm_id
    else:
        fg = hide
        fl = hide
        fn = ""

    eda = ({"display": "block"}
           if pathname == "/eda" and "/eda" in pages_for_role(role)
           else hide)
    note = {"display": "block"} if pathname != "/eda" else hide

    return {"display": "block"}, badge, fg, fl, fn, eda, note


# ---------- Stopword panel: show/hide + load defaults ----------

@callback(
    Output("eda-stopword-picker-wrap", "style"),
    Output("eda-sw-defaults", "options"),
    Output("eda-sw-defaults", "value"),
    Input("eda-exclude-stopwords", "value"),
    State("eda-sw-defaults", "options"),
)
def toggle_stopword_panel(exclude_checked, cur_opts):
    is_on = "exclude" in (exclude_checked or [])
    style = {"marginTop": "8px",
             "display": "block" if is_on else "none"}
    if is_on and not cur_opts:
        words = get_stopwords()
        if not words:
            return style, [], []
        opts = [{"label": w, "value": w} for w in words]
        return style, opts, words          # all checked by default
    return style, no_update, no_update


# ---------- Toggle default-list visibility ----------

@callback(
    Output("eda-sw-default-list-wrap", "style"),
    Output("eda-sw-toggle-btn", "children"),
    Input("eda-sw-toggle-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_sw_list(n_clicks):
    if (n_clicks or 0) % 2 == 1:
        return {"display": "block", "marginTop": "6px"}, "Hide default list"
    return {"display": "none", "marginTop": "6px"}, "Show default list"


# ---------- Extra-words tag input: turn typed text into chip options ---

@callback(
    Output("eda-extra-stopwords", "options"),
    Input("eda-extra-stopwords", "search_value"),
    Input("eda-extra-stopwords", "value"),
    State("eda-extra-stopwords", "options"),
    prevent_initial_call=True,
)
def update_extra_sw_options(search, selected, current_opts):
    """Keep options in sync with whatever the user has typed/selected.

    Dash multi-select Dropdown only allows selecting from `options`.
    We dynamically add every selected value and the current search term
    so the user can type any word and press Enter to create a chip.
    """
    opts = {o["value"]: o for o in (current_opts or [])}
    # Ensure every selected chip stays in options
    for w in (selected or []):
        if w not in opts:
            opts[w] = {"label": w, "value": w}
    # Show the current search text as a selectable option
    if search:
        term = search.strip().lower()
        if term and term not in opts:
            opts[term] = {"label": term, "value": term}
    return list(opts.values())


# ---------- Merge extra words + defaults -> hidden value ----------

@callback(
    Output("eda-custom-stopwords", "value"),
    Input("eda-sw-defaults", "value"),
    Input("eda-extra-stopwords", "value"),
    Input("eda-exclude-stopwords", "value"),
    prevent_initial_call=True,
)
def merge_stopwords(defaults_checked, extras_selected, exclude_checked):
    is_on = "exclude" in (exclude_checked or [])
    if not is_on:
        return []

    extras = []
    for w in (extras_selected or []):
        w = w.strip().lower()
        if w:
            extras.append(w)

    # If all defaults are still checked and no extras added,
    # return empty list -> API uses its built-in NLTK defaults
    # (avoids sending 179 words as query params)
    if not extras:
        return []

    # User customised: merge defaults + extras into explicit list
    words = list(defaults_checked or [])
    for w in extras:
        if w not in words:
            words.append(w)
    return words


# ---------- Content-shell layout mode ----------

@callback(
    Output("content-shell", "style"),
    Output("eda-shell", "style"),
    Output("page-shell", "style"),
    Output("access-denied", "style"),
    Output("access-denied", "children"),
    Input("url", "pathname"),
    Input("user-role", "data"),
)
def toggle_content(pathname, user_role_data):
    pathname = _norm(pathname)
    role, _ = _get_role_and_firm(user_role_data)
    hide = {"display": "none"}
    show = {"display": "block"}

    # Splash / no role: single-column, show page-shell (splash), hide EDA
    if not role or pathname == "/":
        return {"display": "block", "padding": "0"}, hide, show, hide, None

    allowed = pages_for_role(role)

    # EDA: show eda-shell, hide page-shell
    if pathname == "/eda" and "/eda" in allowed:
        return {}, show, hide, hide, None

    # Other allowed pages: hide eda-shell, show page-shell
    if pathname in allowed:
        return {}, hide, show, hide, None

    # Access denied
    denied = html.Div([
        html.H2("Access Restricted"),
        html.P("Your current role does not include this page."),
        html.P(children=["Return to ", dcc.Link("Home", href="/"),
                          " to switch roles."]),
    ])
    return {}, hide, hide, {"display": "block", "padding": "40px",
                             "textAlign": "center"}, denied


# ---------- Entry point ----------

if __name__ == "__main__":
    app.run(debug=True, port=8050)
