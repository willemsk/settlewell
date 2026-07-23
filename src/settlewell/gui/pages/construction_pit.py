"""Step 2 Wizard Page: Construction Pit Geometry."""

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWizardPage,
)


class ConstructionPitPage(QWizardPage):
    """Wizard page for defining construction pit geometry parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 2: Bouwput Geometrie")
        self.setSubTitle(
            "Definieer de lengte, breedte, ontgravingsdiepte en de x,y-positie van het middelpunt van de bouwput."
        )

        layout = QVBoxLayout()
        form_group = QGroupBox("Afmetingen en Positie Bouwput")
        form_layout = QFormLayout()

        # Length
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(0.1, 500.0)
        self.length_spin.setValue(8.0)
        self.length_spin.setSingleStep(0.5)
        self.length_spin.setSuffix(" m")
        self.length_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Lengte L (x-richting):", self.length_spin)

        # Width
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 500.0)
        self.width_spin.setValue(6.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setSuffix(" m")
        self.width_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Breedte B (y-richting):", self.width_spin)

        # Depth
        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setRange(0.1, 50.0)
        self.depth_spin.setValue(3.0)
        self.depth_spin.setSingleStep(0.1)
        self.depth_spin.setSuffix(" m")
        self.depth_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Ontgravingsdiepte (Depth):", self.depth_spin)

        # Center X
        self.center_x_spin = QDoubleSpinBox()
        self.center_x_spin.setRange(-500.0, 500.0)
        self.center_x_spin.setValue(0.0)
        self.center_x_spin.setSingleStep(1.0)
        self.center_x_spin.setSuffix(" m")
        self.center_x_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Middelpunt X-coördinaat:", self.center_x_spin)

        # Center Y
        self.center_y_spin = QDoubleSpinBox()
        self.center_y_spin.setRange(-500.0, 500.0)
        self.center_y_spin.setValue(0.0)
        self.center_y_spin.setSingleStep(1.0)
        self.center_y_spin.setSuffix(" m")
        self.center_y_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Middelpunt Y-coördinaat:", self.center_y_spin)

        # Bottom level
        self.bottom_mtaw_spin = QDoubleSpinBox()
        self.bottom_mtaw_spin.setRange(-50.0, 100.0)
        self.bottom_mtaw_spin.setValue(2.0)
        self.bottom_mtaw_spin.setSingleStep(0.1)
        self.bottom_mtaw_spin.setSuffix(" mTAW")
        self.bottom_mtaw_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow(
            "Putbodemniveauniveau (Bottom level):", self.bottom_mtaw_spin
        )

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self.error_label)

        self.setLayout(layout)

    def _on_values_changed(self) -> None:
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Check validation for construction pit geometry."""
        if self.length_spin.value() <= 0:
            self.error_label.setText("Lengte moet > 0 m zijn.")
            return False
        if self.width_spin.value() <= 0:
            self.error_label.setText("Breedte moet > 0 m zijn.")
            return False
        if self.depth_spin.value() <= 0:
            self.error_label.setText("Diepte moet > 0 m zijn.")
            return False

        self.error_label.setText("")
        return True

    def get_state(self) -> dict:
        """Return serialized state dictionary for construction pit."""
        return {
            "construction_pit": {
                "length": self.length_spin.value(),
                "width": self.width_spin.value(),
                "depth": self.depth_spin.value(),
                "center_x": self.center_x_spin.value(),
                "center_y": self.center_y_spin.value(),
                "bottom_mtaw": self.bottom_mtaw_spin.value(),
            }
        }

    def load_state(self, data: dict) -> None:
        """Populate widgets from serialized state dictionary."""
        pit_data = data.get("construction_pit", {})
        if "length" in pit_data:
            self.length_spin.setValue(float(pit_data["length"]))
        if "width" in pit_data:
            self.width_spin.setValue(float(pit_data["width"]))
        if "depth" in pit_data:
            self.depth_spin.setValue(float(pit_data["depth"]))
        if "center_x" in pit_data:
            self.center_x_spin.setValue(float(pit_data["center_x"]))
        if "center_y" in pit_data:
            self.center_y_spin.setValue(float(pit_data["center_y"]))
        if "bottom_mtaw" in pit_data:
            self.bottom_mtaw_spin.setValue(float(pit_data["bottom_mtaw"]))
        self.completeChanged.emit()
