import csv
import io
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from .database import engine, Base, get_db, SessionLocal
from .models import Department, User, InventoryItem, Requisition, StockTransaction
from .seed_data import seed_database

app = FastAPI(
    title="VRA Akuse Inventory & Requisition Management System",
    description="Standard Enterprise Inventory, SIV/SRV Voucher & Multi-Departmental Requisition Portal for VRA Akuse (Kpong Generating Station)",
    version="2.1.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


def get_authenticated_user(request: Request, db: Session) -> Optional[User]:
    staff_id = request.cookies.get("vra_session_user")
    if not staff_id:
        return None
    return (
        db.query(User)
        .options(joinedload(User.department))
        .filter(User.staff_id == staff_id, User.is_active == True)
        .first()
    )


def get_common_context(
    request: Request,
    db: Session,
    current_user: User,
    active_page: str,
    flash_msg: Optional[str] = None,
):
    all_users = db.query(User).options(joinedload(User.department)).order_by(User.id).all()
    departments = db.query(Department).order_by(Department.code).all()

    if current_user.role == "STAFF":
        pending_count = (
            db.query(Requisition.siv_number)
            .filter(
                Requisition.requester_id == current_user.id,
                Requisition.status == "PENDING_APPROVAL",
            )
            .distinct()
            .count()
        )
        approved_ready_count = (
            db.query(Requisition.siv_number)
            .filter(
                Requisition.requester_id == current_user.id,
                Requisition.status == "APPROVED",
            )
            .distinct()
            .count()
        )
    else:
        pending_count = db.query(Requisition.siv_number).filter(Requisition.status == "PENDING_APPROVAL").distinct().count()
        approved_ready_count = db.query(Requisition.siv_number).filter(Requisition.status == "APPROVED").distinct().count()

    low_stock_count = (
        db.query(InventoryItem)
        .filter(InventoryItem.quantity_on_hand <= InventoryItem.reorder_level)
        .count()
    )
    return {
        "request": request,
        "current_user": current_user,
        "all_users": all_users,
        "departments": departments,
        "active_page": active_page,
        "pending_count": pending_count,
        "approved_ready_count": approved_ready_count,
        "low_stock_count": low_stock_count,
        "flash_msg": flash_msg or request.query_params.get("msg"),
    }


@app.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    error: Optional[str] = None,
    msg: Optional[str] = None,
    mode: str = "STAFF",
    db: Session = Depends(get_db),
):
    demo_accounts = (
        db.query(User)
        .options(joinedload(User.department))
        .filter(User.is_active == True)
        .order_by(User.id)
        .all()
    )
    import json
    demo_accounts_json = json.dumps([
        {
            "staffId": acc.staff_id,
            "name": acc.full_name,
            "dept": acc.department.code,
            "role": acc.role,
            "roleLabel": acc.role.replace("_", " "),
        }
        for acc in demo_accounts
    ])
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "demo_accounts": demo_accounts,
            "demo_accounts_json": demo_accounts_json,
            "error": error,
            "msg": msg,
            "mode": mode if mode in ["STAFF", "SUPERVISOR"] else "STAFF",
        },
    )


@app.post("/login")
def login_submit(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    login_mode: str = Form("STAFF"),
    db: Session = Depends(get_db),
):
    ident = identifier.strip()
    mode = login_mode if login_mode in ["STAFF", "SUPERVISOR"] else "STAFF"
    user = (
        db.query(User)
        .options(joinedload(User.department))
        .filter((User.staff_id.ilike(ident)) | (User.email.ilike(ident)))
        .first()
    )
    if not user or user.password_plain != password.strip():
        return RedirectResponse(
            url=f"/login?mode={mode}&error=Invalid+VRA+Staff+ID+/+Email+or+Password.+Please+try+again.",
            status_code=303,
        )
    if not user.is_active:
        return RedirectResponse(
            url=f"/login?mode={mode}&error=This+account+has+been+deactivated.+Contact+your+Supervisor+or+MIS+Admin.",
            status_code=303,
        )
    if mode == "SUPERVISOR" and user.role != "SUPERVISOR":
        return RedirectResponse(
            url="/login?mode=SUPERVISOR&error=This+account+is+not+authorized+as+a+Supervisor.+Please+switch+to+Staff+Sign+In.",
            status_code=303,
        )
    if mode == "STAFF" and user.role == "SUPERVISOR":
        return RedirectResponse(
            url="/login?mode=SUPERVISOR&error=Supervisor+accounts+must+sign+in+under+the+Supervisor+tab.",
            status_code=303,
        )

    response = RedirectResponse(
        url=f"/?msg=Signed+in+as+{user.full_name}+({user.department.code})",
        status_code=303,
    )
    response.set_cookie(key="vra_session_user", value=user.staff_id, max_age=86400 * 14, httponly=True)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("vra_session_user")
    return response


