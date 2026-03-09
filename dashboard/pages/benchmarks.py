"""Benchmarks page for Wealthtender Dashboard.

Shows peer pool composition, dimension score distributions with filtering,
and peer percentile comparisons when an entity is selected.
"""

import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go

from dashboard.branding import COLORS, FONT_FAMILY
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_COLORS
from dashboard.services.api import (
    get_benchmark_pool_stats,
    get_benchmark_distributions,
    get_dna_method_breakpoints,
    get_dna_entities,
    get_dna_percentile_scores,
    get_dna_advisor_scores,
)

dash.register_page(__name__, path="/benchmarks", title="Benchmarks")


# ---------------------------------------------------------------------------
# Histogram builders
# ---------------------------------------------------------------------------

def _build_distribution_histogram(dim_key: str, raw_scores: list, entity_score=None):
    """Build a histogram for one dimension from raw score values,
    with optional 'You Are Here' marker."""
    if not raw_scores:
        fig = go.Figure()
        fig.add_annotation(text="No data", showarrow=False)
        fig.update_layout(height=300, margin=dict(l=40, r=20, t=40, b=40))
        return fig

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=raw_scores,
        nbinsx=20,
        name=DIM_LABELS[dim_key],
        marker=dict(color=DIM_COLORS[dim_key]),
        hovertemplate="<b>Score Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>",
    ))

    # Add "You Are Here" marker if entity is selected
    if entity_score is not None:
        fig.add_vline(
            x=entity_score,
            line_dash="dash", line_color=COLORS["red"], line_width=2,
            annotation_text="You Are Here",
            annotation_position="top left",
            annotation_font=dict(size=10, color=COLORS["red"]),
        )

    fig.update_layout(
        title=dict(text=DIM_LABELS[dim_key], font=dict(size=13, color=COLORS["ink"])),
        xaxis=dict(title="Score", showgrid=True, gridcolor=COLORS["border"]),
        yaxis=dict(title="Count", showgrid=True, gridcolor=COLORS["border"]),
        font=dict(family=FONT_FAMILY, size=11, color=COLORS["ink"]),
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=40, r=20, t=50, b=40),
        height=300,
        hovermode="x unified",
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

def _build_kpi_card(label: str, value: str, style_override=None):
    """Build a single KPI stat card."""
    style = {
        "backgroundColor": COLORS["soft_lavender"],
        "borderRadius": "10px",
        "padding": "14px 16px",
        "textAlign": "left",
    }
    if style_override:
        style.update(style_override)

    return html.Div(
        style=style,
        children=[
            html.Div(label, style={
                "fontSize": "12px", "color": COLORS["gray"], "fontWeight": "600",
                "textTransform": "uppercase", "letterSpacing": "0.4px",
                "marginBottom": "4px"
            }),
            html.Div(value, style={
                "fontSize": "22px", "fontWeight": "700", "color": COLORS["blue"]
            }),
        ],
    )


# ---------------------------------------------------------------------------
# Peer percentile comparison table
# ---------------------------------------------------------------------------

