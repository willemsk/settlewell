"""Reusable Qt widget wrapping Matplotlib FigureCanvasQTAgg and NavigationToolbar2QT."""

from typing import Optional

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QVBoxLayout, QWidget


class PlotCanvas(QWidget):
    """Qt widget wrapping a Matplotlib FigureCanvas and NavigationToolbar."""

    def __init__(self, fig: Optional[Figure] = None, parent=None):
        super().__init__(parent)
        self._fig: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasQTAgg] = None
        self.toolbar: Optional[NavigationToolbar2QT] = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if fig is not None:
            self.set_figure(fig)

    def set_figure(self, fig: Figure) -> None:
        """Set or replace the current Matplotlib figure and refresh canvas."""
        # Clean up old widgets if replacing figure
        if self._fig is not None and self._fig != fig:
            plt.close(self._fig)

        if self.canvas is not None:
            self.layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
        if self.toolbar is not None:
            self.layout.removeWidget(self.toolbar)
            self.toolbar.deleteLater()

        self._fig = fig
        self.canvas = FigureCanvasQTAgg(fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)
        self.canvas.draw()

    def get_figure(self) -> Optional[Figure]:
        """Return active Matplotlib Figure object."""
        return self._fig
