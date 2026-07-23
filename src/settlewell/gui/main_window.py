"""Main application window for Settlewell GUI."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from settlewell import __version__

from .wizard import SettlewellWizard


class MainWindow(QMainWindow):
    """Main application window shell for Settlewell desktop application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file: Path | None = None

        self.setWindowTitle("Settlewell — Naamloos project")
        self.resize(1200, 800)

        # Wizard central widget container
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.wizard = SettlewellWizard(container)
        self.wizard.setWindowFlags(Qt.WindowType.Widget)
        layout.addWidget(self.wizard)
        self.setCentralWidget(container)

        self.wizard.restart()
        self.wizard.show()

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Gereed")

        # Menu bar
        self._create_menus()

        # Connect signals
        self.wizard.currentIdChanged.connect(self._on_wizard_step_changed)
        self._on_wizard_step_changed(self.wizard.currentId())

    def _create_menus(self) -> None:
        """Create menu bar items and keyboard shortcuts."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&Bestand (File)")

        new_action = QAction("&Nieuw project (New)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open project... (Open)", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        save_action = QAction("&Opslaan (Save)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Opslaan &als... (Save As)", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_pdf_action = QAction("&Exporteer PDF Rapport...", self)
        export_pdf_action.triggered.connect(self._on_export_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        exit_action = QAction("&Afsluiten (Exit)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        about_action = QAction("&Over Settlewell (About)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _on_wizard_step_changed(self, page_id: int) -> None:
        """Update status bar when wizard step changes."""
        page = self.wizard.page(page_id)
        step_title = page.title() if page else f"Stap {page_id + 1}"
        file_name = self._current_file.name if self._current_file else "Naamloos"
        self.status_bar.showMessage(f"Project: {file_name} | Active stap: {step_title}")

    def _on_new_project(self) -> None:
        """Reset wizard state to default blank project."""
        reply = QMessageBox.question(
            self,
            "Nieuw Project",
            "Weet u zeker dat u een nieuw project wilt starten? Niet-opgeslagen wijzigingen gaan verloren.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._current_file = None
            self.setWindowTitle("Settlewell — Naamloos project")
            self.wizard.restart()

    def _on_open_project(self) -> None:
        """Open a .settlewell project file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Settlewell Project",
            "",
            "Settlewell Projecten (*.settlewell);;JSON Bestanden (*.json);;Alle bestanden (*.*)",
        )
        if file_path:
            path = Path(file_path)
            try:
                from .project_io import load_project

                data = load_project(path)
                self.wizard.load_state(data)
                self._current_file = path
                self.setWindowTitle(f"Settlewell — {path.name}")
                self.status_bar.showMessage(f"Project geladen: {path.name}")
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(
                    self, "Fout bij openen", f"Kan project niet laden:\n{e}"
                )

    def _on_save_project(self) -> None:
        """Save current project state."""
        if self._current_file is None:
            self._on_save_project_as()
        else:
            self._do_save(self._current_file)

    def _on_save_project_as(self) -> None:
        """Save project state to a new file path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Opslaan Als",
            "project.settlewell",
            "Settlewell Projecten (*.settlewell);;JSON Bestanden (*.json)",
        )
        if file_path:
            path = Path(file_path)
            if not path.suffix:
                path = path.with_suffix(".settlewell")
            self._do_save(path)

    def _do_save(self, path: Path) -> None:
        """Helper to serialize wizard state and write to disk."""
        try:
            from .project_io import save_project

            state = self.wizard.get_state()
            save_project(state, path)
            self._current_file = path
            self.setWindowTitle(f"Settlewell — {path.name}")
            self.status_bar.showMessage(f"Project opgeslagen: {path.name}")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(
                self, "Fout bij opslaan", f"Kan project niet opslaan:\n{e}"
            )

    def _on_export_pdf(self) -> None:
        """Export analysis result figures as a PDF report."""
        if hasattr(self.wizard.results_page, "export_pdf"):
            self.wizard.results_page.export_pdf()
        else:
            QMessageBox.information(
                self,
                "PDF Export",
                "Voer eerst de analyse uit (Stap 6) om een PDF rapport te kunnen exporteren.",
            )

    def _on_about(self) -> None:
        """Show About dialog."""
        QMessageBox.about(
            self,
            "Over Settlewell",
            f"<b>Settlewell v{__version__}</b><br><br>"
            "Berekeningspakket voor grondwaterverlaging en zetttingsanalyse.<br>"
            "Ontwikkeld voor Vlaamse bouwpraktijk (mTAW).<br><br>"
            "© 2026 Settlewell Contributors",
        )
