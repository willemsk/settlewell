"""Unit test suite for Sprint 6: PDF, DXF, and CSV Export Engine."""

import reacton
from settlewell.solara_app.components.viewport import ExportView
from settlewell.solara_app.export import (
    generate_csv_data,
    generate_dxf_drawing,
    generate_excel_workbook,
    generate_pdf_report,
)
from settlewell.solara_app.state import project_state


def test_pdf_report_generation() -> None:
    """Verify ReportLab PDF report generation."""
    state = project_state.value
    scenario = state.get_active_scenario()

    pdf_bytes = generate_pdf_report(scenario)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_dxf_drawing_generation() -> None:
    """Verify ezdxf DXF CAD drawing generation."""
    state = project_state.value
    scenario = state.get_active_scenario()

    dxf_bytes = generate_dxf_drawing(scenario)
    assert dxf_bytes is not None
    assert len(dxf_bytes) > 200
    assert b"SECTION" in dxf_bytes
    assert b"HEADER" in dxf_bytes


def test_excel_workbook_generation() -> None:
    """Verify Excel workbook (.xlsx) generation."""
    state = project_state.value
    scenario = state.get_active_scenario()

    excel_bytes = generate_excel_workbook(scenario)
    assert excel_bytes is not None
    assert len(excel_bytes) > 500


def test_csv_data_generation() -> None:
    """Verify CSV data export."""
    state = project_state.value
    scenario = state.get_active_scenario()

    csv_bytes = generate_csv_data(scenario)
    assert csv_bytes is not None
    assert len(csv_bytes) > 50
    assert b"Depth_z_m" in csv_bytes or b"Layer" in csv_bytes


def test_export_view_rendering() -> None:
    """Verify ExportView component rendering with reacton."""
    box_export = reacton.render(ExportView())
    assert box_export is not None
