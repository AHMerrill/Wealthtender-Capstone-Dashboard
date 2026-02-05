from dash import html
import dash


dash.register_page(__name__, path="/methodology")


def layout():
    return html.Div(
        children=[
            html.H2("Methodology"),
            html.Div("Placeholder for scoring definitions, thresholds, and data quality notes."),
        ]
    )
