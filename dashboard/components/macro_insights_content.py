from dash import html, dcc, callback, Input, Output, no_update
import plotly.graph_objects as go

from dashboard.services.api import get_macro_insights
from dashboard.services.brand import get_dataviz_palette
from dashboard.plots.macro_insights_charts import (
    rating_distribution_chart,
    reviews_over_time_chart,
    reviews_per_advisor_hist,
    token_count_hist,
    rating_vs_token_scatter,
    lexical_bar_chart,
)


def macro_content():
    return html.Div(
        children=[
            html.Div(
                className="section",
                children=[
                    html.Div(
                        className="section-header",
                        children=[html.H2("Macro Insights")],
                    ),
                ],
            ),
            html.Div(id="macro-summary-cards", className="kpi-grid"),
            html.Div(id="macro-coverage-cards", className="kpi-grid"),
            html.Div(id="macro-quality-cards", className="kpi-grid"),
            html.Div(
                className="section",
                children=[
                    html.Div("Rating Distribution", className="chart-title"),
                    dcc.Graph(id="macro-rating-dist", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Reviews Over Time", className="chart-title"),
                    dcc.Graph(id="macro-reviews-over-time", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Reviews per Advisor", className="chart-title"),
                    dcc.Graph(id="macro-reviews-per-advisor", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Token Count Distribution", className="chart-title"),
                    dcc.Graph(id="macro-token-counts", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Rating vs Token Count", className="chart-title"),
                    dcc.Graph(id="macro-rating-vs-token", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Top Tokens", className="chart-title"),
                    dcc.Graph(id="macro-top-tokens", className="chart-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Top Bigrams", className="chart-title"),
                    dcc.Graph(id="macro-top-bigrams", className="chart-card"),
                ],
            ),
        ]
    )


@callback(
    Output("macro-summary-cards", "children"),
    Output("macro-coverage-cards", "children"),
    Output("macro-quality-cards", "children"),
    Output("macro-rating-dist", "figure"),
    Output("macro-reviews-over-time", "figure"),
    Output("macro-reviews-per-advisor", "figure"),
    Output("macro-token-counts", "figure"),
    Output("macro-rating-vs-token", "figure"),
    Output("macro-top-tokens", "figure"),
    Output("macro-top-bigrams", "figure"),
    Output("macro-date-range", "start_date"),
    Output("macro-date-range", "end_date"),
    Output("macro-token-range", "min"),
    Output("macro-token-range", "max"),
    Output("macro-token-range", "value"),
    Input("macro-scope", "value"),
    Input("firm-dropdown", "value"),
    Input("macro-date-range", "start_date"),
    Input("macro-date-range", "end_date"),
    Input("macro-rating-filter", "value"),
    Input("macro-token-range", "value"),
)
def update_macro_insights(
    scope,
    firm_id,
    start_date,
    end_date,
    rating_value,
    token_range,
):
    palette = get_dataviz_palette()
    params = {}
    params["preset"] = "eda"
    params["scope"] = scope
    if scope == "firm" and firm_id:
        params["firm_id"] = firm_id
    if start_date:
        params["date_start"] = start_date
    if end_date:
        params["date_end"] = end_date
    if rating_value != "all":
        params["rating"] = rating_value
    if token_range and len(token_range) == 2:
        params["min_tokens"] = token_range[0]
        params["max_tokens"] = token_range[1]

    payload = get_macro_insights(params)
    if not payload:
        empty_fig = go.Figure()
        return (
            [],
            [],
            [],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    summary = payload.get("summary", {})
    coverage = payload.get("coverage", {})
    quality = payload.get("quality", {})
    meta = payload.get("meta", {})

    summary_cards = [
        _kpi("Reviews", summary.get("reviews")),
        _kpi("Advisors", summary.get("advisors")),
        _kpi("Pct < 20 tokens", _pct(summary.get("pct_under_20_tokens"))),
        _kpi("Pct < 50 tokens", _pct(summary.get("pct_under_50_tokens"))),
    ]
    coverage_cards = [
        _kpi("Advisors total", coverage.get("advisors_total")),
        _kpi("Pct advisors < 3", _pct(coverage.get("pct_advisors_lt3"))),
        _kpi("Pct advisors < 5", _pct(coverage.get("pct_advisors_lt5"))),
        _kpi("Pct advisors < 10", _pct(coverage.get("pct_advisors_lt10"))),
    ]
    quality_cards = [
        _kpi("Rows", quality.get("n_rows")),
        _kpi("Advisors", quality.get("n_advisors")),
        _kpi("Rating missing", _pct(quality.get("rating_missing_frac"))),
        _kpi("Text empty", _pct(quality.get("text_empty_frac"))),
    ]

    rating_fig = rating_distribution_chart(payload.get("rating_distribution", []), palette)
    time_fig = reviews_over_time_chart(payload.get("reviews_over_time", []), palette)
    reviews_per_adv = payload.get("reviews_per_advisor", {})
    reviews_fig = reviews_per_advisor_hist(
        reviews_per_adv.get("counts", []),
        reviews_per_adv.get("median"),
        reviews_per_adv.get("p90"),
        palette,
    )
    token_fig = token_count_hist(payload.get("token_counts", []), palette)
    scatter_fig = rating_vs_token_scatter(payload.get("rating_vs_token", []), palette)

    lexical = payload.get("lexical", {})
    top_tokens = lexical.get("top_tokens", [])
    top_bigrams = lexical.get("top_bigrams", [])
    tokens_fig = lexical_bar_chart(top_tokens, "token", palette)
    bigrams_fig = lexical_bar_chart(top_bigrams, "bigram", palette)

    token_min = meta.get("token_min", 0)
    token_max = meta.get("token_max", 1000)
    if token_min is None or token_max is None:
        token_min = 0
        token_max = 1000
    token_value = token_range if token_range else [token_min, token_max]
    start_value = start_date if start_date else meta.get("date_min")
    end_value = end_date if end_date else meta.get("date_max")

    return (
        summary_cards,
        coverage_cards,
        quality_cards,
        rating_fig,
        time_fig,
        reviews_fig,
        token_fig,
        scatter_fig,
        tokens_fig,
        bigrams_fig,
        start_value,
        end_value,
        token_min,
        token_max,
        token_value,
    )


def _kpi(label, value):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(label, className="kpi-label"),
            html.Div(value if value is not None else "—", className="kpi-value"),
        ],
    )


def _pct(value):
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"
