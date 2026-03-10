"""Leaderboard page for Wealthtender Dashboard (FB-14, FB-15).

Features:
- Top-N entities per dimension with horizontal bar charts
- Composite (average across all dimensions) leaderboard — computed server-side
- Percentile rank labels on bars, raw score on hover
- Selected bars stay full color; unselected fade to 30 % opacity
- Click up to 2 entities on the chart to compare spider profiles below
- Comparison table shows percentile, raw, and diff
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go

from dashboard.branding import COLORS, FONT_FAMILY
from dashboard.constants import DIMENSIONS, DIM_LABELS, DIM_SHORT, DIM_COLORS
from dashboard.services.api import get_leaderboard, get_dna_advisor_scores

dash.register_page(__name__, path="/leaderboard", title="Leaderboard")

COMPARE_COLORS = [COLORS["blue"], "#D4376E"]

_FADED_OPACITY = 0.30  # opacity for unselected bars


def _ordinal(n):
    """Return ordinal string for a percentile number (e.g. 92 -> '92nd')."""
    n = int(round(n))
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd'][min(n % 10, 4) if n % 10 < 4 else 0]}"


def _hex_to_rgba(hex_color, alpha=1.0):
    """Convert '#RRGGBB' to 'rgba(r,g,b,a)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _create_bar_chart(data, dimension, method, selected_ids=None):
    """Create a horizontal bar chart with percentile labels.

    - Selected bars are full opacity in the dimension color.
    - Unselected bars fade to 30 % opacity of the same color.
    - Raw cosine score shown on hover, percentile ordinal as bar text.
    """
    if not data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["gray"], family=FONT_FAMILY),
        )
        fig.update_layout(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            height=300, margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        return fig

    selected_ids = selected_ids or []

    # Sort descending, then reverse for plotly bottom-to-top rendering
    sorted_data = sorted(data, key=lambda x: x.get("percentile", 0) or 0, reverse=True)
    sorted_data = list(reversed(sorted_data))

    names = [item["advisor_name"] for item in sorted_data]
    percentiles = [item.get("percentile", 0) or 0 for item in sorted_data]
    raw_scores = [item.get("score", 0) for item in sorted_data]
    tiers = [item.get("tier", "") or "" for item in sorted_data]
    entity_ids = [item["advisor_id"] for item in sorted_data]
    customdata = [[eid, raw, tier] for eid, raw, tier in zip(entity_ids, raw_scores, tiers)]

    if dimension == "composite":
        base_hex = COLORS["navy"]
        title_text = f"Composite Score — {method.title()} (Percentile Rank)"
    else:
        base_hex = DIM_COLORS.get(dimension, COLORS["blue"])
        title_text = f"{DIM_LABELS.get(dimension, dimension)} — {method.title()} (Percentile Rank)"

    # Per-bar colors: selected = full opacity, unselected = faded
    bar_colors = []
    line_widths = []
    line_colors = []
    for eid in entity_ids:
        if not selected_ids or eid in selected_ids:
            bar_colors.append(_hex_to_rgba(base_hex, 1.0))
            line_widths.append(1.5 if eid in selected_ids else 1)
            line_colors.append(base_hex)
        else:
            bar_colors.append(_hex_to_rgba(base_hex, _FADED_OPACITY))
            line_widths.append(0.5)
            line_colors.append(_hex_to_rgba(base_hex, _FADED_OPACITY))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=percentiles, orientation="h",
        marker=dict(color=bar_colors,
                    line=dict(color=line_colors, width=line_widths)),
        text=[_ordinal(p) for p in percentiles],
        textposition="outside",
        textfont=dict(family=FONT_FAMILY, size=11, color=COLORS["ink"]),
        hovertemplate=(
            "%{y}<br>"
            "Percentile: %{x:.0f}th<br>"
            "Raw Score: %{customdata[1]:.4f}<br>"
            "Tier: %{customdata[2]}"
            "<extra></extra>"
        ),
        customdata=customdata, name="Percentile",
    ))

    fig.update_layout(
        title={"text": title_text,
               "x": 0.5, "xanchor": "center",
               "font": dict(size=16, color=COLORS["ink"], family=FONT_FAMILY)},
        xaxis=dict(title="Percentile Rank",
                   range=[0, 115],
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


def _build_comparison_spider(profiles):
    """Build overlaid spider chart for 1 or 2 profiles using percentile scores.

    profiles: list of (name, enriched_scores_dict) tuples
    """
    fig = go.Figure()
    for idx, (name, scores) in enumerate(profiles):
        color = COMPARE_COLORS[idx % len(COMPARE_COLORS)]
        values = []
        for dim in DIMENSIONS:
            dim_data = scores.get(dim, {})
            values.append(dim_data.get("percentile", 50) if isinstance(dim_data, dict) else dim_data)
        values.append(values[0])  # close the loop
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[DIM_SHORT[d] for d in DIMENSIONS] + [DIM_SHORT[DIMENSIONS[0]]],
            fill="toself", name=name,
            line={"color": color, "width": 2},
            fillcolor=color, opacity=0.4,
            hovertemplate="%{theta}<br>Percentile: %{r:.0f}th<extra></extra>",
        ))

    if len(profiles) == 1:
        title_text = f"{profiles[0][0]} — Percentile Profile"
    else:
        title_text = f"{profiles[0][0]} vs {profiles[1][0]}"

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(family=FONT_FAMILY, size=9, color=COLORS["gray"]),
                            gridcolor=COLORS["border"]),
            angularaxis=dict(tickfont=dict(family=FONT_FAMILY, size=10, color=COLORS["ink"])),
            bgcolor="rgba(255,255,255,0.5)"),
        title={"text": title_text, "x": 0.5, "xanchor": "center",
               "font": dict(size=15, color=COLORS["ink"], family=FONT_FAMILY)},
        legend={"orientation": "h", "y": -0.12, "x": 0.5, "xanchor": "center",
                "font": {"size": 11, "family": FONT_FAMILY}},
        height=400, margin=dict(l=60, r=60, t=60, b=70),
        paper_bgcolor="white", font=dict(family=FONT_FAMILY),
        showlegend=len(profiles) > 1,
    )
    return fig


