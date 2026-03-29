"""Comparisons page for Wealthtender Dashboard.

Provides head-to-head entity comparison (FB-17): overlaid spider charts
and a detailed score table comparing two entities across all seven dimensions.

Team comparisons (FB-16) have been split out to team_comparisons.py.
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_SHORT
from dashboard.services.api import (
    get_dna_entities,
    get_entity_comparison,
)

dash.register_page(__name__, path="/comparisons", title="Comparisons")


def _empty_fig(message="No data available", height=320):
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font={"size": 14, "color": COLORS["gray"]})
    fig.update_layout(
        height=height, paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


# ---------------------------------------------------------------------------
# Section card helper
# ---------------------------------------------------------------------------

def _section_card(title, subtitle, bg_color, children):
    """Wrap content in a visually distinct section card."""
    return html.Div(
        style={
            "padding": "28px",
            "backgroundColor": bg_color,
            "borderRadius": "10px",
            "marginBottom": "32px",
        },
        children=[
            html.H2(title, style={
                "marginTop": "0", "marginBottom": "6px", "fontSize": "22px",
                "fontWeight": "700", "color": COLORS["ink"],
                "fontFamily": FONT_FAMILY}),
            html.P(subtitle, style={
                "marginTop": "0", "marginBottom": "24px",
                "color": COLORS["gray"], "fontSize": "13px",
                "fontFamily": FONT_FAMILY, "lineHeight": "1.5"}),
            *children,
        ],
    )


def _chart_card(children, margin_bottom="20px"):
    """White card wrapper for a chart."""
    return html.Div(
        style={
            "backgroundColor": "#fff",
            "borderRadius": "8px",
            "border": f"1px solid {COLORS['border']}",
            "padding": "16px",
            "marginBottom": margin_bottom,
            "overflow": "hidden",
        },
        children=children,
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    """Return the page layout."""
    return html.Div(
        style={"padding": "20px", "fontFamily": FONT_FAMILY,
               "maxWidth": "1200px", "margin": "0 auto"},
        children=[
            # ===== Section 1: Head-to-Head (real data) =====
            _section_card(
                "Head-to-Head Comparison",
                "Select two entities to compare their Advisor DNA performance "
                "profiles across all seven dimensions.",
                COLORS.get("soft_lavender", "#f3f0ff"),
                [
                    # Controls Row
                    html.Div(
                        style={"display": "flex", "gap": "24px",
                               "marginBottom": "20px", "flexWrap": "wrap",
                               "alignItems": "flex-end"},
                        children=[
                            html.Div(
                                style={"minWidth": "200px"},
                                children=[
                                    html.Label("Entity Type:", style={
                                        "fontWeight": "600", "marginBottom": "6px",
                                        "display": "block",
                                        "color": COLORS["ink"], "fontSize": "12px"}),
                                    dcc.RadioItems(
                                        id="entity-type-radio",
                                        options=[
                                            {"label": " Firm", "value": "firm"},
                                            {"label": " Advisor", "value": "advisor"},
                                            {"label": " Both", "value": "both"},
                                        ],
                                        value="both", inline=True,
                                        style={"display": "flex", "gap": "14px"},
                                        labelStyle={
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "fontSize": "13px",
                                        }),
                                ],
                            ),
                            html.Div(
                                style={"minWidth": "180px"},
                                children=[
                                    html.Label("Calculation Method:", style={
                                        "fontWeight": "600", "marginBottom": "6px",
                                        "display": "block",
                                        "color": COLORS["ink"], "fontSize": "12px"}),
                                    dcc.Dropdown(
                                        id="entity-method-dropdown",
                                        options=[
                                            {"label": "Mean", "value": "mean"},
                                            {"label": "Penalized", "value": "penalized"},
                                            {"label": "Weighted", "value": "weighted"},
                                        ],
                                        value="mean",
                                        style={"fontSize": "13px"}),
                                ],
                            ),
                            html.Div(
                                style={"minWidth": "200px"},
                                children=[
                                    html.Label("Pool:", style={
                                        "fontWeight": "600", "marginBottom": "6px",
                                        "display": "block",
                                        "color": COLORS["ink"], "fontSize": "12px"}),
                                    dcc.RadioItems(
                                        id="entity-pool-radio",
                                        options=[
                                            {"label": " All", "value": "all"},
                                            {"label": " Premier (20+ reviews)",
                                             "value": "premier"},
                                        ],
                                        value="all", inline=True,
                                        style={"display": "flex", "gap": "14px"},
                                        labelStyle={
                                            "display": "inline-flex",
                                            "alignItems": "center",
                                            "fontSize": "13px",
                                        }),
                                ],
                            ),
                        ],
                    ),

                    # Entity Dropdowns Row
                    html.Div(
                        style={"display": "grid",
                               "gridTemplateColumns": "1fr 1fr",
                               "gap": "16px", "marginBottom": "20px"},
                        children=[
                            html.Div([
                                html.Label("Entity A:", style={
                                    "fontWeight": "600", "marginBottom": "6px",
                                    "display": "block",
                                    "color": COLORS["blue"], "fontSize": "12px"}),
                                dcc.Dropdown(
                                    id="entity-a-dropdown",
                                    placeholder="Select Entity A...",
                                    style={"fontSize": "13px"}),
                            ]),
                            html.Div([
                                html.Label("Entity B:", style={
                                    "fontWeight": "600", "marginBottom": "6px",
                                    "display": "block",
                                    "color": "#D4376E", "fontSize": "12px"}),
                                dcc.Dropdown(
                                    id="entity-b-dropdown",
                                    placeholder="Select Entity B...",
                                    style={"fontSize": "13px"}),
                            ]),
                        ],
                    ),

                    # Entity Spider Chart
                    _chart_card([
                        dcc.Graph(
                            id="entity-spider-chart",
                            figure=_empty_fig("Select two entities above", 420),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "420px"},
                        ),
                    ]),

                    # Comparison Table
                    _chart_card([
                        html.Div(id="entity-comparison-table"),
                    ], margin_bottom="0"),
                ],
            ),

        ],
    )


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("entity-a-dropdown", "options"),
    Output("entity-b-dropdown", "options"),
    Output("entity-a-dropdown", "value"),
    Output("entity-b-dropdown", "value"),
    Input("entity-type-radio", "value"),
    Input("entity-pool-radio", "value"),
    State("entity-a-dropdown", "value"),
    State("entity-b-dropdown", "value"),
)
def update_entity_dropdowns(entity_type, pool, current_a, current_b):
    """Update entity dropdown options based on type and pool filter."""
    entities = get_dna_entities()
    if not entities:
        return [], [], None, None

    min_reviews = 20 if pool == "premier" else 0

    options = []
    if entity_type in ("both", "firm"):
        for f in entities.get("firms", []):
            rc = f.get("review_count") or 0
            if rc < min_reviews:
                continue
            options.append({
                "label": f"{f.get('advisor_name', 'Unknown')} (Firm)",
                "value": f.get("advisor_id", "")
            })
    if entity_type in ("both", "advisor"):
        for a in entities.get("advisors", []):
            rc = a.get("review_count") or 0
            if rc < min_reviews:
                continue
            options.append({
                "label": f"{a.get('advisor_name', 'Unknown')} (Advisor)",
                "value": a.get("advisor_id", "")
            })

    # Preserve current selections if they're still in the filtered options
    valid_ids = {o["value"] for o in options}
    new_a = current_a if current_a in valid_ids else None
    new_b = current_b if current_b in valid_ids else None

    return options, options, new_a, new_b


def _extract_score(dim_data, key="raw"):
    """Extract a score from enriched (dict) or legacy (float) format."""
    if isinstance(dim_data, dict):
        return dim_data.get(key, 0) or 0
    return dim_data or 0


def _ordinal(n):
    """Return ordinal string (e.g. 92 -> '92nd')."""
    n = int(round(n))
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd'][min(n % 10, 4) if n % 10 < 4 else 0]}"


@callback(
    Output("entity-spider-chart", "figure"),
    Output("entity-comparison-table", "children"),
    Input("entity-a-dropdown", "value"),
    Input("entity-b-dropdown", "value"),
    Input("entity-method-dropdown", "value"),
)
def update_entity_comparison(entity_a_id, entity_b_id, method):
    """Update entity comparison chart and table with percentile display."""
    if not entity_a_id or not entity_b_id:
        return _empty_fig("Select two entities to compare.", 420), html.Div()

    results = get_entity_comparison([entity_a_id, entity_b_id], method=method)
    if not results or len(results) < 2:
        return _empty_fig("No comparison data available.", 420), html.Div()

    entity_a = results[0]
    entity_b = results[1]
    a_name = entity_a.get("advisor_name", "Entity A")
    b_name = entity_b.get("advisor_name", "Entity B")
    a_scores = entity_a.get("scores", {})
    b_scores = entity_b.get("scores", {})

    # Spider chart — uses percentile for consistent 0-100 scale
    spider_fig = go.Figure()
    for entity_data, name, color in [
        (a_scores, a_name, COLORS["blue"]),
        (b_scores, b_name, "#D4376E"),
    ]:
        values = [_extract_score(entity_data.get(dim, {}), "percentile") for dim in DIMENSIONS]
        values.append(values[0])
        ordinals = [_ordinal(v) for v in values]
        spider_fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[DIM_SHORT[d] for d in DIMENSIONS] + [DIM_SHORT[DIMENSIONS[0]]],
            fill="toself", name=name,
            line={"color": color, "width": 2}, fillcolor=color, opacity=0.4,
            customdata=ordinals,
            hovertemplate="%{theta}<br>Percentile: %{customdata}<extra></extra>",
        ))

    spider_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont={"size": 10, "family": FONT_FAMILY},
                            gridcolor=COLORS["border"]),
            angularaxis=dict(tickfont={"size": 11, "family": FONT_FAMILY}),
            bgcolor="rgba(255,255,255,0.5)",
        ),
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="closest", showlegend=True,
        legend={"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center",
                "font": {"size": 11}},
        title={"text": f"{a_name} vs {b_name} (Percentile Rank)",
               "x": 0.5, "xanchor": "center",
               "font": {"size": 15, "color": COLORS["ink"]}},
        margin={"l": 60, "r": 60, "t": 60, "b": 80},
        height=420,
        paper_bgcolor="white",
    )

    # Comparison table — shows percentile (raw) per cell + composite row
    all_dims = list(DIMENSIONS) + ["composite"]
    dim_labels_ext = {**DIM_LABELS, "composite": "Composite"}

    table_rows = []
    for dim in all_dims:
        is_composite = dim == "composite"
        a_data = a_scores.get(dim, {})
        b_data = b_scores.get(dim, {})
        a_pctile = _extract_score(a_data, "percentile")
        b_pctile = _extract_score(b_data, "percentile")
        a_raw = _extract_score(a_data, "raw")
        b_raw = _extract_score(b_data, "raw")

        pctile_diff = b_pctile - a_pctile
        if pctile_diff > 0:
            diff_color, diff_text = "#10b981", f"+{pctile_diff:.0f}"
        elif pctile_diff < 0:
            diff_color, diff_text = "#ef4444", f"{pctile_diff:.0f}"
        else:
            diff_color, diff_text = COLORS["gray"], "0"

        border_top = f"2px solid {COLORS['border']}" if is_composite else "none"

        table_rows.append(html.Tr([
            html.Td(dim_labels_ext.get(dim, dim), style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": border_top,
                "fontWeight": "700" if is_composite else "500",
                "color": COLORS["ink"]}),
            html.Td(html.Span([
                html.Span(f"{_ordinal(a_pctile)} ", style={"fontWeight": "700"}),
                html.Span(f"({a_raw:.3f})", style={"fontSize": "11px", "color": COLORS["gray"]}),
            ]), style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": border_top,
                "textAlign": "center", "color": COLORS["blue"]}),
            html.Td(html.Span([
                html.Span(f"{_ordinal(b_pctile)} ", style={"fontWeight": "700"}),
                html.Span(f"({b_raw:.3f})", style={"fontSize": "11px", "color": COLORS["gray"]}),
            ]), style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": border_top,
                "textAlign": "center", "color": "#D4376E"}),
            html.Td(diff_text, style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": border_top,
                "textAlign": "center", "color": diff_color,
                "fontWeight": "600"}),
        ]))

    table = html.Table([
        html.Thead(html.Tr([
            html.Th("Dimension", style={
                "padding": "10px 12px", "textAlign": "left", "fontWeight": "700",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th(a_name, style={
                "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["blue"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th(b_name, style={
                "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
                "backgroundColor": COLORS["soft_blue"], "color": "#D4376E",
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th("Diff (percentile)", style={
                "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
        ])),
        html.Tbody(table_rows),
    ], style={
        "width": "100%", "borderCollapse": "collapse",
        "fontFamily": FONT_FAMILY, "fontSize": "13px"})

    return spider_fig, table
