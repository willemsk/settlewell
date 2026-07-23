"""Step 3 Wizard Page: Dewatering Wells Table."""

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWizardPage,
)

from settlewell.gui.widgets.well_table import WellTable


class WellsPage(QWizardPage):
    """Wizard page for defining dewatering wells layout."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 3: Bemalingsfilters (Wells)")
        self.setSubTitle(
            "Definieer de coördinaten (x, y), debieten Q [m³/s], filterstraal r_w [m] en filterlengtes van de bemalingsbronnen."
        )

        layout = QVBoxLayout()
        well_group = QGroupBox("Bemalingsfilters")
        well_layout = QVBoxLayout()

        self.table = WellTable()
        self.table.data_changed.connect(self._on_values_changed)
        well_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Filter toevoegen (Add Well)")
        self.add_btn.clicked.connect(self._on_add_well)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Geselecteerd filter verwijderen (Remove Well)")
        self.remove_btn.clicked.connect(self.table.remove_selected_well)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()
        well_layout.addLayout(btn_layout)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        well_layout.addWidget(self.error_label)

        well_group.setLayout(well_layout)
        layout.addWidget(well_group)

        self.setLayout(layout)

    def _on_add_well(self) -> None:
        self.table.add_well()

    def _on_values_changed(self) -> None:
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Check validation for wells table."""
        valid, errors = self.table.validate_all()
        if not valid:
            self.error_label.setText(errors[0] if errors else "Ongeldige filterinvoer.")
            return False

        self.error_label.setText("")
        return True

    def get_state(self) -> dict:
        """Return serialized state dictionary for wells."""
        return {"wells": self.table.get_wells()}

    def load_state(self, data: dict) -> None:
        """Populate wells table from serialized state dictionary."""
        wells_data = data.get("wells", [])
        if isinstance(wells_data, list) and wells_data:
            self.table.set_wells(wells_data)
        self.completeChanged.emit()
