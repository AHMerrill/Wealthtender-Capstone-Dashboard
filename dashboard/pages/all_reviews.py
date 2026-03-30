"""All Reviews browser page for Wealthtender Dashboard.

Three-column layout:
  Left   – paginated list of reviews (10 per page) with Prev / Next
  Middle – selected review text, spider chart, and score table
  Right  – cosine-similarity legend + all 7 canonical dimension query texts
"""

import json

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard.branding import COLORS, FONT_FAMILY, DATA_VIZ_PALETTE
from dashboard.constants import (
    DIMENSIONS, DIM_LABELS, DIM_SHORT, DIM_COLORS, DIM_QUERY_TEXTS,
)
from dashboard.services.api import get_all_reviews, get_dna_review_detail

dash.register_page(__name__, path="/all-reviews", name="All Reviews",
                   title="All Reviews")

_PAGE_SIZE = 10

# ---------------------------------------------------------------------------
# Shared button style
# ---------------------------------------------------------------------------

_BTN_STYLE = {
    "background": COLORS["blue"], "color": "white",
    "border": "none", "borderRadius": "6px",
    "padding": "6px 14px", "fontSize": "12px",
    "cursor": "pointer", "fontWeight": "600",
}
_BTN_DISABLED = {
    **_BTN_STYLE,
    "background": COLORS.get("border", "#e2e8f0"),
    "color": COLORS.get("gray", "#999"),
    "cursor": "default",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _review_list_item(r, idx, selected_idx=None):
    """Build a single clickable row for the left-panel list."""
    advisor = r.get("advisor_name", "Unknown Advisor")
    reviewer = r.get("reviewer_name")
    date = r.get("review_date")
    review_idx = r.get("review_idx", idx)

    parts = []
    if reviewer:
        parts.append(reviewer)
    if date:
        parts.append(str(date))
    if not parts:
        text_raw = r.get("review_text_raw") or ""
        preview = text_raw[:60].strip()
        if preview:
            parts.append(f"{preview}...")
        else:
            parts.append(f"Review #{review_idx}")
    subtitle = "  ·  ".join(parts)

    is_selected = (selected_idx is not None and review_idx == selected_idx)

    base_style = {
        "padding": "10px 12px",
        "borderBottom": f"1px solid {COLORS['border']}",
        "cursor": "pointer",
        "transition": "background 0.12s",
    }
    if is_selected:
        base_style["background"] = COLORS.get("soft_blue", "#e3f5fe")
        base_style["borderLeft"] = f"3px solid {COLORS['blue']}"
        base_style["paddingLeft"] = "9px"

    return html.Div(
        id={"type": "review-list-item", "index": review_idx},
        n_clicks=0,
        style=base_style,
        children=[
            html.Div(advisor, style={
                "fontWeight": "700" if is_selected else "600",
                "fontSize": "13px",
                "color": COLORS["blue"] if is_selected else COLORS["ink"],
                "marginBottom": "2px",
                "whiteSpace": "nowrap", "overflow": "hidden",
                "textOverflow": "ellipsis",
            }),
            html.Div(
                subtitle,
                style={"fontSize": "11px", "color": COLORS["gray"],
                       "whiteSpace": "nowrap", "overflow": "hidden",
                       "textOverflow": "ellipsis"},
            ),
        ],
    )


def _build_spider(scores):
    """Build a 7-dimension radar chart from a scores dict."""
    labels = [DIM_SHORT[d] for d in DIMENSIONS]
    values = [scores.get(d) or 0 for d in DIMENSIONS]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(0, 76, 140, 0.12)",
        line=dict(color=COLORS["blue"], width=2),
        marker=dict(
            size=6,
            color=[DIM_COLORS[d] for d in DIMENSIONS]
                  + [DIM_COLORS[DIMENSIONS[0]]],
        ),
        hovertemplate="%{theta}: %{r:.4f}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True,
                            range=[0, max(values + [0.5]) * 1.15],
                            tickfont=dict(size=9)),
            angularaxis=dict(tickfont=dict(size=10, family=FONT_FAMILY)),
        ),
        showlegend=False,
        margin=dict(l=50, r=50, t=20, b=20),
        height=280,
        paper_bgcolor="white",
        font=dict(family=FONT_FAMILY),
    )
    return fig


