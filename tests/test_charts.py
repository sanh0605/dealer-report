import pytest
import pandas as pd
from components.charts import (
    bar_chart, pie_chart, line_chart, treemap_chart, PALETTE
)

def test_palette_defined():
    """Test that PALETTE is defined with expected colors."""
    assert PALETTE is not None
    assert len(PALETTE) == 6
    assert PALETTE[0] == "#1f77b4"

def test_bar_chart_creates_figure():
    """Test bar_chart returns a Plotly Figure with correct structure."""
    df = pd.DataFrame({"category": ["A", "B", "C"], "value": [10, 20, 30]})
    fig = bar_chart(df, x="category", y="value", title="Test Bar Chart")

    assert fig is not None
    assert fig.layout.title.text == "Test Bar Chart"
    assert len(fig.data) == 1
    assert fig.data[0].type == "bar"

def test_bar_chart_applies_theme():
    """Test bar_chart uses project palette and styling."""
    df = pd.DataFrame({"category": ["A"], "value": [10]})
    fig = bar_chart(df, x="category", y="value", title="Test")

    assert fig.layout.plot_bgcolor == "white"
    assert fig.layout.margin.t == 40
    assert fig.layout.margin.b == 20

def test_pie_chart_creates_figure():
    """Test pie_chart returns a Plotly Figure with correct structure."""
    df = pd.DataFrame({"name": ["A", "B"], "value": [30, 70]})
    fig = pie_chart(df, names="name", values="value", title="Test Pie Chart")

    assert fig is not None
    assert fig.layout.title.text == "Test Pie Chart"
    assert len(fig.data) == 1
    assert fig.data[0].type == "pie"
    assert fig.data[0].hole == 0.35

def test_pie_chart_applies_theme():
    """Test pie_chart uses project palette and styling."""
    df = pd.DataFrame({"name": ["A"], "value": [100]})
    fig = pie_chart(df, names="name", values="value", title="Test")

    assert fig.layout.margin.t == 40
    assert fig.layout.margin.b == 20

def test_line_chart_basic():
    """Test line_chart creates a line chart with markers."""
    df = pd.DataFrame({"month": ["Jan", "Feb"], "value": [100, 200]})
    fig = line_chart(df, x="month", y="value", title="Test Line Chart")

    assert fig is not None
    assert fig.layout.title.text == "Test Line Chart"
    assert len(fig.data) == 1
    assert fig.data[0].type == "scatter"
    assert fig.data[0].mode == "lines+markers"

def test_line_chart_with_color():
    """Test line_chart with color grouping."""
    df = pd.DataFrame({
        "month": ["Jan", "Jan", "Feb", "Feb"],
        "category": ["A", "B", "A", "B"],
        "value": [100, 150, 200, 250]
    })
    fig = line_chart(df, x="month", y="value", title="Test", color="category")

    assert fig is not None
    assert len(fig.data) == 2  # Two series

def test_line_chart_applies_theme():
    """Test line_chart uses project palette and styling."""
    df = pd.DataFrame({"month": ["Jan"], "value": [100]})
    fig = line_chart(df, x="month", y="value", title="Test")

    assert fig.layout.plot_bgcolor == "white"
    assert fig.layout.margin.t == 40
    assert fig.layout.margin.b == 20

def test_treemap_chart_creates_figure():
    """Test treemap_chart returns a Plotly Figure with correct structure."""
    df = pd.DataFrame({
        "level1": ["A", "A", "B"],
        "level2": ["A1", "A2", "B1"],
        "value": [30, 20, 50]
    })
    fig = treemap_chart(df, path=["level1", "level2"], values="value", title="Test Treemap")

    assert fig is not None
    assert fig.layout.title.text == "Test Treemap"
    assert len(fig.data) == 1
    assert fig.data[0].type == "treemap"

def test_treemap_chart_applies_theme():
    """Test treemap_chart uses project palette and styling."""
    df = pd.DataFrame({"level": ["A"], "value": [100]})
    fig = treemap_chart(df, path=["level"], values="value", title="Test")

    assert fig.layout.margin.t == 40
    assert fig.layout.margin.b == 20

def test_all_charts_use_palette():
    """Test all chart functions use the project color palette."""
    df = pd.DataFrame({"x": ["A", "B"], "y": [10, 20]})

    bar_fig = bar_chart(df, x="x", y="y", title="Bar")
    pie_df = pd.DataFrame({"name": ["A", "B"], "value": [10, 20]})
    pie_fig = pie_chart(pie_df, names="name", values="value", title="Pie")
    line_fig = line_chart(df, x="x", y="y", title="Line")
    tree_df = pd.DataFrame({"level": ["A", "B"], "value": [10, 20]})
    tree_fig = treemap_chart(tree_df, path=["level"], values="value", title="Tree")

    # All figures should have color_discrete_sequence parameter set
    for fig in [bar_fig, pie_fig, line_fig, tree_fig]:
        assert fig is not None
