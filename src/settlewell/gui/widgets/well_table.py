"""QTableWidget subclass for managing dewatering wells."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class WellTable(QTableWidget):
    """Editable table for managing dewatering wells.

    Columns:
        0: X [m]
        1: Y [m]
        2: Q [m³/s]
        3: r_w [m]
        4: Bovenkant filter (Screen Top) [mTAW]
        5: Onderkant filter (Screen Bottom) [mTAW]
    """

    data_changed = Signal()

    HEADERS = [
        "X [m]",
        "Y [m]",
        "Q [m³/s]",
        "r_w [m]",
        "Screen Top [mTAW]",
        "Screen Bottom [mTAW]",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cellChanged.connect(self._on_cell_changed)

        # Pre-fill 4 corner wells by default
        self.add_default_wells()

    def add_default_wells(
        self, length: float = 8.0, width: float = 6.0, bottom_mtaw: float = 2.0
    ) -> None:
        """Add 4 wells at pit corners."""
        self.blockSignals(True)
        self.setRowCount(0)
        self.blockSignals(False)

        half_l = length / 2.0
        half_w = width / 2.0
        corners = [
            (-half_l, -half_w),
            (half_l, -half_w),
            (half_l, half_w),
            (-half_l, half_w),
        ]

        for x, y in corners:
            self.add_well(
                x=x,
                y=y,
                Q=0.001,
                r_w=0.075,
                screen_top=bottom_mtaw,
                screen_bottom=bottom_mtaw - 5.0,
            )

    def add_well(
        self,
        x: float = 0.0,
        y: float = 0.0,
        Q: float = 0.001,
        r_w: float = 0.075,
        screen_top: float = 2.0,
        screen_bottom: float = -3.0,
    ) -> None:
        """Add a single well row."""
        row = self.rowCount()
        self.blockSignals(True)
        self.insertRow(row)

        values = [str(x), str(y), str(Q), str(r_w), str(screen_top), str(screen_bottom)]

        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            self.setItem(row, col, item)

        self.blockSignals(False)
        self.data_changed.emit()

    def remove_selected_well(self) -> None:
        """Remove selected well row."""
        current_row = self.currentRow()
        if current_row >= 0 and self.rowCount() > 1:
            self.removeRow(current_row)
            self.data_changed.emit()

    def _on_cell_changed(self, row: int, column: int) -> None:
        self.data_changed.emit()

    def get_wells(self) -> list[dict]:
        """Extract all valid well rows as dicts."""
        wells = []
        for row in range(self.rowCount()):
            try:
                x = float(self.item(row, 0).text())
                y = float(self.item(row, 1).text())
                Q = float(self.item(row, 2).text())
                r_w = float(self.item(row, 3).text())
                screen_top = float(self.item(row, 4).text())
                screen_bottom = float(self.item(row, 5).text())

                wells.append(
                    {
                        "x": x,
                        "y": y,
                        "Q": Q,
                        "r_w": r_w,
                        "screen_top_mtaw": screen_top,
                        "screen_bottom_mtaw": screen_bottom,
                    }
                )
            except (ValueError, AttributeError):
                continue
        return wells

    def set_wells(self, wells: list[dict]) -> None:
        """Populate table from list of well dicts."""
        self.blockSignals(True)
        self.setRowCount(0)
        self.blockSignals(False)

        for well in wells:
            self.add_well(
                x=well.get("x", 0.0),
                y=well.get("y", 0.0),
                Q=well.get("Q", 0.001),
                r_w=well.get("r_w", 0.075),
                screen_top=well.get("screen_top_mtaw", well.get("screen_top", 2.0)),
                screen_bottom=well.get(
                    "screen_bottom_mtaw", well.get("screen_bottom", -3.0)
                ),
            )

    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate well parameters."""
        errors = []
        if self.rowCount() == 0:
            errors.append("Minstens 1 bemalingsfilter is vereist.")
            return False, errors

        for row in range(self.rowCount()):
            well_idx = f"Filter {row + 1}"
            try:
                Q = float(self.item(row, 2).text())
                if Q <= 0:
                    errors.append(f"[{well_idx}] Debiet (Q) moet > 0 m³/s zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{well_idx}] Ongeldig debiet (Q).")

            try:
                r_w = float(self.item(row, 3).text())
                if r_w <= 0:
                    errors.append(f"[{well_idx}] Straal (r_w) moet > 0 m zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{well_idx}] Ongeldige filterstraal (r_w).")

            try:
                top = float(self.item(row, 4).text())
                bot = float(self.item(row, 5).text())
                if bot >= top:
                    errors.append(
                        f"[{well_idx}] Onderkant filter moet onder bovenkant filter liggen."
                    )
            except (ValueError, AttributeError):
                errors.append(f"[{well_idx}] Ongeldige filterdieptes.")

        return len(errors) == 0, errors