def _score_table(scores):
    """Build a compact dimension-by-dimension score readout."""
    rows = []
    for d in DIMENSIONS:
        val = scores.get(d)
        display = f"{val:.4f}" if val is not None else "\u2014"
        rows.append(
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "padding": "4px 8px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "fontSize": "12px",
            }, children=[
                html.Span(DIM_LABELS[d], style={
                    "color": DIM_COLORS[d], "fontWeight": "600",
                }),
                html.Span(display, style={
                    "fontFamily": "monospace", "color": COLORS["ink"],
                }),
            ])
        )
    return html.Div(rows)


def _similarity_legend():
    """Build a cosine-similarity interpretation guide."""
    bands = [
        ("0.50 +", "Very strong alignment", "#276749", "#F0FFF4"),
        ("0.35 \u2013 0.50", "Strong alignment", "#2F855A", "#F0FFF4"),
        ("0.20 \u2013 0.35", "Moderate alignment", "#B7791F", "#FEFCBF"),
        ("0.10 \u2013 0.20", "Weak alignment", "#C05621", "#FEFCBF"),
        ("< 0.10", "Little to no alignment", "#9B2C2C", "#FFF5F5"),
    ]
    rows = []
    for score_range, meaning, text_color, bg in bands:
        rows.append(
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "4px 10px",
                "background": bg,
                "borderRadius": "4px",
                "marginBottom": "3px",
                "fontSize": "11px",
            }, children=[
                html.Span(score_range, style={
                    "fontFamily": "monospace", "fontWeight": "700",
                    "color": text_color, "minWidth": "80px",
                }),
                html.Span(meaning, style={
                    "color": text_color, "fontWeight": "500",
                }),
            ])
        )

    return html.Div(style={
        "border": f"1px solid {COLORS['border']}",
        "borderRadius": "10px", "background": "white",
        "padding": "12px 14px", "marginBottom": "14px",
    }, children=[
        html.Div("Cosine Similarity Scale", style={
            "fontWeight": "700", "fontSize": "13px",
            "color": COLORS["blue"], "marginBottom": "8px",
        }),
        html.Div(rows),
        html.Div(
            "Cosine similarity measures how closely a review\u2019s language "
            "aligns with the ideal description for each dimension. "
            "Higher values mean the review more strongly reflects "
            "that quality. Values near zero indicate the review "
            "doesn\u2019t address that theme; negative values (rare) "
            "would suggest opposing language.",
            style={
                "fontSize": "10px", "color": COLORS["gray"],
                "lineHeight": "1.45", "marginTop": "8px",
            },
        ),
    ])


