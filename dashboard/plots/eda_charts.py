import plotly.graph_objects as go


def _apply_base_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=24, r=24, t=40, b=24),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Open Sans", color="#111827"),
        xaxis=dict(gridcolor="#e5e7eb"),
        yaxis=dict(gridcolor="#e5e7eb"),
    )
    return fig


def _add_bar_headroom(fig: go.Figure, counts: list) -> go.Figure:
    """Expand y-axis so textposition='outside' labels don't clip."""
    if counts:
        max_val = max(c for c in counts if c is not None) if counts else 0
        if max_val > 0:
            fig.update_layout(yaxis_range=[0, max_val * 1.18])
    return fig


def rating_distribution_chart(distribution: list[dict], palette: list[str]) -> go.Figure:
    def _rating_sort_key(label):
        if label is None:
            return (-1, -1)
        text = str(label).strip().lower()
        if text == "nan":
            return (-1, -1)
        try:
            return (0, float(text))
        except ValueError:
            return (1, text)

    ordered = sorted(distribution, key=lambda d: _rating_sort_key(d.get("rating")))
    labels = [d.get("rating") for d in ordered]
    counts = [d.get("count") for d in ordered]
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    fig = go.Figure(
        data=[go.Bar(x=labels, y=counts, marker_color=colors, text=counts, textposition="outside")]
    )
    fig.update_layout(xaxis_title="Rating", yaxis_title="Reviews")
    _add_bar_headroom(fig, counts)
    return _apply_base_layout(fig)


def reviews_over_time_chart(series: list[dict], palette: list[str]) -> go.Figure:
    x = [d["period"] for d in series]
    y = [d["count"] for d in series]
    fig = go.Figure(
        data=[go.Scatter(
            x=x, y=y,
            mode="lines+markers",
            line=dict(color=palette[0], width=2.5),
            marker=dict(color=palette[1], size=6),
        )]
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Reviews")
    return _apply_base_layout(fig)


def reviews_per_advisor_hist(counts: list[int], median: float, p90: float, palette: list[str]) -> go.Figure:
    fig = go.Figure(data=[go.Histogram(x=counts, marker_color=palette[1])])
    fig.update_layout(xaxis_title="Reviews per advisor", yaxis_title="Advisor count", bargap=0.05)
    if median is not None:
        fig.add_vline(x=median, line_dash="dash", line_color=palette[0], annotation_text="Median")
    if p90 is not None:
        fig.add_vline(x=p90, line_dash="dot", line_color=palette[6], annotation_text="P90")
    return _apply_base_layout(fig)


def token_count_hist(counts: list[int], palette: list[str]) -> go.Figure:
    fig = go.Figure(data=[go.Histogram(x=counts, marker_color=palette[4])])
    fig.update_layout(xaxis_title="Token count", yaxis_title="Reviews", bargap=0.05)
    return _apply_base_layout(fig)


def rating_vs_token_scatter(points: list[dict], palette: list[str]) -> go.Figure:
    x = [d["token_count"] for d in points]
    y = [d["rating"] for d in points]
    custom = [d.get("review_id") for d in points]
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x,
                y=y,
                mode="markers",
                customdata=custom,
                hovertemplate="Tokens: %{x}<br>Rating: %{y}<extra></extra>",
                marker=dict(
                    color=palette[1],
                    size=7,
                    opacity=0.65,
                    line=dict(width=0.5, color=palette[0]),
                ),
            )
        ]
    )
    fig.update_layout(xaxis_title="Token count", yaxis_title="Rating")
    return _apply_base_layout(fig)


def lexical_bar_chart(items: list[dict], label_key: str, palette: list[str]) -> go.Figure:
    labels = [d[label_key] for d in items]
    counts = [d["count"] for d in items]
    # Gradient through the blue range of the palette for a cohesive look
    n = len(labels)
    if n <= len(palette):
        colors = [palette[i % len(palette)] for i in range(n)]
    else:
        # For many bars, interpolate between primary and secondary brand blue
        colors = _interpolate_colors(palette[0], palette[1], n)
    fig = go.Figure(
        data=[go.Bar(
            x=labels, y=counts,
            marker_color=colors,
            text=counts,
            textposition="outside",
            textfont=dict(size=10),
        )]
    )
    fig.update_layout(
        xaxis_title=label_key.replace("_", " ").title(),
        yaxis_title="Count",
        xaxis_tickangle=-45,
    )
    _add_bar_headroom(fig, counts)
    return _apply_base_layout(fig, height=400)


def _interpolate_colors(hex_a: str, hex_b: str, n: int) -> list[str]:
    """Generate n colors interpolated between two hex colors."""
    def _hex_to_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(r, g, b):
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    ra, ga, ba = _hex_to_rgb(hex_a)
    rb, gb, bb = _hex_to_rgb(hex_b)
    if n <= 1:
        return [hex_a]
    return [
        _rgb_to_hex(
            ra + (rb - ra) * i / (n - 1),
            ga + (gb - ga) * i / (n - 1),
            ba + (bb - ba) * i / (n - 1),
        )
        for i in range(n)
    ]
