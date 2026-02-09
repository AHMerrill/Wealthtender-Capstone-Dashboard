from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import dash
from pathlib import Path

from dashboard.services.api import get_firms
from dashboard.components.macro_insights_content import macro_content
from dashboard.branding import ensure_theme_css

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

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Location(id="url"),
        dcc.Store(id="selected-firm", storage_type="session"),
        html.Div(
            className="top-nav",
            children=[
                html.A(
                    href="https://wealthtender.com",
                    className="brand-block",
                    children=[
                        html.Img(
                            src=app.get_asset_url("brand/logo-mark.svg"),
                            className="brand-mark",
                            alt="Wealthtender mark",
                        ),
                        html.Img(
                            src=app.get_asset_url("brand/logo-wordmark.svg"),
                            className="brand-wordmark",
                            alt="Wealthtender",
                        ),
                    ],
                ),
                html.Div(
                    className="top-nav-links",
                    children=[
                        dcc.Link("Home", href="/"),
                        dcc.Link("EDA", href="/eda"),
                        dcc.Link("Firm Overview", href="/firm-overview"),
                        dcc.Link("Advisor Detail", href="/advisor"),
                        dcc.Link("Personas", href="/personas"),
                        dcc.Link("Benchmarks", href="/benchmarks"),
                        dcc.Link("Methodology", href="/methodology"),
                    ],
                ),
            ],
        ),
        html.Div(
            id="content-shell",
            className="content-shell",
            children=[
                html.Aside(id="sidebar", className="sidebar"),
                html.Main(
                    className="page-container",
                    children=[
                        html.Div(id="macro-shell", children=macro_content()),
                        html.Div(id="page-shell", children=[dash.page_container]),
                    ],
                ),
            ],
        ),
    ],
)


@callback(
    Output("firm-dropdown", "options"),
    Output("firm-dropdown", "value"),
    Input("firm-dropdown", "value"),
    State("firm-dropdown", "options"),
)
def load_firm_options(selected_value, current_options):
    if current_options:
        return no_update, no_update
    firms = get_firms()
    options = [{"label": f["firm_id"], "value": f["firm_id"]} for f in firms]
    if not options:
        options = [{"label": "No firms available", "value": "__none__", "disabled": True}]
    default_value = selected_value or (options[0]["value"] if options else None)
    return options, default_value


@callback(
    Output("sidebar", "children"),
    Input("url", "pathname"),
)
def render_sidebar(pathname):
    header = html.Div(
        className="sidebar-header",
        children=[html.Div("Filters", className="sidebar-title")],
    )

    firm_selector = html.Div(
        className="filter-group",
        style={"marginTop": "12px"},
        children=[
            html.Div("Firm Selector", className="filter-label"),
            dcc.Dropdown(
                id="firm-dropdown",
                placeholder="Select firm",
                searchable=False,
            ),
        ],
    )
    macro_filters = html.Div(
        className="sidebar-section",
        style={"display": "block" if pathname == "/eda" else "none"},
        children=[
            html.Div(
                className="filter-group",
                children=[
                    html.Div("Scope", className="filter-label"),
                    dcc.RadioItems(
                        id="macro-scope",
                        options=[
                            {"label": "Global", "value": "global"},
                            {"label": "Firm", "value": "firm"},
                        ],
                        value="global",
                        inline=False,
                    ),
                ],
            ),
            firm_selector,
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Rating", className="filter-label"),
                    dcc.Dropdown(
                        id="macro-rating-filter",
                        options=[{"label": "All", "value": "all"}]
                        + [{"label": str(i), "value": float(i)} for i in range(1, 6)],
                        value="all",
                        clearable=False,
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Reviews per Advisor", className="filter-label"),
                    dcc.RangeSlider(
                        id="macro-review-range",
                        min=0,
                        max=50,
                        step=1,
                        value=[0, 50],
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Date Range", className="filter-label"),
                    dcc.DatePickerRange(
                        id="macro-date-range",
                        start_date=None,
                        end_date=None,
                        display_format="YYYY-MM-DD",
                        start_date_placeholder_text="Start",
                        end_date_placeholder_text="End",
                        style={"width": "100%"},
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Token Count", className="filter-label"),
                    dcc.RangeSlider(
                        id="macro-token-range",
                        min=0,
                        max=1000,
                        step=10,
                        value=[0, 1000],
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("N-gram Size", className="filter-label"),
                    dcc.Dropdown(
                        id="macro-ngram-size",
                        options=[
                            {"label": "1-gram", "value": 1},
                            {"label": "2-gram", "value": 2},
                            {"label": "3-gram", "value": 3},
                        ],
                        value=1,
                        clearable=False,
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Top N", className="filter-label"),
                    dcc.Slider(
                        id="macro-ngram-topn",
                        min=10,
                        max=50,
                        step=5,
                        value=20,
                        marks={10: "10", 20: "20", 30: "30", 40: "40", 50: "50"},
                    ),
                ],
            ),
            html.Div(
                className="filter-group",
                style={"marginTop": "12px"},
                children=[
                    html.Div("Exclude Stopwords", className="filter-label"),
                    dcc.Checklist(
                        id="macro-exclude-stopwords",
                        options=[{"label": "Exclude common words", "value": "exclude"}],
                        value=["exclude"],
                    ),
                ],
            ),
        ],
    )

    default_filters = html.Div(
        style={"display": "none" if pathname == "/eda" else "block"},
        children=[
            firm_selector,
            html.Div("(Page filters will appear here)", className="sidebar-note"),
        ],
    )

    return [header, macro_filters, default_filters]


@callback(
    Output("macro-shell", "style"),
    Output("page-shell", "style"),
    Input("url", "pathname"),
)
def toggle_macro_shell(pathname):
    if pathname == "/eda":
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}


if __name__ == "__main__":
    app.run(debug=True, port=8050)
