"""Headless PySide6 GUI integration and unit tests for Settlewell."""

import os
from pathlib import Path
import pytest

# Force offscreen platform for headless Qt testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_API"] = "PySide6"

from PySide6.QtWidgets import QApplication

from settlewell.gui.main_window import MainWindow
from settlewell.gui.project_io import load_project, save_project
from settlewell.gui.wizard import SettlewellWizard
from settlewell.gui.worker import AnalysisWorker


@pytest.fixture(scope="session")
def qapp():
    """Shared QApplication fixture for headless Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_instantiation(qapp):
    """Test that MainWindow and SettlewellWizard initialize without errors."""
    win = MainWindow()
    assert win.windowTitle().startswith("Settlewell")
    assert win.wizard is not None
    assert len(win.wizard.pageIds()) == 6


def test_wizard_state_roundtrip(qapp):
    """Test wizard state extraction (get_state) and restoration (load_state)."""
    wizard = SettlewellWizard()
    initial_state = wizard.get_state()

    assert "soil_profile" in initial_state
    assert "construction_pit" in initial_state
    assert "wells" in initial_state
    assert "dewatering" in initial_state
    assert "buildings" in initial_state

    # Modify state and reload
    modified_state = dict(initial_state)
    modified_state["soil_profile"]["surface_level_mtaw"] = 12.5
    modified_state["construction_pit"]["length"] = 15.0

    wizard.load_state(modified_state)

    re_extracted = wizard.get_state()
    assert re_extracted["soil_profile"]["surface_level_mtaw"] == 12.5
    assert re_extracted["construction_pit"]["length"] == 15.0


def test_project_io_roundtrip(tmp_path: Path):
    """Test saving project state to JSON and reading it back."""
    test_state = {
        "soil_profile": {"surface_level_mtaw": 5.0, "gwl_mtaw": 4.0, "layers": []},
        "construction_pit": {"length": 10.0, "width": 8.0, "depth": 3.5},
    }

    file_path = tmp_path / "test_project.settlewell"
    save_project(test_state, file_path)

    assert file_path.exists()

    loaded = load_project(file_path)
    assert loaded["construction_pit"]["length"] == 10.0
    assert loaded["soil_profile"]["surface_level_mtaw"] == 5.0


def test_analysis_worker_pipeline(qapp):
    """Test background calculation worker produces all 7 plot figures."""
    wizard = SettlewellWizard()
    state = wizard.get_state()

    worker = AnalysisWorker(state)
    results = {}

    def on_finished(res):
        nonlocal results
        results = res

    worker.finished.connect(on_finished)
    worker.run()

    assert "figures" in results
    assert len(results["figures"]) == 7


def test_pdf_export(qapp, tmp_path: Path):
    """Test exporting all 7 figures to a multi-page PDF report."""
    wizard = SettlewellWizard()

    # Run worker synchronously
    worker = AnalysisWorker(wizard.get_state())
    results = {}

    def on_finished(res):
        nonlocal results
        results = res

    worker.finished.connect(on_finished)
    worker.run()

    wizard.results_page._on_finished(results)

    pdf_path = tmp_path / "test_report.pdf"
    wizard.results_page.export_pdf(pdf_path, show_dialog=False)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
