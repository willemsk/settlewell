"""Unit test suite for Core Library Export Engine (`settlewell.export`)."""

from pathlib import Path

import pytest
import reacton

from settlewell.export import (
    generate_csv_data,
    generate_dxf_drawing,
    generate_excel_workbook,
    generate_pdf_report,
)
from settlewell.models import ConstructionPit, DewateringConfig, Well
from settlewell.project import Project
from settlewell.solara_app.components.viewport import ExportView
from settlewell.solara_app.state import create_default_project_state, project_state


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset global project state to default baseline for each test."""
    project_state.set(create_default_project_state())


@pytest.fixture
def sample_project() -> Project:
    """Create a sample initialized core Project instance."""
    proj = Project.from_template(
        "Antwerp Boom Clay Formation", gwl_mtaw=3.0, surface_level_mtaw=5.0
    )
    proj.pit = ConstructionPit(length=20.0, width=15.0, depth=4.0)
    proj.dewatering = DewateringConfig(
        wells=[Well(x=0.0, y=0.0, Q=25.0)],
        target_drawdown_mtaw=0.0,
        original_gwl_mtaw=3.0,
    )
    return proj


def test_pdf_report_generation(sample_project: Project) -> None:
    """Verify PDF report generation via generate_pdf_report."""
    pdf_bytes = generate_pdf_report(sample_project)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_dxf_drawing_generation(sample_project: Project) -> None:
    """Verify ezdxf DXF CAD drawing generation via generate_dxf_drawing."""
    dxf_bytes = generate_dxf_drawing(sample_project)
    assert dxf_bytes is not None
    assert len(dxf_bytes) > 200
    assert b"SECTION" in dxf_bytes
    assert b"HEADER" in dxf_bytes


def test_excel_workbook_generation(sample_project: Project) -> None:
    """Verify Excel workbook (.xlsx) generation via generate_excel_workbook."""
    excel_bytes = generate_excel_workbook(sample_project)
    assert excel_bytes is not None
    assert len(excel_bytes) > 500


def test_csv_data_generation(sample_project: Project) -> None:
    """Verify CSV data export via generate_csv_data."""
    csv_bytes = generate_csv_data(sample_project)
    assert csv_bytes is not None
    assert len(csv_bytes) > 50
    assert (
        b"Depth_z_m" in csv_bytes or b"Layer" in csv_bytes or b"Settlewell" in csv_bytes
    )


def test_project_facade_export_methods(sample_project: Project, tmp_path: Path) -> None:
    """Verify Project instance export facade methods (export_pdf, export_dxf, export_excel, export_csv)."""
    pdf_path = tmp_path / "report.pdf"
    dxf_path = tmp_path / "drawing.dxf"
    excel_path = tmp_path / "data.xlsx"
    csv_path = tmp_path / "data.csv"

    sample_project.export_pdf(pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 500

    sample_project.export_dxf(dxf_path)
    assert dxf_path.exists()
    assert dxf_path.stat().st_size > 200

    sample_project.export_excel(excel_path)
    assert excel_path.exists()
    assert excel_path.stat().st_size > 500

    sample_project.export_csv(csv_path)
    assert csv_path.exists()
    assert csv_path.stat().st_size > 50


def test_export_view_rendering() -> None:
    """Verify ExportView component rendering with reacton."""
    box_export = reacton.render(ExportView())
    assert box_export is not None
