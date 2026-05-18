"""
Configuration constants and mappings for Dealer Report System.
"""

ROLES = ["Admin", "Manager", "Sales Staff"]

# AR Aging Configuration
AR_BUCKET_SIZE = 30  # days per bucket
AR_MAX_DAYS = 180     # maximum days to display


PRODUCT_GROUP_MAP: dict[str, str] = {
    # Populate with actual brand names before first upload
    # Example: "Trek": "Premium Bikes", "Shimano": "Components"
}

SUB_REGION_TO_REGION: dict[str, str] = {
    # Populate with actual sub_region names before first upload
    # Example: "Chiang Mai": "North", "Bangkok": "Central", "Phuket": "South"
}

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "sale_records": ["order_id","order_date","date_transfer","dealer_id","item_id",
                     "salesperson","sale_admin","channel_name","sales_volume",
                     "unit_price_standard","total_price_standard","sales_revenue",
                     "cost_of_goods"],
    "accounts_receivable_ledger": ["order_id","order_date","dealer_id","date_posted","due_date",
                                    "total_order_value","refund_amount",
                                    "deduction_amount","paid_amount"],
    "product_master": ["item_id","item_name","product_id","product","brand",
                        "category","subcategory","model","color","size"],
    "dealer_master": ["dealer_id","dealer_name","business_name","province",
                       "sub_region","address"],
    "sales_targets": ["month_year","sub_region","target_revenue"],
    "inventory_status": ["item_id","stock_on_hand","location","location_region"],
    "incoming_shipments": ["item_id","incoming_qty","expected_arrival_date"],
    "open_orders": ["order_id","dealer_id","item_id","open_qty"],
    "field_visit_plans": ["staff_name","month_year","dealer_id"],
    "visit_logs": ["date","staff_name","dealer_id","visit_result"],
}
