import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.services.api import (
    get_dna_macro_totals,
    get_dna_entity_reviews,
    get_dna_advisor_scores,
)

dash.register_page(__name__, path="/advisor-dna", title="Advisor DNA")

DIMENSIONS = [
    "trust_integrity",
    "listening_personalization",
    "communication_clarity",
    "responsiveness_availability",
    "life_event_support",
    "investment_expertise",
]

DIM_LABELS = {
    "trust_integrity": "Trust & Integrity",
    "listening_personalization": "Listening & Personalization",
    "communication_clarity": "Communication Clarity",
    "responsiveness_availability": "Responsiveness",
    "life_event_support": "Life Event Support",
    "investment_expertise": "Investment Expertise",
}

DIM_COLORS = {
    "trust_integrity": DATA_VIZ_PALETTE[0],
    "listening_personalization": DATA_VIZ_PALETTE[1],
    "communication_clarity": DATA_VIZ_PALETTE[2],
    "responsiveness_availability": DATA_VIZ_PALETTE[3],
    "life_event_support": DATA_VIZ_PALETTE[5],
    "investment_expertise": DATA_VIZ_PALETTE[6],
}

DIM_DESCRIPTIONS = {
    "trust_integrity": "Clients feel confident their advisor acts honestly and in their best interest.",
    "listening_personalization": "Advisors tailor plans to individual goals after genuinely listening.",
    "communication_clarity": "Complex financial concepts are explained in plain, understandable language.",
    "responsiveness_availability": "Advisors are accessible and respond promptly to client needs.",
    "life_event_support": "Guidance through major transitions \u2014 retirement, inheritance, career changes.",
    "investment_expertise": "Demonstrated knowledge of markets, portfolios, and financial strategy.",
}

DIM_QUERY_TEXTS = {
    "trust_integrity": "I feel a deep sense of security and peace of mind because my advisor acts as a true fiduciary, always putting my best interest before their own commissions or conflicts of interest. They have earned my trust through years of unwavering integrity, honesty, and transparency regarding fees and performance, proving they are an ethical, principled, and reliable professional with a stand-up character who protects my family\u2019s future and life savings.",
    "listening_personalization": "My advisor takes the time to truly listen, hear my concerns, and understand my unique goals and risk tolerance. They have built a highly personalized, custom-tailored financial plan and investment strategy that fits my specific situation, aspirations, and values, making me feel like a valued partner rather than just another account number or a sales target.",
    "communication_clarity": "Complex financial concepts are made simple and digestible because my advisor is a master communicator who explains things clearly in plain English without using confusing technical jargon. They provide timely updates, regular check-ins, and transparent breakdowns of my portfolio, ensuring I am well-educated, fully informed, and confident in the logic and rationale behind every recommendation or financial decision.",
    "responsiveness_availability": "The level of service is exceptional; they are always accessible, easy to reach, and promptly return calls or emails within hours, not days. Whether I have a quick question or an urgent concern during market volatility or a personal crisis, they are responsive, attentive, and reliable, providing the immediate support and availability I need to feel taken care of and less anxious about my liquidity and financial health.",
    "life_event_support": "Beyond being a numbers person, they have been a compassionate counselor and supportive partner through major life transitions, including retirement, career changes, marriages, inheritance, or the loss of a loved one. They provide empathy, patience, and guidance during emotional times, offering perspective and hand-holding that goes far beyond a spreadsheet to address the human element and life context of my wealth management.",
    "investment_expertise": "I have total confidence in their technical proficiency, investment pedigree, and deep market knowledge. They are a savvy, highly skilled professional with the credentials and expertise to navigate complex asset allocations, tax strategies, and market cycles. Their competence and strategic insight ensure my portfolio is well-positioned for long-term growth, wealth preservation, and solid returns that meet or exceed my financial expectations.",
}

