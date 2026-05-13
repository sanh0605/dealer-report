import pandas as pd

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
