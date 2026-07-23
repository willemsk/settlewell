"""Step 1 Wizard Page: Soil Profile & Layer Table."""

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWizardPage,
)

from settlewell.gui.widgets.soil_table import SoilLayerTable


class SoilProfilePage(QWizardPage):
    """Wizard page for defining the soil profile (surface level, GWL, layers)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 1: Bodemprofiel & Grondlagen")
        self.setSubTitle(
            "Voer het maaiveldniveau (mTAW), de freatische grondwaterstand (mTAW) en de geotechnische eigenschappen van de grondlagen in."
        )

        layout = QVBoxLayout()

        # Top section: Surface level and GWL form
        level_group = QGroupBox("Niveaus (mTAW)")
        form_layout = QFormLayout()

        self.surface_spin = QDoubleSpinBox()
        self.surface_spin.setRange(-50.0, 100.0)
        self.surface_spin.setValue(5.0)
        self.surface_spin.setSingleStep(0.1)
        self.surface_spin.setSuffix(" mTAW")
        self.surface_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Maaiveldniveau (Surface level):", self.surface_spin)

        self.gwl_spin = QDoubleSpinBox()
        self.gwl_spin.setRange(-50.0, 100.0)
        self.gwl_spin.setValue(4.0)
        self.gwl_spin.setSingleStep(0.1)
        self.gwl_spin.setSuffix(" mTAW")
        self.gwl_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Grondwaterstand (GWL):", self.gwl_spin)

        level_group.setLayout(form_layout)
        layout.addWidget(level_group)

        # Main section: Soil layer table
        layer_group = QGroupBox("Grondlagen (Soil Layers)")
        layer_layout = QVBoxLayout()

        self.table = SoilLayerTable()
        self.table.data_changed.connect(self._on_values_changed)
        layer_layout.addWidget(self.table)

        # Buttons for table management
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Laag toevoegen (Add Layer)")
        self.add_btn.clicked.connect(self._on_add_layer)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("Geselecteerde laag verwijderen (Remove Layer)")
        self.remove_btn.clicked.connect(self.table.remove_selected_layer)
        btn_layout.addWidget(self.remove_btn)

        btn_layout.addStretch()
        layer_layout.addLayout(btn_layout)

        # Validation status label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layer_layout.addWidget(self.error_label)

        layer_group.setLayout(layer_layout)
        layout.addWidget(layer_group)

        self.setLayout(layout)

    def _on_add_layer(self) -> None:
        row_count = self.table.rowCount()
        self.table.add_layer(name=f"Laag {row_count + 1}")

    def _on_values_changed(self) -> None:
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Check validation state for page completion."""
        errors = []

        # Validate levels
        surface = self.surface_spin.value()
        gwl = self.gwl_spin.value()
        if gwl > surface:
            errors.append(
                "Grondwaterstand (GWL) kan niet hoger liggen dan het maaiveld."
            )

        # Validate table
        table_valid, table_errors = self.table.validate_all()
        if not table_valid:
            errors.extend(table_errors)

        if errors:
            self.error_label.setText(errors[0])
            return False
        else:
            self.error_label.setText("")
            return True

    def get_state(self) -> dict:
        """Return serialized state dictionary for soil profile."""
        return {
            "soil_profile": {
                "surface_level_mtaw": self.surface_spin.value(),
                "gwl_mtaw": self.gwl_spin.value(),
                "layers": self.table.get_layers(),
            }
        }

    def load_state(self, data: dict) -> None:
        """Populate widgets from serialized state dictionary."""
        prof_data = data.get("soil_profile", {})
        if "surface_level_mtaw" in prof_data:
            self.surface_spin.setValue(float(prof_data["surface_level_mtaw"]))
        if "gwl_mtaw" in prof_data:
            self.gwl_spin.setValue(float(prof_data["gwl_mtaw"]))
        if "layers" in prof_data and isinstance(prof_data["layers"], list):
            self.table.set_layers(prof_data["layers"])
        self.completeChanged.emit()
