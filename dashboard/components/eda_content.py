import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard.services.api import get_eda_charts, get_review_detail
from dashboard.services.brand import get_dataviz_palette
from dashboard.plots.eda_charts import (
    rating_distribution_chart,
    reviews_over_time_chart,
    reviews_per_advisor_hist,
    token_count_hist,
    rating_vs_token_scatter,
    lexical_bar_chart,
)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def _chart_section(title: str, graph_id: str, extra_children=None):
    """Wrap a chart in a titled section with a Loading spinner."""
    children = [
        html.Div(title, className="chart-title"),
        dcc.Loading(
            type="circle",
            color="#004C8C",
            children=dcc.Graph(id=graph_id, className="chart-card"),
        ),
    ]
    if extra_children:
        children.extend(extra_children)
    return html.Div(className="section", children=children)


def eda_content():
    return html.Div(
        children=[
            # -- Header --
            html.Div(
                className="section",
                children=[
                    html.Div(
                        className="section-header",
                        children=[html.H2("Exploratory Data Analysis")],
                    ),
                ],
            ),

            # -- KPI rows (with loading) --
            html.Div("Summary", className="chart-title", style={"marginTop": "16px"}),
            dcc.Loading(
                type="circle",
                color="#004C8C",
                children=html.Div(id="eda-summary-cards", className="kpi-grid"),
            ),

            html.Div("Coverage", className="chart-title", style={"marginTop": "16px"}),
            dcc.Loading(
                type="circle",
                color="#004C8C",
                children=html.Div(id="eda-coverage-cards", className="kpi-grid"),
            ),

            html.Div("Data Quality", className="chart-title", style={"marginTop": "16px"}),
            dcc.Loading(
                type="circle",
                color="#004C8C",
                children=html.Div(id="eda-quality-cards", className="kpi-grid"),
            ),

            # -- Charts --
            _chart_section("Rating Distribution", "eda-rating-dist"),
            _chart_section("Reviews Over Time", "eda-reviews-over-time"),
            _chart_section("Reviews per Advisor", "eda-reviews-per-advisor"),
            _chart_section("Token Count Distribution", "eda-token-counts"),
            _chart_section(
                "Rating vs Token Count",
                "eda-rating-vs-token",
                extra_children=[
                    html.Div(id="eda-review-detail", className="review-detail-card"),
                ],
            ),
            _chart_section("Top N-grams", "eda-top-ngrams"),
        ]
    )


# ---------------------------------------------------------------------------
# Main EDA callback
# ---------------------------------------------------------------------------

