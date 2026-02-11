import dash
from dash import html


dash.register_page(__name__, path="/personas", title="Personas")


def layout():
    return html.Div(
        className="placeholder-page",
        children=[
            html.H2("Personas"),
            html.P(
                "Advisor personas (Headliner, Opener, Indie) will be displayed "
                "here as a distribution chart with drill-down. "
                "Requires firm-scoped scoring artifacts."
            ),
        ],
    )
