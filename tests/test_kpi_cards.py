import pytest
from unittest.mock import patch, MagicMock
from components.kpi_cards import render_kpi_row

def test_render_kpi_row_basic():
    """Test render_kpi_row creates correct number of metrics inside a container."""
    metrics = [
        {"label": "Total Revenue", "value": "$100,000"},
        {"label": "Gross Profit", "value": "$40,000"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        # Verify st.container was called with horizontal=True
        mock_st.container.assert_called_once_with(horizontal=True)

        # Verify metric was called twice
        assert mock_st.metric.call_count == 2

def test_render_kpi_row_single_metric():
    """Test render_kpi_row with single metric."""
    metrics = [{"label": "Revenue", "value": "$50,000"}]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        mock_st.metric.assert_called_once_with(
            label="Revenue",
            value="$50,000",
            delta=None,
            delta_color="normal",
            border=True
        )

def test_render_kpi_row_with_delta():
    """Test render_kpi_row with delta values."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%"},
        {"label": "Profit", "value": "$40,000", "delta": "+5%"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        # Checking the first call
        mock_st.metric.assert_any_call(
            label="Revenue",
            value="$100,000",
            delta="+10%",
            delta_color="normal",
            border=True
        )

def test_render_kpi_row_with_delta_color():
    """Test render_kpi_row with custom delta colors."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%", "delta_color": "normal"},
        {"label": "Cost", "value": "$60,000", "delta": "-5%", "delta_color": "inverse"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        mock_st.metric.assert_any_call(
            label="Revenue",
            value="$100,000",
            delta="+10%",
            delta_color="normal",
            border=True
        )
        mock_st.metric.assert_any_call(
            label="Cost",
            value="$60,000",
            delta="-5%",
            delta_color="inverse",
            border=True
        )

def test_render_kpi_row_default_delta_color():
    """Test render_kpi_row uses 'normal' as default delta_color."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        mock_st.metric.assert_called_once()
        call_kwargs = mock_st.metric.call_args[1]
        assert call_kwargs["delta_color"] == "normal"
        assert call_kwargs["border"] is True

def test_render_kpi_row_empty_metrics():
    """Test render_kpi_row with empty metrics list."""
    metrics = []

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        mock_st.container.assert_called_once_with(horizontal=True)
        assert mock_st.metric.call_count == 0

def test_render_kpi_row_many_metrics():
    """Test render_kpi_row with many metrics (4)."""
    metrics = [
        {"label": f"Metric {i}", "value": f"${i}00,000"}
        for i in range(1, 5)
    ]

    with patch("components.kpi_cards.st") as mock_st:
        render_kpi_row(metrics)

        mock_st.container.assert_called_once_with(horizontal=True)
        assert mock_st.metric.call_count == 4
