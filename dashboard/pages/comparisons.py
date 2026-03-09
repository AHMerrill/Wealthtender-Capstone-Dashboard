"""Comparisons page for Wealthtender Dashboard.

Provides interactive visualizations for:
1. Intra-Firm Team Comparison (FB-16): Side-by-side radar/bar charts of all advisors within a group
2. Entity-to-Entity Comparison (FB-17): Overlaid spider charts comparing two entities

Note: Partner group associations and data are mocked for development.
"""

import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_SHORT
from dashboard.services.api import (
    get_partner_groups,
    get_partner_group_members,
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
                "profiles across all six dimensions.",
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

            # ===== Section 2: Team Comparison (mocked data) =====
            _section_card(
                "Team Comparison",
                "Select a partner group to view side-by-side performance "
                "profiles of all advisors within a firm.",
                COLORS["soft_blue"],
                [
                    # Dev mode banner — scoped to this section only
                    html.Div(
                        style={
                            "display": "flex", "alignItems": "flex-start",
                            "lineHeight": "1.5",
                            "padding": "12px 14px", "backgroundColor": "#fef3c7",
                            "borderLeft": "4px solid #f59e0b", "borderRadius": "4px",
                            "color": "#78350f", "fontSize": "12px",
                            "fontFamily": FONT_FAMILY, "marginBottom": "20px",
                        },
                        children=[
                            html.Span("Dev Mode: ",
                                      style={"fontWeight": "600",
                                             "marginRight": "4px"}),
                            html.Span(
                                "Partner group associations are mocked for "
                                "development. Will be replaced with real data "
                                "in production."),
                        ],
                    ),

                    # Controls Row
                    html.Div(
                        style={"display": "flex", "gap": "16px",
                               "marginBottom": "20px", "flexWrap": "wrap"},
                        children=[
                            html.Div(
                                style={"flex": "2", "minWidth": "250px"},
                                children=[
                                    html.Label("Firm / Partner Group:", style={
                                        "fontWeight": "600", "marginBottom": "6px",
                                        "display": "block",
                                        "color": COLORS["ink"], "fontSize": "12px"}),
                                    dcc.Dropdown(
                                        id="team-partner-group-dropdown",
                                        placeholder="Choose a firm...",
                                        style={"fontSize": "13px"}),
                                ],
                            ),
                            html.Div(
                                style={"flex": "1", "minWidth": "180px"},
                                children=[
                                    html.Label("Calculation Method:", style={
                                        "fontWeight": "600", "marginBottom": "6px",
                                        "display": "block",
                                        "color": COLORS["ink"], "fontSize": "12px"}),
                                    dcc.Dropdown(
                                        id="team-method-dropdown",
                                        options=[
                                            {"label": "Mean", "value": "mean"},
                                            {"label": "Penalized", "value": "penalized"},
                                            {"label": "Weighted", "value": "weighted"},
                                        ],
                                        value="mean",
                                        style={"fontSize": "13px"}),
                                ],
                            ),
                        ],
                    ),

                    # Team Spider Chart
                    _chart_card([
                        dcc.Graph(
                            id="team-spider-chart",
                            figure=_empty_fig("Select a partner group above", 400),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "400px"},
                        ),
                    ]),

                    # Team Bar Chart
                    _chart_card([
                        dcc.Graph(
                            id="team-bar-chart",
                            figure=_empty_fig("Select a partner group above", 350),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "350px"},
                        ),
                    ], margin_bottom="0"),
                ],
            ),
        ],
    )


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("team-partner-group-dropdown", "options"),
    Output("team-partner-group-dropdown", "value"),
    Input("team-partner-group-dropdown", "id"),
)
def populate_partner_groups(_):
    """Populate partner group dropdown on page load."""
    groups = get_partner_groups()
    if not groups:
        return [], None
    options = [
        {"label": f"{g['partner_group_name']} ({g.get('member_count', '?')} members)",
         "value": g["partner_group_code"]}
        for g in groups
    ]
    return options, groups[0]["partner_group_code"]