_DIM_LABEL_TO_KEY = {v: k for k, v in DIM_LABELS.items()}


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _build_pie(dim_totals, review_count, title="Dimension Strength"):
    grand = sum(dim_totals.values()) or 1
    labels = [DIM_LABELS[d] for d in DIMENSIONS]
    values = [dim_totals.get(d, 0) for d in DIMENSIONS]
    colors = [DIM_COLORS[d] for d in DIMENSIONS]
    pcts = [dim_totals.get(d, 0) / grand for d in DIMENSIONS]
    hovers = [
        f"<b>{DIM_LABELS[d]}</b><br>"
        f"Score: {dim_totals.get(d, 0):.3f}<br>"
        f"{pcts[i]:.1%} of overall<br><br>"
        f"<i>{DIM_DESCRIPTIONS[d]}</i>"
        for i, d in enumerate(DIMENSIONS)
    ]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        pull=[0.05] * len(DIMENSIONS),
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(size=13, family=FONT_FAMILY, color=COLORS["ink"]),
        hovertext=hovers,
        hoverinfo="text",
        hole=0.35,
        sort=False,
    )])
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=COLORS["ink"]),
        showlegend=False,
        margin=dict(l=40, r=40, t=50, b=20),
        height=480,
        paper_bgcolor="white",
        plot_bgcolor="white",
        title=dict(text=title, font=dict(size=16, color=COLORS["navy"]), x=0.5),
        annotations=[dict(
            text=f"<b>{review_count:,}</b><br>reviews",
            x=0.5, y=0.5, font_size=14, showarrow=False,
            font=dict(family=FONT_FAMILY, color=COLORS["gray"]),
        )],
    )
    return fig


def _build_deviation_bars(dim_totals):
    """Horizontal bar chart showing each dimension's % vs the ideal 16.7% even split."""
    grand = sum(dim_totals.values()) or 1
    ideal = 1.0 / len(DIMENSIONS)

    dims_sorted = sorted(DIMENSIONS, key=lambda d: dim_totals.get(d, 0) / grand, reverse=True)
    labels = [DIM_LABELS[d] for d in dims_sorted]
    pcts = [dim_totals.get(d, 0) / grand for d in dims_sorted]
    deviations = [p - ideal for p in pcts]
    bar_colors = [
        DIM_COLORS[d] for d in dims_sorted
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels,
        x=[dev * 100 for dev in deviations],
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{p:.1%}" for p in pcts],
        textposition="outside",
        textfont=dict(size=11, family=FONT_FAMILY, color=COLORS["ink"]),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Actual: %{text}<br>"
            f"Ideal: {ideal:.1%}<br>"
            "Deviation: %{x:+.1f}pp"
            "<extra></extra>"
        ),
    ))
    fig.add_vline(x=0, line_width=1, line_dash="dot", line_color=COLORS["gray"])
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=COLORS["ink"]),
        xaxis=dict(
            title="Deviation from even split (pp)",
            titlefont=dict(size=11),
            ticksuffix="pp",
            zeroline=True,
            gridcolor=COLORS["border"],
        ),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=30, t=30, b=40),
        height=220,
        paper_bgcolor="white",
        plot_bgcolor="white",
        title=dict(
            text="Attribute Balance vs Even Split (16.7% each)",
            font=dict(size=13, color=COLORS["navy"]),
            x=0.5,
        ),
    )
    return fig


def _build_radar_figure(scores, title="Dimension Scores"):
    labels = [DIM_LABELS[d] for d in DIMENSIONS]
    values = [scores.get(d, 0) or 0 for d in DIMENSIONS]
    colors_list = [DIM_COLORS[d] for d in DIMENSIONS]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        line=dict(color=COLORS["blue"], width=2),
        fillcolor="rgba(0, 76, 140, 0.08)",
        hoverinfo="skip",
        showlegend=False,
    ))
    for i, d in enumerate(DIMENSIONS):
        fig.add_trace(go.Scatterpolar(
            r=[values[i]],
            theta=[labels[i]],
            mode="markers+text",
            marker=dict(color=colors_list[i], size=10, symbol="circle"),
            text=[f"{values[i]:.0%}"],
            textposition="top center",
            textfont=dict(size=11, color=colors_list[i], family=FONT_FAMILY),
            hovertemplate=f"<b>{DIM_LABELS[d]}</b>: {values[i]:.0%}<extra></extra>",
            showlegend=False,
        ))

    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=COLORS["ink"]),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1],
                            gridcolor=COLORS["border"],
                            linecolor=COLORS["border"]),
            angularaxis=dict(gridcolor=COLORS["border"],
                             linecolor=COLORS["border"],
                             tickfont=dict(size=11)),
            bgcolor="white",
        ),
        showlegend=False,
        title=dict(text=title, font=dict(size=14, color=COLORS["ink"])),
        margin=dict(l=60, r=60, t=50, b=40),
        height=400,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig


