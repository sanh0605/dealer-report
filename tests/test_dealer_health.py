import pytest
import pandas as pd
from services.analytics import classify_dealer_health

def test_classify_dealer_health_good():
    # Good: AR < 30 days, payment > 90%
    assert classify_dealer_health(ar_days=10, payment_score=95) == "Tốt"

def test_classify_dealer_health_warning_ar():
    # Warning: AR 30-60 days
    assert classify_dealer_health(ar_days=45, payment_score=95) == "Cảnh báo"

def test_classify_dealer_health_warning_payment():
    # Warning: payment 70-90%
    assert classify_dealer_health(ar_days=10, payment_score=80) == "Cảnh báo"

def test_classify_dealer_health_critical_ar():
    # Critical: AR > 60 days
    assert classify_dealer_health(ar_days=90, payment_score=95) == "Nguy hiểm"

def test_classify_dealer_health_critical_payment():
    # Critical: payment < 70%
    assert classify_dealer_health(ar_days=10, payment_score=50) == "Nguy hiểm"

def test_classify_dealer_health_inactive():
    # Inactive: no sales in 90 days (indicated by is_active=False)
    assert classify_dealer_health(ar_days=0, payment_score=100, is_active=False) == "Nguy hiểm"

def test_calc_ar_aging():
    from services.analytics import calc_ar_aging
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4"],
        "due_date": [
            today - timedelta(days=10), # 0-30
            today - timedelta(days=45), # 30-60
            today - timedelta(days=100),# 90-120
            today - timedelta(days=200),# 180+
        ],
        "total_order_value": [1000.0, 1000.0, 1000.0, 1000.0],
        "paid_amount": [0.0, 0.0, 0.0, 0.0],
        "refund_amount": [0.0, 0.0, 0.0, 0.0],
        "deduction_amount": [0.0, 0.0, 0.0, 0.0],
    })
    
    # Mocking config constants inside the test if needed, but they are in config.py
    # AR_BUCKET_SIZE = 30, AR_MAX_DAYS = 180
    
    aging = calc_ar_aging(df, today=today)
    
    # Expected buckets: 0-30, 30-60, 60-90, 90-120, 120-150, 150-180, 180+
    assert aging.get("0-30", 0) == 1000.0
    assert aging.get("30-60", 0) == 1000.0
    assert aging.get("90-120", 0) == 1000.0
    assert aging.get("180+", 0) == 1000.0
    assert aging.get("60-90", 0) == 0.0

def test_calc_dealer_health_stats():
    from services.analytics import calc_dealer_health_stats
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    
    # Dealer Master
    dealer_df = pd.DataFrame({
        "dealer_id": ["D1", "D2", "D3", "D4"],
        "dealer_name": ["Dealer 1", "Dealer 2", "Dealer 3", "Dealer 4"]
    })
    
    # Sales Records (to determine active/inactive and new)
    sales_df = pd.DataFrame({
        "dealer_id": ["D1", "D2", "D1"],
        "date_transfer": [
            today - timedelta(days=10), # D1 active
            today - timedelta(days=100),# D2 inactive (no sales in 90 days)
            today - timedelta(days=10), # D1 active
        ],
        "sales_revenue": [1000.0, 1000.0, 1000.0]
    })
    # D3 has no sales (inactive)
    # D4 has no sales (inactive)
    
    # AR Ledger (to determine health)
    ar_df = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "dealer_id": ["D1", "D2"],
        "due_date": [
            today - timedelta(days=10), # D1 AR < 30
            today - timedelta(days=45), # D2 AR 30-60
        ],
        "total_order_value": [1000.0, 1000.0],
        "paid_amount": [950.0, 750.0], # D1 payment 95%, D2 payment 75%
        "refund_amount": [0.0, 0.0],
        "deduction_amount": [0.0, 0.0]
    })
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # Only D1 and D2 are in ar_df
    assert stats["total_dealers"] == 2
    # D1: AR 10, payment 95%, active -> Tốt
    # D2: AR 45, payment 75%, inactive -> Nguy hiểm
    
    # Let's adjust D2 to be active to test Warning.
    sales_df = pd.concat([sales_df, pd.DataFrame({
        "dealer_id": ["D2"],
        "date_transfer": [today - timedelta(days=5)],
        "sales_revenue": [500.0]
    })])
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # D1: AR 10, payment 95%, active -> Tốt
    # D2: AR 45, payment 75%, active -> Cảnh báo
    
    assert stats["total_dealers"] == 2
    assert stats["counts"]["Tốt"] == 1
    assert stats["counts"]["Cảnh báo"] == 1
    assert stats["counts"]["Nguy hiểm"] == 0
    
    assert stats["inactive_dealers"] == 0 # D1, D2 are both active now

