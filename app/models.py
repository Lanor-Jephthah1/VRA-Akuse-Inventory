from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    location = Column(String(120), default="VRA, Akuse")
    head_of_dept = Column(String(100), nullable=True)

    users = relationship("User", back_populates="department")
    items = relationship("InventoryItem", back_populates="owning_department")
    requisitions = relationship("Requisition", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(String(30), unique=True, index=True, nullable=False)  # e.g. VRA-AK-1042 or NSS-AK-2026-08
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    role = Column(String(30), nullable=False, default="STAFF")
    # Roles: SUPERVISOR, STORE_OFFICER, STAFF
    job_title = Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    password_plain = Column(String(100), default="vra123")  # Simple demo auth + quick role switcher
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="users")
    requisitions_requested = relationship(
        "Requisition", foreign_keys="Requisition.requester_id", back_populates="requester"
    )
    requisitions_approved = relationship(
        "Requisition", foreign_keys="Requisition.approved_by_id", back_populates="approved_by"
    )
    requisitions_issued = relationship(
        "Requisition", foreign_keys="Requisition.issued_by_id", back_populates="issued_by"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(40), unique=True, index=True, nullable=False)  # e.g. VRA-MIS-001
    name = Column(String(150), nullable=False)
    category = Column(String(80), nullable=False)  # IT & Networking, Electrical Spares, Mechanical, PPE & Safety, Stationery, Medical/Hospital
    item_type = Column(String(30), nullable=False, default="CONSUMABLE")  # CONSUMABLE or ASSET
    brand_model = Column(String(120), nullable=True)
    serial_or_part_no = Column(String(100), nullable=True)
    vra_asset_tag = Column(String(80), nullable=True)
    unit = Column(String(30), nullable=False, default="pcs")  # pcs, boxes, meters, sets, rolls, packs
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=5)
    store_location = Column(String(120), nullable=False, default="MIS Store - Rack A1")
    condition = Column(String(40), nullable=False, default="New / Good")  # New / Good, Fair, Faulty, Under Repair
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owning_department = relationship("Department", back_populates="items")
    requisitions = relationship("Requisition", back_populates="item")
    transactions = relationship("StockTransaction", back_populates="item")


class Requisition(Base):
    __tablename__ = "requisitions"

    id = Column(Integer, primary_key=True, index=True)
    siv_number = Column(String(40), index=True, nullable=False)  # e.g. SIV-AK-2026-0001 (shared across line items in a requisition order)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    purpose = Column(Text, nullable=False)
    job_card_ref = Column(String(80), nullable=True)  # e.g. WO-KGS-4412 or INC-MIS-809
    is_returnable = Column(Boolean, default=False)
    expected_return_date = Column(String(40), nullable=True)

    # Workflow statuses:
    # PENDING_APPROVAL -> APPROVED -> ISSUED -> RETURNED
    # or REJECTED
    status = Column(String(40), nullable=False, default="PENDING_APPROVAL")

    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    supervisor_remarks = Column(Text, nullable=True)

    issued_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)

    requester = relationship("User", foreign_keys=[requester_id], back_populates="requisitions_requested")
    approved_by = relationship("User", foreign_keys=[approved_by_id], back_populates="requisitions_approved")
    issued_by = relationship("User", foreign_keys=[issued_by_id], back_populates="requisitions_issued")
    department = relationship("Department", back_populates="requisitions")
    item = relationship("InventoryItem", back_populates="requisitions")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    voucher_no = Column(String(50), index=True, nullable=False)  # SRV-AK-2026-001 or SIV-AK-2026-001
    transaction_type = Column(String(30), nullable=False)  # RECEIVE_SRV, ISSUE_SIV, RETURN, ADJUSTMENT
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # +10 or -2
    balance_after = Column(Integer, nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_or_supplier = Column(String(150), nullable=True)
    reference_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("InventoryItem", back_populates="transactions")
    performed_by = relationship("User")
