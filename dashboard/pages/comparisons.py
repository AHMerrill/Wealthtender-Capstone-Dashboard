"""Comparisons page for Wealthtender Dashboard.

Provides interactive visualizations for:
1. Intra-Firm Team Comparison (FB-16): Side-by-side radar/bar charts of all advisors within a group
2. Entity-to-Entity Comparison (FB-17): Overlaid spider charts comparing two entities

Note: Partner group associations and data are mocked for development.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.services.api import (
    get_partner_groups,
    get_partner_group_members,
    get_dna_entities,
    get_entity_comparison,
)

dash.register_page(__name__, path="/comparisons", title="Comparisons")

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
    "listening_personalization": "Customer Empathy & Personalization",
    "communication_clarity": "Communication Clarity",
    "responsiveness_availability": "Responsiveness",
    "life_event_support": "Life Event Support",
    "investment_expertise": "Investment Expertise",
}

DIM_SHORT = {
    "trust_integrity": "Trust",
    "listening_personalization": "Empathy",
    "communication_clarity": "Clarity",
    "responsiveness_availability": "Responsive",
    "life_event_support": "Life Events",
    "investment_expertise": "Expertise",
}


def _empty_fig(message="No data available"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font={"size": 14, "color": COLORS["gray"]})
    fig.update_layout(height=350, paper_bgcolor="white", plot_bgcolor="white",
                      margin=dict(l=20, r=20, t=20, b=20))
    return fig


def layout():
    """Return the page layout."""
    return html.Div([
        # Synthetic Data Disclaimer Banner
        html.Div([
            html.Div([
                html.Span("⚠️ ", style={"fontSize": "18px", "marginRight": "8px"}),
                html.Span("Development Mode: ",
                           style={"fontWeight": "600", "marginRight": "4px"}),
                html.Span(
                    "Partner group associations and all comparison data are mocked "
                    "for development purposes. This will be replaced with real data "
                    "in production."),
            ], style={
                "display": "flex", "alignItems": "flex-start", "lineHeight": "1.5",
                "padding": "14px 16px", "backgroundColor": "#fef3c7",
                "borderLeft": "4px solid #f59e0b", "borderRadius": "4px",
                "color": "#78350f", "fontSize": "13px", "fontFamily": FONT_FAMILY,
            }),
        ], style={"marginBottom": "28px"}),

        # Section 1: Intra-Firm Team Comparison
        html.Div([
            html.H2("Team Comparison", style={
                "marginTop": "0", "marginBottom": "12px", "fontSize": "24px",
                "fontWeight": "600", "color": COLORS["ink"], "fontFamily": FONT_FAMILY}),
            html.P(
                "Select a partner group to view side-by-side performance profiles "
                "of all advisors.",
                style={"marginTop": "0", "marginBottom": "20px",
                       "color": COLORS["gray"], "fontSize": "14px",
                       "fontFamily": FONT_FAMILY}),

            # Controls Row
            html.Div([
                html.Div([
                    html.Label("Select Firm / Partner Group:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="team-partner-group-dropdown",
                        placeholder="Choose a firm...",
                        style={"fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ], style={"flex": "1", "minWidth": "250px"}),
                html.Div([
                    html.Label("Calculation Method:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="team-method-dropdown",
                        options=[{"label": "Mean", "value": "mean"},
                                 {"label": "Penalized", "value": "penalized"},
                                 {"label": "Weighted", "value": "weighted"}],
                        value="mean",
                        style={"fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ], style={"flex": "1", "minWidth": "200px"}),
            ], style={"display": "flex", "marginBottom": "24px",
                      "gap": "20px", "flexWrap": "wrap"}),

            # Team Spider Chart
            html.Div([
                dcc.Loading(type="default", children=[
                    dcc.Graph(id="team-spider-chart",
                              config={"responsive": True, "displayModeBar": True}),
                ]),
            ], style={
                "marginBottom": "24px", "padding": "16px", "backgroundColor": "#fff",
                "borderRadius": "6px", "border": f"1px solid {COLORS['border']}"}),

            # Team Bar Chart
            html.Div([
                dcc.Loading(type="default", children=[
                    dcc.Graph(id="team-bar-chart",
                              config={"responsive": True, "displayModeBar": True}),
                ]),
            ], style={
                "padding": "16px", "backgroundColor": "#fff",
                "borderRadius": "6px", "border": f"1px solid {COLORS['border']}"}),
        ], style={
            "marginBottom": "48px", "padding": "24px",
            "backgroundColor": COLORS["soft_blue"], "borderRadius": "8px"}),

        # Section 2: Entity-to-Entity Comparison
        html.Div([
            html.H2("Head-to-Head Comparison", style={
                "marginTop": "0", "marginBottom": "12px", "fontSize": "24px",
                "fontWeight": "600", "color": COLORS["ink"], "fontFamily": FONT_FAMILY}),
            html.P(
                "Select two entities to compare their performance profiles "
                "across all dimensions.",
                style={"marginTop": "0", "marginBottom": "20px",
                       "color": COLORS["gray"], "fontSize": "14px",
                       "fontFamily": FONT_FAMILY}),

            # Controls Row
            html.Div([
                html.Div([
                    html.Label("Entity Type:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.RadioItems(
                        id="entity-type-radio",
                        options=[{"label": " Firm", "value": "firm"},
                                 {"label": " Advisor", "value": "advisor"},
                                 {"label": " Both", "value": "both"}],
                        value="both", inline=True,
                        style={"display": "flex", "gap": "16px"},
                        labelStyle={"display": "inline-flex", "alignItems": "center",
                                    "fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ]),
                html.Div([
                    html.Label("Calculation Method:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="entity-method-dropdown",
                        options=[{"label": "Mean", "value": "mean"},
                                 {"label": "Penalized", "value": "penalized"},
                                 {"label": "Weighted", "value": "weighted"}],
                        value="mean",
                        style={"fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ], style={"minWidth": "200px"}),
            ], style={"display": "flex", "gap": "40px", "marginBottom": "24px",
                      "flexWrap": "wrap"}),

            # Entity Dropdowns Row
            html.Div([
                html.Div([
                    html.Label("Entity A:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="entity-a-dropdown", placeholder="Select Entity A...",
                        style={"fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ], style={"flex": "1", "minWidth": "250px"}),
                html.Div([
                    html.Label("Entity B:", style={
                        "fontWeight": "500", "marginBottom": "8px",
                        "color": COLORS["ink"], "fontSize": "13px",
                        "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="entity-b-dropdown", placeholder="Select Entity B...",
                        style={"fontFamily": FONT_FAMILY, "fontSize": "13px"}),
                ], style={"flex": "1", "minWidth": "250px"}),
            ], style={"display": "flex", "marginBottom": "24px",
                      "gap": "20px", "flexWrap": "wrap"}),

            # Entity Spider Chart
            html.Div([
                dcc.Loading(type="default", children=[
                    dcc.Graph(id="entity-spider-chart",
                              config={"responsive": True, "displayModeBar": True}),
                ]),
            ], style={
                "marginBottom": "24px", "padding": "16px", "backgroundColor": "#fff",
                "borderRadius": "6px", "border": f"1px solid {COLORS['border']}"}),

            # Comparison Table
            html.Div([
                html.Div(id="entity-comparison-table"),
            ], style={
                "padding": "16px", "backgroundColor": "#fff",
                "borderRadius": "6px", "border": f"1px solid {COLORS['border']}"}),
        ], style={
            "padding": "24px", "backgroundColor": COLORS["soft_lavender"],
            "borderRadius": "8px"}),
    ], style={"padding": "20px", "fontFamily": FONT_FAMILY})


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
    # API returns: [{"partner_group_code": ..., "partner_group_name": ..., "member_count": ...}]
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
        return _empty_fig("Select a partner group"), _empty_fig("Select a partner group")

    # API returns {"group_code", "group_name", "members": [profile_dicts]}
    data = get_partner_group_members(group_code, method=method)
    if not data or not data.get("members"):
        return _empty_fig("No data for this group"), _empty_fig("No data for this group")

    members = data["members"]
    colors = DATA_VIZ_PALETTE[:len(members)]

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
            line={"color": colors[idx]},
            fillcolor=colors[idx], opacity=0.6,
        ))

    spider_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True,
                            tickfont={"size": 11, "family": FONT_FAMILY}),
            angularaxis=dict(tickfont={"size": 11, "family": FONT_FAMILY})),
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="closest", showlegend=True,
        legend={"x": 1.1, "y": 1, "font": {"size": 11}},
        title={"text": f"{data.get('group_name', group_code)} — Performance Profiles",
               "x": 0.5, "xanchor": "center",
               "font": {"size": 16, "color": COLORS["ink"]}},
        margin={"l": 80, "r": 200, "t": 100, "b": 80},
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
            y=values, marker={"color": colors[idx]}, opacity=0.8,
        ))

    bar_fig.update_layout(
        barmode="group",
        title={"text": "Team Scores by Dimension", "x": 0.5, "xanchor": "center",
               "font": {"size": 16, "color": COLORS["ink"]}},
        xaxis={"title": "Dimension", "tickfont": {"size": 11}, "title_font": {"size": 12}},
        yaxis={"title": "Score", "tickfont": {"size": 11}, "title_font": {"size": 12}},
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="x unified",
        legend={"x": 1.02, "y": 1, "font": {"size": 11}},
        margin={"l": 60, "r": 150, "t": 100, "b": 80},
        paper_bgcolor="white",
    )

    return spider_fig, bar_fig


@callback(
    Output("entity-a-dropdown", "options"),
    Output("entity-b-dropdown", "options"),
    Input("entity-type-radio", "value"),
)
def update_entity_dropdowns(entity_type):
    """Update entity dropdown options based on type filter."""
    # get_dna_entities() returns {"firms": [...], "advisors": [...]}
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
        return _empty_fig("Select two entities to compare."), html.Div()

    # API returns list of score dicts for each entity
    results = get_entity_comparison([entity_a_id, entity_b_id], method=method)
    if not results or len(results) < 2:
        return _empty_fig("No comparison data available."), html.Div()

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
            line={"color": color}, fillcolor=color, opacity=0.5,
        ))

    spider_fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True,
                            tickfont={"size": 11, "family": FONT_FAMILY}),
            angularaxis=dict(tickfont={"size": 11, "family": FONT_FAMILY})),
        font={"family": FONT_FAMILY, "size": 12},
        hovermode="closest", showlegend=True,
        legend={"x": 1.1, "y": 1, "font": {"size": 11}},
        title={"text": "Head-to-Head Performance Comparison",
               "x": 0.5, "xanchor": "center",
               "font": {"size": 16, "color": COLORS["ink"]}},
        margin={"l": 80, "r": 200, "t": 100, "b": 80},
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
                "padding": "12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "fontWeight": "500", "color": COLORS["ink"]}),
            html.Td(f"{a_val:.3f}", style={
                "padding": "12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "textAlign": "center", "color": COLORS["blue"], "fontWeight": "500"}),
            html.Td(f"{b_val:.3f}", style={
                "padding": "12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "textAlign": "center", "color": "#D4376E", "fontWeight": "500"}),
            html.Td(diff_text, style={
                "padding": "12px",
                "borderBottom": f"1px solid {COLORS['border']}",
                "textAlign": "center", "color": diff_color, "fontWeight": "500"}),
        ]))

    table = html.Table([
        html.Thead(html.Tr([
            html.Th("Dimension", style={
                "padding": "12px", "textAlign": "left", "fontWeight": "600",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th(a_name, style={
                "padding": "12px", "textAlign": "center", "fontWeight": "600",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["blue"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th(b_name, style={
                "padding": "12px", "textAlign": "center", "fontWeight": "600",
                "backgroundColor": COLORS["soft_blue"], "color": "#D4376E",
                "borderBottom": f"2px solid {COLORS['border']}"}),
            html.Th("Difference (B − A)", style={
                "padding": "12px", "textAlign": "center", "fontWeight": "600",
                "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
                "borderBottom": f"2px solid {COLORS['border']}"}),
        ])),
        html.Tbody(table_rows),
    ], style={
        "width": "100%", "borderCollapse": "collapse",
        "fontFamily": FONT_FAMILY, "fontSize": "13px"})

    return spider_fig, table