def _build_peer_comparison_table(entity_scores: dict, percentile_scores: dict,
                                  breakpoints: dict, method: str):
    """Build a comparison table: Entity scores vs P25/P50/P75 breakpoints."""
    if not entity_scores or not breakpoints:
        return html.Div("No peer comparison data available.", style={
            "color": COLORS["gray"], "fontSize": "13px", "padding": "20px"
        })

    rows = []
    for dim in DIMENSIONS:
        entity_val = entity_scores.get(dim, 0)
        pctile_rank = percentile_scores.get(dim, 0)
        bp = breakpoints.get(dim, {})
        p25 = bp.get("p25", 0)
        p50 = bp.get("p50", 0)
        p75 = bp.get("p75", 0)

        rows.append(html.Tr([
            html.Td(DIM_LABELS[dim], style={
                "padding": "10px", "fontWeight": "600", "color": COLORS["ink"],
                "borderBottom": f"1px solid {COLORS['border']}"
            }),
            html.Td(f"{entity_val:.3f}", style={
                "padding": "10px", "textAlign": "center", "fontWeight": "700",
                "color": DIM_COLORS[dim], "borderBottom": f"1px solid {COLORS['border']}"
            }),
            html.Td(f"{pctile_rank:.0f}%", style={
                "padding": "10px", "textAlign": "center", "fontWeight": "600",
                "color": COLORS["blue"], "borderBottom": f"1px solid {COLORS['border']}"
            }),
            html.Td(f"{p25:.3f}", style={
                "padding": "10px", "textAlign": "center", "color": COLORS["gray"],
                "borderBottom": f"1px solid {COLORS['border']}", "fontSize": "12px"
            }),
            html.Td(f"{p50:.3f}", style={
                "padding": "10px", "textAlign": "center", "color": COLORS["gray"],
                "borderBottom": f"1px solid {COLORS['border']}", "fontSize": "12px"
            }),
            html.Td(f"{p75:.3f}", style={
                "padding": "10px", "textAlign": "center", "color": COLORS["gray"],
                "borderBottom": f"1px solid {COLORS['border']}", "fontSize": "12px"
            }),
        ]))

    return html.Div([
        html.Table([
            html.Thead(html.Tr([
                html.Th("Dimension", style={
                    "padding": "10px", "textAlign": "left", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
                html.Th("Your Score", style={
                    "padding": "10px", "textAlign": "center", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
                html.Th("Percentile", style={
                    "padding": "10px", "textAlign": "center", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
                html.Th("P25", style={
                    "padding": "10px", "textAlign": "center", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
                html.Th("P50", style={
                    "padding": "10px", "textAlign": "center", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
                html.Th("P75", style={
                    "padding": "10px", "textAlign": "center", "fontWeight": "700",
                    "backgroundColor": COLORS["soft_lavender"],
                    "borderBottom": f"2px solid {COLORS['border']}"
                }),
            ])),
            html.Tbody(rows),
        ], style={
            "width": "100%", "borderCollapse": "collapse",
            "fontFamily": FONT_FAMILY, "fontSize": "13px"
        }),
    ], style={"overflowX": "auto", "marginTop": "12px"})


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    return html.Div(
        className="benchmarks-page",
        style={"padding": "20px", "fontFamily": FONT_FAMILY},
        children=[
            # Data stores
            dcc.Store(id="benchmarks-init-trigger", data=True),
            dcc.Store(id="benchmarks-pool-stats", data={}),
            dcc.Store(id="benchmarks-distributions", data={}),
            dcc.Store(id="benchmarks-entities-list", data={"firms": [], "advisors": []}),

            # Page header
            html.H2("Benchmarks", style={
                "marginBottom": "4px", "color": COLORS["navy"],
                "fontFamily": FONT_FAMILY,
            }),
            html.P(
                "Compare peer pools and dimension score distributions. "
                "Select an entity to view percentile rankings.",
                style={"color": COLORS["gray"], "fontSize": "13px",
                       "marginBottom": "20px", "fontFamily": FONT_FAMILY},
            ),

            # Controls row
            html.Div(
                style={
                    "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
                    "gap": "12px", "marginBottom": "20px", "alignItems": "flex-end"
                },
                children=[
                    html.Div([
                        html.Label("Method:", style={
                            "fontSize": "12px", "fontWeight": "600",
                            "color": COLORS["gray"], "marginBottom": "4px"
                        }),
                        dcc.Dropdown(
                            id="benchmarks-method-select",
                            options=[
                                {"label": "Mean", "value": "mean"},
                                {"label": "Penalized", "value": "penalized"},
                                {"label": "Weighted", "value": "weighted"},
                            ],
                            value="mean",
                            style={"fontSize": "12px"},
                        ),
                    ]),
                    html.Div([
                        html.Label("Entity Type:", style={
                            "fontSize": "12px", "fontWeight": "600",
                            "color": COLORS["gray"], "marginBottom": "4px"
                        }),
                        dcc.Dropdown(
                            id="benchmarks-entity-type-select",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Firm", "value": "firm"},
                                {"label": "Advisor", "value": "advisor"},
                            ],
                            value="all",
                            style={"fontSize": "12px"},
                        ),
                    ]),
                    html.Div([
                        html.Label("Pool:", style={
                            "fontSize": "12px", "fontWeight": "600",
                            "color": COLORS["gray"], "marginBottom": "4px"
                        }),
                        dcc.Dropdown(
                            id="benchmarks-pool-select",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Premier (20+ reviews)", "value": "premier"},
                            ],
                            value="premier",
                            style={"fontSize": "12px"},
                        ),
                    ]),
                    html.Div([
                        html.Label("Select Entity:", style={
                            "fontSize": "12px", "fontWeight": "600",
                            "color": COLORS["gray"], "marginBottom": "4px"
                        }),
                        dcc.Dropdown(
                            id="benchmarks-entity-search",
                            options=[],
                            placeholder="Search entity...",
                            style={"fontSize": "12px"},
                        ),
                    ]),
                ],
            ),

            # Section 1: Pool Composition KPIs
            html.Div(
                id="benchmarks-kpi-section",
                style={"marginBottom": "28px"},
                children=[
                    html.H3("Pool Composition", style={
                        "fontSize": "16px", "fontWeight": "700",
                        "marginBottom": "12px", "color": COLORS["ink"]
                    }),
                    html.Div(
                        style={
                            "display": "grid", "gridTemplateColumns": "repeat(2, 1fr)",
                            "gap": "20px"
                        },
                        children=[
                            html.Div([
                                html.Div("All Pool", style={
                                    "fontSize": "13px", "fontWeight": "600",
                                    "color": COLORS["navy"], "marginBottom": "12px"
                                }),
                                html.Div(
                                    id="benchmarks-kpi-all",
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "repeat(2, 1fr)",
                                        "gap": "10px"
                                    }
                                ),
                            ]),
                            html.Div([
                                html.Div("Premier Pool (20+ reviews)", style={
                                    "fontSize": "13px", "fontWeight": "600",
                                    "color": COLORS["navy"], "marginBottom": "12px"
                                }),
                                html.Div(
                                    id="benchmarks-kpi-premier",
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "repeat(2, 1fr)",
                                        "gap": "10px"
                                    }
                                ),
                            ]),
                        ],
                    ),
                ],
            ),

            # Section 2: Dimension Score Distributions
            html.Div(
                style={"marginBottom": "28px"},
                children=[
                    html.H3("Dimension Score Distributions", style={
                        "fontSize": "16px", "fontWeight": "700",
                        "marginBottom": "12px", "color": COLORS["ink"]
                    }),
                    html.Div(
                        id="benchmarks-histograms",
                        style={
                            "display": "grid", "gridTemplateColumns": "repeat(3, 1fr)",
                            "gap": "16px"
                        },
                        children=[
                            dcc.Graph(
                                id=f"benchmarks-hist-{dim}",
                                figure=go.Figure(),
                                config={"displayModeBar": False},
                            )
                            for dim in DIMENSIONS
                        ],
                    ),
                ],
            ),

            # Section 3: Peer Percentile Comparison
            html.Div(
                id="benchmarks-percentile-section",
                style={"display": "none", "marginTop": "28px"},
                children=[
                    html.H3("Your Percentile Scores vs Peers", style={
                        "fontSize": "16px", "fontWeight": "700",
                        "marginBottom": "12px", "color": COLORS["ink"]
                    }),
                    html.Div(
                        id="benchmarks-percentile-table",
                        style={
                            "backgroundColor": COLORS["card_bg"],
                            "borderRadius": "8px", "padding": "16px",
                            "border": f"1px solid {COLORS['border']}"
                        }
                    ),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("benchmarks-pool-stats", "data"),
    Output("benchmarks-distributions", "data"),
    Output("benchmarks-entities-list", "data"),
    Input("benchmarks-init-trigger", "data"),
    Input("benchmarks-method-select", "value"),
    Input("benchmarks-entity-type-select", "value"),
    Input("benchmarks-pool-select", "value"),
    prevent_initial_call=False,
)
def fetch_benchmark_data(trigger, method, entity_type, pool):
    """Fetch pool stats, distributions, and entity list."""
    min_peer_reviews = 20 if pool == "premier" else 0

    # Always fetch pool stats with default threshold so BOTH All and Premier
    # KPI cards are always populated (avoids cards appearing/disappearing).
    pool_stats = get_benchmark_pool_stats()
    distributions = get_benchmark_distributions(
        method=method, entity_type=entity_type, min_peer_reviews=min_peer_reviews
    )
    entities = get_dna_entities()

    return pool_stats, distributions, entities


@callback(
    Output("benchmarks-kpi-all", "children"),
    Output("benchmarks-kpi-premier", "children"),
    Input("benchmarks-pool-stats", "data"),
)
def update_kpi_cards(pool_stats):
    """Update KPI cards from pool stats."""
    if not pool_stats:
        return [], []

    all_stats = pool_stats.get("all", {})
    premier_stats = pool_stats.get("premier", {})

    all_cards = [
        _build_kpi_card("Total Entities", str(all_stats.get("total", 0))),
        _build_kpi_card("Firms", str(all_stats.get("firms", 0))),
        _build_kpi_card("Advisors", str(all_stats.get("advisors", 0))),
        _build_kpi_card("Avg Reviews",
                        f"{all_stats.get('review_count_stats', {}).get('mean', 0):.1f}"),
    ]

    premier_cards = [
        _build_kpi_card("Total Entities", str(premier_stats.get("total", 0))),
        _build_kpi_card("Firms", str(premier_stats.get("firms", 0))),
        _build_kpi_card("Advisors", str(premier_stats.get("advisors", 0))),
        _build_kpi_card("Avg Reviews",
                        f"{premier_stats.get('review_count_stats', {}).get('mean', 0):.1f}"),
    ]

    return all_cards, premier_cards


@callback(
    Output("benchmarks-entity-search", "options"),
    Input("benchmarks-entities-list", "data"),
    Input("benchmarks-entity-type-select", "value"),
)
def update_entity_dropdown(entities_data, entity_type):
    """Update entity search dropdown based on entity type filter."""
    if not entities_data:
        return []

    options = []

    if entity_type in ("all", "firm"):
        for firm in entities_data.get("firms", []):
            options.append({
                "label": f"{firm.get('advisor_name', 'Unknown')} (Firm)",
                "value": firm.get("advisor_id", "")
            })

    if entity_type in ("all", "advisor"):
        for advisor in entities_data.get("advisors", []):
            options.append({
                "label": f"{advisor.get('advisor_name', 'Unknown')} (Advisor)",
                "value": advisor.get("advisor_id", "")
            })

    return options


@callback(
    Output("benchmarks-hist-trust_integrity", "figure"),
    Output("benchmarks-hist-listening_personalization", "figure"),
    Output("benchmarks-hist-communication_clarity", "figure"),
    Output("benchmarks-hist-responsiveness_availability", "figure"),
    Output("benchmarks-hist-life_event_support", "figure"),
    Output("benchmarks-hist-investment_expertise", "figure"),
    Input("benchmarks-distributions", "data"),
    Input("benchmarks-entity-search", "value"),
    Input("benchmarks-method-select", "value"),
    Input("benchmarks-pool-select", "value"),
)
def update_histograms(distributions, selected_entity, method, pool):
    """Update histograms for all dimensions."""
    if not distributions:
        return [go.Figure()] * 6

    # Get entity scores if selected
    entity_scores = {}
    if selected_entity:
        entity_data = get_dna_advisor_scores(selected_entity, method=method)
        if entity_data:
            entity_scores = entity_data.get("scores", {})

    figs = []
    for dim in DIMENSIONS:
        # distributions returns {dim: [raw_score_list]}
        raw_scores = distributions.get(dim, [])
        entity_score = entity_scores.get(dim)
        fig = _build_distribution_histogram(dim, raw_scores, entity_score=entity_score)
        figs.append(fig)

    return tuple(figs)


@callback(
    Output("benchmarks-percentile-section", "style"),
    Output("benchmarks-percentile-table", "children"),
    Input("benchmarks-entity-search", "value"),
    Input("benchmarks-method-select", "value"),
    Input("benchmarks-pool-select", "value"),
    Input("benchmarks-entity-type-select", "value"),
)
def update_percentile_section(selected_entity, method, pool, entity_type):
    """Show/hide percentile comparison section and update table."""
    if not selected_entity:
        return {"display": "none"}, ""

    min_peer_reviews = 20 if pool == "premier" else 0
    percentile_data = get_dna_percentile_scores(
        selected_entity, method=method, min_peer_reviews=min_peer_reviews
    )
    advisor_scores = get_dna_advisor_scores(selected_entity, method=method)
    breakpoints = get_dna_method_breakpoints(method=method, entity_type=entity_type)

    if not percentile_data or not advisor_scores:
        return (
            {"display": "block", "marginTop": "28px"},
            html.Div("No percentile data available.", style={
                "color": COLORS["gray"], "fontSize": "13px", "padding": "20px"
            })
        )

    entity_scores = advisor_scores.get("scores", {})
    percentile_scores = percentile_data.get("scores", {})

    table = _build_peer_comparison_table(
        entity_scores, percentile_scores, breakpoints, method
    )

    return {"display": "block", "marginTop": "28px"}, table
