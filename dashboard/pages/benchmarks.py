from dash import html
import dash


dash.register_page(__name__, path="/benchmarks")


def layout():
    return html.Div(
        children=[
            html.H2("Benchmarks"),
            html.Div("Placeholder for firm vs peer benchmarks."),
        ]
    )
