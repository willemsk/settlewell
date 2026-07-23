"""Step 5 Wizard Page: Neighboring Buildings Table."""

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWizardPage,
)

from settlewell.gui.widgets.building_table import BuildingTable


class BuildingsPage(QWizardPage):
    """Wizard page for defining neighboring buildings to assess for settlement damage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 5: Omliggende Bebouwing")
        self.setSubTitle(
            "Definieer de locaties, afmetingen, funderingsdiepte en constructietype van naburige gebouwen."
        )

        layout = QVBoxLayout()
        building_group = QGroupBox("Te beoordelen gebouwen")
        b_layout = QVBoxLayout()

        self.table = BuildingTable()
        self.table.data_changed.connect(self._on_values_changed)
        b_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Gebouw toevoegen (Add Building)")
        self.add_btn.clicked.connect(self._on_add_building)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton(
            "Geselecteerd gebouw verwijderen (Remove Building)"
        )
        self.remove_btn.clicked.connect(self.table.remove_selected_building)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()
        b_layout.addLayout(btn_layout)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        b_layout.addWidget(self.error_label)

        building_group.setLayout(b_layout)
        layout.addWidget(building_group)

        self.setLayout(layout)

    def _on_add_building(self) -> None:
        row = self.table.rowCount()
        self.table.add_building(x=15.0 + row * 5.0, y=0.0)

    def _on_values_changed(self) -> None:
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Check validation for buildings table."""
        valid, errors = self.table.validate_all()
        if not valid:
            self.error_label.setText(errors[0] if errors else "Ongeldige gebouwinvoer.")
            return False

        self.error_label.setText("")
        return True

    def get_state(self) -> dict:
        """Return serialized state dictionary for buildings."""
        return {"buildings": self.table.get_buildings()}

    def load_state(self, data: dict) -> None:
        """Populate buildings table from serialized state dictionary."""
        b_data = data.get("buildings", [])
        if isinstance(b_data, list) and b_data:
            self.table.set_buildings(b_data)
        self.completeChanged.emit()
