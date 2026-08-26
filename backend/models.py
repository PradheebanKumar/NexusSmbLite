from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    whatsapp_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inventory = relationship("Inventory", back_populates="owner", cascade="all, delete")
    sales = relationship("Sale", back_populates="owner", cascade="all, delete")
    expenses = relationship("Expense", back_populates="owner", cascade="all, delete")
    conversations = relationship("Conversation", back_populates="owner", cascade="all, delete")
    demand_signals = relationship("DemandSignal", back_populates="owner", cascade="all, delete")
    pending_actions = relationship("PendingAction", back_populates="owner", cascade="all, delete")
    alerts = relationship("Alert", back_populates="owner", cascade="all, delete")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    item_name = Column(String, nullable=False, index=True)
    quantity = Column(Float, default=0)
    unit = Column(String, default="units")
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    low_stock_threshold = Column(Float, default=10)
    last_sold_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("Owner", back_populates="inventory")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity_sold = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Owner", back_populates="sales")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    amount = Column(Float, nullable=False)
    expense_type = Column(String, nullable=False)  # rent, electricity, salary, supplier, other
    description = Column(String, nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Owner", back_populates="expenses")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    role = Column(String, nullable=False)  # user or assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Owner", back_populates="conversations")


class DemandSignal(Base):
    __tablename__ = "demand_signals"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    product_name = Column(String, nullable=False)
    count = Column(Integer, default=1)
    customer_phone = Column(String, nullable=True)
    last_requested = Column(DateTime(timezone=True), server_default=func.now())
    notified = Column(Boolean, default=False)

    owner = relationship("Owner", back_populates="demand_signals")


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    action_type = Column(String, nullable=False)  # send_offer, update_price, reorder, notify_customers
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    generated_content = Column(Text, nullable=True)  # offer message, etc.
    action_data = Column(JSON, nullable=True)  # structured data for execution
    status = Column(String, default="pending")  # pending, approved, rejected, executed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("Owner", back_populates="pending_actions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    alert_type = Column(String, nullable=False)  # low_stock, slow_mover, cash_warning, demand
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Owner", back_populates="alerts")
