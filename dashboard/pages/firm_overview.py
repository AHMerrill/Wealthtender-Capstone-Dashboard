from dash import html
import dash

from dashboard.services.api import get_firm_summary


dash.register_page(__name__, path="/")


def layout():
    summary = get_firm_summary("firm_1")
    return html.Div(
        children=[
            html.H2("Firm Overview"),
            html.Div(
                className="kpi-grid",
                children=[
                    _kpi("Advisor Count", summary.get("advisor_count")),
                    _kpi("Dimensions", summary.get("dimension_count")),
                    _kpi("Avg Score", summary.get("avg_score")),
                    _kpi("Avg Confidence", summary.get("avg_confidence")),
                ],
            ),
            html.Div(
                style={"marginTop": "24px"},
                children="Placeholder for firm-level charts and insights.",
            ),
        ]
    )


def _kpi(label, value):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(label, className="kpi-label"),
            html.Div(value, className="kpi-value"),
        ],
    )
