import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

def _format_axis_data(df: pd.DataFrame, col: str) -> tuple[pd.DataFrame, str, str]:
    """Scales the data to Millions (M) or Billions (B) to avoid Plotly's default Giga (G) SI prefix."""
    df_plot = df.copy()
    max_val = df_plot[col].max() if not df_plot.empty else 0
    
    if max_val >= 1e9:
        df_plot[f"{col}_scaled"] = df_plot[col] / 1e9
        suffix = "B"
    elif max_val >= 1e6:
        df_plot[f"{col}_scaled"] = df_plot[col] / 1e6
        suffix = "M"
    else:
        df_plot[f"{col}_scaled"] = df_plot[col]
        suffix = ""
        
    return df_plot, f"{col}_scaled", suffix

def bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    if x == "region":
        x_label = "Miền"
    elif x == "brand_group_label":
        x_label = "Nhóm thương hiệu"
    elif x == "brand_group":
        x_label = "Nhóm thương hiệu"
    elif x == "salesperson":
        x_label = "Nhân viên"
    else:
        x_label = "Hạng mục"
        
    df_plot, y_scaled, suffix = _format_axis_data(df, y)
    fig = px.bar(df_plot, x=x, y=y_scaled, title=title, color_discrete_sequence=PALETTE,
                 custom_data=[y],
                 labels={x: x_label, y_scaled: "Doanh số", "color": "Phân loại"})
    fig.update_traces(hovertemplate="%{x}<br>Doanh số: %{customdata[0]:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    fig.update_yaxes(ticksuffix=suffix, rangemode="normal")
    return fig

def horizontal_bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    if y == "salesperson":
        y_label = "Nhân viên"
    elif y == "dealer_name":
        y_label = "Đối tác"
    else:
        y_label = "Hạng mục"
        
    df_plot, x_scaled, suffix = _format_axis_data(df, x)
    fig = px.bar(df_plot, x=x_scaled, y=y, title=title, color_discrete_sequence=PALETTE, orientation="h",
                 custom_data=[x],
                 labels={x_scaled: "Doanh số", y: y_label})
    fig.update_traces(hovertemplate="%{y}<br>Doanh số: %{customdata[0]:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    fig.update_xaxes(ticksuffix=suffix, rangemode="normal")
    return fig

def stacked_bar_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> go.Figure:
    x_label = "Miền" if x == "region" else "Vùng"
    df_plot, y_scaled, suffix = _format_axis_data(df, y)
    fig = px.bar(df_plot, x=x, y=y_scaled, color=color, title=title, color_discrete_sequence=PALETTE,
                 custom_data=[y],
                 labels={x: x_label, y_scaled: "Doanh số", color: "Nhóm thương hiệu"})
    fig.update_traces(hovertemplate="%{x} (%{fullData.name})<br>Doanh số: %{customdata[0]:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    fig.update_yaxes(ticksuffix=suffix, rangemode="normal")
    return fig

def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    # Pie charts handle their own percentages, but we can still format hover
    color_map = {
        "Nguy hiểm": "#d62728", # Red
        "Cảnh báo": "#ff7f0e",  # Orange
        "Tốt": "#2ca02c"        # Green
    }
    
    fig = px.pie(df, names=names, values=values, title=title,
                 color=names,
                 color_discrete_map=color_map,
                 hole=0.35,
                 labels={names: "Phân loại", values: "Doanh số"})
    fig.update_traces(textposition="inside", textinfo="percent+label", 
                      hovertemplate="%{label}<br>Doanh số: %{value:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20))
    return fig

def line_chart(df: pd.DataFrame, x: str, y: str, title: str,
               color: str | None = None) -> go.Figure:
    df_plot, y_scaled, suffix = _format_axis_data(df, y)
    fig = px.line(df_plot, x=x, y=y_scaled, color=color, title=title,
                  color_discrete_sequence=PALETTE, markers=True,
                  custom_data=[y],
                  labels={x: "Thời gian", y_scaled: "Doanh số", color: "Phân loại"})
    fig.update_traces(hovertemplate="%{x}<br>Doanh số: %{customdata[0]:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    fig.update_yaxes(ticksuffix=suffix, rangemode="normal")
    return fig

def treemap_chart(df: pd.DataFrame, path: list[str], values: str, title: str) -> go.Figure:
    fig = px.treemap(df, path=path, values=values, title=title,
                   color_discrete_sequence=PALETTE)
    fig.update_traces(hovertemplate="%{label}<br>Doanh số: %{value:,.0f} VND<extra></extra>")
    fig.update_layout(margin=dict(t=40, b=20))
    return fig

def scatter_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str, hover_name: str | None = None) -> go.Figure:
    fig = px.scatter(df, x=x, y=y, color=color, title=title,
                     hover_name=hover_name,
                     color_discrete_map={"Tốt": "#2ca02c", "Cảnh báo": "#ff7f0e", "Nguy hiểm": "#d62728"},
                     labels={x: "Hạng mục X", y: "Hạng mục Y", color: "Trạng thái"})
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white")
    return fig

def histogram_chart(df: pd.DataFrame, x: str, title: str, nbins: int = 20) -> go.Figure:
    fig = px.histogram(df, x=x, title=title, nbins=nbins,
                       color_discrete_sequence=PALETTE,
                       labels={x: "Giá trị", "count": "Số lượng"})
    fig.update_layout(margin=dict(t=40, b=20), plot_bgcolor="white", bargap=0.1)
    return fig
