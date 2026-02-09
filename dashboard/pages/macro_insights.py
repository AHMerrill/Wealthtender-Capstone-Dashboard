import dash
from dash import html


dash.register_page(__name__, path="/macro-insights")


def layout():
    return html.Div()
