"""Dark QSS theme stylesheet and Matplotlib dark theme configuration."""

DARK_STYLESHEET: str = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 10pt;
}

QMainWindow, QWizard, QWizardPage, QDialog {
    background-color: #1e1e1e;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #007acc;
}

QLabel {
    color: #e0e0e0;
}

QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 22px;
}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #007acc;
}

QLineEdit[invalid="true"], QDoubleSpinBox[invalid="true"] {
    border: 2px solid #d32f2f;
    background-color: #381e1e;
}

QPushButton {
    background-color: #252525;
    color: #ffffff;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #007acc;
    border-color: #007acc;
}

QPushButton:pressed {
    background-color: #005999;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    color: #666666;
    border-color: #333333;
}

QTableWidget {
    background-color: #252525;
    alternate-background-color: #2a2a2a;
    gridline-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #1e1e1e;
    color: #007acc;
    padding: 6px;
    border: 1px solid #3c3c3c;
    font-weight: bold;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #252525;
}

QTabBar::tab {
    background-color: #1e1e1e;
    color: #aaaaaa;
    padding: 8px 16px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #252525;
    color: #007acc;
    font-weight: bold;
    border-bottom: 2px solid #007acc;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a2a;
    color: #ffffff;
}

QProgressBar {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    background-color: #252525;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #007acc;
    border-radius: 3px;
}

QMenuBar {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border-bottom: 1px solid #3c3c3c;
}

QMenuBar::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

QMenu {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

QStatusBar {
    background-color: #1e1e1e;
    color: #aaaaaa;
    border-top: 1px solid #3c3c3c;
}
"""

MATPLOTLIB_DARK_PARAMS = {
    "figure.facecolor": "#1e1e1e",
    "axes.facecolor": "#252525",
    "axes.edgecolor": "#3c3c3c",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#aaaaaa",
    "ytick.color": "#aaaaaa",
    "grid.color": "#3c3c3c",
    "legend.facecolor": "#1e1e1e",
    "legend.edgecolor": "#3c3c3c",
}
