import pandas as pd
from datetime import date
from config import AR_BUCKET_SIZE, AR_MAX_DAYS

def calc_total_revenue(sales_df: pd.DataFrame) -> float:
    if sales_df.empty or "sales_revenue" not in sales_df.columns:
        return 0.0
    return float(sales_df["sales_revenue"].sum())

def calc_gross_profit(sales_df: pd.DataFrame) -> tuple[float, float]:
    if sales_df.empty:
        return 0.0, 0.0
    revenue = float(sales_df["sales_revenue"].sum())
    cogs = float(sales_df["cost_of_goods"].sum())
    profit = revenue - cogs
    margin = (profit / revenue * 100) if revenue > 0 else 0.0
    return profit, margin

def calc_target_completion(actual: float, target: float) -> float:
    if target == 0:
        return 0.0
    return actual / target * 100

def calc_ar_outstanding(ar_df: pd.DataFrame) -> float:
    if ar_df.empty:
        return 0.0
    per_order = ar_df.groupby("order_id").agg(
        total=("total_order_value", "max"),
        paid=("paid_amount", "sum"),
        refund=("refund_amount", "sum"),
        deduction=("deduction_amount", "sum"),
    )
    per_order["outstanding"] = (
        per_order["total"] - per_order["paid"]
        - per_order["refund"] - per_order["deduction"]
    ).clip(lower=0)
    return float(per_order["outstanding"].sum())

def calc_visit_adherence(
    plans_df: pd.DataFrame,
    logs_df: pd.DataFrame,
) -> tuple[float, list[str]]:
    if plans_df.empty:
        return 0.0, []
    planned = set(plans_df["dealer_id"].unique())
    visited = set(logs_df["dealer_id"].unique()) if not logs_df.empty else set()
    hit = planned & visited
    missed = sorted(planned - visited)
    adherence = len(hit) / len(planned) * 100
    return adherence, missed

def classify_dealer_health(ar_days: int, payment_score: float, is_active: bool = True) -> str:
    """
    Classify dealer health based on AR aging, payment performance and activity.
    Criteria (from MASTER_DECISIONS.md):
    - Good (Tốt): Active sales, AR < 30 days, payment > 90%
    - Warning (Cảnh báo): Active sales, AR 30-60 days, payment 70-90%
    - Critical (Nguy hiểm): AR > 60 days, payment < 70%, or inactive
    """
    if not is_active:
        return "Nguy hiểm"
    
    if ar_days > 60 or payment_score < 70:
        return "Nguy hiểm"
    
    if ar_days >= 30 or payment_score <= 90:
        return "Cảnh báo"
        
    return "Tốt"

