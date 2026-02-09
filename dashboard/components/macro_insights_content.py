from dash import html, dcc, callback, Input, Output, no_update
import plotly.graph_objects as go

from dashboard.services.api import get_macro_insights, get_review_detail
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
                        children=[html.H2("EDA")],
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
                    html.Div(id="macro-review-detail", className="review-detail-card"),
                ],
            ),
            html.Div(
                className="section",
                children=[
                    html.Div("Top N-grams", className="chart-title"),
                    dcc.Graph(id="macro-top-ngrams", className="chart-card"),
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
    Output("macro-top-ngrams", "figure"),
    Output("macro-date-range", "start_date"),
    Output("macro-date-range", "end_date"),
    Output("macro-token-range", "min"),
    Output("macro-token-range", "max"),
    Output("macro-token-range", "value"),
    Output("macro-token-range", "marks"),
    Output("macro-review-range", "min"),
    Output("macro-review-range", "max"),
    Output("macro-review-range", "value"),
    Output("macro-review-range", "marks"),
    Input("macro-scope", "value"),
    Input("firm-dropdown", "value"),
    Input("macro-date-range", "start_date"),
    Input("macro-date-range", "end_date"),
    Input("macro-rating-filter", "value"),
    Input("macro-token-range", "value"),
    Input("macro-review-range", "value"),
    Input("macro-ngram-size", "value"),
    Input("macro-ngram-topn", "value"),
    Input("macro-exclude-stopwords", "value"),
)
def update_macro_insights(
    scope,
    firm_id,
    start_date,
    end_date,
    rating_value,
    token_range,
    review_range,
    ngram_size,
    ngram_topn,
    exclude_stopwords,
):
    palette = get_dataviz_palette()
    params = {}
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
    if review_range and len(review_range) == 2:
        params["min_reviews_per_advisor"] = review_range[0]
        params["max_reviews_per_advisor"] = review_range[1]
    if ngram_size:
        params["lexical_n"] = ngram_size
    if ngram_topn:
        params["lexical_top_n"] = ngram_topn
    params["exclude_stopwords"] = bool(exclude_stopwords)

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
    top_ngrams = lexical.get("top_ngrams", [])
    ngrams_fig = lexical_bar_chart(top_ngrams, "ngram", palette)

    token_min = meta.get("token_min", 0)
    token_max = meta.get("token_max", 1000)
    if token_min is None or token_max is None:
        token_min = 0
        token_max = 1000
    token_value = token_range if token_range else [token_min, token_max]
    token_marks = _range_marks(token_min, token_max)
    start_value = start_date if start_date else meta.get("date_min")
    end_value = end_date if end_date else meta.get("date_max")
    review_min = meta.get("reviews_per_advisor_min", 0)
    review_max = meta.get("reviews_per_advisor_max", 50)
    if review_min is None or review_max is None:
        review_min = 0
        review_max = 50
    review_value = review_range if review_range else [review_min, review_max]
    review_marks = _range_marks(review_min, review_max)

    return (
        summary_cards,
        coverage_cards,
        quality_cards,
        rating_fig,
        time_fig,
        reviews_fig,
        token_fig,
        scatter_fig,
        ngrams_fig,
        start_value,
        end_value,
        token_min,
        token_max,
        token_value,
        token_marks,
        review_min,
        review_max,
        review_value,
        review_marks,
    )


@callback(
    Output("macro-review-detail", "children"),
    Input("macro-rating-vs-token", "clickData"),
)
def show_review_detail(click_data):
    if not click_data or "points" not in click_data or not click_data["points"]:
        return _review_placeholder("Click a point to view the review.")
    review_id = click_data["points"][0].get("customdata")
    if not review_id:
        return _review_placeholder("No review data is available for that point.")
    detail = get_review_detail(str(review_id))
    if not detail:
        return _review_placeholder("Review not found.")
    return _review_card(detail)


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


def _review_placeholder(message: str):
    return html.Div(message, className="review-detail-empty")


def _review_card(detail: dict):
    title = detail.get("title") or "Review"
    reviewer = detail.get("reviewer_name") or "Unknown reviewer"
    advisor = detail.get("advisor_name") or "Unknown advisor"
    review_date = detail.get("review_date") or "Unknown date"
    rating = detail.get("rating")
    token_count = detail.get("token_count")
    url = detail.get("review_url")
    content = detail.get("content") or "No review text available."
    meta_bits = [
        f"Reviewer: {reviewer}",
        f"Advisor: {advisor}",
        f"Date: {review_date}",
    ]
    if rating is not None:
        meta_bits.append(f"Rating: {rating}")
    if token_count is not None:
        meta_bits.append(f"Tokens: {token_count}")
    meta_line = " • ".join(meta_bits)
    return html.Div(
        children=[
            html.Div(title, className="review-detail-title"),
            html.Div(meta_line, className="review-detail-meta"),
            html.Div(content, className="review-detail-text"),
            html.A("Open review", href=url, target="_blank", className="review-detail-link")
            if url
            else html.Div("No review link available.", className="review-detail-link"),
        ]
    )


def _range_marks(min_value, max_value):
    if min_value is None or max_value is None:
        return {}
    if min_value == max_value:
        return {min_value: str(min_value)}
    return {min_value: str(min_value), max_value: str(max_value)}
