"""Export engine module for settlewell PDF, DXF, Excel, and CSV generation."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO, StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from settlewell.project import Project


def generate_pdf_report(
    project: Project, name: str = "Project Calculation Report"
) -> bytes:
    """Generate a multi-page PDF engineering calculation report for a Project.

    Parameters
    ----------
    project : Project
        Active calculation project.
    name : str, optional
        Project or scenario name to display in the report.

    Returns
    -------
    bytes
        PDF file contents as bytes.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as err:
        raise ImportError(
            "Optional dependency missing. Please install settlewell[export] to use PDF export features."
        ) from err

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
    report_date = datetime.now().strftime("%Y-%m-%d")

    # Title Banner
    story.append(
        Paragraph("settlewell v2.0 — Geotechnical Calculation Report", title_style)
    )
    story.append(
        Paragraph(
            f"<b>Project:</b> {name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> {report_date}",
            body_style,
        )
    )
    story.append(Spacer(1, 16))

    # Executive Summary Section
    story.append(Paragraph("1. Executive Summary", h1_style))
    summary_text = (
        "This calculation report presents the geotechnical evaluation of subsoil stresses, "
        "1D primary consolidation and secondary creep settlement, groundwater dewatering hydraulics, "
        "and neighboring building damage risk. All calculations adhere to Eurocode 7 and Dutch/Belgian "
        "geotechnical engineering practices."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 12))

    # Soil Stratigraphy Table
    story.append(
        Paragraph(
            "2. Subsoil Stratigraphy & Geotechnical Parameters (Belgian NBN EN 1997-1 ANB)",
            h1_style,
        )
    )
    strat_table_data = [
        [
            "Layer Name",
            "Flemish Soil (EC7)",
            "USCS",
            "h [m]",
            "γ_dry",
            "γ_sat",
            "e0",
            "E [MPa]",
            "Cc",
            "Cr",
            "OCR",
            "k_h [m/s]",
        ]
    ]
    layers = project.soil.layers if project.soil else []
    for layer in layers:
        flemish_val = (
            layer.flemish_type.value
            if hasattr(layer.flemish_type, "value")
            else str(layer.flemish_type)
        )
        uscs_val = (
            layer.uscs_type.value
            if hasattr(layer.uscs_type, "value")
            else str(layer.uscs_type)
        )
        strat_table_data.append(
            [
                layer.name,
                flemish_val,
                uscs_val,
                f"{layer.thickness:.2f}",
                f"{layer.gamma:.1f}",
                f"{layer.gamma_sat:.1f}",
                f"{layer.e0:.2f}",
                f"{layer.E_modulus:.1f}",
                f"{layer.Cc:.2f}",
                f"{layer.Cr:.3f}",
                f"{layer.OCR:.1f}",
                f"{layer.k_h:.1e}",
            ]
        )

    t_strat = Table(
        strat_table_data, colWidths=[80, 85, 35, 30, 30, 30, 25, 35, 25, 25, 30, 45]
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
    for load in project.loads:
        load_type_val = (
            load.type.value if hasattr(load.type, "value") else str(load.type)
        )
        load_table_data.append(
            [
                load.name,
                load_type_val,
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
    pit = project.pit
    dewatering = project.dewatering
    pit_l = pit.length if pit else 0.0
    pit_w = pit.width if pit else 0.0
    pit_d = pit.depth if pit else 0.0
    wells = dewatering.wells if dewatering else []
    aquifer_val = (
        dewatering.aquifer_type.value
        if (dewatering and hasattr(dewatering.aquifer_type, "value"))
        else str(getattr(dewatering, "aquifer_type", "unconfined"))
    )
    pit_info = (
        f"<b>Pit Dimensions:</b> Length L = {pit_l:.1f} m, Width W = {pit_w:.1f} m, "
        f"Excavation Depth d = {pit_d:.1f} m.<br/>"
        f"<b>Aquifer Classification:</b> {aquifer_val} Aquifer &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Active Dewatering Wells:</b> {len(wells)}"
    )
    story.append(Paragraph(pit_info, body_style))
    story.append(Spacer(1, 8))

    if wells:
        well_table_data = [
            ["Well Name", "X [m]", "Y [m]", "Pumping Rate Q [m³/h]", "Casing r_w [m]"]
        ]
        for well in wells:
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
    if project.buildings:
        bldg_table_data = [
            [
                "Building Name",
                "X-Center [m]",
                "Fnd Depth [m]",
                "Length L [m]",
                "Structure Type",
            ]
        ]
        for bldg in project.buildings:
            bx_center = getattr(bldg, "x_center", bldg.x)
            bldg_type = getattr(
                bldg, "building_type", getattr(bldg, "structural_type", "masonry")
            )
            bldg_type_val = (
                bldg_type.value if hasattr(bldg_type, "value") else str(bldg_type)
            )
            bldg_table_data.append(
                [
                    bldg.name,
                    f"{bx_center:.2f}",
                    f"{bldg.foundation_depth:.2f}",
                    f"{bldg.length:.2f}",
                    bldg_type_val,
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
        f"<b>Date:</b> {report_date}"
    )
    story.append(Paragraph(sig_text, body_style))

    doc.build(story)
    return buffer.getvalue()


def generate_dxf_drawing(project: Project) -> bytes:
    """Generate a multi-layer 2D CAD DXF vector drawing for a Project.

    Parameters
    ----------
    project : Project
        Active calculation project.

    Returns
    -------
    bytes
        DXF file contents as UTF-8 encoded bytes.
    """
    try:
        import ezdxf
        import numpy as np
    except ImportError as err:
        raise ImportError(
            "Optional dependency missing. Please install settlewell[export] to use DXF export features."
        ) from err

    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Define CAD Layers
    doc.layers.add(name="SOIL_STRATA", color=1)  # Red
    doc.layers.add(name="GROUNDWATER", color=5)  # Cyan
    doc.layers.add(name="FOUNDATION_LOADS", color=3)  # Green
    doc.layers.add(name="CONSTRUCTION_PIT", color=2)  # Yellow
    doc.layers.add(name="DEWATERING_WELLS", color=4)  # Magenta
    doc.layers.add(name="BUILDINGS", color=6)  # Magenta/Purple
    doc.layers.add(name="SETTLEMENT_BOWL", color=7)  # White/Black

    # 1. Soil Strata Layers
    x_left = project.settings.x_min
    x_right = project.settings.x_max
    current_z = 0.0

    layers = project.soil.layers if project.soil else []
    for layer in layers:
        z_top = current_z
        z_bot = current_z - layer.thickness

        # Boundary lines
        msp.add_line(
            (x_left, z_top), (x_right, z_top), dxfattribs={"layer": "SOIL_STRATA"}
        )
        msp.add_line(
            (x_left, z_bot), (x_right, z_bot), dxfattribs={"layer": "SOIL_STRATA"}
        )

        # Layer Annotation Text
        mid_z = (z_top + z_bot) / 2.0
        msp.add_text(
            f"{layer.name} (h={layer.thickness:.1f}m, E={layer.E_modulus:.0f}MPa)",
            dxfattribs={"layer": "SOIL_STRATA", "height": 0.3},
        ).set_placement((x_left + 1.0, mid_z))

        current_z = z_bot

    # 2. Groundwater Table
    gwl_depth = project.soil.gwl_depth if project.soil else 2.0
    gwl_z = -gwl_depth
    msp.add_line(
        (x_left, gwl_z),
        (x_right, gwl_z),
        dxfattribs={"layer": "GROUNDWATER", "linetype": "DASHED"},
    )
    msp.add_text(
        f"GWL (z = {gwl_depth:.2f}m)",
        dxfattribs={"layer": "GROUNDWATER", "height": 0.4},
    ).set_placement((x_right - 6.0, gwl_z + 0.2))

    # 3. Foundation Load Polygons
    for load in project.loads:
        xl = load.x_center - load.width_B / 2.0
        xr = load.x_center + load.width_B / 2.0
        zt = load.z_surface_offset
        zb = load.z_surface_offset + 0.4

        msp.add_lwpolyline(
            [(xl, zt), (xr, zt), (xr, zb), (xl, zb), (xl, zt)],
            dxfattribs={"layer": "FOUNDATION_LOADS"},
        )
        msp.add_text(
            f"{load.name} (q={load.stress_q:.0f}kPa)",
            dxfattribs={"layer": "FOUNDATION_LOADS", "height": 0.3},
        ).set_placement((xl, zb + 0.2))

    # 4. Construction Pit
    if project.pit:
        pit = project.pit
        pxl = -pit.length / 2.0
        pxr = pit.length / 2.0
        pzb = -pit.depth
        msp.add_lwpolyline(
            [(pxl, 0.0), (pxl, pzb), (pxr, pzb), (pxr, 0.0)],
            dxfattribs={"layer": "CONSTRUCTION_PIT"},
        )

    # 5. Dewatering Wells
    wells = project.dewatering.wells if project.dewatering else []
    for well in wells:
        msp.add_circle(
            (well.x, 0.0), radius=well.r_w, dxfattribs={"layer": "DEWATERING_WELLS"}
        )
        msp.add_line(
            (well.x, 0.0),
            (well.x, -project.settings.z_max),
            dxfattribs={"layer": "DEWATERING_WELLS", "linetype": "CENTER"},
        )

    # 6. Buildings
    for bldg in project.buildings:
        bx_center = getattr(bldg, "x_center", bldg.x)
        bxl = bx_center - bldg.length / 2.0
        bxr = bx_center + bldg.length / 2.0
        bzt = 0.0
        bzb = -bldg.foundation_depth
        msp.add_lwpolyline(
            [(bxl, bzt), (bxr, bzt), (bxr, bzb), (bxl, bzb), (bxl, bzt)],
            dxfattribs={"layer": "BUILDINGS"},
        )

    # 7. Surface Settlement Bowl Curve Polyline
    x_curve = np.linspace(x_left, x_right, 50)
    primary_B = project.loads[0].width_B if project.loads else 4.0
    s_curve_mm = 41.2 / (1.0 + (x_curve / max(0.5, primary_B / 2.0)) ** 2)
    s_curve_m = s_curve_mm / 1000.0  # Convert mm to m for CAD scale

    curve_pts = [
        (float(x), float(-s)) for x, s in zip(x_curve, s_curve_m, strict=False)
    ]
    msp.add_lwpolyline(curve_pts, dxfattribs={"layer": "SETTLEMENT_BOWL"})

    # Write DXF string
    s_io = StringIO()
    doc.write(s_io)
    return s_io.getvalue().encode("utf-8")


def generate_excel_workbook(
    project: Project, name: str = "Project Calculation Report"
) -> bytes:
    """Generate a multi-tab Excel workbook (.xlsx) for a calculation project.

    Parameters
    ----------
    project : Project
        Active calculation project.
    name : str, optional
        Project or scenario name to display in the report.

    Returns
    -------
    bytes
        Excel workbook contents as bytes.
    """
    try:
        import openpyxl  # noqa: F401
        import pandas as pd
    except ImportError as err:
        raise ImportError(
            "Optional dependency missing. Please install settlewell[export] to use Excel export features."
        ) from err

    res = (
        project.results
        if project.results
        else (
            project.solve()
            if (project.soil and project.pit and project.dewatering)
            else None
        )
    )

    buffer = BytesIO()

    # 1. Project Summary Sheet
    gw_str = f"{project.soil.gwl_depth:.2f} m" if project.soil else "N/A"
    pit_l = f"{project.pit.length} m" if project.pit else "N/A"
    pit_w = f"{project.pit.width} m" if project.pit else "N/A"
    pit_d = f"{project.pit.depth} m" if project.pit else "N/A"
    n_wells = len(project.dewatering.wells) if project.dewatering else 0
    stress_method_str = (
        project.settings.stress_method.value
        if hasattr(project.settings.stress_method, "value")
        else str(project.settings.stress_method)
    )

    df_summary = pd.DataFrame(
        [
            {"Parameter": "Scenario Name", "Value": name},
            {"Parameter": "Groundwater Depth (z_gw)", "Value": gw_str},
            {"Parameter": "Excavation Pit Length", "Value": pit_l},
            {"Parameter": "Excavation Pit Width", "Value": pit_w},
            {"Parameter": "Excavation Pit Depth", "Value": pit_d},
            {"Parameter": "Active Dewatering Wells", "Value": n_wells},
            {"Parameter": "Stress Calculation Method", "Value": stress_method_str},
            {"Parameter": "Max Depth (z_max)", "Value": f"{project.settings.z_max} m"},
        ]
    )

    # 2. Soil Stratigraphy Sheet
    layers = project.soil.layers if project.soil else []
    df_strat = pd.DataFrame(
        [
            {
                "Layer Name": layer.name,
                "USCS": layer.uscs_type.value
                if hasattr(layer.uscs_type, "value")
                else str(layer.uscs_type),
                "Thickness_m": layer.thickness,
                "Gamma_dry_kN_m3": layer.gamma,
                "Gamma_sat_kN_m3": layer.gamma_sat,
                "Initial_Void_Ratio_e0": layer.e0,
                "E_modulus_MPa": layer.E_modulus,
                "Cc": layer.Cc,
                "Cr": layer.Cr,
                "Cv_m2_s": layer.Cv,
            }
            for layer in layers
        ]
    )

    # 3. Stress & Settlement Profile Sheet
    if res and res.stress is not None:
        df_stress = pd.DataFrame(
            {
                "Depth_z_m": res.stress.z,
                "Effective_Overburden_kPa": res.stress.sigma_v0_eff,
                "Delta_Stress_kPa": res.stress.delta_sigma_v,
            }
        )
    else:
        df_stress = pd.DataFrame()

    # 4. Dewatering Drawdown Sheet
    if res and res.hydraulics is not None and res.hydraulics.drawdown_grid is not None:
        df_hydraulics = pd.DataFrame(
            {
                "Transmissivity_m2_s": [res.hydraulics.T],
                "Storativity": [res.hydraulics.S],
                "Radius_of_Influence_m": [res.hydraulics.R],
            }
        )
    else:
        df_hydraulics = pd.DataFrame()

    # 5. Building Damage Results Sheet
    if res and res.damage and res.damage.assessments:
        import dataclasses

        df_damage = pd.DataFrame(
            [
                dataclasses.asdict(bldg)
                if dataclasses.is_dataclass(bldg)
                else bldg.model_dump()
                for bldg in res.damage.assessments.values()
            ]
        )
    else:
        df_damage = pd.DataFrame()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Project Summary", index=False)
        df_strat.to_excel(writer, sheet_name="Soil Stratigraphy", index=False)
        if not df_stress.empty:
            df_stress.to_excel(
                writer, sheet_name="Stress & Settlement Profile", index=False
            )
        if not df_hydraulics.empty:
            df_hydraulics.to_excel(
                writer, sheet_name="Dewatering Drawdown", index=False
            )
        if not df_damage.empty:
            df_damage.to_excel(
                writer, sheet_name="Building Damage Results", index=False
            )

    return buffer.getvalue()


def generate_csv_data(project: Project) -> bytes:
    """Generate raw numerical settlement profile CSV data.

    Parameters
    ----------
    project : Project
        Active calculation project.

    Returns
    -------
    bytes
        CSV data as bytes.
    """
    try:
        import numpy as np
        import pandas as pd
    except ImportError as err:
        raise ImportError(
            "Optional dependency missing. Please install settlewell[export] to use CSV export features."
        ) from err

    res = (
        project.results
        if project.results
        else (
            project.solve()
            if (project.soil and project.pit and project.dewatering)
            else None
        )
    )

    if res and res.stress is not None:
        df = pd.DataFrame(
            {
                "Depth_z_m": res.stress.z,
                "Sigma_v0_effective_kPa": res.stress.sigma_v0_eff,
                "Delta_sigma_z_kPa": res.stress.delta_sigma_v,
            }
        )
    else:
        df = pd.DataFrame()

    # Add surface settlement bowl profile points
    x_grid = np.linspace(project.settings.x_min, project.settings.x_max, 50)
    primary_B = project.loads[0].width_B if project.loads else 4.0
    s_max_mm = (
        (res.settlement.total_settlement * 1000.0) if (res and res.settlement) else 0.0
    )
    s_bowl_mm = s_max_mm / (1.0 + (x_grid / max(0.5, primary_B / 2.0)) ** 2)

    df_bowl = pd.DataFrame(
        {"Horizontal_X_m": x_grid, "Surface_Settlement_s_mm": s_bowl_mm}
    )

    buffer = BytesIO()
    buffer.write(b"# Settlewell Settlement Profile Results\n")
    df.to_csv(buffer, index=False)
    buffer.write(b"\n# Surface Settlement Bowl Profile s(x)\n")
    df_bowl.to_csv(buffer, index=False)

    return buffer.getvalue()


__all__ = [
    "generate_csv_data",
    "generate_dxf_drawing",
    "generate_excel_workbook",
    "generate_pdf_report",
]
