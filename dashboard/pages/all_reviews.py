"""All Reviews browser page for Wealthtender Dashboard.

Scrollable list of every review on the left; full review detail, spider chart,
score table, and clickable dimension query text on the right.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard.branding import COLORS, FONT_FAMILY, DATA_VIZ_PALETTE
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_SHORT, DIM_COLORS
from dashboard.pages.advisor_dna import DIM_QUERY_TEXTS
from dashboard.services.api import get_all_reviews, get_dna_review_detail

dash.register_page(__name__, path="/all-reviews", name="All Reviews",
                   title="All Reviews")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _review_list_item(r, idx):
    """Build a single clickable row for the left-panel list."""
    advisor = r.get("advisor_name", "Unknown Advisor")
    reviewer = r.get("reviewer_name") or "Anonymous"
    date = r.get("review_date", "")
    review_idx = r.get("review_idx", idx)

    return html.Div(
        id={"type": "review-list-item", "index": review_idx},
        n_clicks=0,
        style={
            "padding": "10px 12px",
            "borderBottom": f"1px solid {COLORS['border']}",
            "cursor": "pointer",
            "transition": "background 0.12s",
        },
        children=[
            html.Div(advisor, style={
                "fontWeight": "600", "fontSize": "13px",
                "color": COLORS["ink"], "marginBottom": "2px",
                "whiteSpace": "nowrap", "overflow": "hidden",
                "textOverflow": "ellipsis",
            }),
            html.Div(
                f"{reviewer}  ·  {date}",
                style={"fontSize": "11px", "color": COLORS["gray"]},
            ),
        ],
    )


def _build_spider(scores):
    """Build a 7-dimension radar chart from a scores dict."""
    labels = [DIM_SHORT[d] for d in DIMENSIONS]
    values = [scores.get(d) or 0 for d in DIMENSIONS]
    colors = [DIM_COLORS[d] for d in DIMENSIONS]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(0, 76, 140, 0.12)",
        line=dict(color=COLORS["blue"], width=2),
        marker=dict(size=6, color=[DIM_COLORS[d] for d in DIMENSIONS] + [DIM_COLORS[DIMENSIONS[0]]]),
        hovertemplate="%{theta}: %{r:.4f}<extra></extra>",
        customdata=DIMENSIONS + [DIMENSIONS[0]],
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(values + [0.5]) * 1.15],
                            tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11, family=FONT_FAMILY)),
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=340,
        paper_bgcolor="white",
        font=dict(family=FONT_FAMILY),
    )
    return fig


def _score_table(scores):
    """Build a dimension-by-dimension score readout."""
    rows = []
    for d in DIMENSIONS:
        val = scores.get(d)
        display = f"{val:.4f}" if val is not None else "—"
        rows.append(
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "padding": "6px 10px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "fontSize": "13px",
            }, children=[
                html.Span(DIM_LABELS[d], style={"color": DIM_COLORS[d], "fontWeight": "600"}),
                html.Span(display, style={"fontFamily": "monospace", "color": COLORS["ink"]}),
            ])
        )
    return html.Div(rows)


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**_kwargs):
    return html.Div(style={"padding": "24px"}, children=[
        html.H2("All Reviews", style={"marginBottom": "16px", "color": COLORS["ink"]}),

        # Data stores
        dcc.Store(id="all-reviews-data"),
        dcc.Store(id="all-reviews-selected-idx"),

        # Load trigger
        dcc.Interval(id="all-reviews-load-trigger", interval=500, max_intervals=1),

        # Two-column layout
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "35% 1fr",
            "gap": "20px",
            "minHeight": "70vh",
        }, children=[
            # ===== LEFT: Scrollable review list =====
            html.Div(style={
                "border": f"1px solid {COLORS['border']}",
                "borderRadius": "12px",
                "background": "white",
                "overflow": "hidden",
                "display": "flex",
                "flexDirection": "column",
            }, children=[
                html.Div("Reviews", style={
                    "padding": "12px 14px",
                    "fontWeight": "700", "fontSize": "14px",
                    "color": COLORS["blue"],
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "background": COLORS.get("soft_blue", "#e3f5fe"),
                }),
                html.Div(
                    id="all-reviews-list-container",
                    style={
                        "overflowY": "auto",
                        "height": "calc(100vh - 180px)",
                        "minHeight": "500px",
                    },
                    children=[
                        html.Div("Loading reviews...",
                                 style={"padding": "20px", "color": COLORS["gray"],
                                        "textAlign": "center"}),
                    ],
                ),
            ]),

            # ===== RIGHT: Detail panel =====
            html.Div(id="all-reviews-detail-panel", children=[
                html.Div(
                    "Select a review from the list to view its details.",
                    style={
                        "padding": "40px 24px", "textAlign": "center",
                        "color": COLORS["gray"], "fontSize": "15px",
                        "border": f"1px solid {COLORS['border']}",
                        "borderRadius": "12px", "background": "white",
                    },
                ),
            ]),
        ]),

        # ===== BOTTOM: Dimension query text (hidden until spider click) =====
        html.Div(id="all-reviews-query-panel", style={"display": "none"}),
    ])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

# 1. Load review list on page open
@callback(
    Output("all-reviews-data", "data"),
    Input("all-reviews-load-trigger", "n_intervals"),
    prevent_initial_call=True,
)
def load_reviews(_):
    reviews = get_all_reviews()
    return reviews


# 2. Render the scrollable list
@callback(
    Output("all-reviews-list-container", "children"),
    Input("all-reviews-data", "data"),
)
def render_list(reviews):
    if not reviews:
        return html.Div("No reviews available.",
                        style={"padding": "20px", "color": COLORS["gray"],
                               "textAlign": "center"})
    return [_review_list_item(r, i) for i, r in enumerate(reviews)]


# 3. Handle review selection (pattern-matching callback)
@callback(
    Output("all-reviews-selected-idx", "data"),
    Input({"type": "review-list-item", "index": dash.ALL}, "n_clicks"),
    State({"type": "review-list-item", "index": dash.ALL}, "id"),
    prevent_initial_call=True,
)
def select_review(n_clicks_list, id_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    # Find which item was clicked
    trigger = ctx.triggered[0]["prop_id"]
    # Parse the index from the trigger prop_id
    import json
    try:
        trigger_id = json.loads(trigger.rsplit(".", 1)[0])
        return int(trigger_id["index"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return no_update


# 4. Render detail panel when a review is selected
@callback(
    Output("all-reviews-detail-panel", "children"),
    Output("all-reviews-query-panel", "style"),
    Output("all-reviews-query-panel", "children"),
    Input("all-reviews-selected-idx", "data"),
)
def render_detail(review_idx):
    if review_idx is None:
        placeholder = html.Div(
            "Select a review from the list to view its details.",
            style={
                "padding": "40px 24px", "textAlign": "center",
                "color": COLORS["gray"], "fontSize": "15px",
                "border": f"1px solid {COLORS['border']}",
                "borderRadius": "12px", "background": "white",
            },
        )
        return placeholder, {"display": "none"}, ""

    detail = get_dna_review_detail(review_idx)
    if not detail:
        return html.Div("Could not load review details.",
                        style={"padding": "20px", "color": COLORS["gray"]}), \
               {"display": "none"}, ""

    scores = detail.get("scores", {})
    advisor = detail.get("advisor_name", "Unknown")
    reviewer = detail.get("reviewer_name") or "Anonymous"
    date = detail.get("review_date", "")
    text = detail.get("review_text") or ""

    # Build the right-panel content
    panel = html.Div([
        # Review text card
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "18px 20px", "marginBottom": "16px",
        }, children=[
            html.Div(style={"marginBottom": "10px"}, children=[
                html.Span(advisor, style={
                    "fontWeight": "700", "fontSize": "15px", "color": COLORS["ink"],
                }),
                html.Span(f"  ·  {reviewer}  ·  {date}", style={
                    "fontSize": "12px", "color": COLORS["gray"], "marginLeft": "4px",
                }),
            ]),
            html.P(text, style={
                "fontSize": "14px", "lineHeight": "1.65", "color": COLORS["ink"],
                "maxHeight": "200px", "overflowY": "auto",
                "whiteSpace": "pre-wrap",
            }),
        ]),

        # Spider chart
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "12px", "marginBottom": "16px",
        }, children=[
            html.Div("Dimension Scores", style={
                "fontWeight": "700", "fontSize": "14px",
                "color": COLORS["blue"], "marginBottom": "4px",
                "paddingLeft": "8px",
            }),
            dcc.Graph(
                id="all-reviews-spider",
                figure=_build_spider(scores),
                config={"displayModeBar": False},
                style={"height": "340px"},
            ),
        ]),

        # Score table
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "14px 16px",
        }, children=[
            html.Div("Cosine Similarities", style={
                "fontWeight": "700", "fontSize": "14px",
                "color": COLORS["blue"], "marginBottom": "8px",
            }),
            _score_table(scores),
        ]),
    ])

    return panel, {"display": "none"}, ""


# 5. Spider chart click → show dimension query text
@callback(
    Output("all-reviews-query-panel", "children", allow_duplicate=True),
    Output("all-reviews-query-panel", "style", allow_duplicate=True),
    Input("all-reviews-spider", "clickData"),
    prevent_initial_call=True,
)
def show_query_text(click_data):
    if not click_data:
        return "", {"display": "none"}

    point = click_data["points"][0]
    dim_key = point.get("customdata")

    if not dim_key or dim_key not in DIM_QUERY_TEXTS:
        return "", {"display": "none"}

    return html.Div(style={
        "marginTop": "16px",
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "12px", "background": "white",
        "padding": "18px 20px",
    }, children=[
        html.Div(style={"marginBottom": "8px"}, children=[
            html.Span("Canonical Query: ", style={
                "fontWeight": "700", "fontSize": "14px", "color": COLORS["blue"],
            }),
            html.Span(DIM_LABELS[dim_key], style={
                "fontWeight": "600", "fontSize": "14px",
                "color": DIM_COLORS[dim_key],
            }),
        ]),
        html.P(
            f'"{DIM_QUERY_TEXTS[dim_key]}"',
            style={
                "fontSize": "13px", "lineHeight": "1.6",
                "color": COLORS["ink"], "fontStyle": "italic",
            },
        ),
    ]), {"display": "block"}
