"""Step 4 Wizard Page: Dewatering System Configuration."""

from typing import ClassVar

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWizardPage,
)

from settlewell.models import AquiferType


class DewateringConfigPage(QWizardPage):
    """Wizard page for configuring dewatering system parameters."""

    AQUIFER_MAP: ClassVar[dict[str, str]] = {
        "Freatisch (Unconfined)": AquiferType.UNCONFINED.value,
        "Afgesloten (Confined)": AquiferType.CONFINED.value,
    }
    REVERSE_AQUIFER_MAP: ClassVar[dict[str, str]] = {
        v: k for k, v in AQUIFER_MAP.items()
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Stap 4: Bemalingsinstellingen")
        self.setSubTitle(
            "Definieer het doelpeil voor de bemalingsverlaging, de bemalingsduur, het type watervoerend pakket en optionele parameters."
        )

        layout = QVBoxLayout()

        # Main config section
        config_group = QGroupBox("Bemalingsparameters")
        form_layout = QFormLayout()

        self.target_drawdown_spin = QDoubleSpinBox()
        self.target_drawdown_spin.setRange(-50.0, 100.0)
        self.target_drawdown_spin.setValue(2.0)
        self.target_drawdown_spin.setSingleStep(0.1)
        self.target_drawdown_spin.setSuffix(" mTAW")
        self.target_drawdown_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow(
            "Doelpeil verlaging (Target drawdown):", self.target_drawdown_spin
        )

        self.original_gwl_spin = QDoubleSpinBox()
        self.original_gwl_spin.setRange(-50.0, 100.0)
        self.original_gwl_spin.setValue(4.0)
        self.original_gwl_spin.setSingleStep(0.1)
        self.original_gwl_spin.setSuffix(" mTAW")
        self.original_gwl_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Oorspronkelijke GWL:", self.original_gwl_spin)

        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 3650.0)
        self.duration_spin.setValue(90.0)
        self.duration_spin.setSingleStep(1.0)
        self.duration_spin.setSuffix(" dagen")
        self.duration_spin.valueChanged.connect(self._on_values_changed)
        form_layout.addRow("Bemalingsduur (Duration):", self.duration_spin)

        self.aquifer_combo = QComboBox()
        self.aquifer_combo.addItems(list(self.AQUIFER_MAP.keys()))
        self.aquifer_combo.currentTextChanged.connect(self._on_values_changed)
        form_layout.addRow("Aquifertype:", self.aquifer_combo)

        config_group.setLayout(form_layout)
        layout.addWidget(config_group)

        # Optional parameter overrides section
        override_group = QGroupBox(
            "Optionele Parameter Overrides (Leeg laten voor auto-berekening)"
        )
        override_layout = QFormLayout()

        self.t_override_edit = QLineEdit()
        self.t_override_edit.setPlaceholderText(
            "Auto-computed (Transmissiviteit T [m²/s])"
        )
        self.t_override_edit.textChanged.connect(self._on_values_changed)
        override_layout.addRow("Transmissiviteit T [m²/s]:", self.t_override_edit)

        self.s_override_edit = QLineEdit()
        self.s_override_edit.setPlaceholderText("Auto-computed (Berging S [-])")
        self.s_override_edit.textChanged.connect(self._on_values_changed)
        override_layout.addRow("Berging (Storativity) S [-]:", self.s_override_edit)

        self.r_override_edit = QLineEdit()
        self.r_override_edit.setPlaceholderText(
            "Auto-computed (Sichardt Invloedsstraal R [m])"
        )
        self.r_override_edit.textChanged.connect(self._on_values_changed)
        override_layout.addRow("Invloedsstraal R [m]:", self.r_override_edit)

        override_group.setLayout(override_layout)
        layout.addWidget(override_group)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self.error_label)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Auto-fill target drawdown from Pit page and GWL from Soil Profile page if available."""
        wizard = self.wizard()
        if wizard:
            if hasattr(wizard, "soil_page"):
                self.original_gwl_spin.setValue(wizard.soil_page.gwl_spin.value())
            if hasattr(wizard, "pit_page"):
                self.target_drawdown_spin.setValue(
                    wizard.pit_page.bottom_mtaw_spin.value()
                )
        self.completeChanged.emit()

    def _on_values_changed(self) -> None:
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Check validation for dewatering parameters."""
        target = self.target_drawdown_spin.value()
        orig = self.original_gwl_spin.value()

        if target >= orig:
            self.error_label.setText(
                "Doelpeil verlaging moet lager zijn dan de oorspronkelijke grondwaterstand."
            )
            return False

        if self.duration_spin.value() <= 0:
            self.error_label.setText("Bemalingsduur moet > 0 dagen zijn.")
            return False

        # Validate numeric overrides if supplied
        for name, widget in [
            ("T", self.t_override_edit),
            ("S", self.s_override_edit),
            ("R", self.r_override_edit),
        ]:
            text = widget.text().strip()
            if text:
                try:
                    val = float(text)
                    if val <= 0:
                        self.error_label.setText(
                            f"Override parameter {name} moet > 0 zijn."
                        )
                        return False
                except ValueError:
                    self.error_label.setText(
                        f"Ongeldige getalswaarde voor parameter {name}."
                    )
                    return False

        self.error_label.setText("")
        return True

    def get_state(self) -> dict:
        """Return serialized state dictionary for dewatering configuration."""
        a_type = self.AQUIFER_MAP.get(
            self.aquifer_combo.currentText(), AquiferType.UNCONFINED.value
        )
        state = {
            "dewatering": {
                "target_drawdown_mtaw": self.target_drawdown_spin.value(),
                "original_gwl_mtaw": self.original_gwl_spin.value(),
                "pumping_duration_days": self.duration_spin.value(),
                "aquifer_type": a_type,
            }
        }

        # Add overrides if provided
        t_text = self.t_override_edit.text().strip()
        if t_text:
            state["dewatering"]["T_override"] = float(t_text)
        s_text = self.s_override_edit.text().strip()
        if s_text:
            state["dewatering"]["S_override"] = float(s_text)
        r_text = self.r_override_edit.text().strip()
        if r_text:
            state["dewatering"]["R_override"] = float(r_text)

        return state

    def load_state(self, data: dict) -> None:
        """Populate widgets from serialized state dictionary."""
        dew_data = data.get("dewatering", {})
        if "target_drawdown_mtaw" in dew_data:
            self.target_drawdown_spin.setValue(float(dew_data["target_drawdown_mtaw"]))
        if "original_gwl_mtaw" in dew_data:
            self.original_gwl_spin.setValue(float(dew_data["original_gwl_mtaw"]))
        if "pumping_duration_days" in dew_data:
            self.duration_spin.setValue(float(dew_data["pumping_duration_days"]))
        if "aquifer_type" in dew_data:
            a_str = self.REVERSE_AQUIFER_MAP.get(
                dew_data["aquifer_type"], next(iter(self.AQUIFER_MAP.keys()))
            )
            self.aquifer_combo.setCurrentText(a_str)

        if "T_override" in dew_data and dew_data["T_override"] is not None:
            self.t_override_edit.setText(str(dew_data["T_override"]))
        if "S_override" in dew_data and dew_data["S_override"] is not None:
            self.s_override_edit.setText(str(dew_data["S_override"]))
        if "R_override" in dew_data and dew_data["R_override"] is not None:
            self.r_override_edit.setText(str(dew_data["R_override"]))

        self.completeChanged.emit()
