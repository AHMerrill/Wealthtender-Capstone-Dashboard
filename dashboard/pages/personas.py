from dash import html
import dash


dash.register_page(__name__, path="/personas")


def layout():
    return html.Div(
        children=[
            html.H2("Personas"),
            html.Div("Placeholder for advisor personas and distribution."),
        ]
    )
