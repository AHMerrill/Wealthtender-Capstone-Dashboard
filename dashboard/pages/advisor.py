from dash import html
import dash


dash.register_page(__name__, path="/advisor")


def layout():
    return html.Div(
        children=[
            html.H2("Advisor Detail"),
            html.Div("Placeholder for advisor scorecard, benchmark, and themes."),
        ]
    )
