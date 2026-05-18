import uuid
from sqlalchemy import Column, Text, Integer, Float, Date, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def _uuid() -> str:
    return str(uuid.uuid4())

class SaleRecord(Base):
    __tablename__ = "sale_records"
    order_id              = Column(Text, primary_key=True)
    item_id               = Column(Text, primary_key=True)
    order_date            = Column(DateTime)
    date_transfer         = Column(Date, primary_key=True)
    dealer_id             = Column(Text, index=True)
    salesperson           = Column(Text)
    sale_admin            = Column(Text)
    channel_name          = Column(Text)
    sales_volume          = Column(Integer)
    unit_price_standard   = Column(Float)
    total_price_standard  = Column(Float)
    sales_revenue         = Column(Float)
    cost_of_goods         = Column(Float)

class AccountsReceivableLedger(Base):
    __tablename__ = "accounts_receivable_ledger"
    id                = Column(Text, primary_key=True, default=_uuid)
    order_id          = Column(Text, index=True)
    order_date        = Column(Date)
    dealer_id         = Column(Text, index=True)
    date_posted       = Column(Date)
    due_date          = Column(Date)
    total_order_value = Column(Float)
    refund_amount     = Column(Float)
    deduction_amount  = Column(Float)
    paid_amount       = Column(Float)

class ProductMaster(Base):
    __tablename__ = "product_master"
    item_id      = Column(Text, primary_key=True)
    item_name    = Column(Text)
    product_id   = Column(Text)
    product      = Column(Text)
    product_group  = Column(Text)
    brand        = Column(Text)
    category     = Column(Text)
    subcategory  = Column(Text)
    model        = Column(Text)
    color        = Column(Text)
    size         = Column(Text)

class DealerMaster(Base):
    __tablename__ = "dealer_master"
    dealer_id     = Column(Text, primary_key=True)
    dealer_name   = Column(Text)
    business_name = Column(Text)
    province      = Column(Text)
    sub_region    = Column(Text)
    region        = Column(Text)
    address       = Column(Text)

class SalesTarget(Base):
    __tablename__ = "sales_targets"
    target_id      = Column(Text, primary_key=True, default=_uuid)
    month_year     = Column(Text, index=True)
    sub_region     = Column(Text)
    target_revenue = Column(Float)

class InventoryStatus(Base):
    __tablename__ = "inventory_status"
    item_id         = Column(Text, primary_key=True)
    stock_on_hand   = Column(Integer)
    location        = Column(Text)
    location_region = Column(Text)

class IncomingShipment(Base):
    __tablename__ = "incoming_shipments"
    id                    = Column(Text, primary_key=True, default=_uuid)
    item_id               = Column(Text, index=True)
    incoming_qty          = Column(Integer)
    expected_arrival_date = Column(Date)

class OpenOrder(Base):
    __tablename__ = "open_orders"
    order_id  = Column(Text, primary_key=True)
    dealer_id = Column(Text, index=True)
    item_id   = Column(Text, index=True)
    open_qty  = Column(Integer)

class LostSalesEntry(Base):
    __tablename__ = "lost_sales_entry"
    entry_id     = Column(Text, primary_key=True, default=_uuid)
    date         = Column(Date)
    staff_name   = Column(Text)
    dealer_id    = Column(Text, index=True)
    item_id      = Column(Text, index=True)
    lost_volume  = Column(Integer)
    lost_revenue = Column(Float)

class FieldVisitPlan(Base):
    __tablename__ = "field_visit_plans"
    plan_id    = Column(Text, primary_key=True, default=_uuid)
    staff_name = Column(Text)
    month_year = Column(Text, index=True)
    dealer_id  = Column(Text, index=True)

class VisitLog(Base):
    __tablename__ = "visit_logs"
    log_id       = Column(Text, primary_key=True, default=_uuid)
    date         = Column(Date)
    staff_name   = Column(Text)
    dealer_id    = Column(Text, index=True)
    plan_id      = Column(Text)
    visit_result = Column(Text)

class User(Base):
    __tablename__ = "users"
    id            = Column(Text, primary_key=True, default=_uuid)
    username      = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role          = Column(Text, nullable=False)
    display_name  = Column(Text)
    created_at    = Column(DateTime)
    last_login    = Column(DateTime)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id          = Column(Text, primary_key=True, default=_uuid)
    timestamp   = Column(DateTime)
    username    = Column(Text)
    action_type = Column(Text)
    record_id   = Column(Text)
    table_name  = Column(Text)
    details     = Column(Text)
