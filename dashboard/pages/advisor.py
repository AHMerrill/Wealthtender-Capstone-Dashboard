import dash
from dash import html


dash.register_page(__name__, path="/advisor", title="Advisor Detail")


def layout():
    return html.Div(
        className="placeholder-page",
        children=[
            html.H2("Advisor Detail"),
            html.P(
                "Select an advisor to view their individual scorecard, "
                "benchmark comparison, and extracted review themes. "
                "This page activates once advisor-level artifacts are loaded."
            ),
        ],
    )
