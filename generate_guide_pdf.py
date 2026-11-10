import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        # Top running header on pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 800, "VRA Akuse Stores & Inventory System — Prototype Walkthrough Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 792, 540, 792)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(540, 36, footer_text)
        self.drawString(54, 36, "Volta River Authority • Kpong Generating Station, Akuse")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 540, 48)
        self.restoreState()


def build_pdf(output_paths):
    doc = SimpleDocTemplate(
        output_paths[0],
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#00529B'),
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569'),
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6,
    )

    sub_heading = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#00529B'),
        spaceBefore=8,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6,
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0F172A'),
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155'),
    )

    story = []

    # 1. Header with Logo & Title
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'vra_logo.png')
    header_data = []
    if os.path.exists(logo_path):
        img = Image(logo_path, width=1.4*inch, height=0.6*inch)
        header_data.append([
            img,
            [
                Paragraph("VRA AKUSE INVENTORY & REQUISITIONS PORTAL", title_style),
                Spacer(1, 3),
                Paragraph("Simple Step-by-Step Guide for Team & Management Presentation", subtitle_style),
            ]
        ])
    else:
        header_data.append([
            "",
            [
                Paragraph("VRA AKUSE INVENTORY & REQUISITIONS PORTAL", title_style),
                Spacer(1, 3),
                Paragraph("Simple Step-by-Step Guide for Team & Management Presentation", subtitle_style),
            ]
        ])

    header_table = Table(header_data, colWidths=[1.5*inch, 5.3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(header_table)

    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#00529B'), spaceBefore=4, spaceAfter=10))

    # Note / Intro block
    intro_p = Paragraph(
        "<b>Yo bro!</b> Here's a clean, straightforward guide explaining how the entire VRA Akuse Stores & Inventory system works. "
        "No complicated tech talk—just plain English so you or anyone presenting the prototype can explain it to the bosses and "
        "colleagues easily. Everything is live at: <b><u>https://vra-akuse-inventory.vercel.app</u></b>",
        callout_style
    )
    intro_table = Table([[intro_p]], colWidths=[6.8*inch])
    intro_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(intro_table)
    story.append(Spacer(1, 10))

    # SECTION 1: Why Did We Build This?
    story.append(Paragraph("1. What Is This System and Why Do We Need It?", section_heading))
    story.append(Paragraph(
        "At VRA Akuse (Kpong Generating Station), technicians and engineers constantly need spare parts, lubricants, toner, "
        "safety gear, and test meters from the warehouse. Previously, this meant paper chits, handwritten SIV logbooks, "
        "and running around looking for supervisors to sign paper forms. Paper gets lost, people forget who borrowed which multimeter, "
        "and store officers don't know items are out of stock until someone physically checks the shelf.",
        body_style
    ))
    story.append(Paragraph(
        "<b>This system fixes that completely:</b> Everything is done digitally in 3 simple steps: "
        "<b>Request &rarr; Supervisor Approves &rarr; Store Officer Issues.</b> Plus, every voucher produces an official VRA Stores Issue Voucher (SIV) PDF with a unique voucher number, tracking timestamps, and digital stamp.",
        body_style
    ))

    # SECTION 2: The 3 User Roles
    story.append(Paragraph("2. The Three User Roles (Who Does What?)", section_heading))
    story.append(Paragraph(
        "The system has 3 distinct levels of access. When presenting, you can show each one:",
        body_style
    ))

    roles_data = [
        [
            Paragraph("<b>Role</b>", table_header),
            Paragraph("<b>Who It Represents</b>", table_header),
            Paragraph("<b>What They Can Do in the App</b>", table_header)
        ],
        [
            Paragraph("<b>STAFF</b>", table_cell),
            Paragraph("Any technician, engineer, nurse, or officer in any department (e.g. Electrical, Mechanical, Control Room, Hospital).", table_cell),
            Paragraph("Browses available catalog stock, submits new requisitions (SIV) with a reason, tracks their requests, and downloads their approved vouchers.", table_cell),
        ],
        [
            Paragraph("<b>SUPERVISOR</b>", table_cell),
            Paragraph("Heads of Department (e.g. Ing. Mensah-Bonsu for MIS, Ing. Samuel Tetteh for Electrical).", table_cell),
            Paragraph("Reviews pending requisitions from their staff, clicks <b>Approve</b> or <b>Decline</b> (with feedback remarks), monitors low-stock alerts, and tracks all departmental spending.", table_cell),
        ],
        [
            Paragraph("<b>STORE OFFICER (NSS)</b>", table_cell),
            Paragraph("The warehouse personnel managing physical stores (e.g. Kelvin Osei-Tutu or Bright Agyapong).", table_cell),
            Paragraph("Checks vouchers presented by staff, clicks <b>Issue Stock</b> to deduct inventory, receives incoming restock shipments (SRV), and checks in returned tools.", table_cell),
        ],
    ]
    roles_table = Table(roles_data, colWidths=[1.4*inch, 2.2*inch, 3.2*inch])
    roles_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(roles_table)
    story.append(Spacer(1, 10))

    # SECTION 3: How to Log In
    story.append(Paragraph("3. How to Log In (Show This First in the Presentation)", section_heading))
    story.append(Paragraph(
        "Open <b>https://vra-akuse-inventory.vercel.app</b>. You'll see a clean, professional VRA login screen:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Staff vs Supervisor Toggle:</b> At the top of the login card, there are two tabs. Clicking <b>Staff</b> prepares you to log in as a field technician. Clicking <b>Supervisor</b> switches you to supervisor/admin mode.<br/>"
        "• <b>Quick Demo Selector:</b> At the bottom of the login card, there is a handy dropdown: <i>'Quick demo account'</i>. You can just pick any person (e.g. <b>Ing. Kwesi Mensah-Bonsu (MIS Supervisor)</b> or <b>Michael Teye Narh (Control Room Staff)</b>) and it auto-fills everything!<br/>"
        "• <b>Default Password:</b> For every account in this prototype, the password is simply <b>vra123</b>.",
        body_style
    ))

    story.append(Spacer(1, 6))

    # SECTION 4: The 4 Main Workflows
    story.append(Paragraph("4. Step-by-Step Walkthrough of the Main Workflows", section_heading))

    story.append(Paragraph("Workflow A: How a Staff Member Requests an Item (SIV)", sub_heading))
    story.append(Paragraph(
        "1. Log in as a Staff member (e.g. <b>Michael Teye Narh</b>).<br/>"
        "2. Click the blue <b>'+ New Requisition'</b> button (at top right).<br/>"
        "3. A clean popup appears dead-center on the screen. Select the item you need (e.g. <i>HP LaserJet 85A Toner</i>).<br/>"
        "4. Enter quantity and a clear reason (e.g. <i>'Replacement cartridge for Control Room shift log printer'</i>).<br/>"
        "5. If it is a tool that must be returned (like a Fluke multimeter or laptop), check the <i>'Returnable asset loan'</i> box and choose the return date.<br/>"
        "6. Click <b>Submit Requisition</b>. The request now shows with badge <b>[ ◷ Pending Approval ]</b>.",
        body_style
    ))

    story.append(Paragraph("Workflow B: How the Supervisor Approves the Request", sub_heading))
    story.append(Paragraph(
        "1. Switch accounts and log in as the Supervisor (e.g. <b>Ing. Kwesi Mensah-Bonsu</b>).<br/>"
        "2. On the Overview screen, under <i>'Pending Approval'</i>, the supervisor immediately sees the request.<br/>"
        "3. The supervisor reads the reason. With just one click on the dark <b>Approve</b> button, the voucher status changes to <b>[ ✓ Approved ]</b>.<br/>"
        "4. (If the request is unnecessary or excessive, the supervisor can decline it and leave a note explaining why).",
        body_style
    ))

    story.append(Paragraph("Workflow C: How the Store Officer Issues Stock & Generates the PDF", sub_heading))
    story.append(Paragraph(
        "1. Log in as the Store Officer (e.g. <b>Kelvin Osei-Tutu - NSS</b>).<br/>"
        "2. The Store Officer goes to <b>Requisitions</b> &rarr; <i>'Ready for Issue'</i>.<br/>"
        "3. The technician comes to the store counter. The Store Officer hands over the item and clicks <b>Issue Stock</b>.<br/>"
        "4. The system automatically subtracts the quantity from the store balance.<br/>"
        "5. Click <b>Voucher</b> to view the official <b>Stores Issue Voucher (SIV)</b>. Click <b>Print / Save SIV (PDF)</b>. It automatically saves with the standard name: <i>VRA_Akuse_SIV-AK-2026-0001_OPS_Michael_Teye_Narh.pdf</i>.",
        body_style
    ))

    story.append(Paragraph("Workflow D: Receiving New Stock into Store (SRV - Waybill Restock)", sub_heading))
    story.append(Paragraph(
        "1. When a truck or delivery arrives from VRA Central Stores (Tema) or a supplier, go to <b>Inventory Catalog</b>.<br/>"
        "2. Click <b>+ Receive Stock (SRV)</b>.<br/>"
        "3. Pick the item, enter the Waybill number (e.g. <i>SRV-AK-2026-0092</i>), the quantity received, and supplier name.<br/>"
        "4. Click <b>Record SRV</b>. The store balance increases immediately and is logged in the permanent audit ledger.",
        body_style
    ))

    story.append(Paragraph("Workflow E: Borrowed Equipment & Tool Returns", sub_heading))
    story.append(Paragraph(
        "Whenever returnable tools (e.g. Fluke Multimeters, Network Testers, Torque Wrenches) are issued, they stay visible right on the main dashboard under <b>Checked-Out Returnable Assets</b>. When the technician brings the tool back to the store, the Store Officer clicks <b>Check in</b>, and the tool is marked as returned.",
        body_style
    ))

    story.append(Spacer(1, 6))

    # SECTION 5: Presentation Tips
    story.append(Paragraph("5. Top Tips for Presenting the Prototype to Management", section_heading))

    tips_data = [
        [
            Paragraph("<b>1. Start on Mobile First</b>", table_header),
            Paragraph("Open the link on your phone. Show how responsive it is. Tap <b>+ New Requisition</b> or <b>+ Register Personnel</b> to prove that the popup centers immediately on mobile without scrolling.", table_cell),
        ],
        [
            Paragraph("<b>2. Demonstrate Live 1-Click Approval</b>", table_header),
            Paragraph("Submit a requisition as Staff, log in as Supervisor, and click <b>Approve</b>. Then show how the NSS Store Officer clicks <b>Issue Stock</b>. That live 3-step lifecycle always blows executives away.", table_cell),
        ],
        [
            Paragraph("<b>3. Download the PDF Voucher</b>", table_header),
            Paragraph("Open any issued voucher and hit <b>Print / Save SIV (PDF)</b>. Show the clean VRA letterhead, item classification, authorization signatures, and auto-generated filename.", table_cell),
        ],
        [
            Paragraph("<b>4. Highlight Audit & Accountability</b>", table_header),
            Paragraph("Point out that every transaction logs who did it, exact timestamp, department, and work order reference. Nothing leaves the store 'off the record'.", table_cell),
        ],
    ]
    tips_table = Table(tips_data, colWidths=[2.2*inch, 4.6*inch])
    tips_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tips_table)

    story.append(Spacer(1, 10))

    # Closing sign-off
    signoff = Paragraph(
        "<i>All the best with the presentation bro! Everything is solid, tested, and live at https://vra-akuse-inventory.vercel.app</i>",
        ParagraphStyle('Signoff', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9.5, textColor=colors.HexColor('#00529B'), alignment=TA_CENTER)
    )
    story.append(signoff)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF built successfully at: {output_paths[0]}")

    # Copy to additional destinations if requested
    if len(output_paths) > 1:
        import shutil
        for p in output_paths[1:]:
            shutil.copy2(output_paths[0], p)
            print(f"Copied PDF to: {p}")


if __name__ == '__main__':
    destinations = [
        os.path.join(r"C:\Users\Jephthah Kwame Lanor\Desktop\VRA-Akuse-Inventory", "VRA_Akuse_System_Guide_For_Friend.pdf"),
        os.path.join(r"C:\Users\Jephthah Kwame Lanor\Desktop\VRA-Akuse-Inventory\app\static", "VRA_Akuse_System_Guide.pdf"),
    ]
    build_pdf(destinations)