@callback(
    Output("eda-summary-cards", "children"),
    Output("eda-coverage-cards", "children"),
    Output("eda-quality-cards", "children"),
    Output("eda-rating-dist", "figure"),
    Output("eda-reviews-over-time", "figure"),
    Output("eda-reviews-per-advisor", "figure"),
    Output("eda-token-counts", "figure"),
    Output("eda-rating-vs-token", "figure"),
    Output("eda-top-ngrams", "figure"),
    Output("eda-date-range", "start_date"),
    Output("eda-date-range", "end_date"),
    Output("eda-token-range", "min"),
    Output("eda-token-range", "max"),
    Output("eda-token-range", "value"),
    Output("eda-token-range", "marks"),
    Output("eda-review-range", "min"),
    Output("eda-review-range", "max"),
    Output("eda-review-range", "value"),
    Output("eda-review-range", "marks"),
    Output("eda-sliders-initialized", "data"),
    Input("eda-scope", "value"),
    Input("firm-dropdown", "value"),
    Input("eda-date-range", "start_date"),
    Input("eda-date-range", "end_date"),
    Input("eda-rating-filter", "value"),
    Input("eda-token-range", "value"),
    Input("eda-review-range", "value"),
    Input("eda-ngram-size", "value"),
    Input("eda-ngram-topn", "value"),
    Input("eda-exclude-stopwords", "value"),
    Input("eda-custom-stopwords", "value"),
    Input("url", "pathname"),
    State("eda-sliders-initialized", "data"),
    prevent_initial_call=True,
)
def update_eda_charts(
    scope, firm_id, start_date, end_date, rating_value,
    token_range, review_range, ngram_size, ngram_topn,
    exclude_stopwords, custom_stopwords, pathname,
    sliders_initialized,
):
    # Don't run when EDA page isn't loaded (outputs don't exist yet)
    if pathname != "/eda":
        raise dash.exceptions.PreventUpdate

    palette = get_dataviz_palette()

    # -- Build API query params --
    params = {"scope": scope}
    if scope == "firm" and firm_id:
        params["firm_id"] = firm_id
    if start_date:
        params["date_start"] = start_date
    if end_date:
        params["date_end"] = end_date
    if rating_value != "all":
        params["rating"] = rating_value
    # Only send slider values as filters AFTER the first successful load.
    # On the first fire the sliders still hold layout placeholders (e.g.
    # [0, 50] for reviews, [0, 1000] for tokens).  Sending those would
    # incorrectly constrain the data.  After the first load we replace
    # them with the real data range and set sliders_initialized = True.
    if sliders_initialized:
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
    # Only send custom_stopwords when user has explicitly picked specific words.
    # Empty list = use full NLTK defaults (handled server-side).
    if exclude_stopwords and custom_stopwords:
        params["custom_stopwords"] = custom_stopwords
    # (when exclude is on but custom_stopwords is empty/None, the API uses
    #  the full NLTK set -- no custom_stopwords param needed)

    payload = get_eda_charts(params)

    # -- Empty state --
    if not payload:
        empty_fig = _empty_figure("Waiting for data...")
        return (
            [_kpi("Reviews", "..."), _kpi("Advisors", "..."),
             _kpi("Pct < 20 tokens", "..."), _kpi("Pct < 50 tokens", "...")],
            [_kpi("Advisors total", "..."), _kpi("Pct < 3", "..."),
             _kpi("Pct < 5", "..."), _kpi("Pct < 10", "...")],
            [_kpi("Rows", "..."), _kpi("Advisors", "..."),
             _kpi("Rating missing", "..."), _kpi("Text empty", "...")],
            empty_fig, empty_fig, empty_fig,
            empty_fig, empty_fig, empty_fig,
            *(no_update,) * 10,
            no_update,  # sliders_initialized stays as-is
        )

    # -- Unpack payload --
    summary = payload.get("summary", {})
    coverage = payload.get("coverage", {})
    quality = payload.get("quality", {})
    meta = payload.get("meta", {})

    # -- KPI cards --
    summary_cards = [
        _kpi("Reviews", _fmt_int(summary.get("reviews"))),
        _kpi("Advisors", _fmt_int(summary.get("advisors"))),
        _kpi("Pct < 20 tokens", _pct(summary.get("pct_under_20_tokens"))),
        _kpi("Pct < 50 tokens", _pct(summary.get("pct_under_50_tokens"))),
    ]
    coverage_cards = [
        _kpi("Advisors total", _fmt_int(coverage.get("advisors_total"))),
        _kpi("Pct advisors < 3", _pct(coverage.get("pct_advisors_lt3"))),
        _kpi("Pct advisors < 5", _pct(coverage.get("pct_advisors_lt5"))),
        _kpi("Pct advisors < 10", _pct(coverage.get("pct_advisors_lt10"))),
    ]
    quality_cards = [
        _kpi("Rows", _fmt_int(quality.get("n_rows"))),
        _kpi("Advisors", _fmt_int(quality.get("n_advisors"))),
        _kpi("Rating missing", _pct(quality.get("rating_missing_frac"))),
        _kpi("Text empty", _pct(quality.get("text_empty_frac"))),
    ]

    # -- Charts --
    rating_fig = rating_distribution_chart(payload.get("rating_distribution", []), palette)
    time_fig = reviews_over_time_chart(payload.get("reviews_over_time", []), palette)
    rpa = payload.get("reviews_per_advisor", {})
    reviews_fig = reviews_per_advisor_hist(
        rpa.get("counts", []), rpa.get("median"), rpa.get("p90"), palette,
    )
    token_fig = token_count_hist(payload.get("token_counts", []), palette)
    scatter_fig = rating_vs_token_scatter(payload.get("rating_vs_token", []), palette)
    ngrams_fig = lexical_bar_chart(
        payload.get("lexical", {}).get("top_ngrams", []), "ngram", palette,
    )

    # -- Slider / date-picker meta updates --
    token_min = meta.get("token_min", 0) or 0
    token_max = meta.get("token_max", 1000) or 1000
    # Always snap to full data range — user adjustments trigger a new call
    # which returns filtered meta, so the sliders stay consistent.
    token_value = [token_min, token_max]

    start_value = start_date if start_date else meta.get("date_min")
    end_value = end_date if end_date else meta.get("date_max")

    review_min = meta.get("reviews_per_advisor_min", 0) or 0
    review_max = meta.get("reviews_per_advisor_max", 50) or 50
    review_value = [review_min, review_max]

    return (
        summary_cards, coverage_cards, quality_cards,
        rating_fig, time_fig, reviews_fig, token_fig, scatter_fig, ngrams_fig,
        start_value, end_value,
        token_min, token_max, token_value, _range_marks(token_min, token_max),
        review_min, review_max, review_value, _range_marks(review_min, review_max),
        True,  # mark sliders as initialized so future fires send filters
    )


# ---------------------------------------------------------------------------
# Review detail click callback
# ---------------------------------------------------------------------------

@callback(
    Output("eda-review-detail", "children"),
    Input("eda-rating-vs-token", "clickData"),
    prevent_initial_call=True,
)
def show_review_detail(click_data):
    if not click_data or "points" not in click_data or not click_data["points"]:
        return _review_placeholder("Click a point on the scatter plot to view the full review.")
    review_id = click_data["points"][0].get("customdata")
    if not review_id:
        return _review_placeholder("No review data is available for that point.")
    detail = get_review_detail(str(review_id))
    if not detail:
        return _review_placeholder("Review not found.")
    return _review_card(detail)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_figure(annotation: str = "") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=200, margin=dict(l=24, r=24, t=24, b=24),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(
            text=annotation, xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#6b7280"),
        )] if annotation else [],
    )
    return fig


def _kpi(label: str, value):
    return html.Div(className="kpi-card", children=[
        html.Div(label, className="kpi-label"),
        html.Div(str(value) if value is not None else "\u2014", className="kpi-value"),
    ])


def _fmt_int(value) -> str:
    if value is None:
        return "\u2014"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _pct(value) -> str:
    if value is None:
        return "\u2014"
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
    meta_bits = [f"Reviewer: {reviewer}", f"Advisor: {advisor}", f"Date: {review_date}"]
    if rating is not None:
        meta_bits.append(f"Rating: {rating}")
    if token_count is not None:
        meta_bits.append(f"Tokens: {token_count}")
    children = [
        html.Div(title, className="review-detail-title"),
        html.Div(" \u2022 ".join(meta_bits), className="review-detail-meta"),
        html.Div(content, className="review-detail-text"),
    ]
    if url:
        children.append(html.A("Open review", href=url, target="_blank", className="review-detail-link"))
    return html.Div(children=children)


def _range_marks(mn, mx):
    if mn is None or mx is None:
        return {}
    if mn == mx:
        return {mn: str(mn)}
    return {mn: str(mn), mx: str(mx)}