def _query_reference_panel():
    """Build the always-visible panel showing all 7 canonical query texts."""
    cards = []
    for d in DIMENSIONS:
        cards.append(
            html.Div(style={
                "borderLeft": f"4px solid {DIM_COLORS[d]}",
                "padding": "10px 12px",
                "marginBottom": "10px",
                "background": "#FAFBFC",
                "borderRadius": "0 8px 8px 0",
            }, children=[
                html.Div(DIM_LABELS[d], style={
                    "fontWeight": "700", "fontSize": "12px",
                    "color": DIM_COLORS[d], "marginBottom": "4px",
                }),
                html.Div(
                    f'"{DIM_QUERY_TEXTS[d]}"',
                    style={
                        "fontSize": "11px", "lineHeight": "1.55",
                        "color": COLORS["ink"], "fontStyle": "italic",
                    },
                ),
            ])
        )
    return cards


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**_kwargs):
    return html.Div(style={"padding": "24px"}, children=[
        html.H2("All Reviews", style={
            "marginBottom": "16px", "color": COLORS["ink"],
        }),

        # Data stores
        dcc.Store(id="all-reviews-page", data=0),         # current page index
        dcc.Store(id="all-reviews-total", data=0),         # total review count
        dcc.Store(id="all-reviews-items", data=[]),        # current page items
        dcc.Store(id="all-reviews-selected-idx"),

        # Load trigger — retries every 3s up to 20 times to handle
        # Render cold-start (API may not be ready for 30-60s).
        dcc.Interval(id="all-reviews-load-trigger",
                     interval=3000, max_intervals=20),

        # Three-column layout
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "22% 38% 40%",
            "gap": "16px",
            "minHeight": "70vh",
        }, children=[

            # ===== LEFT: Review list + pagination =====
            html.Div(style={
                "border": f"1px solid {COLORS['border']}",
                "borderRadius": "12px",
                "background": "white",
                "overflow": "hidden",
                "display": "flex",
                "flexDirection": "column",
            }, children=[
                html.Div(id="all-reviews-header", children="Reviews", style={
                    "padding": "10px 12px",
                    "fontWeight": "700", "fontSize": "13px",
                    "color": COLORS["blue"],
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "background": COLORS.get("soft_blue", "#e3f5fe"),
                }),
                html.Div(
                    id="all-reviews-list-container",
                    style={
                        "overflowY": "auto",
                        "flex": "1",
                        "minHeight": "400px",
                    },
                    children=[
                        html.Div("Loading reviews...",
                                 style={"padding": "20px",
                                        "color": COLORS["gray"],
                                        "textAlign": "center"}),
                    ],
                ),
                # Pagination bar (always present in DOM)
                html.Div(
                    id="all-reviews-pagination",
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "padding": "8px 10px",
                        "borderTop": f"1px solid {COLORS['border']}",
                        "background": COLORS.get("soft_blue", "#e3f5fe"),
                        "fontSize": "11px",
                    },
                    children=[
                        html.Button("Prev",
                                    id="all-reviews-prev-btn", n_clicks=0,
                                    style=_BTN_DISABLED, disabled=True),
                        html.Span("", id="all-reviews-page-info",
                                  style={"color": COLORS["gray"]}),
                        html.Button("Next",
                                    id="all-reviews-next-btn", n_clicks=0,
                                    style=_BTN_DISABLED, disabled=True),
                    ],
                ),
            ]),

            # ===== MIDDLE: Detail panel =====
            html.Div(id="all-reviews-detail-panel", style={
                "overflowY": "auto",
                "height": "calc(100vh - 120px)",
            }, children=[
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

            # ===== RIGHT: Reference panel (always visible) =====
            html.Div(style={
                "overflowY": "auto",
                "height": "calc(100vh - 120px)",
            }, children=[
                _similarity_legend(),
                html.Div(style={
                    "border": f"1px solid {COLORS['border']}",
                    "borderRadius": "12px", "background": "white",
                    "padding": "14px",
                }, children=[
                    html.Div("Canonical Dimension Queries", style={
                        "fontWeight": "700", "fontSize": "13px",
                        "color": COLORS["blue"], "marginBottom": "10px",
                    }),
                    html.Div(
                        "Each review is compared against these ideal "
                        "descriptions using sentence embeddings. The "
                        "cosine similarity score reflects how closely "
                        "a review\u2019s language matches each dimension.",
                        style={
                            "fontSize": "11px", "color": COLORS["gray"],
                            "lineHeight": "1.45", "marginBottom": "12px",
                        },
                    ),
                    *_query_reference_panel(),
                ]),
            ]),
        ]),
    ])


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def _fetch_page(page_num):
    """Fetch a single page of reviews from the API."""
    offset = page_num * _PAGE_SIZE
    return get_all_reviews(offset=offset, limit=_PAGE_SIZE)


# 1. Initial load (retries on cold-start)
@callback(
    Output("all-reviews-items", "data"),
    Output("all-reviews-total", "data"),
    Output("all-reviews-page", "data"),
    Output("all-reviews-load-trigger", "max_intervals"),
    Input("all-reviews-load-trigger", "n_intervals"),
    State("all-reviews-items", "data"),
    prevent_initial_call=True,
)
def initial_load(_, existing_items):
    if existing_items:
        return no_update, no_update, no_update, 0
    resp = _fetch_page(0)
    items = resp.get("items", [])
    if items:
        return items, resp.get("total", 0), 0, 0
    return no_update, no_update, no_update, 20