def _build_score_table(profiles):
    """Build a comparison table showing percentile + raw per dimension."""
    header_cells = [html.Th("Dimension", style={
        "padding": "10px 12px", "textAlign": "left", "fontWeight": "700",
        "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
        "borderBottom": f"2px solid {COLORS['border']}"})]

    for idx, (name, _) in enumerate(profiles):
        color = COMPARE_COLORS[idx % len(COMPARE_COLORS)]
        header_cells.append(html.Th(name, style={
            "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
            "backgroundColor": COLORS["soft_blue"], "color": color,
            "borderBottom": f"2px solid {COLORS['border']}"}))

    if len(profiles) == 2:
        header_cells.append(html.Th("Diff", style={
            "padding": "10px 12px", "textAlign": "center", "fontWeight": "700",
            "backgroundColor": COLORS["soft_blue"], "color": COLORS["ink"],
            "borderBottom": f"2px solid {COLORS['border']}"}))

    rows = []
    all_dims = list(DIMENSIONS) + ["composite"]
    dim_labels_ext = {**DIM_LABELS, "composite": "Composite"}

    for dim in all_dims:
        is_composite = dim == "composite"
        cells = [html.Td(
            dim_labels_ext.get(dim, dim),
            style={
                "padding": "10px 12px",
                "fontWeight": "700" if is_composite else "500",
                "color": COLORS["ink"],
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": f"2px solid {COLORS['border']}" if is_composite else "none",
            })]

        pctiles = []
        for idx, (_, scores) in enumerate(profiles):
            dim_data = scores.get(dim, {})
            if isinstance(dim_data, dict):
                pctile = dim_data.get("percentile", 0) or 0
                raw = dim_data.get("raw", 0) or 0
            else:
                pctile = 0
                raw = dim_data
            pctiles.append(pctile)
            color = COMPARE_COLORS[idx % len(COMPARE_COLORS)]
            cells.append(html.Td(
                html.Span([
                    html.Span(f"{_ordinal(pctile)} ",
                              style={"fontWeight": "700"}),
                    html.Span(f"({raw:.3f})",
                              style={"fontSize": "11px", "color": COLORS["gray"]}),
                ]),
                style={
                    "padding": "10px 12px", "textAlign": "center",
                    "color": color,
                    "borderBottom": f"1px solid {COLORS['border']}",
                    "borderTop": f"2px solid {COLORS['border']}" if is_composite else "none",
                }))

        if len(profiles) == 2:
            diff = pctiles[1] - pctiles[0]
            if diff > 0:
                dc, dt = "#10b981", f"+{diff:.0f}"
            elif diff < 0:
                dc, dt = "#ef4444", f"{diff:.0f}"
            else:
                dc, dt = COLORS["gray"], "0"
            cells.append(html.Td(dt, style={
                "padding": "10px 12px", "textAlign": "center",
                "fontWeight": "600", "color": dc,
                "borderBottom": f"1px solid {COLORS['border']}",
                "borderTop": f"2px solid {COLORS['border']}" if is_composite else "none",
            }))

        rows.append(html.Tr(cells))

    return html.Table([
        html.Thead(html.Tr(header_cells)),
        html.Tbody(rows),
    ], style={"width": "100%", "borderCollapse": "collapse",
              "fontFamily": FONT_FAMILY, "fontSize": "13px"})


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout():
    dim_options = [{"label": "Composite (All Dimensions)", "value": "composite"}] + \
                  [{"label": DIM_LABELS[d], "value": d} for d in DIMENSIONS]

    return html.Div([
        html.Div([
            html.H2("Leaderboard", style={
                "margin": "0 0 8px 0", "color": COLORS["ink"],
                "fontSize": "24px", "fontFamily": FONT_FAMILY}),
            html.P("Top-performing entities across Advisor DNA dimensions. "
                   "Bars show percentile rank among all peers. "
                   "The #1 and last-ranked entities are compared below — click any "
                   "name on the chart to swap a selection.",
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
                dcc.Graph(id="lb-chart",
                          config={"displayModeBar": True, "responsive": True}),
            ]),
        ], style={
            "backgroundColor": "white", "padding": "20px", "borderRadius": "8px",
            "border": f"1px solid {COLORS['border']}", "marginBottom": "24px"}),

        # Comparison panel — holds spider + table for up to 2 clicked entities
        html.Div(id="lb-compare-panel", children=[
            html.P("Loading comparison...",
                   style={"color": COLORS["gray"], "fontSize": "13px",
                          "textAlign": "center", "padding": "16px"}),
        ], style={
            "backgroundColor": COLORS["soft_blue"], "borderRadius": "8px",
            "padding": "20px", "marginBottom": "20px",
            "border": f"1px solid {COLORS['border']}"}),

        # Hidden stores
        dcc.Store(id="lb-selected-ids", data=[]),
        dcc.Store(id="lb-chart-entity-ids", data=[]),
    ], style={"padding": "20px", "fontFamily": FONT_FAMILY})


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("lb-chart", "figure"),
    Output("lb-chart-entity-ids", "data"),
    Output("lb-selected-ids", "data", allow_duplicate=True),
    Input("lb-dimension-dropdown", "value"),
    Input("lb-method-dropdown", "value"),
    Input("lb-entity-type-dropdown", "value"),
    Input("lb-pool-dropdown", "value"),
    Input("lb-top-n-slider", "value"),
    prevent_initial_call="initial_duplicate",
)
def update_leaderboard_chart(dimension, method, entity_type, pool, top_n):
    """Fetch leaderboard data from API (now includes composite + percentiles)."""
    min_peer_reviews = 20 if pool == "premier" else 0

    data = get_leaderboard(
        method=method, entity_type=entity_type,
        min_peer_reviews=min_peer_reviews, top_n=top_n,
        dimension=dimension,
    )

    chart_entries = data.get(dimension, []) if data else []

    # Auto-select top and bottom entities
    sorted_entries = sorted(chart_entries,
                            key=lambda x: x.get("percentile", 0) or 0,
                            reverse=True)
    entity_ids = [e["advisor_id"] for e in sorted_entries if e.get("advisor_id")]
    if len(entity_ids) >= 2:
        auto_selected = [entity_ids[0], entity_ids[-1]]
    elif len(entity_ids) == 1:
        auto_selected = [entity_ids[0]]
    else:
        auto_selected = []

    fig = _create_bar_chart(chart_entries, dimension, method, selected_ids=auto_selected)
    return fig, entity_ids, auto_selected


