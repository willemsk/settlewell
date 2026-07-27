"""PDF, DXF, and Excel/CSV Export Dashboard Viewport Component."""

import solara

from settlewell.solara_app.export import (
    generate_csv_data,
    generate_dxf_drawing,
    generate_excel_workbook,
    generate_pdf_report,
)
from settlewell.solara_app.state import project_state


@solara.component
def ExportView() -> solara.Element:
    """Render export dashboard with report preview overview cards and direct file download buttons."""
    state = project_state.value
    active_sc = state.get_active_scenario()

    pdf_bytes = generate_pdf_report(active_sc)
    dxf_bytes = generate_dxf_drawing(active_sc)
    excel_bytes = generate_excel_workbook(active_sc)
    csv_bytes = generate_csv_data(active_sc)

    return solara.Row(
        style={"width": "100%", "gap": "24px", "padding": "12px 0px"},
        children=[
            # Left Column: Executive Report Overview Summary Card
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px", "gap": "16px"},
                children=[
                    solara.Markdown("### 📄 Calculation Report Summary"),
                    solara.Column(
                        style={
                            "padding": "16px",
                            "border": "1px solid rgba(2, 132, 199, 0.3)",
                            "border-radius": "10px",
                            "background-color": "rgba(2, 132, 199, 0.03)",
                        },
                        children=[
                            solara.Markdown(f"**Project Title:** `{active_sc.name}`"),
                            solara.Markdown(
                                f"**Groundwater Table ($z_{{gw}}$):** `{active_sc.water_table.depth_z:.2f} m`"
                            ),
                            solara.Markdown(
                                f"**Subsoil Stratigraphy:** `{len(active_sc.stratigraphy)} Soil Layers`"
                            ),
                            solara.Markdown(
                                f"**Surface Footing Loads:** `{len(active_sc.loads)} Active Loads`"
                            ),
                            solara.Markdown(
                                f"**Excavation Construction Pit:** `{active_sc.construction_pit.length}m × {active_sc.construction_pit.width}m × {active_sc.construction_pit.depth}m`"
                            ),
                            solara.Markdown(
                                f"**Dewatering Wells:** `{len(active_sc.dewatering.wells)} Active Wells`"
                            ),
                            solara.Markdown(
                                f"**Neighboring Buildings:** `{len(active_sc.buildings)} Assessed Buildings`"
                            ),
                            solara.Markdown(
                                f"**Stress Method:** `{active_sc.solver_settings.stress_method.value}`"
                            ),
                        ],
                    ),
                ],
            ),
            # Right Column: Export Action Cards & Download Buttons
            solara.Column(
                style={"flex": "1 1 50%", "min-width": "0px", "gap": "16px"},
                children=[
                    solara.Markdown("### 📥 Download Calculation Deliverables"),
                    # 1. PDF Report Card
                    solara.Column(
                        style={
                            "padding": "14px",
                            "border": "1px solid rgba(2, 132, 199, 0.3)",
                            "border-radius": "8px",
                            "background-color": "rgba(2, 132, 199, 0.04)",
                        },
                        children=[
                            solara.Row(
                                justify="space-between",
                                style={"align-items": "center"},
                                children=[
                                    solara.Markdown("📄 **PDF Engineering Report**"),
                                    solara.FileDownload(
                                        data=pdf_bytes,
                                        filename=f"{active_sc.name.replace(' ', '_')}_Report.pdf",
                                        label="Download PDF Report",
                                    ),
                                ],
                            ),
                            solara.Markdown(
                                "_Includes cover page, stratigraphy table, loads, dewatering layout, drawdown contours, and building damage assessment._",
                                style={"font-size": "0.85rem", "color": "#64748b"},
                            ),
                        ],
                    ),
                    # 2. DXF CAD Card
                    solara.Column(
                        style={
                            "padding": "14px",
                            "border": "1px solid rgba(217, 119, 6, 0.3)",
                            "border-radius": "8px",
                            "background-color": "rgba(217, 119, 6, 0.04)",
                        },
                        children=[
                            solara.Row(
                                justify="space-between",
                                style={"align-items": "center"},
                                children=[
                                    solara.Markdown("📐 **DXF CAD Vector Drawing**"),
                                    solara.FileDownload(
                                        data=dxf_bytes,
                                        filename=f"{active_sc.name.replace(' ', '_')}_Drawing.dxf",
                                        label="Download DXF CAD",
                                    ),
                                ],
                            ),
                            solara.Markdown(
                                "_Multi-layer CAD drawing containing soil strata, groundwater line, footings, excavation pit, wells, buildings, and settlement curve._",
                                style={"font-size": "0.85rem", "color": "#64748b"},
                            ),
                        ],
                    ),
                    # 3. Excel Workbook Card
                    solara.Column(
                        style={
                            "padding": "14px",
                            "border": "1px solid rgba(5, 150, 105, 0.3)",
                            "border-radius": "8px",
                            "background-color": "rgba(5, 150, 105, 0.04)",
                        },
                        children=[
                            solara.Row(
                                justify="space-between",
                                style={"align-items": "center"},
                                children=[
                                    solara.Markdown("📊 **Excel Workbook (.xlsx)**"),
                                    solara.FileDownload(
                                        data=excel_bytes,
                                        filename=f"{active_sc.name.replace(' ', '_')}_Data.xlsx",
                                        label="Download Excel (.xlsx)",
                                    ),
                                ],
                            ),
                            solara.Markdown(
                                "_Structured multi-tab workbook with summary, stratigraphy, stress profiles, drawdown grid, and building damage tables._",
                                style={"font-size": "0.85rem", "color": "#64748b"},
                            ),
                        ],
                    ),
                    # 4. CSV Data Card
                    solara.Column(
                        style={
                            "padding": "14px",
                            "border": "1px solid rgba(100, 116, 139, 0.3)",
                            "border-radius": "8px",
                            "background-color": "rgba(100, 116, 139, 0.04)",
                        },
                        children=[
                            solara.Row(
                                justify="space-between",
                                style={"align-items": "center"},
                                children=[
                                    solara.Markdown("💾 **Raw CSV Data (.csv)**"),
                                    solara.FileDownload(
                                        data=csv_bytes,
                                        filename=f"{active_sc.name.replace(' ', '_')}_Data.csv",
                                        label="Download CSV (.csv)",
                                    ),
                                ],
                            ),
                            solara.Markdown(
                                "_Raw numerical comma-separated values for custom post-processing and analysis._",
                                style={"font-size": "0.85rem", "color": "#64748b"},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
