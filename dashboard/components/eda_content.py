import dash
from dash import html, dcc, callback, Input, Output, no_update
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
            _chart_section("Review Length Distribution", "eda-token-counts"),
            _chart_section(
                "Rating vs Review Length",
                "eda-rating-vs-token",
                extra_children=[
                    html.Div(id="eda-review-detail", className="review-detail-card"),
                ],
            ),
            _chart_section("Top N-grams", "eda-top-ngrams"),
        ]
    )


# ---------------------------------------------------------------------------
# "All" toggle helpers — selecting "All" clears others, selecting a
# category clears "All"
# ---------------------------------------------------------------------------

@callback(
    Output("eda-token-range", "value"),
    Input("eda-token-range", "value"),
    prevent_initial_call=True,
)
def sync_token_all(selected):
    if not selected:
        return ["all"]
    if "all" in selected and len(selected) > 1:
        # User added "all" while categories were selected — keep only "all"
        if selected[-1] == "all":
            return ["all"]
        # User added a category while "all" was selected — drop "all"
        return [v for v in selected if v != "all"]
    return selected


@callback(
    Output("eda-review-range", "value"),
    Input("eda-review-range", "value"),
    prevent_initial_call=True,
)
def sync_review_all(selected):
    if not selected:
        return ["all"]
    if "all" in selected and len(selected) > 1:
        if selected[-1] == "all":
            return ["all"]
        return [v for v in selected if v != "all"]
    return selected


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
    Output("eda-date-range", "start_date", allow_duplicate=True),
    Output("eda-date-range", "end_date", allow_duplicate=True),
    Output("eda-token-range", "options"),
    Output("eda-review-range", "options"),
    Input("eda-entity-search", "value"),
    Input("eda-date-range", "start_date"),
    Input("eda-date-range", "end_date"),
    Input("eda-rating-filter", "value"),
    Input("eda-token-range", "value"),
    Input("eda-review-range", "value"),
    Input("eda-ngram-size", "value"),
    Input("eda-ngram-topn", "value"),
    Input("eda-exclude-stopwords", "value"),
    Input("eda-custom-stopwords", "value"),
    Input("eda-time-freq", "value"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def update_eda_charts(
    entity_id, start_date, end_date, rating_value,
    token_cat, review_cat, ngram_size, ngram_topn,
    exclude_stopwords, custom_stopwords, time_freq, pathname,
):
    if pathname != "/eda":
        raise dash.exceptions.PreventUpdate

    palette = get_dataviz_palette()

    base_params = {"scope": "global"}
    if entity_id:
        base_params["advisor_id"] = entity_id

    # -- Build API query params --
    params = dict(base_params)
    if start_date:
        params["date_start"] = start_date
    if end_date:
        params["date_end"] = end_date
    if rating_value and rating_value != "all":
        params["rating"] = rating_value

    # Map category selections to numeric ranges.
    # We need the meta from a base (unfiltered) call to know the quartiles,
    # but we can use the meta from any call since the base_params are scope-
    # level.  We'll apply category filters after we get meta back.
    # For now, skip token/review filters — we'll add them below after
    # a first call to get quartile info.

    if ngram_size:
        params["lexical_n"] = ngram_size
    if ngram_topn:
        params["lexical_top_n"] = ngram_topn
    params["exclude_stopwords"] = bool(exclude_stopwords)
    if exclude_stopwords and custom_stopwords:
        params["custom_stopwords"] = custom_stopwords
    if time_freq:
        params["time_freq"] = time_freq

    # Normalize multi-select values: dropdown gives a list like ["all"],
    # ["low", "medium"], etc.  Treat empty or ["all"] as no filter.
    token_cats = set(token_cat or ["all"])
    review_cats = set(review_cat or ["all"])
    if "all" in token_cats:
        token_cats = set()
    if "all" in review_cats:
        review_cats = set()

    needs_filter = bool(token_cats) or bool(review_cats)

    if needs_filter:
        # Get base meta with quartiles (no token/review filters)
        base_payload = get_eda_charts(base_params)
        base_meta = (base_payload or {}).get("meta", {})

        # Map selected categories to a combined min/max range
        if token_cats:
            t_min = base_meta.get("token_min", 0) or 0
            t_max = base_meta.get("token_max", 10000) or 10000
            t_q1 = base_meta.get("token_q1", t_min)
            t_q3 = base_meta.get("token_q3", t_max)
            combined_min, combined_max = _categories_to_range(
                token_cats, t_min, t_max, t_q1, t_q3)
            params["min_tokens"] = combined_min
            params["max_tokens"] = combined_max

        if review_cats:
            r_min = base_meta.get("reviews_per_advisor_min", 0) or 0
            r_max = base_meta.get("reviews_per_advisor_max", 1000) or 1000
            r_q1 = base_meta.get("rpa_q1", r_min)
            r_q3 = base_meta.get("rpa_q3", r_max)
            combined_min, combined_max = _categories_to_range(
                review_cats, r_min, r_max, r_q1, r_q3)
            params["min_reviews_per_advisor"] = combined_min
            params["max_reviews_per_advisor"] = combined_max

    payload = get_eda_charts(params)

    # -- Empty state --
    if not payload:
        empty_fig = _empty_figure("Waiting for data...")
        return (
            [_kpi("Reviews", "..."), _kpi("Advisors", "..."),
             _kpi("Pct < 20 words", "..."), _kpi("Pct < 50 words", "...")],
            [_kpi("Advisors total", "..."), _kpi("Pct < 3", "..."),
             _kpi("Pct < 5", "..."), _kpi("Pct < 10", "...")],
            [_kpi("Rows", "..."), _kpi("Advisors", "..."),
             _kpi("Rating missing", "..."), _kpi("Text empty", "...")],
            empty_fig, empty_fig, empty_fig,
            empty_fig, empty_fig, empty_fig,
            *(no_update,) * 4,  # date range + button options
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
        _kpi("Pct < 20 words", _pct(summary.get("pct_under_20_tokens"))),
        _kpi("Pct < 50 words", _pct(summary.get("pct_under_50_tokens"))),
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

    # -- Date picker --
    start_value = start_date if start_date else meta.get("date_min")
    end_value = end_date if end_date else meta.get("date_max")

    # -- Build dynamic button labels from quartile meta --
    # Use base_meta if we fetched it, otherwise use the payload's meta
    q_meta = base_meta if needs_filter else meta
    token_opts = _category_options(
        q_meta.get("token_min"), q_meta.get("token_max"),
        q_meta.get("token_q1"), q_meta.get("token_q3"),
    )
    review_opts = _category_options(
        q_meta.get("reviews_per_advisor_min"), q_meta.get("reviews_per_advisor_max"),
        q_meta.get("rpa_q1"), q_meta.get("rpa_q3"),
    )

    return (
        summary_cards, coverage_cards, quality_cards,
        rating_fig, time_fig, reviews_fig, token_fig, scatter_fig, ngrams_fig,
        start_value, end_value,
        token_opts, review_opts,
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
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "\u2014"


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
        meta_bits.append(f"Words: {token_count}")
    children = [
        html.Div(title, className="review-detail-title"),
        html.Div(" \u2022 ".join(meta_bits), className="review-detail-meta"),
        html.Div(content, className="review-detail-text"),
    ]
    if url:
        children.append(html.A("Open review", href=url, target="_blank", className="review-detail-link"))
    return html.Div(children=children)


def _category_options(data_min, data_max, q1, q3):
    """Build dropdown options with dynamic quartile labels."""
    opts = [{"label": "All", "value": "all"}]
    if data_min is None or data_max is None or q1 is None or q3 is None:
        return opts
    opts.append({"label": f"Low ({data_min}–{q1})", "value": "low"})
    opts.append({"label": f"Med ({q1 + 1}–{q3})", "value": "medium"})
    opts.append({"label": f"High ({q3 + 1}–{data_max})", "value": "high"})
    return opts


def _categories_to_range(cats: set, data_min: int, data_max: int,
                         q1: int, q3: int) -> tuple:
    """Map a set of category selections to a combined (min, max) range.

    When multiple categories are selected (e.g. Low + Medium), the range
    spans the lowest min to the highest max across those categories.
    """
    boundaries = {
        "low": (data_min, q1),
        "medium": (q1 + 1, q3),
        "high": (q3 + 1, data_max),
    }
    mins = []
    maxes = []
    for cat in cats:
        if cat in boundaries:
            lo, hi = boundaries[cat]
            mins.append(lo)
            maxes.append(hi)
    if not mins:
        return data_min, data_max
    return min(mins), max(maxes)
