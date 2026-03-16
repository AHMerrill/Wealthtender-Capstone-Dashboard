"""Team Comparisons page for Wealthtender Dashboard.

Provides intra-firm team comparison (FB-16): side-by-side radar/bar charts
of all advisors within a partner group.

Split out from comparisons.py to give Team Comparisons its own tab.
"""

import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_SHORT
from dashboard.services.api import (
    get_partner_groups,
    get_partner_group_members,
)

dash.register_page(__name__, path="/team-comparisons", title="Team Comparisons")


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


def _ordinal(n):
    """Return ordinal string (e.g. 92 -> '92nd')."""
    n = int(round(n))
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd'][min(n % 10, 4) if n % 10 < 4 else 0]}"


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    """Return the page layout."""
    return html.Div(
        style={"padding": "20px", "fontFamily": FONT_FAMILY,
               "maxWidth": "1200px", "margin": "0 auto"},
        children=[
            _section_card(
                "Team Comparison",
                "Select a partner group to view side-by-side performance "
                "profiles of all advisors within a firm.",
                COLORS["soft_blue"],
                [
                    # Dev mode banner
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
                                        id="tc-partner-group-dropdown",
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
                                        id="tc-method-dropdown",
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
                            id="tc-spider-chart",
                            figure=_empty_fig("Select a partner group above", 400),
                            config={"responsive": True, "displayModeBar": False},
                            style={"height": "400px"},
                        ),
                    ]),

                    # Team Bar Chart
                    _chart_card([
                        dcc.Graph(
                            id="tc-bar-chart",
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
    Output("tc-partner-group-dropdown", "options"),
    Output("tc-partner-group-dropdown", "value"),
    Input("tc-partner-group-dropdown", "id"),
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
    Output("tc-spider-chart", "figure"),
    Output("tc-bar-chart", "figure"),
    Input("tc-partner-group-dropdown", "value"),
    Input("tc-method-dropdown", "value"),
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

    def _get_dim_val(scores, dim, key="percentile"):
        """Extract a value from enriched or legacy score dicts."""
        v = scores.get(dim, {})
        if isinstance(v, dict):
            return v.get(key, 0) or 0
        return v or 0

    # Spider chart
    spider_fig = go.Figure()
    for idx, member in enumerate(members):
        name = member.get("advisor_name", "Unknown")
        scores = member.get("scores", {})
        values = [_get_dim_val(scores, dim, "percentile") for dim in DIMENSIONS]
        values.append(values[0])  # close loop
        ordinals = [_ordinal(v) for v in values]

        spider_fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[DIM_SHORT[d] for d in DIMENSIONS] + [DIM_SHORT[DIMENSIONS[0]]],
            fill="toself", name=name,
            line={"color": colors[idx], "width": 2},
            fillcolor=colors[idx], opacity=0.5,
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
        title={"text": f"{group_name} -- Performance Profiles (Percentile)",
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
        values = [_get_dim_val(scores, dim, "percentile") for dim in DIMENSIONS]
        bar_fig.add_trace(go.Bar(
            name=name,
            x=[DIM_SHORT[d] for d in DIMENSIONS],
            y=values, marker={"color": colors[idx]}, opacity=0.85,
        ))

    bar_fig.update_layout(
        barmode="group",
        title={"text": "Team Percentile Ranks by Dimension", "x": 0.5, "xanchor": "center",
               "font": {"size": 15, "color": COLORS["ink"]}},
        xaxis={"title": "", "tickfont": {"size": 11}},
        yaxis={"title": "Percentile Rank", "tickfont": {"size": 11},
               "title_font": {"size": 12}, "range": [0, 105],
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
