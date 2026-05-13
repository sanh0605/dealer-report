import pytest
from unittest.mock import patch, MagicMock
from components.kpi_cards import render_kpi_row

def test_render_kpi_row_basic():
    """Test render_kpi_row creates correct number of columns."""
    metrics = [
        {"label": "Total Revenue", "value": "$100,000"},
        {"label": "Gross Profit", "value": "$40,000"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        mock_cols = [MagicMock() for _ in range(2)]
        mock_st.columns.return_value = mock_cols

        render_kpi_row(metrics)

        # Verify st.columns was called with correct number
        mock_st.columns.assert_called_once_with(2)

        # Verify each column.metric was called
        mock_cols[0].metric.assert_called_once()
        mock_cols[1].metric.assert_called_once()

def test_render_kpi_row_single_metric():
    """Test render_kpi_row with single metric."""
    metrics = [{"label": "Revenue", "value": "$50,000"}]

    with patch("components.kpi_cards.st") as mock_st:
        mock_col = MagicMock()
        mock_st.columns.return_value = [mock_col]

        render_kpi_row(metrics)

        mock_st.columns.assert_called_once_with(1)
        mock_col.metric.assert_called_once_with(
            label="Revenue",
            value="$50,000",
            delta=None,
            delta_color="normal",
        )

def test_render_kpi_row_with_delta():
    """Test render_kpi_row with delta values."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%"},
        {"label": "Profit", "value": "$40,000", "delta": "+5%"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        mock_cols = [MagicMock() for _ in range(2)]
        mock_st.columns.return_value = mock_cols

        render_kpi_row(metrics)

        mock_cols[0].metric.assert_called_once_with(
            label="Revenue",
            value="$100,000",
            delta="+10%",
            delta_color="normal",
        )

def test_render_kpi_row_with_delta_color():
    """Test render_kpi_row with custom delta colors."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%", "delta_color": "normal"},
        {"label": "Cost", "value": "$60,000", "delta": "-5%", "delta_color": "inverse"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        mock_cols = [MagicMock() for _ in range(2)]
        mock_st.columns.return_value = mock_cols

        render_kpi_row(metrics)

        mock_cols[0].metric.assert_called_once_with(
            label="Revenue",
            value="$100,000",
            delta="+10%",
            delta_color="normal",
        )
        mock_cols[1].metric.assert_called_once_with(
            label="Cost",
            value="$60,000",
            delta="-5%",
            delta_color="inverse",
        )

def test_render_kpi_row_default_delta_color():
    """Test render_kpi_row uses 'normal' as default delta_color."""
    metrics = [
        {"label": "Revenue", "value": "$100,000", "delta": "+10%"},
    ]

    with patch("components.kpi_cards.st") as mock_st:
        mock_col = MagicMock()
        mock_st.columns.return_value = [mock_col]

        render_kpi_row(metrics)

        mock_col.metric.assert_called_once()
        call_kwargs = mock_col.metric.call_args[1]
        assert call_kwargs["delta_color"] == "normal"

def test_render_kpi_row_empty_metrics():
    """Test render_kpi_row with empty metrics list."""
    metrics = []

    with patch("components.kpi_cards.st") as mock_st:
        mock_st.columns.return_value = []

        render_kpi_row(metrics)

        mock_st.columns.assert_called_once_with(0)

def test_render_kpi_row_many_metrics():
    """Test render_kpi_row with many metrics (4)."""
    metrics = [
        {"label": f"Metric {i}", "value": f"${i}00,000"}
        for i in range(1, 5)
    ]

    with patch("components.kpi_cards.st") as mock_st:
        mock_cols = [MagicMock() for _ in range(4)]
        mock_st.columns.return_value = mock_cols

        render_kpi_row(metrics)

        mock_st.columns.assert_called_once_with(4)
        for i, col in enumerate(mock_cols):
            col.metric.assert_called_once()