def calc_ar_aging(ar_df: pd.DataFrame, today: date | None = None) -> dict[str, float]:
    """
    Calculate AR aging buckets based on due_date.
    """
    if ar_df.empty:
        return {}
    
    if today is None:
        today = date.today()
        
    df = ar_df.copy()
    df["due_date"] = pd.to_datetime(df["due_date"]).dt.date
    
    # Calculate outstanding per order
    per_order = df.groupby("order_id").agg({
        "due_date": "first",
        "total_order_value": "max",
        "paid_amount": "sum",
        "refund_amount": "sum",
        "deduction_amount": "sum"
    }).reset_index()
    
    per_order["outstanding"] = (
        per_order["total_order_value"] - per_order["paid_amount"] 
        - per_order["refund_amount"] - per_order["deduction_amount"]
    ).clip(lower=0)
    
    # Only keep orders with outstanding amount
    per_order = per_order[per_order["outstanding"] > 0]
    
    if per_order.empty:
        return {}
        
    # Calculate days overdue (non-negative)
    per_order["days_overdue"] = per_order["due_date"].apply(lambda d: max(0, (today - d).days) if pd.notna(d) else 0)
    
    # Initialize buckets
    buckets = {}
    for i in range(0, AR_MAX_DAYS, AR_BUCKET_SIZE):
        label = f"{i}-{i+AR_BUCKET_SIZE}"
        buckets[label] = 0.0
    buckets[f"{AR_MAX_DAYS}+"] = 0.0
    
    # Fill buckets
    for _, row in per_order.iterrows():
        days = row["days_overdue"]
        if days >= AR_MAX_DAYS:
            buckets[f"{AR_MAX_DAYS}+"] += row["outstanding"]
        else:
            bucket_idx = (days // AR_BUCKET_SIZE) * AR_BUCKET_SIZE
            label = f"{bucket_idx}-{bucket_idx+AR_BUCKET_SIZE}"
            buckets[label] += row["outstanding"]
            
    return buckets

def calc_dealer_health_stats(
    ar_df: pd.DataFrame, 
    dealer_df: pd.DataFrame, 
    sales_df: pd.DataFrame,
    today: date | None = None
) -> dict:
    """
    Calculate comprehensive dealer health statistics.
    """
    if dealer_df.empty:
        return {
            "total_dealers": 0, "healthy_dealers": 0, "at_risk_dealers": 0,
            "new_dealers": 0, "inactive_dealers": 0, "counts": {}, "health_df": pd.DataFrame()
        }
        
    if today is None:
        today = date.today()
        
    # 1. Determine activity status (active if sale in last 90 days)
    ninety_days_ago = today - pd.Timedelta(days=90)
    sales_copy = sales_df.copy()
    sales_copy["date_transfer"] = pd.to_datetime(sales_copy["date_transfer"]).dt.date
    
    last_sale = sales_copy.groupby("dealer_id")["date_transfer"].max().reset_index()
    last_sale.columns = ["dealer_id", "last_sale_date"]
    
    first_sale = sales_copy.groupby("dealer_id")["date_transfer"].min().reset_index()
    first_sale.columns = ["dealer_id", "first_sale_date"]
    
    # 2. Determine payment performance and AR aging per dealer
    ar_copy = ar_df.copy()
    ar_copy["due_date"] = pd.to_datetime(ar_copy["due_date"]).dt.date
    
    # Calculate per order first to handle multiple payments/items
    per_order = ar_copy.groupby(["order_id", "dealer_id"]).agg({
        "due_date": "first",
        "total_order_value": "max",
        "paid_amount": "sum",
        "refund_amount": "sum",
        "deduction_amount": "sum"
    }).reset_index()
    
    per_order["outstanding"] = (
        per_order["total_order_value"] - per_order["paid_amount"] 
        - per_order["refund_amount"] - per_order["deduction_amount"]
    ).clip(lower=0)
    
    # Apply tolerance threshold (e.g., 50,000 VND)
    # If debt is less than threshold, treat as 0 for aging
    TOLERANCE = 50000 
    
    # Only calculate days_overdue for orders with outstanding debt > TOLERANCE
    per_order["days_overdue"] = per_order.apply(
        lambda row: max(0, (today - row["due_date"]).days) if (row["outstanding"] > TOLERANCE and pd.notna(row["due_date"])) else 0,
        axis=1
    )
    
    # Aggregated per dealer
    dealer_ar = per_order.groupby("dealer_id").agg({
        "total_order_value": "sum",
        "paid_amount": "sum",
        "refund_amount": "sum",
        "deduction_amount": "sum",
        "outstanding": "sum",
        "days_overdue": "max" # Worst case aging
    }).reset_index()
    
    # New Logic: Recovery Rate = (Paid + Deduction) / (Total - Refund)
    # Only consider orders that are already due to avoid penalizing future debt in "Health"
    due_orders = per_order[per_order["due_date"].apply(lambda d: d <= today if pd.notna(d) else False)].copy()
    
    if due_orders.empty:
        # If no orders are due, payment score is 100% (perfect)
        dealer_ar = per_order.groupby("dealer_id").agg({
            "total_order_value": "sum",
            "paid_amount": "sum",
            "refund_amount": "sum",
            "deduction_amount": "sum",
            "outstanding": "sum",
            "days_overdue": "max" 
        }).reset_index()
        dealer_ar["payment_score"] = 100.0
    else:
        # Aggregated per dealer for status calculation (using only due orders for score)
        dealer_due = due_orders.groupby("dealer_id").agg({
            "total_order_value": "sum",
            "paid_amount": "sum",
            "refund_amount": "sum",
            "deduction_amount": "sum"
        }).reset_index()
        
        net_total = dealer_due["total_order_value"] - dealer_due["refund_amount"]
        recovery_total = dealer_due["paid_amount"] + dealer_due["deduction_amount"]
        dealer_due["payment_score"] = (recovery_total / net_total * 100).fillna(100)
        
        # Aggregate ALL orders for totals, but join with the payment_score from due orders
        dealer_totals = per_order.groupby("dealer_id").agg({
            "total_order_value": "sum",
            "paid_amount": "sum",
            "refund_amount": "sum",
            "deduction_amount": "sum",
            "outstanding": "sum",
            "days_overdue": "max"
        }).reset_index()
        
        dealer_ar = dealer_totals.merge(dealer_due[["dealer_id", "payment_score"]], on="dealer_id", how="left")
        dealer_ar["payment_score"] = dealer_ar["payment_score"].fillna(100.0)
    
    # Cap score at 100% 
    dealer_ar["payment_score"] = dealer_ar["payment_score"].clip(upper=100)
    
    # 3. Merge all data starting from AR population
    # Use dealer_ar (from ar_df) as the base population
    health_df = dealer_ar.merge(dealer_df[["dealer_id", "dealer_name"]], on="dealer_id", how="left")
    health_df = health_df.merge(last_sale, on="dealer_id", how="left")
    health_df = health_df.merge(first_sale, on="dealer_id", how="left")
    
    # Ensure dealer_name is not empty for display
    health_df["dealer_name"] = health_df["dealer_name"].fillna(health_df["dealer_id"])
    
    # Fill missing values
    health_df["outstanding"] = health_df["outstanding"].fillna(0)
    health_df["days_overdue"] = health_df["days_overdue"].fillna(0)
    health_df["payment_score"] = health_df["payment_score"].fillna(100)
    
    # 4. Apply health classification
    health_df["is_active"] = health_df["last_sale_date"].apply(lambda d: d >= ninety_days_ago if pd.notna(d) else False)
    
    health_df["status"] = health_df.apply(
        lambda row: classify_dealer_health(int(row["days_overdue"]), row["payment_score"], row["is_active"]),
        axis=1
    )
    
    # 5. New dealers (first sale this month)
    this_month_start = date(today.year, today.month, 1)
    health_df["is_new"] = health_df["first_sale_date"].apply(lambda d: d >= this_month_start if pd.notna(d) else False)
    
    # 6. Aggregate results
    counts = health_df["status"].value_counts().to_dict()
    for status in ["Tốt", "Cảnh báo", "Nguy hiểm"]:
        if status not in counts:
            counts[status] = 0
            
    return {
        "total_dealers": len(health_df),
        "healthy_dealers": counts.get("Tốt", 0),
        "at_risk_dealers": counts.get("Nguy hiểm", 0) + counts.get("Cảnh báo", 0),
        "new_dealers": int(health_df["is_new"].sum()),
        "inactive_dealers": int((~health_df["is_active"]).sum()),
        "counts": counts,
        "health_df": health_df
    }
