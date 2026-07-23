"""Application entry point for Settlewell PySide6 GUI."""

import os
import sys

import matplotlib
from PySide6.QtWidgets import QApplication

from settlewell import __version__
from .main_window import MainWindow
from .theme import DARK_STYLESHEET, MATPLOTLIB_DARK_PARAMS


def apply_matplotlib_theme() -> None:
    """Apply dark theme default rcParams to matplotlib."""
    for key, value in MATPLOTLIB_DARK_PARAMS.items():
        matplotlib.rcParams[key] = value


def main() -> None:
    """Launch the Settlewell GUI application.

    Sets QT_API environment variable, configures QApplication,
    applies the dark QSS stylesheet, and starts the event loop.
    """
    os.environ["QT_API"] = "PySide6"
    try:
        matplotlib.use("QtAgg")
    except Exception:
        pass

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("Settlewell")
    app.setApplicationVersion(__version__)

    apply_matplotlib_theme()
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.showMaximized()

    if "pytest" not in sys.modules:
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
