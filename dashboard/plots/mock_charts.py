import plotly.graph_objects as go


def dimension_bar_chart(dimensions: list[str], scores: list[float], palette: list[str]) -> go.Figure:
    colors = [palette[i % len(palette)] for i in range(len(dimensions))]
    fig = go.Figure(
        data=[
            go.Bar(
                x=dimensions,
                y=scores,
                marker_color=colors,
                text=[f"{s:.0f}" for s in scores],
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        height=360,
        margin=dict(l=24, r=24, t=24, b=24),
        yaxis=dict(range=[0, 100], gridcolor="#e5e7eb"),
        xaxis=dict(tickangle=-25),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Open Sans", color="#111827"),
    )
    return fig
