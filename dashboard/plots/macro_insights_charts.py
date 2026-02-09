import plotly.graph_objects as go


def _apply_base_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=24, b=24),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Open Sans", color="#111827"),
        xaxis=dict(gridcolor="#e5e7eb"),
        yaxis=dict(gridcolor="#e5e7eb"),
    )
    return fig


def rating_distribution_chart(distribution: list[dict], palette: list[str]) -> go.Figure:
    labels = [d["rating"] for d in distribution]
    counts = [d["count"] for d in distribution]
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    fig = go.Figure(
        data=[go.Bar(x=labels, y=counts, marker_color=colors, text=counts, textposition="outside")]
    )
    fig.update_layout(xaxis_title="Rating", yaxis_title="Reviews")
    return _apply_base_layout(fig)


def reviews_over_time_chart(series: list[dict], palette: list[str]) -> go.Figure:
    x = [d["period"] for d in series]
    y = [d["count"] for d in series]
    fig = go.Figure(
        data=[go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=palette[0]))]
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Reviews")
    return _apply_base_layout(fig)


def reviews_per_advisor_hist(counts: list[int], median: float, p90: float, palette: list[str]) -> go.Figure:
    fig = go.Figure(data=[go.Histogram(x=counts, marker_color=palette[1])])
    fig.update_layout(xaxis_title="Reviews per advisor", yaxis_title="Advisor count", bargap=0.05)
    if median is not None:
        fig.add_vline(x=median, line_dash="dash", line_color=palette[0], annotation_text="Median")
    if p90 is not None:
        fig.add_vline(x=p90, line_dash="dot", line_color=palette[2], annotation_text="P90")
    return _apply_base_layout(fig)


def token_count_hist(counts: list[int], palette: list[str]) -> go.Figure:
    fig = go.Figure(data=[go.Histogram(x=counts, marker_color=palette[2])])
    fig.update_layout(xaxis_title="Token count", yaxis_title="Reviews", bargap=0.05)
    return _apply_base_layout(fig)


def rating_vs_token_scatter(points: list[dict], palette: list[str]) -> go.Figure:
    x = [d["token_count"] for d in points]
    y = [d["rating"] for d in points]
    custom = [d.get("review_id") for d in points]
    # Force a visible brand color (avoid white/light palette slots).
    marker_color = palette[1] if len(palette) > 1 else palette[0]
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                customdata=custom,
                hovertemplate="Tokens: %{x}<br>Rating: %{y}<extra></extra>",
                marker=dict(color=marker_color, size=7, opacity=0.7, line=dict(width=0.5, color="#111827")),
            )
        ]
    )
    fig.update_layout(xaxis_title="Token count", yaxis_title="Rating")
    return _apply_base_layout(fig)


def lexical_bar_chart(items: list[dict], label_key: str, palette: list[str]) -> go.Figure:
    labels = [d[label_key] for d in items]
    counts = [d["count"] for d in items]
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    fig = go.Figure(
        data=[go.Bar(x=labels, y=counts, marker_color=colors, text=counts, textposition="outside")]
    )
    fig.update_layout(xaxis_title=label_key.replace("_", " ").title(), yaxis_title="Count")
    return _apply_base_layout(fig)
