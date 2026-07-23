"""Step 6 Wizard Page: Run Analysis & Display Multi-Tab Results."""

from pathlib import Path
from typing import List, Optional, Tuple

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWizardPage,
)

from settlewell.gui.widgets.plot_canvas import PlotCanvas
from settlewell.gui.worker import AnalysisWorker


class ResultsPage(QWizardPage):
    """Wizard page for running the calculation pipeline and viewing multi-tab results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 6: Resultaten & Visualisatie")
        self.setSubTitle(
            "Voer de berekening uit en bekijk de 7 gedetailleerde grafische weergaven."
        )

        self._thread: Optional[QThread] = None
        self._worker: Optional[AnalysisWorker] = None
        self._figures: List[Tuple[str, Figure]] = []

        layout = QVBoxLayout()

        # Controls top row
        ctrl_layout = QHBoxLayout()
        self.run_btn = QPushButton("Start Analyse (Run Analysis)")
        self.run_btn.clicked.connect(self._start_analysis)
        ctrl_layout.addWidget(self.run_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        ctrl_layout.addWidget(self.progress_bar)

        layout.addLayout(ctrl_layout)

        self.status_label = QLabel(
            "Klik op 'Start Analyse' om de berekening te starten."
        )
        layout.addWidget(self.status_label)

        # Tab widget for 7 plots
        self.tab_widget = QTabWidget()
        self.canvases: List[PlotCanvas] = []

        # Create 7 tab canvases
        tab_names = [
            "Dwarsdoorsnede",
            "Grondplan",
            "Zettingskom",
            "Tijd-Zetting",
            "Spanningsverloop",
            "3D Bemalingskegel",
            "Schadesamenvatting",
        ]

        for name in tab_names:
            canvas = PlotCanvas()
            self.canvases.append(canvas)
            self.tab_widget.addTab(canvas, name)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def initializePage(self) -> None:
        """Trigger analysis automatically when entering Step 6."""
        self._start_analysis()

    def _start_analysis(self) -> None:
        """Launch background worker thread for analysis."""
        wizard = self.wizard()
        if not wizard:
            return

        state = wizard.get_state()

        self.run_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Analyse wordt gestart...")

        # Setup thread and worker
        self._thread = QThread()
        self._worker = AnalysisWorker(state)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_progress(self, percent: int, msg: str) -> None:
        self.progress_bar.setValue(percent)
        self.status_label.setText(msg)

    def _on_finished(self, results: dict) -> None:
        self.run_btn.setEnabled(True)
        self.status_label.setText("Analyse succesvol voltooid.")
        self._figures = results.get("figures", [])

        # Populate tabs with generated figures
        for idx, (title, fig) in enumerate(self._figures):
            if idx < len(self.canvases):
                self.canvases[idx].set_figure(fig)

        self.completeChanged.emit()

    def _on_error(self, err_msg: str) -> None:
        self.run_btn.setEnabled(True)
        self.status_label.setText(f"Fout bij analyse: {err_msg}")
        QMessageBox.critical(
            self, "Analyse Fout", f"Er is een fout opgetreden:\n{err_msg}"
        )

    def export_pdf(
        self, file_path: Optional[Path] = None, show_dialog: bool = True
    ) -> None:
        """Export all generated figures to a multi-page PDF report."""
        if not self._figures:
            if show_dialog:
                QMessageBox.warning(
                    self,
                    "Geen Resultaten",
                    "Er zijn nog geen resultaten beschikbaar om te exporteren.",
                )
            return

        if file_path is None:
            save_str, _ = QFileDialog.getSaveFileName(
                self,
                "Exporteer PDF Rapport",
                "Settlewell_Rapport.pdf",
                "PDF Bestanden (*.pdf)",
            )
            if not save_str:
                return
            file_path = Path(save_str)

        try:
            with PdfPages(file_path) as pdf:
                for title, fig in self._figures:
                    pdf.savefig(fig)
            if show_dialog:
                QMessageBox.information(
                    self,
                    "PDF Exporteer Succes",
                    f"PDF rapport succesvol opgeslagen in:\n{file_path}",
                )
        except Exception as e:
            if show_dialog:
                QMessageBox.critical(
                    self, "Fout bij exporteren", f"Kan PDF rapport niet opslaan:\n{e}"
                )

    def isComplete(self) -> bool:
        """Page is complete once figures are generated."""
        return len(self._figures) > 0
