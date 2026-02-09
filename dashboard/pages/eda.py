import dash
from dash import html


dash.register_page(__name__, path="/eda", name="EDA", title="EDA")


def layout():
    return html.Div()