# 2. Previous / Next button clicks → fetch that page
@callback(
    Output("all-reviews-items", "data", allow_duplicate=True),
    Output("all-reviews-page", "data", allow_duplicate=True),
    Input("all-reviews-prev-btn", "n_clicks"),
    Input("all-reviews-next-btn", "n_clicks"),
    State("all-reviews-page", "data"),
    State("all-reviews-total", "data"),
    prevent_initial_call=True,
)
def change_page(prev_clicks, next_clicks, current_page, total):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
    trigger_id = ctx.triggered[0]["prop_id"]

    last_page = max(0, (total - 1) // _PAGE_SIZE) if total else 0

    if "prev" in trigger_id:
        new_page = max(0, current_page - 1)
    elif "next" in trigger_id:
        new_page = min(last_page, current_page + 1)
    else:
        return no_update, no_update

    if new_page == current_page:
        return no_update, no_update

    resp = _fetch_page(new_page)
    items = resp.get("items", [])
    return items if items else no_update, new_page


# 3. Render the list + update pagination controls
@callback(
    Output("all-reviews-list-container", "children"),
    Output("all-reviews-prev-btn", "disabled"),
    Output("all-reviews-prev-btn", "style"),
    Output("all-reviews-next-btn", "disabled"),
    Output("all-reviews-next-btn", "style"),
    Output("all-reviews-page-info", "children"),
    Output("all-reviews-header", "children"),
    Input("all-reviews-items", "data"),
    Input("all-reviews-selected-idx", "data"),
    State("all-reviews-page", "data"),
    State("all-reviews-total", "data"),
)
def render_list(items, selected_idx, page, total):
    if not items:
        return (
            html.Div("No reviews available.",
                     style={"padding": "20px", "color": COLORS["gray"],
                            "textAlign": "center"}),
            True, _BTN_DISABLED,
            True, _BTN_DISABLED,
            "", "Reviews",
        )

    children = [_review_list_item(r, i, selected_idx)
                for i, r in enumerate(items)]

    last_page = max(0, (total - 1) // _PAGE_SIZE) if total else 0
    on_first = (page or 0) <= 0
    on_last = (page or 0) >= last_page

    page_display = page + 1 if page is not None else 1
    total_pages = last_page + 1

    start_num = (page or 0) * _PAGE_SIZE + 1
    end_num = min(start_num + len(items) - 1, total or 0)

    return (
        children,
        on_first, _BTN_DISABLED if on_first else _BTN_STYLE,
        on_last, _BTN_DISABLED if on_last else _BTN_STYLE,
        f"{start_num}\u2013{end_num} of {total}",
        f"Reviews ({total})",
    )


# 4. Handle review selection (pattern-matching callback)
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
    trigger = ctx.triggered[0]["prop_id"]
    try:
        trigger_id = json.loads(trigger.rsplit(".", 1)[0])
        return int(trigger_id["index"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return no_update


# 5. Render detail panel when a review is selected
@callback(
    Output("all-reviews-detail-panel", "children"),
    Input("all-reviews-selected-idx", "data"),
)
def render_detail(review_idx):
    if review_idx is None:
        return html.Div(
            "Select a review from the list to view its details.",
            style={
                "padding": "40px 24px", "textAlign": "center",
                "color": COLORS["gray"], "fontSize": "15px",
                "border": f"1px solid {COLORS['border']}",
                "borderRadius": "12px", "background": "white",
            },
        )

    detail = get_dna_review_detail(review_idx)
    if not detail:
        return html.Div("Could not load review details.",
                        style={"padding": "20px", "color": COLORS["gray"]})

    scores = detail.get("scores", {})
    advisor = detail.get("advisor_name", "Unknown")
    reviewer = detail.get("reviewer_name") or "Anonymous"
    date = detail.get("review_date", "")
    text = detail.get("review_text") or ""

    return html.Div([
        # Review text card
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "16px 18px", "marginBottom": "14px",
        }, children=[
            html.Div(style={"marginBottom": "8px"}, children=[
                html.Span(advisor, style={
                    "fontWeight": "700", "fontSize": "14px",
                    "color": COLORS["ink"],
                }),
                html.Span(f"  \u00b7  {reviewer}  \u00b7  {date}", style={
                    "fontSize": "11px", "color": COLORS["gray"],
                    "marginLeft": "4px",
                }),
            ]),
            html.P(text, style={
                "fontSize": "13px", "lineHeight": "1.65",
                "color": COLORS["ink"],
                "maxHeight": "220px", "overflowY": "auto",
                "whiteSpace": "pre-wrap",
            }),
        ]),

        # Spider chart
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "10px", "marginBottom": "14px",
        }, children=[
            html.Div("Dimension Scores", style={
                "fontWeight": "700", "fontSize": "13px",
                "color": COLORS["blue"], "marginBottom": "2px",
                "paddingLeft": "6px",
            }),
            dcc.Graph(
                id="all-reviews-spider",
                figure=_build_spider(scores),
                config={"displayModeBar": False},
                style={"height": "280px"},
            ),
        ]),

        # Score table
        html.Div(style={
            "border": f"1px solid {COLORS['border']}",
            "borderRadius": "12px", "background": "white",
            "padding": "12px 14px",
        }, children=[
            html.Div("Cosine Similarities", style={
                "fontWeight": "700", "fontSize": "13px",
                "color": COLORS["blue"], "marginBottom": "6px",
            }),
            _score_table(scores),
        ]),
    ])
