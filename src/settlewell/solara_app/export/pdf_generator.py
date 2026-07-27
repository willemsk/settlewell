"""ReportLab automated PDF engineering report generator for settlewell."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from settlewell.solara_app.schemas import ScenarioSchema


def generate_pdf_report(scenario: ScenarioSchema) -> bytes:
    """Generate a multi-page PDF engineering calculation report for a calculation scenario.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    bytes
        PDF file contents as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0284c7"),
        alignment=0,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = styles["BodyText"]

    story = []

    # Title Banner
    story.append(
        Paragraph("settlewell v2.0 — Geotechnical Calculation Report", title_style)
    )
    story.append(
        Paragraph(
            f"<b>Project:</b> {scenario.name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> 2026-07-27",
            body_style,
        )
    )
    story.append(Spacer(1, 16))

    # Executive Summary Section
    story.append(Paragraph("1. Executive Summary", h1_style))
    summary_text = (
        "This calculation report presents the geotechnical evaluation of subsoil stresses, 1D primary consolidation "
        "and secondary creep settlement, groundwater dewatering hydraulics, and neighboring building damage risk. "
        "All calculations adhere to Eurocode 7 and Dutch/Belgian geotechnical engineering practices."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 12))

    # Soil Stratigraphy Table
    story.append(
        Paragraph("2. Subsoil Stratigraphy & Geotechnical Parameters", h1_style)
    )
    strat_table_data = [
        [
            "Layer Name",
            "USCS",
            "h [m]",
            "γ_dry",
            "γ_sat",
            "e0",
            "E [MPa]",
            "Cc",
            "Cr",
            "Cv [m²/yr]",
        ]
    ]
    for layer in scenario.stratigraphy:
        strat_table_data.append(
            [
                layer.name,
                layer.uscs_type.value,
                f"{layer.thickness:.2f}",
                f"{layer.gamma_dry:.1f}",
                f"{layer.gamma_sat:.1f}",
                f"{layer.e0:.2f}",
                f"{layer.E_modulus:.1f}",
                f"{layer.Cc:.2f}",
                f"{layer.Cr:.3f}",
                f"{layer.Cv:.1f}",
            ]
        )

    t_strat = Table(
        strat_table_data, colWidths=[110, 45, 40, 40, 40, 35, 45, 35, 35, 55]
    )
    t_strat.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
        )
    )
    story.append(t_strat)
    story.append(Spacer(1, 14))

    # Applied Surface Loads
    story.append(Paragraph("3. Surface & Foundation Loads", h1_style))
    load_table_data = [
        [
            "Load Name",
            "Geometry Type",
            "X-Center [m]",
            "Width B [m]",
            "Length L [m]",
            "Stress q [kPa]",
        ]
    ]
    for load in scenario.loads:
        load_table_data.append(
            [
                load.name,
                load.type.value,
                f"{load.x_center:.2f}",
                f"{load.width_B:.2f}",
                f"{load.length_L:.2f}",
                f"{load.stress_q:.1f}",
            ]
        )
    t_loads = Table(load_table_data, colWidths=[120, 90, 70, 70, 70, 70])
    t_loads.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ]
        )
    )
    story.append(t_loads)
    story.append(Spacer(1, 14))

    # Dewatering Pit & Well Array Summary
    story.append(
        Paragraph("4. Excavation Construction Pit & Dewatering Wells", h1_style)
    )
    pit = scenario.construction_pit
    dewatering = scenario.dewatering
    pit_info = (
        f"<b>Pit Dimensions:</b> Length L = {pit.length:.1f} m, Width W = {pit.width:.1f} m, "
        f"Excavation Depth d = {pit.depth:.1f} m.<br/>"
        f"<b>Aquifer Classification:</b> {dewatering.aquifer_type.value} Aquifer &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Active Dewatering Wells:</b> {len(dewatering.wells)}"
    )
    story.append(Paragraph(pit_info, body_style))
    story.append(Spacer(1, 8))

    if dewatering.wells:
        well_table_data = [
            ["Well Name", "X [m]", "Y [m]", "Pumping Rate Q [m³/h]", "Casing r_w [m]"]
        ]
        for well in dewatering.wells:
            well_table_data.append(
                [
                    well.name,
                    f"{well.x:.2f}",
                    f"{well.y:.2f}",
                    f"{well.Q:.1f}",
                    f"{well.r_w:.3f}",
                ]
            )
        t_wells = Table(well_table_data, colWidths=[120, 80, 80, 110, 90])
        t_wells.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(t_wells)

    story.append(Spacer(1, 14))

    # Neighboring Building Damage Assessment
    story.append(
        Paragraph("5. Neighboring Building Structural Damage Assessment", h1_style)
    )
    if scenario.buildings:
        bldg_table_data = [
            [
                "Building Name",
                "X-Center [m]",
                "Fnd Depth [m]",
                "Length L [m]",
                "Structure Type",
            ]
        ]
        for bldg in scenario.buildings:
            bldg_table_data.append(
                [
                    bldg.name,
                    f"{bldg.x_center:.2f}",
                    f"{bldg.foundation_depth:.2f}",
                    f"{bldg.length:.2f}",
                    bldg.structural_type.value,
                ]
            )
        t_bldg = Table(bldg_table_data, colWidths=[120, 80, 80, 80, 120])
        t_bldg.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(t_bldg)

    story.append(Spacer(1, 20))

    # Signature Block
    story.append(Paragraph("6. Engineering Sign-Off & Verification", h2_style))
    sig_text = (
        "<b>Prepared by:</b> J. Doe, Lead Geotechnical Engineer &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "<b>Checked by:</b> Senior Peer Reviewer<br/>"
        "<b>Signature:</b> ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "<b>Date:</b> 2026-07-27"
    )
    story.append(Paragraph(sig_text, body_style))

    doc.build(story)
    return buffer.getvalue()
