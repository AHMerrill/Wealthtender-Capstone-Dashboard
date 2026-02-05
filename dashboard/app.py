from dash import Dash, html, dcc
import dash

from dashboard.services.api import get_firms

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
)
app.title = "Wealthtender Dashboard"

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Store(id="selected-firm", storage_type="session"),
        html.Div(
            className="top-nav",
            children=[
                html.Div(
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
                        dcc.Link("Firm Overview", href="/"),
                        dcc.Link("Advisor Detail", href="/advisor"),
                        dcc.Link("Personas", href="/personas"),
                        dcc.Link("Benchmarks", href="/benchmarks"),
                        dcc.Link("Methodology", href="/methodology"),
                    ],
                ),
            ],
        ),
        html.Div(
            className="content-shell",
            children=[
                html.Aside(
                    className="sidebar",
                    children=[
                        html.Div("Firm Selector", className="sidebar-title"),
                        dcc.Dropdown(
                            id="firm-dropdown",
                            options=[{"label": f["firm_id"], "value": f["firm_id"]} for f in get_firms()],
                            placeholder="Select firm",
                        ),
                        html.Div("Filters", className="sidebar-title"),
                        html.Div("(Add filters per view)", className="sidebar-note"),
                    ],
                ),
                html.Main(className="page-container", children=[dash.page_container]),
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
