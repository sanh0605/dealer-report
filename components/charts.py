import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

def bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, color_discrete_sequence=PALETTE)
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    return fig

def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    fig = px.pie(df, names=names, values=values, title=title,
                 color_discrete_sequence=PALETTE, hole=0.35)
    fig.update_layout(margin=dict(t=40, b=20))
    return fig

def line_chart(df: pd.DataFrame, x: str, y: str, title: str,
               color: str | None = None) -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, title=title,
                  color_discrete_sequence=PALETTE, markers=True)
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    return fig

def treemap_chart(df: pd.DataFrame, path: list[str], values: str, title: str) -> go.Figure:
    fig = px.treemap(df, path=path, values=values, title=title,
                   color_discrete_sequence=PALETTE)
    fig.update_layout(margin=dict(t=40, b=20))
    return fig
