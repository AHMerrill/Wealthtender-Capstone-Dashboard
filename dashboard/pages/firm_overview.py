import dash
from dash import html


dash.register_page(__name__, path="/firm-overview", title="Firm Overview")


def layout():
    return html.Div(
        className="placeholder-page",
        children=[
            html.H2("Firm Overview"),
            html.P(
                "This view will display firm-level KPIs, dimension scores, "
                "and aggregate advisor performance. Data will populate once "
                "firm-scoped scoring artifacts are available."
            ),
        ],
    )