# ---------------------------------------------------------------------------
# Description cards
# ---------------------------------------------------------------------------

def _build_dim_description_cards(id_prefix):
    """Build clickable dimension cards. id_prefix differentiates macro vs entity."""
    cards = []
    for d in DIMENSIONS:
        cards.append(html.Button(
            id={"type": f"{id_prefix}-dim-card", "dim": d},
            style={
                "padding": "8px 10px",
                "borderRadius": "6px",
                "border": f"2px solid {DIM_COLORS[d]}",
                "backgroundColor": "white",
                "cursor": "pointer",
                "textAlign": "left",
                "width": "100%",
            },
            children=[
                html.Div(DIM_LABELS[d], style={
                    "fontWeight": "700", "fontSize": "11px",
                    "color": DIM_COLORS[d], "marginBottom": "3px",
                }),
                html.Div(DIM_DESCRIPTIONS[d], style={
                    "fontSize": "10px", "lineHeight": "1.3",
                    "color": COLORS["ink"],
                }),
            ],
        ))
    return cards


# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------

_HIDE = {"display": "none"}
_SHOW = {"display": "block"}

_PANEL_STYLE = {
    "marginTop": "16px", "padding": "20px", "borderRadius": "8px",
    "backgroundColor": COLORS["card_bg"],
    "border": f"1px solid {COLORS['border']}",
}


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def _desc_grid(prefix):
    return html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(6, 1fr)",
            "gap": "10px",
            "marginTop": "16px",
        },
        children=_build_dim_description_cards(prefix),
    )