@callback(
    Output("lb-selected-ids", "data"),
    Input("lb-chart", "clickData"),
    State("lb-selected-ids", "data"),
    prevent_initial_call=True,
)
def on_chart_click(click_data, current_ids):
    """Track up to 2 clicked entities. Clicking a 3rd replaces the oldest."""
    if not click_data or "points" not in click_data:
        return no_update
    points = click_data["points"]
    if not points:
        return no_update
    point = points[0]
    if "customdata" not in point or not point["customdata"]:
        return no_update

    new_id = point["customdata"][0]
    current_ids = current_ids or []

    # If already selected, remove it (toggle off)
    if new_id in current_ids:
        current_ids = [eid for eid in current_ids if eid != new_id]
        return current_ids

    # Add to selection; if already 2, drop the oldest
    if len(current_ids) >= 2:
        current_ids = [current_ids[1], new_id]
    else:
        current_ids = current_ids + [new_id]

    return current_ids


@callback(
    Output("lb-chart", "figure", allow_duplicate=True),
    Input("lb-selected-ids", "data"),
    State("lb-chart", "figure"),
    State("lb-dimension-dropdown", "value"),
    prevent_initial_call=True,
)
def restyle_bars_on_selection(selected_ids, fig, dimension):
    """Fade unselected bars to 30 % opacity; keep selected at full opacity."""
    if not fig or not fig.get("data"):
        return no_update
    selected_ids = selected_ids or []

    trace = fig["data"][0]
    customdata = trace.get("customdata", [])
    entity_ids = [cd[0] if cd else "" for cd in customdata]

    # Determine the base color hex
    if dimension == "composite":
        base_hex = COLORS["navy"]
    else:
        base_hex = DIM_COLORS.get(dimension, COLORS["blue"])

    new_colors = []
    new_line_widths = []
    new_line_colors = []
    for eid in entity_ids:
        if not selected_ids or eid in selected_ids:
            new_colors.append(_hex_to_rgba(base_hex, 1.0))
            new_line_widths.append(1.5 if eid in selected_ids else 1)
            new_line_colors.append(base_hex)
        else:
            new_colors.append(_hex_to_rgba(base_hex, _FADED_OPACITY))
            new_line_widths.append(0.5)
            new_line_colors.append(_hex_to_rgba(base_hex, _FADED_OPACITY))

    fig["data"][0]["marker"]["color"] = new_colors
    fig["data"][0]["marker"]["line"]["color"] = new_line_colors
    fig["data"][0]["marker"]["line"]["width"] = new_line_widths
    return fig


