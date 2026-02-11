import dash
from dash import html


dash.register_page(__name__, path="/benchmarks", title="Benchmarks")


def layout():
    return html.Div(
        className="placeholder-page",
        children=[
            html.H2("Benchmarks"),
            html.P(
                "Compare a firm's dimension scores against peer-group "
                "percentiles (P25 / P50 / P75). Benchmark data will appear "
                "once the scoring pipeline produces peer comparisons."
            ),
        ],
    )
