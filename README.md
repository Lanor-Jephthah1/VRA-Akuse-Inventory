# VRA Akuse (Kpong Generating Station) — Inventory & Requisition Management System

A full-stack, corporate-grade **Inventory, Asset & Stores Requisition (SIV / SRV) Management System** built with **Python (FastAPI + SQLAlchemy + SQLite + Jinja2 + Tailwind CSS)** for the **Volta River Authority (VRA), Akuse / Kpong Generating Station**.

Designed specifically to support **everyone at the station** (Regular Staff, NSS / Store Officers, and Department Supervisors) across **MIS (IT)** and all major VRA Akuse departments.

---

## Key Features Included

1. **Multi-Departmental Structure (MIS + All VRA Akuse Units)**
   - **MIS** — Management Information Systems (IT & Networking)
   - **ELEC** — Electrical Maintenance
   - **MECH** — Mechanical Maintenance
   - **OPS** — Plant Operations & Control Room
   - **CIVIL** — Civil & Estates Management
   - **HSE** — Health, Safety & Environment
   - **HOSP** — VRA Hospital / Medical Services (Akuse)
   - **STORES** — Procurement, Finance & Technical Stores

2. **3-Tier Role Workflow (Staff $\rightarrow$ Supervisor $\rightarrow$ NSS / Store Officer)**
   - **All Staff (`STAFF`)**: Browse the live store catalog and submit **Stores Issue Voucher (SIV)** requisitions with a Work Order / Incident Reference and purpose.
   - **Department Supervisor (`SUPERVISOR`)**: One-click approval or rejection of staff requisitions with supervisor remarks.
   - **NSS / Store Officer (`STORE_OFFICER`)**: Receives new stock deliveries via **Stores Receipt Vouchers (SRV)**, issues approved SIV items (automatically deducting stock), and logs returned field assets/tools.
   - **Instant Demo Role Switcher**: Use the top-right dropdown in the navigation bar to switch between Supervisor, NSS Store Officer, and Staff views immediately during your presentation to the supervisor.

3. **Both Consumables & Returnable Fixed Assets**
   - Tracks **Consumables** (HP LaserJet Toners, Cat6 Cable Rolls, Circuit Breakers, Bearings, PPE kits) with automatic **Low-Stock Reorder Alerts**.
   - Tracks **Fixed Assets & Returnable Tools** (Dell Latitude Laptops, Cisco Catalyst Switches, APC Smart-UPS, Fluke Network/Electrical Testers) with **VRA Asset Tags**, **Serial Numbers**, and **Expected Return Dates**.

4. **Official Printable VRA Stores Issue Voucher (SIV) & Excel/CSV Reports**
   - Click **Print SIV** on any requisition to generate a clean, signable **VRA Stores Issue Voucher** ready for paper filing or PDF saving.
   - One-click **CSV / Excel Export** for both the current Stock Balance Sheet and the full SRV/SIV Audit Ledger.

---

## Quick Start

### Option 1: Double-Click `run_vra_inventory.bat` (Windows)
Simply double-click `run_vra_inventory.bat` or run:

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://127.0.0.1:8000** in your browser.
*(Because it binds to `0.0.0.0:8000`, any staff computer on the same VRA Akuse office LAN can also access it via your machine's IP address!)*