@callback(
    Output("team-spider-chart", "figure"),
    Output("team-bar-chart", "figure"),
    Input("team-partner-group-dropdown", "value"),
    Input("team-method-dropdown", "value"),
)
def update_team_charts(group_code, method):
    """Update team comparison charts."""
    if not group_code:
        return _empty_fig("Select a partner group", 400), \
               _empty_fig("Select a partner group", 350)

    data = get_partner_group_members(group_code, method=method)
    if not data or not data.get("members"):
        return _empty_fig("No data for this group", 400), \
               _empty_fig("No data for this group", 350)

    members = data["members"]
    colors = DATA_VIZ_PALETTE[:len(members)]
    group_name = data.get("group_name", group_code)

    # Spider chart
    spider_fig = go.Figure()
    for idx, member in enumerate(members):
        name = member.get("advisor_name", "Unknown")
        scores = member.get("scores", {})
        values = [scores.get(dim, 0) for dim in DIMENSIONS]
        values.append(values[0])  # close loop

        spider_fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[DIM_SHORT[d] for d in DIMENSIONS] + [DIM_SHORT[DIMENSIONS[0]]],
            fill="toself", name=name,
            line={"color": colors[idx], "width": 2},
            fillcolor=colors[idx], opacity=0.5,
        ))

    spider_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True,
                            tickfont={"size": 10, "family": FONT_FAMILY},
                            gridcolor=COLORS["border"]),
            angularaxis=dict(tickfont={"size": 11, "family": FONT_FAMILY}),
            bgcolor="rgba(255,255,255,0.5)",
        ),
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="closest", showlegend=True,
        legend={"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center",
                "font": {"size": 11}},
        title={"text": f"{group_name} — Performance Profiles",
               "x": 0.5, "xanchor": "center",
               "font": {"size": 15, "color": COLORS["ink"]}},
        margin={"l": 60, "r": 60, "t": 60, "b": 80},
        height=400,
        paper_bgcolor="white",
    )

    # Bar chart
    bar_fig = go.Figure()
    for idx, member in enumerate(members):
        name = member.get("advisor_name", "Unknown")
        scores = member.get("scores", {})
        values = [scores.get(dim, 0) for dim in DIMENSIONS]
        bar_fig.add_trace(go.Bar(
            name=name,
            x=[DIM_SHORT[d] for d in DIMENSIONS],
            y=values, marker={"color": colors[idx]}, opacity=0.85,
        ))

    bar_fig.update_layout(
        barmode="group",
        title={"text": "Team Scores by Dimension", "x": 0.5, "xanchor": "center",
               "font": {"size": 15, "color": COLORS["ink"]}},
        xaxis={"title": "", "tickfont": {"size": 11}},
        yaxis={"title": "Score", "tickfont": {"size": 11}, "title_font": {"size": 12},
               "gridcolor": COLORS["border"]},
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.18, "x": 0.5, "xanchor": "center",
                "font": {"size": 11}},
        margin={"l": 50, "r": 20, "t": 60, "b": 70},
        height=350,
        paper_bgcolor="white", plot_bgcolor="white",
    )

    return spider_fig, bar_fig


@callback(
    Output("entity-a-dropdown", "options"),
    Output("entity-b-dropdown", "options"),
    Input("entity-type-radio", "value"),
)
def update_entity_dropdowns(entity_type):
    """Update entity dropdown options based on type filter."""
    entities = get_dna_entities()
    if not entities:
        return [], []

    options = []
    if entity_type in ("both", "firm"):
        for f in entities.get("firms", []):
            options.append({
                "label": f"{f.get('advisor_name', 'Unknown')} (Firm)",
                "value": f.get("advisor_id", "")
            })
    if entity_type in ("both", "advisor"):
        for a in entities.get("advisors", []):
            options.append({
                "label": f"{a.get('advisor_name', 'Unknown')} (Advisor)",
                "value": a.get("advisor_id", "")
            })

    return options, options


@callback(
    Output("entity-spider-chart", "figure"),
    Output("entity-comparison-table", "children"),
    Input("entity-a-dropdown", "value"),
    Input("entity-b-dropdown", "value"),
    Input("entity-method-dropdown", "value"),
)
def update_entity_comparison(entity_a_id, entity_b_id, method):
    """Update entity comparison chart and table."""
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

    # Spider chart
    spider_fig = go.Figure()
    for entity_data, name, color in [
        (a_scores, a_name, COLORS["blue"]),
        (b_scores, b_name, "#D4376E"),
    ]:
        values = [entity_data.get(dim, 0) for dim in DIMENSIONS]
        values.append(values[0])
        spider_fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[DIM_SHORT[d] for d in DIMENSIONS] + [DIM_SHORT[DIMENSIONS[0]]],
            fill="toself", name=name,
            line={"color": color, "width": 2}, fillcolor=color, opacity=0.4,
        ))

    spider_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True,
                            tickfont={"size": 10, "family": FONT_FAMILY},
                            gridcolor=COLORS["border"]),
            angularaxis=dict(tickfont={"size": 11, "family": FONT_FAMILY}),
            bgcolor="rgba(255,255,255,0.5)",
        ),
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="closest", showlegend=True,
        legend={"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center",
                "font": {"size": 11}},
        title={"text": f"{a_name} vs {b_name}",
               "x": 0.5, "xanchor": "center",
               "font": {"size": 15, "color": COLORS["ink"]}},
        margin={"l": 60, "r": 60, "t": 60, "b": 80},
        height=420,
        paper_bgcolor="white",
    )

    # Comparison table
    table_rows = []
    for dim in DIMENSIONS:
        a_val = a_scores.get(dim, 0)
        b_val = b_scores.get(dim, 0)
        diff = b_val - a_val
        if diff > 0:
            diff_color, diff_text = "#10b981", f"+{diff:.3f}"
        elif diff < 0:
            diff_color, diff_text = "#ef4444", f"{diff:.3f}"
        else:
            diff_color, diff_text = COLORS["gray"], "0.000"

        table_rows.append(html.Tr([
            html.Td(DIM_LABELS[dim], style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "fontWeight": "500", "color": COLORS["ink"]}),
            html.Td(f"{a_val:.3f}", style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "textAlign": "center", "color": COLORS["blue"],
                "fontWeight": "600"}),
            html.Td(f"{b_val:.3f}", style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "textAlign": "center", "color": "#D4376E",
                "fontWeight": "600"}),
            html.Td(diff_text, style={
                "padding": "10px 12px",
                "borderBottom": f"1px solid {COLORS['border']}",
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
            html.Th("Difference (B − A)", style={
                "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
        ])),
        html.Tbody(table_rows),
    ], style={
        "width": "100%", "borderCollapse": "collapse",
        "fontFamily": FONT_FAMILY, "fontSize": "13px"})

    return spider_fig, table