@app.post("/switch-user")
def switch_user(
    staff_id: str = Form(...),
    redirect_to: str = Form("/"),
):
    target_url = redirect_to if redirect_to not in ["/admin", "/departments", "/audit-log"] else "/"
    response = RedirectResponse(
        url=f"{target_url}?msg=Switched+active+session+to+{staff_id}",
        status_code=303,
    )
    response.set_cookie(key="vra_session_user", value=staff_id, max_age=86400 * 14, httponly=True)
    return response


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    ctx = get_common_context(request, db, current_user, active_page="dashboard")

    items = db.query(InventoryItem).options(joinedload(InventoryItem.owning_department)).all()
    total_sku_count = len(items)
    available_sku_count = sum(1 for i in items if i.quantity_on_hand > 0)
    total_units = sum(i.quantity_on_hand for i in items)
    low_stock_items = [i for i in items if i.quantity_on_hand <= i.reorder_level]
    asset_count = sum(1 for i in items if i.item_type == "ASSET")

    req_query = db.query(Requisition).options(
        joinedload(Requisition.requester),
        joinedload(Requisition.department),
        joinedload(Requisition.item),
        joinedload(Requisition.approved_by),
    )
    if current_user.role == "STAFF":
        req_query = req_query.filter(Requisition.requester_id == current_user.id)

    raw_recent = req_query.order_by(Requisition.requested_at.desc(), Requisition.id.desc()).all()
    from collections import OrderedDict
    siv_map = OrderedDict()
    for r in raw_recent:
        if r.siv_number not in siv_map:
            siv_map[r.siv_number] = []
        siv_map[r.siv_number].append(r)

    recent_requisitions = []
    for siv_no, item_rows in list(siv_map.items())[:8]:
        primary = item_rows[0]
        recent_requisitions.append({
            "id": primary.id,
            "siv_number": siv_no,
            "requester": primary.requester,
            "requester_id": primary.requester_id,
            "department": primary.department,
            "requested_at": primary.requested_at,
            "job_card_ref": primary.job_card_ref,
            "purpose": primary.purpose,
            "status": primary.status,
            "line_items": item_rows,
            "item_count": len(item_rows),
            "primary": primary,
            "item": primary.item,
            "quantity": sum(it.quantity for it in item_rows),
            "is_returnable": any(it.is_returnable for it in item_rows),
        })

    recent_transactions = (
        db.query(StockTransaction)
        .options(joinedload(StockTransaction.item), joinedload(StockTransaction.performed_by))
        .order_by(StockTransaction.created_at.desc())
        .limit(6)
        .all()
    )

    loans_query = (
        db.query(Requisition)
        .options(joinedload(Requisition.requester), joinedload(Requisition.item), joinedload(Requisition.department))
        .filter(Requisition.is_returnable == True, Requisition.status == "ISSUED")
    )
    if current_user.role == "STAFF":
        loans_query = loans_query.filter(Requisition.requester_id == current_user.id)
    active_loans = loans_query.all()

    ctx.update(
        {
            "total_sku_count": total_sku_count,
            "available_sku_count": available_sku_count,
            "total_units": total_units,
            "low_stock_items": low_stock_items,
            "asset_count": asset_count,
            "recent_requisitions": recent_requisitions,
            "recent_transactions": recent_transactions,
            "active_loans": active_loans,
        }
    )
    return templates.TemplateResponse(request, "dashboard.html", ctx)


