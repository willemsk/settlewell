"""QTableWidget subclass for soil layers input and editing."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class SoilLayerTable(QTableWidget):
    """Editable table for managing soil layer parameters.

    Columns:
        0: Naam (str)
        1: Dikte [m] (float > 0)
        2: γ [kN/m³] (float > 0)
        3: γ_sat [kN/m³] (float >= γ)
        4: k_h [m/s] (float > 0)
        5: e₀ [-] (float >= 0)
        6: Cc [-] (float >= 0)
        7: Cr [-] (float >= 0, <= Cc)
        8: E_oed [kPa] (float > 0)
        9: Cv [m²/s] (float >= 0)
        10: OCR [-] (float >= 1.0)
    """

    data_changed = Signal()

    COLUMNS = [
        ("Naam", "Sand"),
        ("Dikte [m]", "2.0"),
        ("γ [kN/m³]", "17.5"),
        ("γ_sat [kN/m³]", "20.0"),
        ("k_h [m/s]", "1e-4"),
        ("e₀ [-]", "0.5"),
        ("Cc [-]", "0.02"),
        ("Cr [-]", "0.005"),
        ("E_oed [kPa]", "30000"),
        ("Cv [m²/s]", "1e-2"),
        ("OCR [-]", "1.0"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels([col[0] for col in self.COLUMNS])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cellChanged.connect(self._on_cell_changed)

        # Pre-fill one default row
        self.add_layer()

    def add_layer(
        self,
        name: str = "Sand",
        thickness: float = 2.0,
        gamma: float = 17.5,
        gamma_sat: float = 20.0,
        k_h: float = 1e-4,
        e0: float = 0.5,
        Cc: float = 0.02,
        Cr: float = 0.005,
        Eoed: float = 30000.0,
        Cv: float = 1e-2,
        OCR: float = 1.0,
    ) -> None:
        """Add a new soil layer row."""
        row = self.rowCount()
        self.blockSignals(True)
        self.insertRow(row)

        values = [
            str(name),
            str(thickness),
            str(gamma),
            str(gamma_sat),
            str(k_h),
            str(e0),
            str(Cc),
            str(Cr),
            str(Eoed),
            str(Cv),
            str(OCR),
        ]

        for col, val in enumerate(values):
            item = QTableWidgetItem(val)
            self.setItem(row, col, item)

        self.blockSignals(False)
        self.data_changed.emit()

    def remove_selected_layer(self) -> None:
        """Remove the currently selected row in the table."""
        current_row = self.currentRow()
        if current_row >= 0 and self.rowCount() > 1:
            self.removeRow(current_row)
            self.data_changed.emit()

    def _on_cell_changed(self, row: int, column: int) -> None:
        self.data_changed.emit()

    def get_layers(self) -> list[dict]:
        """Extract all valid soil layer rows as dictionaries."""
        layers = []
        for row in range(self.rowCount()):
            try:
                name = (
                    self.item(row, 0).text().strip()
                    if self.item(row, 0)
                    else f"Layer {row + 1}"
                )
                thickness = float(self.item(row, 1).text())
                gamma = float(self.item(row, 2).text())
                gamma_sat = float(self.item(row, 3).text())
                k_h = float(self.item(row, 4).text())
                e0 = float(self.item(row, 5).text())
                Cc = float(self.item(row, 6).text())
                Cr = float(self.item(row, 7).text())
                Eoed = float(self.item(row, 8).text())
                Cv = float(self.item(row, 9).text())
                OCR = float(self.item(row, 10).text())

                layers.append(
                    {
                        "name": name,
                        "thickness": thickness,
                        "gamma": gamma,
                        "gamma_sat": gamma_sat,
                        "k_h": k_h,
                        "e0": e0,
                        "Cc": Cc,
                        "Cr": Cr,
                        "Eoed": Eoed,
                        "Cv": Cv,
                        "OCR": OCR,
                    }
                )
            except (ValueError, AttributeError):
                continue
        return layers

    def set_layers(self, layers: list[dict]) -> None:
        """Populate table from a list of soil layer dictionaries."""
        self.blockSignals(True)
        self.setRowCount(0)
        self.blockSignals(False)

        for layer in layers:
            self.add_layer(
                name=layer.get("name", "Layer"),
                thickness=layer.get("thickness", 2.0),
                gamma=layer.get("gamma", 17.5),
                gamma_sat=layer.get("gamma_sat", 20.0),
                k_h=layer.get("k_h", 1e-4),
                e0=layer.get("e0", 0.5),
                Cc=layer.get("Cc", 0.02),
                Cr=layer.get("Cr", 0.005),
                Eoed=layer.get("Eoed", 30000.0),
                Cv=layer.get("Cv", 1e-2),
                OCR=layer.get("OCR", 1.0),
            )

    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate all numeric values in the table.

        Returns:
            (is_valid, list_of_error_messages)
        """
        errors = []
        if self.rowCount() == 0:
            errors.append("Minstens 1 bodemlaag is vereist.")
            return False, errors

        for row in range(self.rowCount()):
            layer_name = (
                self.item(row, 0).text().strip()
                if self.item(row, 0)
                else f"Rij {row + 1}"
            )
            try:
                thickness = float(self.item(row, 1).text())
                if thickness <= 0:
                    errors.append(f"[{layer_name}] Dikte moet > 0 m zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige dikte.")

            try:
                gamma = float(self.item(row, 2).text())
                gamma_sat = float(self.item(row, 3).text())
                if gamma <= 0:
                    errors.append(f"[{layer_name}] γ moet > 0 kN/m³ zijn.")
                if gamma_sat < gamma:
                    errors.append(f"[{layer_name}] γ_sat moet >= γ zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige volumieke massa.")

            try:
                k_h = float(self.item(row, 4).text())
                if k_h <= 0:
                    errors.append(f"[{layer_name}] k_h moet > 0 m/s zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige doorlatendheid (k_h).")

            try:
                Cc = float(self.item(row, 6).text())
                Cr = float(self.item(row, 7).text())
                if Cr > Cc:
                    errors.append(f"[{layer_name}] Cr moet <= Cc zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige Cc of Cr.")

            try:
                Eoed = float(self.item(row, 8).text())
                if Eoed <= 0:
                    errors.append(f"[{layer_name}] E_oed moet > 0 kPa zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige E_oed.")

            try:
                OCR = float(self.item(row, 10).text())
                if OCR < 1.0:
                    errors.append(f"[{layer_name}] OCR moet >= 1.0 zijn.")
            except (ValueError, AttributeError):
                errors.append(f"[{layer_name}] Ongeldige OCR.")

        return len(errors) == 0, errors
