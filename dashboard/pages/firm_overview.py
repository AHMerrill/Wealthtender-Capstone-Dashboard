from dash import html
import dash


dash.register_page(__name__, path="/firm-overview")


def layout():
    return html.Div(
        children=[
            html.H2("Firm Overview"),
            html.Div("Placeholder for firm overview KPIs and charts."),
        ]
    )