@app.get("/inventory", response_class=HTMLResponse)
def inventory_catalog(
    request: Request,
    q: Optional[str] = None,
    dept: Optional[str] = None,
    item_type: Optional[str] = None,
    stock_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    ctx = get_common_context(request, db, current_user, active_page="inventory")
    query = db.query(InventoryItem).options(joinedload(InventoryItem.owning_department))

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            (InventoryItem.name.ilike(search))
            | (InventoryItem.item_code.ilike(search))
            | (InventoryItem.serial_or_part_no.ilike(search))
            | (InventoryItem.vra_asset_tag.ilike(search))
            | (InventoryItem.category.ilike(search))
        )
    if dept:
        query = query.join(Department).filter(Department.code == dept)
    if item_type:
        query = query.filter(InventoryItem.item_type == item_type)

    items = query.order_by(InventoryItem.item_code).all()
    if stock_filter == "low":
        items = [i for i in items if i.quantity_on_hand <= i.reorder_level]

    ctx.update(
        {
            "items": items,
            "q": q or "",
            "selected_dept": dept or "",
            "selected_type": item_type or "",
            "stock_filter": stock_filter or "",
        }
    )
    return templates.TemplateResponse(request, "inventory.html", ctx)


@app.post("/inventory/add")
def add_inventory_item(
    request: Request,
    item_code: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    item_type: str = Form("CONSUMABLE"),
    brand_model: str = Form(""),
    serial_or_part_no: str = Form(""),
    vra_asset_tag: str = Form(""),
    unit: str = Form("pcs"),
    quantity_on_hand: int = Form(0),
    reorder_level: int = Form(5),
    store_location: str = Form("MIS Store - Rack A1"),
    department_id: int = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role == "STAFF":
        return RedirectResponse(url="/inventory?msg=Unauthorized+action", status_code=303)

    existing = db.query(InventoryItem).filter(InventoryItem.item_code == item_code.strip().upper()).first()
    if existing:
        return RedirectResponse(url="/inventory?msg=Error:+Item+Code+already+exists", status_code=303)

    new_item = InventoryItem(
        item_code=item_code.strip().upper(),
        name=name.strip(),
        category=category.strip(),
        item_type=item_type,
        brand_model=brand_model.strip() or None,
        serial_or_part_no=serial_or_part_no.strip() or None,
        vra_asset_tag=vra_asset_tag.strip() or None,
        unit=unit.strip(),
        quantity_on_hand=quantity_on_hand,
        reorder_level=reorder_level,
        store_location=store_location.strip(),
        department_id=department_id,
        notes=notes.strip() or None,
    )
    db.add(new_item)
    db.flush()

    if quantity_on_hand > 0:
        srv_no = f"SRV-AK-{datetime.utcnow().year}-{100 + new_item.id:04d}"
        tx = StockTransaction(
            voucher_no=srv_no,
            transaction_type="RECEIVE_SRV",
            item_id=new_item.id,
            quantity_change=quantity_on_hand,
            balance_after=quantity_on_hand,
            performed_by_id=current_user.id,
            recipient_or_supplier="Initial Store Registration",
            reference_note=f"Initial stock entry for {new_item.item_code}",
        )
        db.add(tx)

    db.commit()
    return RedirectResponse(
        url=f"/inventory?msg=Added+{new_item.item_code}+({new_item.name})+to+VRA+Akuse+Store",
        status_code=303,
    )


@app.post("/inventory/restock")
def restock_inventory_item(
    request: Request,
    item_id: int = Form(...),
    quantity_added: int = Form(...),
    voucher_no: str = Form(...),
    supplier: str = Form(...),
    reference_note: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role == "STAFF":
        return RedirectResponse(url="/inventory?msg=Unauthorized+action", status_code=303)

    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item or quantity_added <= 0:
        return RedirectResponse(url="/inventory?msg=Invalid+restock+request", status_code=303)

    item.quantity_on_hand += quantity_added
    tx = StockTransaction(
        voucher_no=voucher_no.strip().upper(),
        transaction_type="RECEIVE_SRV",
        item_id=item.id,
        quantity_change=quantity_added,
        balance_after=item.quantity_on_hand,
        performed_by_id=current_user.id,
        recipient_or_supplier=supplier.strip(),
        reference_note=reference_note.strip() or "Stores Receipt Voucher (SRV) restock",
    )
    db.add(tx)
    db.commit()
    return RedirectResponse(
        url=f"/inventory?msg=Received+{quantity_added}+{item.unit}+for+{item.item_code}+via+{voucher_no}",
        status_code=303,
    )


@app.get("/requisitions", response_class=HTMLResponse)
def requisitions_page(
    request: Request,
    status_filter: Optional[str] = None,
    scope: Optional[str] = None,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    ctx = get_common_context(request, db, current_user, active_page="requisitions")
    query = db.query(Requisition).options(
        joinedload(Requisition.requester),
        joinedload(Requisition.department),
        joinedload(Requisition.item),
        joinedload(Requisition.approved_by),
        joinedload(Requisition.issued_by),
    )

    if current_user.role == "STAFF" and scope != "all":
        query = query.filter(Requisition.requester_id == current_user.id)

    if status_filter:
        query = query.filter(Requisition.status == status_filter)

    raw_requisitions = query.order_by(Requisition.requested_at.desc(), Requisition.id.desc()).all()

    # Group by siv_number to bundle multi-item orders into one clean entry
    from collections import OrderedDict
    siv_map = OrderedDict()
    for r in raw_requisitions:
        if r.siv_number not in siv_map:
            siv_map[r.siv_number] = []
        siv_map[r.siv_number].append(r)

    grouped_requisitions = []
    for siv_no, item_rows in siv_map.items():
        primary = item_rows[0]
        grouped_requisitions.append({
            "id": primary.id,
            "siv_number": siv_no,
            "requester": primary.requester,
            "requester_id": primary.requester_id,
            "department": primary.department,
            "requested_at": primary.requested_at,
            "job_card_ref": primary.job_card_ref,
            "purpose": primary.purpose,
            "status": primary.status,
            "line_items": item_rows,
            "item_count": len(item_rows),
            "primary": primary,
            "item": primary.item,
            "quantity": sum(it.quantity for it in item_rows),
            "is_returnable": any(it.is_returnable for it in item_rows),
        })

    items = db.query(InventoryItem).filter(InventoryItem.quantity_on_hand > 0).order_by(InventoryItem.name).all()

    ctx.update(
        {
            "requisitions": grouped_requisitions,
            "raw_requisitions": raw_requisitions,
            "items": items,
            "status_filter": status_filter or "",
            "scope": scope or ("mine" if current_user.role == "STAFF" else "all"),
        }
    )
    return templates.TemplateResponse(request, "requisitions.html", ctx)


@app.post("/requisitions/create")
async def create_requisition(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    form = await request.form()
    job_card_ref = str(form.get("job_card_ref") or "").strip() or None
    purpose = str(form.get("purpose") or "").strip()
    if not purpose:
        return RedirectResponse(url="/requisitions?msg=Please+provide+an+operational+purpose", status_code=303)

    item_id_list = form.getlist("item_ids")
    if not item_id_list and form.get("item_id"):
        item_id_list = [form.get("item_id")]

    qty_list = form.getlist("quantities")
    if not qty_list and form.get("quantity"):
        qty_list = [form.get("quantity")]

    if not item_id_list:
        return RedirectResponse(url="/requisitions?msg=Please+select+at+least+one+item", status_code=303)

    distinct_siv_count = db.query(Requisition.siv_number).distinct().count()
    siv_number = f"SIV-AK-{datetime.utcnow().year}-{distinct_siv_count + 1:04d}"
    expected_return_date = str(form.get("expected_return_date") or "").strip() or None
    now = datetime.utcnow()

    items_created = 0
    for idx, raw_item_id in enumerate(item_id_list):
        if not raw_item_id:
            continue
        try:
            i_id = int(raw_item_id)
            qty = int(qty_list[idx]) if idx < len(qty_list) else 1
            if qty < 1:
                qty = 1
        except (ValueError, TypeError):
            continue

        item = db.query(InventoryItem).filter(InventoryItem.id == i_id).first()
        if not item:
            continue

        returnable_flag = True if (item.item_type == "ASSET" or form.get("is_returnable") == "on") else False

        req = Requisition(
            siv_number=siv_number,
            requester_id=current_user.id,
            department_id=current_user.department_id,
            item_id=item.id,
            quantity=qty,
            purpose=purpose,
            job_card_ref=job_card_ref,
            is_returnable=returnable_flag,
            expected_return_date=expected_return_date,
            status="PENDING_APPROVAL",
            requested_at=now,
        )
        db.add(req)
        items_created += 1

    if items_created == 0:
        return RedirectResponse(url="/requisitions?msg=No+valid+items+selected", status_code=303)

    db.commit()
    return RedirectResponse(
        url=f"/requisitions?msg=Submitted+Requisition+{siv_number}+({items_created}+items)+for+Supervisor+Approval",
        status_code=303,
    )


@app.post("/requisitions/{req_id}/approve")
def approve_or_reject_requisition(
    req_id: int,
    request: Request,
    decision: str = Form(...),
    supervisor_remarks: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role != "SUPERVISOR":
        return RedirectResponse(url="/requisitions?msg=Supervisor+authorization+required", status_code=303)

    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req:
        return RedirectResponse(url="/requisitions?msg=Requisition+not+found", status_code=303)

    now = datetime.utcnow()
    remarks = supervisor_remarks.strip() or ("Approved for store issuance." if decision == "APPROVE" else "Declined by supervisor.")
    all_reqs = db.query(Requisition).filter(Requisition.siv_number == req.siv_number).all()
    for r in all_reqs:
        r.status = "APPROVED" if decision == "APPROVE" else "REJECTED"
        r.approved_by_id = current_user.id
        r.approved_at = now
        r.supervisor_remarks = remarks

    db.commit()
    msg = f"Requisition+{req.siv_number}+APPROVED+by+{current_user.full_name}" if decision == "APPROVE" else f"Requisition+{req.siv_number}+declined"
    return RedirectResponse(url=f"/requisitions?msg={msg}", status_code=303)


@app.post("/requisitions/{req_id}/issue")
def issue_requisition_stock(
    req_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role not in ["STORE_OFFICER", "SUPERVISOR"]:
        return RedirectResponse(url="/requisitions?msg=Store+Officer+or+Supervisor+required", status_code=303)

    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req or req.status != "APPROVED":
        return RedirectResponse(url="/requisitions?msg=Requisition+must+be+APPROVED+before+issuing", status_code=303)

    all_reqs = (
        db.query(Requisition)
        .options(joinedload(Requisition.item), joinedload(Requisition.requester), joinedload(Requisition.department))
        .filter(Requisition.siv_number == req.siv_number, Requisition.status == "APPROVED")
        .all()
    )

    # Check stock for all items
    for r in all_reqs:
        if r.item.quantity_on_hand < r.quantity:
            return RedirectResponse(
                url=f"/requisitions?msg=Insufficient+Stock!+Only+{r.item.quantity_on_hand}+available+for+{r.item.item_code}",
                status_code=303,
            )

    now = datetime.utcnow()
    issued_count = 0
    for r in all_reqs:
        r.item.quantity_on_hand -= r.quantity
        r.status = "ISSUED"
        r.issued_by_id = current_user.id
        r.issued_at = now

        tx = StockTransaction(
            voucher_no=r.siv_number,
            transaction_type="ISSUE_SIV",
            item_id=r.item.id,
            quantity_change=-r.quantity,
            balance_after=r.item.quantity_on_hand,
            performed_by_id=current_user.id,
            recipient_or_supplier=f"{r.requester.full_name} ({r.department.code})",
            reference_note=f"{r.purpose} [Job/Ref: {r.job_card_ref or 'N/A'}]",
        )
        db.add(tx)
        issued_count += 1

    db.commit()
    return RedirectResponse(
        url=f"/requisitions?msg=Issued+{issued_count}+items+on+{req.siv_number}+to+{req.requester.full_name}",
        status_code=303,
    )


@app.post("/requisitions/{req_id}/return")
def return_borrowed_item(
    req_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role not in ["STORE_OFFICER", "SUPERVISOR"]:
        return RedirectResponse(url="/requisitions?msg=Store+Officer+or+Supervisor+required", status_code=303)

    req = (
        db.query(Requisition)
        .options(joinedload(Requisition.item), joinedload(Requisition.requester), joinedload(Requisition.department))
        .filter(Requisition.id == req_id)
        .first()
    )
    if not req or req.status != "ISSUED":
        return RedirectResponse(url="/requisitions?msg=Invalid+return+operation", status_code=303)

    req.item.quantity_on_hand += req.quantity
    req.status = "RETURNED"
    req.returned_at = datetime.utcnow()

    tx = StockTransaction(
        voucher_no=f"RET-{req.siv_number}",
        transaction_type="RETURN",
        item_id=req.item.id,
        quantity_change=req.quantity,
        balance_after=req.item.quantity_on_hand,
        performed_by_id=current_user.id,
        recipient_or_supplier=f"Returned by {req.requester.full_name} ({req.department.code})",
        reference_note=f"Asset/Tool returned to store from {req.siv_number}",
    )
    db.add(tx)
    db.commit()
    return RedirectResponse(
        url=f"/requisitions?msg=Logged+return+of+{req.item.name}+from+{req.requester.full_name}",
        status_code=303,
    )


@app.post("/requisitions/{req_id}/cancel")
def cancel_pending_requisition(
    req_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    req = db.query(Requisition).filter(Requisition.id == req_id).first()
    if not req or req.status != "PENDING_APPROVAL" or req.requester_id != current_user.id:
        return RedirectResponse(
            url="/requisitions?msg=Only+your+own+pending+requisitions+can+be+cancelled",
            status_code=303,
        )

    siv_no = req.siv_number
    db.query(Requisition).filter(Requisition.siv_number == siv_no, Requisition.status == "PENDING_APPROVAL").delete()
    db.commit()
    return RedirectResponse(
        url=f"/requisitions?msg=Cancelled+pending+requisition+{siv_no}",
        status_code=303,
    )


@app.get("/voucher/{req_id}", response_class=HTMLResponse)
def printable_siv_voucher(req_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    req = (
        db.query(Requisition)
        .options(
            joinedload(Requisition.requester),
            joinedload(Requisition.department),
            joinedload(Requisition.item),
            joinedload(Requisition.approved_by),
            joinedload(Requisition.issued_by),
        )
        .filter(Requisition.id == req_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Voucher not found")

    # If this requisition is part of a batch with the same SIV number or Work Order / Job Ref, bundle them on one voucher
    items_list = (
        db.query(Requisition)
        .options(
            joinedload(Requisition.item),
            joinedload(Requisition.requester),
            joinedload(Requisition.department),
        )
        .filter(
            (Requisition.siv_number == req.siv_number) |
            (
                (Requisition.requester_id == req.requester_id) &
                (Requisition.job_card_ref == req.job_card_ref) &
                (Requisition.job_card_ref.isnot(None)) &
                (Requisition.job_card_ref != "") &
                (Requisition.job_card_ref != "Standard Departmental Request")
            )
        )
        .order_by(Requisition.id)
        .all()
    )
    if not items_list:
        items_list = [req]

    return templates.TemplateResponse(
        request,
        "voucher_print.html",
        {
            "request": request,
            "req": req,
            "items_list": items_list,
            "printed_at": datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"),
        },
    )


@app.get("/departments", response_class=HTMLResponse)
def departments_and_staff(request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if current_user.role == "STAFF":
        return RedirectResponse(url="/?msg=Access+restricted+to+Store+Officers+and+Supervisors", status_code=303)

    ctx = get_common_context(request, db, current_user, active_page="departments")
    dept_list = (
        db.query(Department)
        .options(joinedload(Department.users), joinedload(Department.items), joinedload(Department.requisitions))
        .order_by(Department.code)
        .all()
    )
    ctx["dept_list"] = dept_list
    return templates.TemplateResponse(request, "departments.html", ctx)


@app.post("/staff/add")
def add_staff_member(
    request: Request,
    staff_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    role: str = Form("STAFF"),
    job_title: str = Form(""),
    password_plain: str = Form("vra123"),
    department_id: int = Form(...),
    redirect_to: str = Form("/departments"),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not current_user or current_user.role == "STAFF":
        return RedirectResponse(url="/?msg=Unauthorized", status_code=303)

    existing = db.query(User).filter((User.staff_id == staff_id.strip()) | (User.email == email.strip())).first()
    if existing:
        return RedirectResponse(url=f"{redirect_to}?msg=Staff+ID+or+Email+already+exists", status_code=303)

    user = User(
        staff_id=staff_id.strip().upper(),
        full_name=full_name.strip(),
        email=email.strip().lower(),
        phone=phone.strip() or None,
        role=role,
        job_title=job_title.strip() or "Staff Member",
        password_plain=password_plain.strip() or "vra123",
        department_id=department_id,
    )
    db.add(user)
    db.commit()
    return RedirectResponse(
        url=f"{redirect_to}?msg=Registered+{user.full_name}+({user.staff_id})+successfully",
        status_code=303,
    )


@app.get("/audit-log", response_class=HTMLResponse)
def audit_log_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if current_user.role == "STAFF":
        return RedirectResponse(url="/?msg=Ledger+access+restricted+to+Store+Officers+and+Supervisors", status_code=303)

    ctx = get_common_context(request, db, current_user, active_page="audit")
    transactions = (
        db.query(StockTransaction)
        .options(joinedload(StockTransaction.item), joinedload(StockTransaction.performed_by))
        .order_by(StockTransaction.created_at.desc())
        .all()
    )
    ctx["transactions"] = transactions
    return templates.TemplateResponse(request, "audit.html", ctx)


# ==============================================================================
# SUPERVISOR / ADMIN CONTROL PANEL ROUTES
# ==============================================================================

def is_mis_admin(user: Optional[User]) -> bool:
    return bool(user and user.role == "SUPERVISOR" and user.department and user.department.code == "MIS")


@app.get("/admin", response_class=HTMLResponse)
def admin_control_panel(request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    if not is_mis_admin(current_user):
        return RedirectResponse(
            url="/?msg=Access+Denied:+System+Administration+is+restricted+to+MIS+Administrators+(VRA-AK-1004).",
            status_code=303,
        )

    ctx = get_common_context(request, db, current_user, active_page="admin")
    items = db.query(InventoryItem).options(joinedload(InventoryItem.owning_department)).order_by(InventoryItem.item_code).all()
    dept_list = (
        db.query(Department)
        .options(joinedload(Department.users), joinedload(Department.items))
        .order_by(Department.code)
        .all()
    )
    total_tx = db.query(StockTransaction).count()
    total_reqs = db.query(Requisition).count()
    db_size_kb = round(os.path.getsize("vra_akuse_inventory.db") / 1024, 1) if os.path.exists("vra_akuse_inventory.db") else 0

    ctx.update(
        {
            "items": items,
            "dept_list": dept_list,
            "total_tx": total_tx,
            "total_reqs": total_reqs,
            "db_size_kb": db_size_kb,
        }
    )
    return templates.TemplateResponse(request, "admin.html", ctx)


@app.post("/admin/user/{user_id}/update")
def admin_update_user(
    user_id: int,
    request: Request,
    role: str = Form(...),
    department_id: int = Form(...),
    is_active: str = Form("true"),
    new_password: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not is_mis_admin(current_user):
        return RedirectResponse(url="/?msg=Unauthorized:+MIS+Admin+required", status_code=303)

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return RedirectResponse(url="/admin?msg=User+not+found", status_code=303)

    target_user.role = role
    target_user.department_id = department_id
    target_user.is_active = (is_active == "true")
    if new_password.strip():
        target_user.password_plain = new_password.strip()

    db.commit()
    return RedirectResponse(
        url=f"/admin?msg=Updated+permissions/profile+for+{target_user.full_name}+({target_user.staff_id})",
        status_code=303,
    )


@app.post("/admin/item/{item_id}/adjust")
def admin_adjust_stock_and_metadata(
    item_id: int,
    request: Request,
    physical_qty: int = Form(...),
    reorder_level: int = Form(...),
    store_location: str = Form(...),
    condition: str = Form("New / Good"),
    reason: str = Form("Quarterly Physical Stocktake Adjustment"),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not is_mis_admin(current_user):
        return RedirectResponse(url="/?msg=Unauthorized:+MIS+Admin+required", status_code=303)

    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item or physical_qty < 0:
        return RedirectResponse(url="/admin?msg=Invalid+item+or+quantity", status_code=303)

    delta = physical_qty - item.quantity_on_hand
    item.quantity_on_hand = physical_qty
    item.reorder_level = reorder_level
    item.store_location = store_location.strip()
    item.condition = condition.strip()

    if delta != 0:
        adj_voucher = f"ADJ-AK-{datetime.utcnow().year}-{100 + db.query(StockTransaction).count():04d}"
        tx = StockTransaction(
            voucher_no=adj_voucher,
            transaction_type="ADJUSTMENT",
            item_id=item.id,
            quantity_change=delta,
            balance_after=physical_qty,
            performed_by_id=current_user.id,
            recipient_or_supplier="Supervisor Stocktake Audit",
            reference_note=reason.strip() or "Physical count reconciliation",
        )
        db.add(tx)

    db.commit()
    return RedirectResponse(
        url=f"/admin?msg=Reconciled+{item.item_code}+(New+Balance:+{physical_qty}+{item.unit})",
        status_code=303,
    )


@app.post("/admin/department/add")
def admin_add_department(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    location: str = Form("Kpong GS, Akuse"),
    head_of_dept: str = Form(""),
    db: Session = Depends(get_db),
):
    current_user = get_authenticated_user(request, db)
    if not is_mis_admin(current_user):
        return RedirectResponse(url="/?msg=Unauthorized:+MIS+Admin+required", status_code=303)

    code_clean = code.strip().upper()
    if db.query(Department).filter(Department.code == code_clean).first():
        return RedirectResponse(url="/admin?msg=Department+code+already+exists", status_code=303)

    dept = Department(
        code=code_clean,
        name=name.strip(),
        location=location.strip(),
        head_of_dept=head_of_dept.strip() or None,
    )
    db.add(dept)
    db.commit()
    return RedirectResponse(
        url=f"/admin?msg=Created+department+{dept.code}+({dept.name})",
        status_code=303,
    )


@app.get("/admin/backup-db")
def download_sqlite_backup(request: Request, db: Session = Depends(get_db)):
    current_user = get_authenticated_user(request, db)
    if not is_mis_admin(current_user):
        return RedirectResponse(url="/?msg=Unauthorized:+MIS+Admin+required", status_code=303)

    db_path = "vra_akuse_inventory.db"
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found")

    filename = f"vra_akuse_inventory_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.db"
    return FileResponse(
        path=db_path,
        media_type="application/octet-stream",
        filename=filename,
    )


@app.get("/export/inventory.csv")
def export_inventory_csv(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).options(joinedload(InventoryItem.owning_department)).order_by(InventoryItem.item_code).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Item Code",
        "Item Name",
        "Category",
        "Type",
        "Department",
        "Brand / Model",
        "Serial / Part No.",
        "VRA Asset Tag",
        "Qty On Hand",
        "Unit",
        "Reorder Level",
        "Status",
        "Store Location",
    ])
    for i in items:
        status = "LOW STOCK" if i.quantity_on_hand <= i.reorder_level else "OK"
        writer.writerow([
            i.item_code,
            i.name,
            i.category,
            i.item_type,
            i.owning_department.code if i.owning_department else "GENERAL",
            i.brand_model or "",
            i.serial_or_part_no or "",
            i.vra_asset_tag or "",
            i.quantity_on_hand,
            i.unit,
            i.reorder_level,
            status,
            i.store_location,
        ])
    output.seek(0)
    filename = f"VRA_Akuse_Inventory_Report_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/export/transactions.csv")
def export_transactions_csv(db: Session = Depends(get_db)):
    txs = (
        db.query(StockTransaction)
        .options(joinedload(StockTransaction.item), joinedload(StockTransaction.performed_by))
        .order_by(StockTransaction.created_at.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date / Time (UTC)",
        "Voucher No (SIV / SRV)",
        "Transaction Type",
        "Item Code",
        "Item Name",
        "Quantity Change",
        "Stock Balance After",
        "Recipient / Supplier",
        "Processed By (Staff)",
        "Reference / Notes",
    ])
    for t in txs:
        writer.writerow([
            t.created_at.strftime("%Y-%m-%d %H:%M"),
            t.voucher_no,
            t.transaction_type,
            t.item.item_code if t.item else "",
            t.item.name if t.item else "",
            t.quantity_change,
            t.balance_after,
            t.recipient_or_supplier or "",
            f"{t.performed_by.full_name} ({t.performed_by.staff_id})" if t.performed_by else "",
            t.reference_note or "",
        ])
    output.seek(0)
    filename = f"VRA_Akuse_SIV_SRV_Ledger_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