def test_calc_dealer_health_stats_paid_orders():
    from services.analytics import calc_dealer_health_stats
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    
    # Dealer Master
    dealer_df = pd.DataFrame({
        "dealer_id": ["D1"],
        "dealer_name": ["Dealer 1"]
    })
    
    # Sales Records
    sales_df = pd.DataFrame({
        "dealer_id": ["D1"],
        "date_transfer": [today - timedelta(days=10)],
        "sales_revenue": [1000.0]
    })
    
    # AR Ledger: Fully paid but OLD due date
    ar_df = pd.DataFrame({
        "order_id": ["O1"],
        "dealer_id": ["D1"],
        "due_date": [today - timedelta(days=100)], # 100 days ago
        "total_order_value": [1000.0],
        "paid_amount": [1000.0], # Fully paid
        "refund_amount": [0.0],
        "deduction_amount": [0.0]
    })
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # Should be "Tốt" because outstanding is 0, so debt age should be 0, not 100
    assert stats["health_df"].iloc[0]["status"] == "Tốt"
    assert stats["health_df"].iloc[0]["days_overdue"] == 0

def test_calc_dealer_health_stats_tolerance():
    from services.analytics import calc_dealer_health_stats
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    dealer_df = pd.DataFrame({"dealer_id": ["D1"], "dealer_name": ["Dealer 1"]})
    sales_df = pd.DataFrame({"dealer_id": ["D1"], "date_transfer": [today - timedelta(days=10)], "sales_revenue": [1000.0]})
    
    # AR Ledger: 10,000 VND debt (below 50k tolerance)
    ar_df = pd.DataFrame({
        "order_id": ["O1"],
        "dealer_id": ["D1"],
        "due_date": [today - timedelta(days=100)], # Overdue 100 days
        "total_order_value": [1000000.0],
        "paid_amount": [990000.0], # 10k remaining
        "refund_amount": [0.0],
        "deduction_amount": [0.0]
    })
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # Should still be "Tốt" because 10k < 50k threshold
    assert stats["health_df"].iloc[0]["status"] == "Tốt"
    assert stats["health_df"].iloc[0]["days_overdue"] == 0

def test_calc_dealer_health_stats_future_due_date():
    from services.analytics import calc_dealer_health_stats
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    dealer_df = pd.DataFrame({"dealer_id": ["D1"], "dealer_name": ["Dealer 1"]})
    sales_df = pd.DataFrame({"dealer_id": ["D1"], "date_transfer": [today - timedelta(days=10)], "sales_revenue": [1000.0]})
    
    # AR Ledger: Due in the future
    ar_df = pd.DataFrame({
        "order_id": ["O1"],
        "dealer_id": ["D1"],
        "due_date": [today + timedelta(days=30)], # Due in 30 days
        "total_order_value": [1000000.0],
        "paid_amount": [0.0],
        "refund_amount": [0.0],
        "deduction_amount": [0.0]
    })
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # Should be "Tốt" and days_overdue should be 0 (not negative)
    assert stats["health_df"].iloc[0]["status"] == "Tốt"
    assert stats["health_df"].iloc[0]["days_overdue"] == 0

def test_calc_dealer_health_stats_none_due_date():
    from services.analytics import calc_dealer_health_stats
    from datetime import date, timedelta
    
    today = date(2026, 5, 15)
    dealer_df = pd.DataFrame({"dealer_id": ["D1"], "dealer_name": ["Dealer 1"]})
    sales_df = pd.DataFrame({"dealer_id": ["D1"], "date_transfer": [today - timedelta(days=10)], "sales_revenue": [1000.0]})
    
    # AR Ledger: Due date is None/NaN
    ar_df = pd.DataFrame({
        "order_id": ["O1"],
        "dealer_id": ["D1"],
        "due_date": [None], 
        "total_order_value": [1000000.0],
        "paid_amount": [0.0],
        "refund_amount": [0.0],
        "deduction_amount": [0.0]
    })
    
    stats = calc_dealer_health_stats(ar_df, dealer_df, sales_df, today=today)
    
    # Should handle None gracefully and be Nguy hiểm (inactive rules apply or payment score 0)
    # Actually if due_date is None, score_val is 0 (not due yet), so payment_score is 100
    # days_overdue is 0. is_active is True.
    assert stats["health_df"].iloc[0]["status"] == "Tốt"
    assert stats["health_df"].iloc[0]["days_overdue"] == 0
