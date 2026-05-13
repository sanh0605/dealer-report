import pytest
import pandas as pd
from services.analytics import (
    calc_total_revenue, calc_gross_profit, calc_target_completion,
    calc_ar_outstanding, calc_visit_adherence,
)

def test_calc_total_revenue():
    df = pd.DataFrame({"sales_revenue": [100.0, 200.0, 300.0]})
    assert calc_total_revenue(df) == 600.0

def test_calc_total_revenue_empty():
    df = pd.DataFrame({"sales_revenue": []})
    assert calc_total_revenue(df) == 0.0

def test_calc_gross_profit():
    df = pd.DataFrame({"sales_revenue": [1000.0], "cost_of_goods": [600.0]})
    profit, margin = calc_gross_profit(df)
    assert profit == 400.0
    assert margin == pytest.approx(40.0)

def test_calc_target_completion():
    assert calc_target_completion(actual=800.0, target=1000.0) == pytest.approx(80.0)

def test_calc_target_completion_zero_target():
    assert calc_target_completion(actual=800.0, target=0.0) == 0.0

def test_calc_ar_outstanding():
    df = pd.DataFrame({
        "order_id": ["O1", "O1", "O2"],
        "total_order_value": [1000.0, 1000.0, 500.0],
        "paid_amount": [400.0, 0.0, 500.0],
        "refund_amount": [0.0, 0.0, 0.0],
        "deduction_amount": [0.0, 0.0, 0.0],
    })
    result = calc_ar_outstanding(df)
    assert result == pytest.approx(600.0)

def test_calc_visit_adherence():
    plans = pd.DataFrame({"dealer_id": ["D1", "D2", "D3"], "staff_name": ["Alice"]*3})
    logs = pd.DataFrame({"dealer_id": ["D1", "D3"], "staff_name": ["Alice"]*2})
    adherence, missed = calc_visit_adherence(plans, logs)
    assert adherence == pytest.approx(2/3 * 100)
    assert set(missed) == {"D2"}

def test_calc_visit_adherence_no_plans():
    plans = pd.DataFrame({"dealer_id": ["D1", "D2"], "staff_name": ["Alice"]*2})
    logs = pd.DataFrame({"dealer_id": ["D1"], "staff_name": ["Alice"]})
    adherence, missed = calc_visit_adherence(plans, logs)
    assert adherence == pytest.approx(1/2 * 100)
    assert set(missed) == {"D2"}
