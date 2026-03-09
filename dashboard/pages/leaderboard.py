"""Leaderboard page for Wealthtender Dashboard (FB-14, FB-15).

Features:
- Top-N entities per dimension with horizontal bar charts
- Composite (average across all dimensions) leaderboard
- Filterable by entity type, pool, and scoring method
- Click to expand inline detail card with full 6-dimension profile
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ALL, ctx
import plotly.graph_objects as go

from dashboard.branding import COLORS, DATA_VIZ_PALETTE, FONT_FAMILY
from dashboard.services.api import get_leaderboard, get_dna_advisor_scores

dash.register_page(__name__, path="/leaderboard", title="Leaderboard")

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

DIM_COLORS = {dim: DATA_VIZ_PALETTE[i] for i, dim in enumerate(DIMENSIONS[:6])}


def _create_bar_chart(data, dimension, method):
    """Create a horizontal bar chart for the leaderboard."""
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["gray"], family=FONT_FAMILY),
        )
        fig.update_layout(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            height=300, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor="white",
        )
        return fig

    sorted_data = sorted(data, key=lambda x: x.get("score", 0), reverse=True)
    names = [item["advisor_name"] for item in sorted_data]
    scores = [item.get("score", 0) for item in sorted_data]
    entity_ids = [item["advisor_id"] for item in sorted_data]
    customdata = [[eid] for eid in entity_ids]

    # Pick color: composite gets navy, individual dims get their palette color
    if dimension == "composite":
        bar_color = COLORS["navy"]
        title_text = f"Composite Score — {method.title()}"
    else:
        bar_color = DIM_COLORS.get(dimension, COLORS["blue"])
        title_text = f"{DIM_LABELS.get(dimension, dimension)} — {method.title()}"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=scores, orientation="h",
        marker=dict(color=bar_color,
                    line=dict(color=COLORS["navy"], width=1)),
        text=[f"{s:.3f}" for s in scores],
        textposition="outside",
        textfont=dict(family=FONT_FAMILY, size=11, color=COLORS["ink"]),
        hovertemplate="%{y}<br>Score: %{x:.3f}<extra></extra>",
        customdata=customdata, name="Score",
    ))

    fig.update_layout(
        title={"text": title_text,
               "x": 0.5, "xanchor": "center",
               "font": dict(size=16, color=COLORS["ink"], family=FONT_FAMILY)},
        xaxis=dict(title="Score",
                   titlefont=dict(family=FONT_FAMILY, size=12, color=COLORS["ink"]),
                   tickfont=dict(family=FONT_FAMILY, size=10, color=COLORS["gray"]),
                   gridcolor=COLORS["border"], showgrid=True, zeroline=False),
        yaxis=dict(tickfont=dict(family=FONT_FAMILY, size=11, color=COLORS["ink"]),
                   automargin=True),
        height=max(300, len(names) * 36 + 120),
        margin=dict(l=200, r=100, t=80, b=60),
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="y unified", showlegend=False,
    )
    return fig


def _create_spider_chart(profile_scores, entity_name):
    """Create a spider/radar chart for the detail panel."""
    categories = [DIM_LABELS[dim] for dim in DIMENSIONS]
    values = [profile_scores.get(dim, 0) for dim in DIMENSIONS]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill="toself",
        marker=dict(color=COLORS["soft_blue"]),
        line=dict(color=COLORS["blue"], width=2),
        fillcolor="rgba(227, 245, 254, 0.6)",
        name=entity_name,
        hovertemplate="%{theta}<br>Score: %{r:.3f}<extra></extra>",
    ))

    fig.update_layout(
        title={"text": f"{entity_name} — Full Profile", "x": 0.5, "xanchor": "center",
               "font": dict(size=14, color=COLORS["ink"], family=FONT_FAMILY)},
        polar=dict(
            radialaxis=dict(visible=True,
                            tickfont=dict(family=FONT_FAMILY, size=9, color=COLORS["gray"]),
                            gridcolor=COLORS["border"]),
            angularaxis=dict(tickfont=dict(family=FONT_FAMILY, size=10, color=COLORS["ink"])),
            bgcolor="rgba(255,255,255,0.5)"),
        height=350, margin=dict(l=80, r=80, t=60, b=60),
        paper_bgcolor="white", font=dict(family=FONT_FAMILY), showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    dim_options = [{"label": "⭐ Composite (All Dimensions)", "value": "composite"}] + \
                  [{"label": DIM_LABELS[d], "value": d} for d in DIMENSIONS]

    return html.Div([
        html.Div([
            html.H2("Leaderboard", style={
                "margin": "0 0 8px 0", "color": COLORS["ink"],
                "fontSize": "24px", "fontFamily": FONT_FAMILY}),
            html.P("View top-performing entities across Advisor DNA dimensions.",
                   style={"margin": "0", "color": COLORS["gray"],
                          "fontSize": "14px", "fontFamily": FONT_FAMILY}),
        ], style={"paddingBottom": "24px",
                  "borderBottom": f"1px solid {COLORS['border']}"}),

        # Controls row
        html.Div([
            html.Div([
                html.Label("Dimension:", style={
                    "fontSize": "12px", "fontWeight": "600",
                    "color": COLORS["gray"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="lb-dimension-dropdown",
                    options=dim_options,
                    value="composite", clearable=False, style={"fontSize": "12px"}),
            ], style={"flex": "2", "minWidth": "250px"}),
            html.Div([
                html.Label("Method:", style={
                    "fontSize": "12px", "fontWeight": "600",
                    "color": COLORS["gray"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="lb-method-dropdown",
                    options=[{"label": "Mean", "value": "mean"},
                             {"label": "Penalized", "value": "penalized"},
                             {"label": "Weighted", "value": "weighted"}],
                    value="mean", clearable=False, style={"fontSize": "12px"}),
            ], style={"flex": "1", "minWidth": "150px"}),
            html.Div([
                html.Label("Entity Type:", style={
                    "fontSize": "12px", "fontWeight": "600",
                    "color": COLORS["gray"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="lb-entity-type-dropdown",
                    options=[{"label": "All", "value": "all"},
                             {"label": "Firm", "value": "firm"},
                             {"label": "Advisor", "value": "advisor"}],
                    value="all", clearable=False, style={"fontSize": "12px"}),
            ], style={"flex": "1", "minWidth": "150px"}),
            html.Div([
                html.Label("Pool:", style={
                    "fontSize": "12px", "fontWeight": "600",
                    "color": COLORS["gray"], "marginBottom": "4px"}),
                dcc.Dropdown(
                    id="lb-pool-dropdown",
                    options=[{"label": "All", "value": "all"},
                             {"label": "Premier", "value": "premier"}],
                    value="all", clearable=False, style={"fontSize": "12px"}),
            ], style={"flex": "1", "minWidth": "120px"}),
        ], style={"display": "flex", "gap": "12px", "marginTop": "24px",
                  "marginBottom": "16px", "flexWrap": "wrap"}),

        # Top N slider
        html.Div([
            html.Label("Top N:", style={
                "fontSize": "12px", "fontWeight": "600",
                "color": COLORS["gray"], "marginRight": "12px"}),
            html.Div([
                dcc.Slider(
                    id="lb-top-n-slider", min=5, max=25, step=1, value=5,
                    marks={5: "5", 10: "10", 15: "15", 20: "20", 25: "25"},
                    tooltip={"placement": "bottom", "always_visible": True}),
            ], style={"flex": "1", "minWidth": "300px", "marginLeft": "16px"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "24px"}),

        # Chart container
        html.Div([
            dcc.Loading(type="default", children=[
                dcc.Graph(id="lb-chart", config={"displayModeBar": True, "responsive": True}),
            ]),
        ], style={
            "backgroundColor": "white", "padding": "20px", "borderRadius": "8px",
            "border": f"1px solid {COLORS['border']}", "marginBottom": "24px"}),

        # Detail panel
        html.Div(id="lb-detail-panel", children=[]),

        # Hidden store for selected entity
        dcc.Store(id="lb-clicked-entity", data=None),
    ], style={"padding": "20px", "fontFamily": FONT_FAMILY})


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("lb-chart", "figure"),
    Input("lb-dimension-dropdown", "value"),
    Input("lb-method-dropdown", "value"),
    Input("lb-entity-type-dropdown", "value"),
    Input("lb-pool-dropdown", "value"),
    Input("lb-top-n-slider", "value"),
)
def update_leaderboard_chart(dimension, method, entity_type, pool, top_n):
    """Fetch leaderboard data and render the bar chart."""
    min_peer_reviews = 20 if pool == "premier" else 0

    # Request a generous top_n for composite calculation — we need entries
    # from ALL dimensions to compute averages, then trim to the requested N.
    request_n = max(top_n, 25) if dimension == "composite" else top_n

    data = get_leaderboard(
        method=method, entity_type=entity_type,
        min_peer_reviews=min_peer_reviews, top_n=request_n,
    )

    if dimension == "composite":
        # Compute composite: average across all 6 dimensions per entity
        entity_totals = {}   # advisor_id -> {"name": str, "sum": float, "count": int}
        for dim in DIMENSIONS:
            for entry in (data.get(dim, []) if data else []):
                eid = entry.get("advisor_id", "")
                if not eid:
                    continue
                if eid not in entity_totals:
                    entity_totals[eid] = {
                        "advisor_name": entry.get("advisor_name", "Unknown"),
                        "sum": 0.0, "count": 0,
                    }
                entity_totals[eid]["sum"] += entry.get("score", 0)
                entity_totals[eid]["count"] += 1

        # Build composite entries — only include entities present in at least 3 dims
        composite_entries = []
        for eid, info in entity_totals.items():
            if info["count"] >= 3:
                composite_entries.append({
                    "advisor_id": eid,
                    "advisor_name": info["advisor_name"],
                    "score": info["sum"] / info["count"],
                })

        # Sort and trim
        composite_entries.sort(key=lambda x: x["score"], reverse=True)
        composite_entries = composite_entries[:top_n]
        fig = _create_bar_chart(composite_entries, "composite", method)
    else:
        dim_entries = data.get(dimension, []) if data else []
        fig = _create_bar_chart(dim_entries, dimension, method)

    return fig


@callback(
    Output("lb-clicked-entity", "data"),
    Input("lb-chart", "clickData"),
    prevent_initial_call=True,
)
def on_chart_click(click_data):
    """Detect which entity was clicked on the bar chart."""
    if not click_data or "points" not in click_data:
        return None
    points = click_data["points"]
    if not points:
        return None
    point = points[0]
    if "customdata" not in point or not point["customdata"]:
        return None
    return point["customdata"][0]


@callback(
    Output("lb-detail-panel", "children"),
    Input("lb-clicked-entity", "data"),
    Input("lb-method-dropdown", "value"),
)
def update_detail_panel(clicked_entity_id, method):
    """Fetch entity profile and display detail card."""
    if not clicked_entity_id:
        return []

    profile = get_dna_advisor_scores(clicked_entity_id, method=method)
    if not profile:
        return []

    entity_name = profile.get("advisor_name", "Unknown")
    scores = profile.get("scores", {})

    spider = _create_spider_chart(scores, entity_name)

    score_rows = []
    for dim in DIMENSIONS:
        val = scores.get(dim, 0)
        score_rows.append(html.Div([
            html.Span(DIM_LABELS[dim], style={
                "flex": "1", "fontSize": "13px", "color": COLORS["ink"]}),
            html.Span(f"{val:.3f}", style={
                "fontSize": "13px", "fontWeight": "bold", "color": COLORS["blue"]}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "paddingBottom": "8px",
                  "borderBottom": f"1px solid {COLORS['border']}"}))

    return [html.Div([
        html.Div([
            html.H3(f"Profile: {entity_name}", style={
                "margin": "0 0 16px 0", "color": COLORS["ink"],
                "fontSize": "18px", "fontFamily": FONT_FAMILY}),
        ], style={"marginBottom": "16px"}),
        html.Div([
            html.Div([
                dcc.Graph(figure=spider, config={"displayModeBar": False, "responsive": True}),
            ], style={"flex": "1", "minWidth": "300px"}),
            html.Div(score_rows, style={
                "flex": "1", "minWidth": "250px",
                "paddingLeft": "20px", "paddingTop": "20px",
                "display": "flex", "flexDirection": "column", "gap": "0"}),
        ], style={"display": "flex", "gap": "20px", "marginTop": "16px", "flexWrap": "wrap"}),
    ], style={
        "padding": "20px", "backgroundColor": COLORS["soft_blue"],
        "borderLeft": f"4px solid {COLORS['blue']}", "borderRadius": "4px",
        "marginTop": "20px", "marginBottom": "20px"})]
