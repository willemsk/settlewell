"""QTableWidget subclass for managing neighboring buildings."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QHeaderView, QTableWidget, QTableWidgetItem

from settlewell.models import BuildingType


class BuildingTable(QTableWidget):
    """Editable table for managing neighboring buildings.

    Columns:
        0: X [m]
        1: Y [m]
        2: Lengte [m]
        3: Breedte [m]
        4: Oriëntatie [°]
        5: Funderingsdiepte [m]
        6: Type (Metselwerk / Betonskelet)
    """

    data_changed = Signal()

    HEADERS = [
        "X [m]",
        "Y [m]",
        "Lengte [m]",
        "Breedte [m]",
        "Oriëntatie [°]",
        "Funderingsdiepte [m]",
        "Type Constructie",
    ]

    TYPE_MAP = {
        "Metselwerk (Masonry)": BuildingType.MASONRY.value,
        "Betonskelet (Concrete Frame)": BuildingType.CONCRETE_FRAME.value,
    }
    REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cellChanged.connect(self._on_cell_changed)

        # Pre-fill default building
        self.add_building()

    def add_building(
        self,
        x: float = 15.0,
        y: float = 0.0,
        length: float = 10.0,
        width: float = 8.0,
        orientation_deg: float = 0.0,
        foundation_depth: float = 0.6,
        building_type: str = "masonry",
    ) -> None:
        """Add a new building row."""
        row = self.rowCount()
        self.blockSignals(True)
        self.insertRow(row)

        numeric_vals = [
            str(x),
            str(y),
            str(length),
            str(width),
            str(orientation_deg),
            str(foundation_depth),
        ]

        for col, val in enumerate(numeric_vals):
            item = QTableWidgetItem(val)
            self.setItem(row, col, item)

        # Column 6: QComboBox delegate
        combo = QComboBox()
        combo.addItems(list(self.TYPE_MAP.keys()))
        type_str = self.REVERSE_TYPE_MAP.get(
            building_type, list(self.TYPE_MAP.keys())[0]
        )
        combo.setCurrentText(type_str)
        combo.currentTextChanged.connect(lambda _: self.data_changed.emit())
        self.setCellWidget(row, 6, combo)

        self.blockSignals(False)
        self.data_changed.emit()

    def remove_selected_building(self) -> None:
        """Remove selected building row."""
        current_row = self.currentRow()
        if current_row >= 0 and self.rowCount() > 1:
            self.removeRow(current_row)
            self.data_changed.emit()

    def _on_cell_changed(self, row: int, column: int) -> None:
        self.data_changed.emit()

    def get_buildings(self) -> list[dict]:
        """Extract all valid building rows as dicts."""
        buildings = []
        for row in range(self.rowCount()):
            try:
                x = float(self.item(row, 0).text())
                y = float(self.item(row, 1).text())
                length = float(self.item(row, 2).text())
                width = float(self.item(row, 3).text())
                orient = float(self.item(row, 4).text())
                f_depth = float(self.item(row, 5).text())

                combo = self.cellWidget(row, 6)
                b_type_str = (
                    combo.currentText() if combo else list(self.TYPE_MAP.keys())[0]
                )
                b_type = self.TYPE_MAP.get(b_type_str, BuildingType.MASONRY.value)

                buildings.append(
                    {
                        "x": x,
                        "y": y,
                        "length": length,
                        "width": width,
                        "orientation_deg": orient,
                        "foundation_depth": f_depth,
                        "building_type": b_type,
                    }
                )
            except (ValueError, AttributeError):
                continue
        return buildings

    def set_buildings(self, buildings: list[dict]) -> None:
        """Populate table from list of building dicts."""
        self.blockSignals(True)
        self.setRowCount(0)
        self.blockSignals(False)

        for b in buildings:
            self.add_building(
                x=b.get("x", 15.0),
                y=b.get("y", 0.0),
                length=b.get("length", 10.0),
                width=b.get("width", 8.0),
                orientation_deg=b.get("orientation_deg", 0.0),
                foundation_depth=b.get("foundation_depth", 0.6),
                building_type=b.get("building_type", "masonry"),
            )

    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate building parameters."""
        errors = []
        if self.rowCount() == 0:
            errors.append("Minstens 1 nabijgelegen gebouw is vereist.")
            return False, errors

        for row in range(self.rowCount()):
            b_idx = f"Gebouw {row + 1}"
            try:
                length = float(self.item(row, 2).text())
                width = float(self.item(row, 3).text())
                if length <= 0 or width <= 0:
                    errors.append(f"[{b_idx}] Lengte en breedte moeten > 0 m zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{b_idx}] Ongeldige afmetingen.")

            try:
                f_depth = float(self.item(row, 5).text())
                if f_depth < 0:
                    errors.append(f"[{b_idx}] Funderingsdiepte moet >= 0 m zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{b_idx}] Ongeldige funderingsdiepte.")

        return len(errors) == 0, errors
