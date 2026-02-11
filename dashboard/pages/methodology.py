import dash
from dash import html


dash.register_page(__name__, path="/methodology", title="Methodology")


def layout():
    return html.Div(
        className="placeholder-page",
        children=[
            html.H2("Methodology"),
            html.P(
                "This section will document scoring definitions, threshold logic, "
                "data quality rules, and the review-text processing pipeline. "
                "Content will be added as the scoring methodology is finalised."
            ),
        ],
    )