@callback(
    Output("lb-compare-panel", "children"),
    Input("lb-selected-ids", "data"),
    Input("lb-method-dropdown", "value"),
)
def update_compare_panel(selected_ids, method):
    """Fetch enriched profiles for selected entities and show spider + table."""
    selected_ids = selected_ids or []
    if not selected_ids:
        return [html.P(
            "Click on a name in the chart to view their profile.",
            style={"color": COLORS["gray"], "fontSize": "13px",
                   "textAlign": "center", "padding": "16px"})]

    profiles = []  # list of (name, enriched_scores_dict)
    for eid in selected_ids:
        profile = get_dna_advisor_scores(eid, method=method)
        if profile:
            name = profile.get("advisor_name", "Unknown")
            scores = profile.get("scores", {})
            profiles.append((name, scores))

    if not profiles:
        return [html.P(
            "Could not load profile data.",
            style={"color": COLORS["gray"], "fontSize": "13px",
                   "textAlign": "center", "padding": "16px"})]

    spider_fig = _build_comparison_spider(profiles)
    score_table = _build_score_table(profiles)

    # Header
    if len(profiles) == 1:
        header_text = f"Profile: {profiles[0][0]}"
    else:
        header_text = f"Comparing: {profiles[0][0]} vs {profiles[1][0]}"

    return [
        html.Div([
            html.H3(header_text, style={
                "margin": "0", "color": COLORS["ink"],
                "fontSize": "17px", "fontFamily": FONT_FAMILY}),
            html.Span(
                "Click another name to compare" if len(profiles) == 1
                else "Click a name to toggle selection",
                style={"color": COLORS["gray"], "fontSize": "12px"}),
        ], style={"marginBottom": "16px"}),

        html.Div([
            # Spider chart
            html.Div([
                dcc.Graph(figure=spider_fig,
                          config={"displayModeBar": False, "responsive": True},
                          style={"height": "400px"}),
            ], style={"flex": "1", "minWidth": "380px"}),

            # Score table
            html.Div([
                score_table,
            ], style={"flex": "1", "minWidth": "350px", "paddingTop": "8px"}),
        ], style={"display": "flex", "gap": "24px", "flexWrap": "wrap"}),
    ]