def layout():
    return html.Div(
        className="advisor-dna-page",
        style={"padding": "20px", "fontFamily": FONT_FAMILY},
        children=[
            dcc.Store(id="dna-current-view", data="macro"),
            dcc.Store(id="dna-graph-data", data=[]),
            dcc.Store(id="dna-entity-reviews-store", data=[]),
            dcc.Store(id="dna-selected-dim", data=None),

            html.H2("Advisor DNA", style={
                "marginBottom": "4px", "color": COLORS["navy"],
                "fontFamily": FONT_FAMILY,
            }),
            html.P(
                "Advisor-dimension similarity scores derived from client reviews. "
                "Select a firm or advisor from the sidebar to drill down.",
                style={"color": COLORS["gray"], "fontSize": "13px",
                       "marginBottom": "16px", "fontFamily": FONT_FAMILY},
            ),

            html.Div(
                id="dna-view-label",
                style={"fontWeight": "600", "marginBottom": "8px",
                       "fontSize": "14px", "color": COLORS["ink"],
                       "fontFamily": FONT_FAMILY},
                children="Macro View \u2014 Dimension Overview",
            ),

            # ---- Macro section ----
            html.Div(
                id="dna-macro-section",
                children=[
                    dcc.Graph(
                        id="dna-macro-chart",
                        figure=go.Figure(),
                        config={"displayModeBar": False},
                    ),
                    _desc_grid("macro"),
                    html.Div(
                        id="dna-query-detail",
                        style=_HIDE,
                        children=[
                            html.Div(id="dna-query-title", style={
                                "fontWeight": "700", "fontSize": "15px",
                                "marginBottom": "8px",
                            }),
                            html.Div(
                                "Embedding Query \u2014 the text each review is compared against:",
                                style={"fontSize": "12px", "color": COLORS["gray"],
                                       "marginBottom": "8px", "fontStyle": "italic"},
                            ),
                            html.Div(id="dna-query-text", style={
                                "fontSize": "13px", "lineHeight": "1.6",
                                "color": COLORS["ink"], "fontFamily": FONT_FAMILY,
                            }),
                        ],
                    ),
                ],
            ),

            # ---- Entity section (firm / advisor) ----
            html.Div(
                id="dna-entity-section",
                style=_HIDE,
                children=[
                    dcc.Graph(
                        id="dna-entity-chart",
                        figure=go.Figure(),
                        config={"displayModeBar": False},
                    ),
                    dcc.Graph(
                        id="dna-deviation-bars",
                        figure=go.Figure(),
                        config={"displayModeBar": False},
                        style={"marginTop": "8px"},
                    ),
                    _desc_grid("entity"),
                    # Attribute detail: definition + review list
                    html.Div(
                        id="dna-attr-panel",
                        style=_HIDE,
                        children=[
                            html.Div(id="dna-attr-title", style={
                                "fontWeight": "700", "fontSize": "15px",
                                "marginBottom": "8px",
                            }),
                            html.Div(id="dna-attr-query", style={
                                "fontSize": "13px", "lineHeight": "1.6",
                                "color": COLORS["ink"], "fontFamily": FONT_FAMILY,
                                "marginBottom": "16px", "fontStyle": "italic",
                            }),
                            html.Div("Select a review to see full details:", style={
                                "fontSize": "12px", "color": COLORS["gray"],
                                "marginBottom": "6px",
                            }),
                            dcc.Dropdown(
                                id="dna-review-selector",
                                placeholder="Choose a review...",
                                searchable=True,
                                clearable=True,
                                style={"marginBottom": "12px"},
                            ),
                        ],
                    ),
                    # Review detail: text + spider side by side
                    html.Div(
                        id="dna-review-panel",
                        style=_HIDE,
                        children=[
                            html.Div(
                                style={"display": "flex", "justifyContent": "space-between",
                                       "alignItems": "center", "marginBottom": "12px"},
                                children=[
                                    html.H3(id="dna-review-title", style={
                                        "margin": "0", "color": COLORS["navy"],
                                        "fontFamily": FONT_FAMILY,
                                    }),
                                    html.Button("Close", id="dna-close-review",
                                                style={
                                                    "fontSize": "12px", "cursor": "pointer",
                                                    "background": "none",
                                                    "border": f"1px solid {COLORS['border']}",
                                                    "borderRadius": "4px",
                                                    "padding": "4px 12px",
                                                    "color": COLORS["ink"],
                                                    "fontFamily": FONT_FAMILY,
                                                }),
                                ],
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "24px", "flexWrap": "wrap"},
                                children=[
                                    html.Div(
                                        style={"flex": "1", "minWidth": "300px"},
                                        children=[
                                            html.Div("Review Text", style={
                                                "fontWeight": "600", "marginBottom": "8px",
                                                "fontSize": "13px", "color": COLORS["navy"],
                                            }),
                                            html.Div(
                                                id="dna-review-text",
                                                style={
                                                    "fontSize": "13px", "lineHeight": "1.7",
                                                    "color": COLORS["ink"],
                                                    "fontFamily": FONT_FAMILY,
                                                    "padding": "16px",
                                                    "backgroundColor": "white",
                                                    "borderRadius": "8px",
                                                    "border": f"1px solid {COLORS['border']}",
                                                    "maxHeight": "360px",
                                                    "overflowY": "auto",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        style={"flex": "1", "minWidth": "300px"},
                                        children=[
                                            dcc.Graph(
                                                id="dna-review-radar",
                                                figure=go.Figure(),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Main view callback — switches between macro / firm / advisor
# ---------------------------------------------------------------------------

@callback(
    Output("dna-macro-section", "style"),
    Output("dna-macro-chart", "figure"),
    Output("dna-entity-section", "style"),
    Output("dna-entity-chart", "figure"),
    Output("dna-deviation-bars", "figure"),
    Output("dna-view-label", "children"),
    Output("dna-entity-reviews-store", "data"),
    Output("dna-attr-panel", "style", allow_duplicate=True),
    Output("dna-review-panel", "style", allow_duplicate=True),
    Output("dna-review-selector", "options", allow_duplicate=True),
    Output("dna-review-selector", "value", allow_duplicate=True),
    Output("dna-query-detail", "style", allow_duplicate=True),
    Input("dna-current-view", "data"),
    Input("dna-entity-search", "value"),
    Input("dna-method-selector", "value"),
    State("dna-entity-type", "value"),
    prevent_initial_call="initial_duplicate",
)
def update_main_view(current_view, entity_id, method, entity_type):
    empty_fig = go.Figure()

    if entity_id:
        reviews = get_dna_entity_reviews(entity_id)
        if not reviews:
            label = "No reviews found for this entity."
            return (_HIDE, empty_fig, _SHOW, empty_fig, empty_fig,
                    label, [], _HIDE, _HIDE, [], None, _HIDE)

        name = reviews[0].get("advisor_name", entity_id)
        kind = "Firm" if entity_type == "firm" else "Advisor"
        method_label = (method or "mean").capitalize()

        agg = get_dna_advisor_scores(entity_id, method or "mean")
        if agg and "scores" in agg:
            dim_totals = {d: agg["scores"].get(d, 0) for d in DIMENSIONS}
        else:
            dim_totals = {d: sum(r.get(f"sim_{d}", 0) or 0 for r in reviews)
                          for d in DIMENSIONS}

        title = f"{name} \u2014 {method_label} Scores"
        pie = _build_pie(dim_totals, len(reviews), title=title)
        dev_bars = _build_deviation_bars(dim_totals)

        return (
            _HIDE, empty_fig,
            _SHOW, pie, dev_bars,
            f"{kind} View \u2014 {name} ({len(reviews)} reviews, {method_label})",
            reviews,
            _HIDE, _HIDE, [], None, _HIDE,
        )

    macro_data = get_dna_macro_totals()
    if not macro_data or "totals" not in macro_data:
        return (_SHOW, empty_fig, _HIDE, empty_fig, empty_fig,
                "Loading data...", [], _HIDE, _HIDE, [], None, _HIDE)

    raw_totals = macro_data["totals"]
    review_count = macro_data.get("review_count", 0)
    dim_totals = {d: raw_totals.get(f"sim_{d}", 0) for d in DIMENSIONS}
    pie = _build_pie(dim_totals, review_count, title="Dimension Strength Across All Reviews")

    return (
        _SHOW, pie,
        _HIDE, empty_fig, empty_fig,
        f"Macro View \u2014 Dimension Overview ({review_count:,} reviews)",
        [],
        _HIDE, _HIDE, [], None, _HIDE,
    )


# ---------------------------------------------------------------------------
# Macro: pie wedge click OR card click -> show query text
# ---------------------------------------------------------------------------

def _query_panel_output(dim_key):
    return (
        {**_PANEL_STYLE, "border": f"2px solid {DIM_COLORS[dim_key]}"},
        html.Span([
            html.Span(DIM_LABELS[dim_key], style={"color": DIM_COLORS[dim_key]}),
            html.Span(" \u2014 Query Definition",
                       style={"color": COLORS["gray"], "fontWeight": "400"}),
        ]),
        f'"{DIM_QUERY_TEXTS[dim_key]}"',
    )


@callback(
    Output("dna-query-detail", "style"),
    Output("dna-query-title", "children"),
    Output("dna-query-text", "children"),
    Input("dna-macro-chart", "clickData"),
    Input({"type": "macro-dim-card", "dim": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def show_macro_query(pie_click, card_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger = ctx.triggered[0]["prop_id"]

    if "dna-macro-chart" in trigger:
        if not pie_click:
            return no_update, no_update, no_update
        points = pie_click.get("points", [])
        if not points:
            return no_update, no_update, no_update
        label = points[0].get("label", "")
        dim_key = _DIM_LABEL_TO_KEY.get(label)
    else:
        import json as _json
        try:
            parsed = _json.loads(trigger.split(".")[0])
            dim_key = parsed.get("dim")
        except Exception:
            return no_update, no_update, no_update

    if not dim_key or dim_key not in DIM_QUERY_TEXTS:
        return no_update, no_update, no_update

    return _query_panel_output(dim_key)


# ---------------------------------------------------------------------------
# Entity pie wedge click -> show definition + sorted review list
# ---------------------------------------------------------------------------

@callback(
    Output("dna-attr-panel", "style"),
    Output("dna-attr-title", "children"),
    Output("dna-attr-query", "children"),
    Output("dna-review-selector", "options"),
    Output("dna-review-selector", "value"),
    Output("dna-selected-dim", "data"),
    Output("dna-review-panel", "style", allow_duplicate=True),
    Input("dna-entity-chart", "clickData"),
    Input({"type": "entity-dim-card", "dim": ALL}, "n_clicks"),
    State("dna-entity-reviews-store", "data"),
    prevent_initial_call=True,
)
def handle_entity_pie_click(pie_click, card_clicks, reviews):
    _no = (no_update,) * 7
    if not reviews:
        return _no

    ctx = dash.callback_context
    if not ctx.triggered:
        return _no

    trigger = ctx.triggered[0]["prop_id"]
    dim_key = None

    if "dna-entity-chart" in trigger:
        if not pie_click:
            return _no
        points = pie_click.get("points", [])
        if not points:
            return _no
        label = points[0].get("label", "")
        dim_key = _DIM_LABEL_TO_KEY.get(label)
    else:
        import json as _json
        try:
            parsed = _json.loads(trigger.split(".")[0])
            dim_key = parsed.get("dim")
        except Exception:
            return _no

    if not dim_key:
        return _no

    sim_col = f"sim_{dim_key}"
    sorted_reviews = sorted(reviews, key=lambda r: r.get(sim_col, 0) or 0, reverse=True)

    options = []
    for i, r in enumerate(sorted_reviews):
        score = r.get(sim_col, 0) or 0
        reviewer = r.get("reviewer_name", "") or "Anonymous"
        review_date = r.get("review_date", "") or ""
        date_str = str(review_date).split("T")[0].split(" ")[0] if review_date else ""
        label_text = (
            f"{DIM_LABELS[dim_key]} \u2014 {score:.0%} \u2014 "
            f"{reviewer} \u2014 {date_str}"
        )
        options.append({"label": label_text, "value": r.get("review_idx", i)})

    title = html.Span([
        html.Span(DIM_LABELS[dim_key], style={"color": DIM_COLORS[dim_key]}),
        html.Span(f" \u2014 {len(reviews)} reviews ranked by association",
                   style={"color": COLORS["gray"], "fontWeight": "400"}),
    ])

    return (
        {**_PANEL_STYLE, "border": f"2px solid {DIM_COLORS[dim_key]}"},
        title,
        f'"{DIM_QUERY_TEXTS[dim_key]}"',
        options,
        None,
        dim_key,
        _HIDE,
    )


# ---------------------------------------------------------------------------
# Review selector -> show text + spider chart
# ---------------------------------------------------------------------------

@callback(
    Output("dna-review-panel", "style"),
    Output("dna-review-title", "children"),
    Output("dna-review-text", "children"),
    Output("dna-review-radar", "figure"),
    Input("dna-review-selector", "value"),
    Input("dna-close-review", "n_clicks"),
    State("dna-entity-reviews-store", "data"),
    prevent_initial_call=True,
)
def handle_review_select(review_idx, close_clicks, reviews):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "dna-close-review":
        return _HIDE, "", "", go.Figure()

    if review_idx is None or not reviews:
        return _HIDE, "", "", go.Figure()

    review = next((r for r in reviews if r.get("review_idx") == review_idx), None)
    if not review:
        return _HIDE, "", "", go.Figure()

    scores = {d: review.get(f"sim_{d}", 0) or 0 for d in DIMENSIONS}
    advisor_name = review.get("advisor_name", "")
    reviewer = review.get("reviewer_name", "") or "Anonymous"
    review_date = review.get("review_date", "") or ""
    raw_text = review.get("review_text_raw", "") or "No review text available."
    radar = _build_radar_figure(scores, title=f"Review \u2014 {advisor_name}")

    meta_items = [
        html.Span(f"Reviewer: {reviewer}", style={
            "fontWeight": "700", "color": COLORS["navy"],
        }),
    ]
    if review_date:
        date_str = str(review_date).split("T")[0].split(" ")[0]
        meta_items.append(html.Span(f"  \u00b7  {date_str}", style={
            "color": COLORS["gray"],
        }))

    text_content = html.Div([
        html.Div(meta_items, style={
            "fontSize": "14px", "marginBottom": "10px",
        }),
        html.Div(raw_text),
    ])

    return (
        {**_PANEL_STYLE, "marginTop": "12px"},
        f"Review Detail \u2014 {advisor_name}",
        text_content,
        radar,
    )
