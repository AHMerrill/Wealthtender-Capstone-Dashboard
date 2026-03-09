from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import dash
import logging
import threading
from pathlib import Path

from dashboard.services.api import (
    get_stopwords, warm_api, is_api_ready, get_dna_entities,
)
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
        dcc.Store(id="eda-scope", data="global"),
        html.Div(id="firm-dropdown", style={"display": "none"}),
        html.Div(id="firm-selector-group", style={"display": "none"}),
        html.Div(id="firm-locked-display", style={"display": "none"}),
        html.Div(id="firm-locked-name", style={"display": "none"}),
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

                        # EDA-specific filters
                        html.Div(
                            id="eda-filters-section",
                            className="sidebar-section",
                            style={"display": "none"},
                            children=[
                                html.Div(className="filter-group", children=[
                                    html.Div("Search By", className="filter-label"),
                                    dcc.RadioItems(
                                        id="eda-entity-type",
                                        options=[
                                            {"label": "Firm", "value": "firm"},
                                            {"label": "Advisor", "value": "advisor"},
                                        ],
                                        value="firm",
                                        inline=True,
                                    ),
                                ]),
                                html.Div(className="filter-group",
                                         style={"marginTop": "8px"}, children=[
                                    html.Div("Select Entity", className="filter-label"),
                                    dcc.Dropdown(
                                        id="eda-entity-search",
                                        placeholder="Search...",
                                        searchable=True,
                                        clearable=True,
                                    ),
                                ]),
                                html.Button(
                                    "Return to Global",
                                    id="eda-reset-btn",
                                    n_clicks=0,
                                    style={
                                        "marginTop": "8px",
                                        "marginBottom": "12px",
                                        "fontSize": "12px",
                                        "cursor": "pointer",
                                        "background": "none",
                                        "border": "1px solid #ccc",
                                        "borderRadius": "4px",
                                        "padding": "6px 12px",
                                        "width": "100%",
                                    },
                                ),
                                _filter("Rating", dcc.Dropdown(
                                    id="eda-rating-filter",
                                    options=[{"label": "All", "value": "all"}]
                                    + [{"label": str(i), "value": float(i)}
                                       for i in range(1, 6)],
                                    value="all", clearable=False)),
                                _filter("Reviews per Advisor", dcc.Dropdown(
                                    id="eda-review-range",
                                    options=[{"label": "All", "value": "all"}],
                                    value=["all"],
                                    multi=True,
                                    clearable=False,
                                    placeholder="Select range...")),
                                _filter("Date Range", html.Div([
                                    dcc.DatePickerRange(
                                        id="eda-date-range",
                                        start_date=None, end_date=None,
                                        display_format="YYYY-MM-DD",
                                        start_date_placeholder_text="Start",
                                        end_date_placeholder_text="End",
                                        style={"width": "100%"},
                                    ),
                                    html.Button(
                                        "Use Max Range",
                                        id="eda-date-max-btn",
                                        n_clicks=0,
                                        style={
                                            "marginTop": "6px",
                                            "fontSize": "11px",
                                            "cursor": "pointer",
                                            "background": "none",
                                            "color": "#004C8C",
                                            "border": "none",
                                            "textDecoration": "underline",
                                            "fontFamily": "inherit",
                                            "padding": "0",
                                        },
                                    ),
                                ])),
                                _filter("Review Length", dcc.Dropdown(
                                    id="eda-token-range",
                                    options=[{"label": "All", "value": "all"}],
                                    value=["all"],
                                    multi=True,
                                    clearable=False,
                                    placeholder="Select range...")),
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

                        # Advisor DNA filters
                        html.Div(
                            id="dna-filters-section",
                            className="sidebar-section",
                            style={"display": "none"},
                            children=[
                                html.Div(className="filter-group", children=[
                                    html.Div("Search By", className="filter-label"),
                                    dcc.RadioItems(
                                        id="dna-entity-type",
                                        options=[
                                            {"label": "Firm", "value": "firm"},
                                            {"label": "Advisor", "value": "advisor"},
                                        ],
                                        value="firm",
                                        inline=True,
                                    ),
                                ]),
                                html.Div(className="filter-group",
                                         style={"marginTop": "8px"}, children=[
                                    html.Div("Select Entity", className="filter-label"),
                                    dcc.Dropdown(
                                        id="dna-entity-search",
                                        placeholder="Search...",
                                        searchable=True,
                                        clearable=True,
                                    ),
                                ]),
                                html.Div(
                                    id="dna-method-group",
                                    className="filter-group",
                                    style={"display": "none", "marginTop": "12px"},
                                    children=[
                                        html.Div("Scoring Method",
                                                 className="filter-label"),
                                        dcc.RadioItems(
                                            id="dna-method-selector",
                                            options=[
                                                {"label": "Mean \u2014 equal weight across all reviews",
                                                 "value": "mean"},
                                                {"label": "Penalized \u2014 older reviews down-weighted",
                                                 "value": "penalized"},
                                                {"label": "Weighted \u2014 recent reviews weighted more",
                                                 "value": "weighted"},
                                            ],
                                            value="mean",
                                            inline=False,
                                            labelStyle={"display": "block",
                                                        "marginBottom": "6px",
                                                        "fontSize": "12px"},
                                        ),
                                        html.Button(
                                            "Read more \u25bc",
                                            id="dna-method-info-toggle",
                                            n_clicks=0,
                                            style={
                                                "fontSize": "11px",
                                                "cursor": "pointer",
                                                "background": "none",
                                                "color": "#004C8C",
                                                "border": "none",
                                                "textDecoration": "underline",
                                                "fontFamily": "inherit",
                                                "padding": "0",
                                                "marginTop": "2px",
                                            },
                                        ),
                                        html.Div(
                                            id="dna-method-info-panel",
                                            style={"display": "none"},
                                            children=[
                                                html.Div([
                                                    html.Div("Mean", style={
                                                        "fontWeight": "700",
                                                        "fontSize": "12px",
                                                        "marginBottom": "2px",
                                                    }),
                                                    html.Div(
                                                        "Averages the embedding vectors of all "
                                                        "reviews for this entity. Every review "
                                                        "contributes equally regardless of age. "
                                                        "Best for a balanced, all-time view.",
                                                        style={"fontSize": "11px",
                                                               "marginBottom": "8px"},
                                                    ),
                                                    html.Div("Penalized", style={
                                                        "fontWeight": "700",
                                                        "fontSize": "12px",
                                                        "marginBottom": "2px",
                                                    }),
                                                    html.Div(
                                                        "Applies a staleness penalty that "
                                                        "down-weights older reviews. Reviews "
                                                        "lose influence as they age. Useful for "
                                                        "surfacing whether recent feedback "
                                                        "differs from the historical pattern.",
                                                        style={"fontSize": "11px",
                                                               "marginBottom": "8px"},
                                                    ),
                                                    html.Div("Weighted", style={
                                                        "fontWeight": "700",
                                                        "fontSize": "12px",
                                                        "marginBottom": "2px",
                                                    }),
                                                    html.Div(
                                                        "Time-weighted average where the most "
                                                        "recent reviews carry the greatest "
                                                        "influence. Best reflects current client "
                                                        "sentiment and performance trajectory.",
                                                        style={"fontSize": "11px",
                                                               "marginBottom": "8px"},
                                                    ),
                                                    html.Div(
                                                        "All three methods operate on the "
                                                        "embedding vectors before computing "
                                                        "similarity to each dimension, not on "
                                                        "the final scores.",
                                                        style={"fontSize": "11px",
                                                               "fontStyle": "italic",
                                                               "color": "#6b7280"},
                                                    ),
                                                ], style={
                                                    "marginTop": "8px",
                                                    "padding": "10px 12px",
                                                    "border": "1px solid #e5e7eb",
                                                    "borderRadius": "8px",
                                                    "background": "#fafafa",
                                                    "color": "#1e293b",
                                                    "lineHeight": "1.5",
                                                }),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Button(
                                    "Reset to Macro View",
                                    id="dna-reset-btn",
                                    n_clicks=0,
                                    style={
                                        "marginTop": "12px",
                                        "fontSize": "12px",
                                        "cursor": "pointer",
                                        "background": "none",
                                        "border": "1px solid #ccc",
                                        "borderRadius": "4px",
                                        "padding": "6px 12px",
                                        "width": "100%",
                                    },
                                ),
                            ],
                        ),

                        # Placeholder for non-EDA/non-DNA pages
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


# ---------- Sidebar visibility ----------

@callback(
    Output("sidebar", "style"),
    Output("sidebar-role-badge", "children"),
    Output("eda-filters-section", "style"),
    Output("dna-filters-section", "style"),
    Output("sidebar-page-note", "style"),
    Input("url", "pathname"),
    Input("user-role", "data"),
)
def update_sidebar(pathname, user_role_data):
    pathname = _norm(pathname)
    role, firm_id = _get_role_and_firm(user_role_data)
    hide = {"display": "none"}

    if not role or pathname == "/":
        return hide, "", hide, hide, hide

    cfg = get_role_config(role)
    badge = html.Span(
        cfg.get("label", role.title()),
        style={"fontSize": "11px", "color": "#6b7280", "fontStyle": "italic"})

    allowed = pages_for_role(role)
    eda = {"display": "block"} if pathname == "/eda" and "/eda" in allowed else hide
    dna = {"display": "block"} if pathname == "/advisor-dna" and "/advisor-dna" in allowed else hide
    note = {"display": "block"} if pathname not in ("/eda", "/advisor-dna") else hide

    return {"display": "block"}, badge, eda, dna, note


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


# ---------- EDA sidebar callbacks ----------

@callback(
    Output("eda-entity-search", "options"),
    Output("eda-entity-search", "value"),
    Input("eda-entity-type", "value"),
    Input("eda-reset-btn", "n_clicks"),
    Input("url", "pathname"),
)
def update_eda_entity_options(entity_type, reset_clicks, pathname):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    if trigger == "eda-reset-btn":
        entity_type = entity_type or "firm"

    entity_type = entity_type or "firm"
    entities = get_dna_entities()
    if entity_type == "firm":
        items = entities.get("firms", [])
    else:
        items = entities.get("advisors", [])

    max_len = 60
    options = []
    for e in items:
        full_name = e.get("advisor_name", e.get("advisor_id", ""))
        label = (full_name[:max_len] + "\u2026") if len(full_name) > max_len else full_name
        options.append({
            "label": label,
            "value": e.get("advisor_id", ""),
            "title": full_name,
        })
    options.sort(key=lambda o: o["label"])
    return options, None


@callback(
    Output("eda-date-range", "start_date", allow_duplicate=True),
    Output("eda-date-range", "end_date", allow_duplicate=True),
    Input("eda-date-max-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_date_range_to_max(n_clicks):
    if not n_clicks:
        return no_update, no_update
    return None, None


# ---------- Advisor DNA sidebar callbacks ----------

@callback(
    Output("dna-entity-search", "options"),
    Output("dna-entity-search", "value"),
    Input("dna-entity-type", "value"),
    Input("dna-reset-btn", "n_clicks"),
    Input("url", "pathname"),
)
def update_dna_entity_options(entity_type, reset_clicks, pathname):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else ""

    clear_value = trigger == "dna-reset-btn"

    entity_type = entity_type or "firm"
    entities = get_dna_entities()
    if entity_type == "firm":
        items = entities.get("firms", [])
    else:
        items = entities.get("advisors", [])

    max_len = 60
    options = []
    for e in items:
        full_name = e.get("advisor_name", e.get("advisor_id", ""))
        label = (full_name[:max_len] + "\u2026") if len(full_name) > max_len else full_name
        options.append({
            "label": label,
            "value": e.get("advisor_id", ""),
            "title": full_name,
        })
    options.sort(key=lambda o: o["label"])
    return options, None


@callback(
    Output("dna-method-group", "style"),
    Input("dna-entity-type", "value"),
    Input("dna-entity-search", "value"),
)
def toggle_method_selector(entity_type, entity_id):
    if entity_id:
        return {"display": "block", "marginTop": "12px"}
    return {"display": "none", "marginTop": "12px"}


@callback(
    Output("dna-method-info-panel", "style"),
    Output("dna-method-info-toggle", "children"),
    Input("dna-method-info-toggle", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_method_info(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return {"display": "block"}, "Read less \u25b2"
    return {"display": "none"}, "Read more \u25bc"


@callback(
    Output("dna-current-view", "data"),
    Input("dna-reset-btn", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dna_view(n_clicks):
    if n_clicks:
        return "macro"
    return no_update


# ---------- Entry point ----------

if __name__ == "__main__":
    app.run(debug=True, port=8050)
