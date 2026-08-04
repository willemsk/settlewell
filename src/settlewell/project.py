"""Top-level Project orchestrator for ground settlement analysis."""

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from settlewell.damage import DamageAssessment, assess_building_damage
from settlewell.hydraulics import (
    compute_drawdown_at_points,
    compute_drawdown_grid,
    compute_radius_of_influence,
    compute_storativity,
    compute_transmissivity,
)
from settlewell.models import (
    Building,
    ConstructionPit,
    DewateringConfig,
    DrainageType,
    LoadGeometry,
    SoilLayer,
    SoilProfile,
    SolverSettings,
)
from settlewell.numerical import create_grid, solve_steady_state
import settlewell.plotting as plotting
from settlewell.settlement import (
    compute_elastic_settlement,
    compute_equivalent_cv,
    compute_full_consolidation_curve,
    compute_initial_stress_profile,
    compute_total_settlement,
    compute_secondary_creep,
)
from settlewell.soils import FLEMISH_PROFILE_TEMPLATES, FLEMISH_SOIL_PRESETS
from settlewell.stress import compute_stress_profile_under_loads


class BaseModelFrozen(BaseModel):
    """Base Pydantic model with frozen immutability and arbitrary types allowed for NumPy arrays."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)


class HydraulicsResults(BaseModelFrozen):
    """Result container for hydraulic calculations."""

    T: float
    S: float
    R: float
    drawdown_grid: NDArray[np.float64] | None = None
    X_grid: NDArray[np.float64] | None = None
    Y_grid: NDArray[np.float64] | None = None


class StressResults(BaseModelFrozen):
    """Result container for vertical stress calculations."""

    z: NDArray[np.float64]
    sigma_v0_eff: NDArray[np.float64]
    delta_sigma_v: NDArray[np.float64]


class SettlementResults(BaseModelFrozen):
    """Result container for ground settlement calculations."""

    total_settlement: float
    per_layer_settlements: list[float]
    elastic_settlement: float = 0.0
    primary_settlement: float = 0.0
    creep_settlement: float = 0.0
    per_layer_elastic: list[float] = Field(default_factory=list)
    per_layer_creep: list[float] = Field(default_factory=list)
    time_settlement_curve: NDArray[np.float64] | None = None
    degree_of_consolidation_curve: NDArray[np.float64] | None = None
    times_days: NDArray[np.float64] | None = None


class DamageResults(BaseModelFrozen):
    """Result container for building damage assessments."""

    assessments: dict[str, DamageAssessment] = Field(default_factory=dict)


class ProjectResults(BaseModelFrozen):
    """Top-level container aggregating all computation results."""

    hydraulics: HydraulicsResults | None = None
    stress: StressResults | None = None
    settlement: SettlementResults | None = None
    damage: DamageResults | None = None


class ProjectDataModel(BaseModel):
    """Pydantic model for JSON serialization of Project inputs."""

    soil: SoilProfile | None = None
    pit: ConstructionPit | None = None
    dewatering: DewateringConfig | None = None
    buildings: list[Building] = Field(default_factory=list)
    loads: list[LoadGeometry] = Field(default_factory=list)
    settings: SolverSettings = Field(default_factory=SolverSettings)


class Project:
    """Top-level orchestrator class for Settlewell analysis projects."""

    def __init__(
        self,
        soil: SoilProfile | None = None,
        pit: ConstructionPit | None = None,
        dewatering: DewateringConfig | None = None,
        buildings: list[Building] | None = None,
        loads: list[LoadGeometry] | None = None,
        settings: SolverSettings | None = None,
    ) -> None:
        """
        Initialize a Settlewell analysis project.

        Parameters
        ----------
        soil : SoilProfile, optional
            Multi-layer soil profile.
        pit : ConstructionPit, optional
            Construction pit geometry.
        dewatering : DewateringConfig, optional
            Dewatering system configuration.
        buildings : list[Building], optional
            List of neighboring buildings.
        loads : list[LoadGeometry], optional
            List of surface load geometries.
        settings : SolverSettings, optional
            Calculation and mesh settings.
        """
        self._soil = soil
        self._pit = pit
        self._dewatering = dewatering
        self._buildings = list(buildings) if buildings else []
        self._loads = list(loads) if loads else []
        self._settings = settings if settings is not None else SolverSettings()
        self._results: ProjectResults | None = None

        self._validate_cross_dependencies()

    def _invalidate_results(self) -> None:
        self._results = None

    def _validate_cross_dependencies(self) -> None:
        if self._soil is not None and self._dewatering is not None:
            if self._dewatering.original_gwl_mtaw > self._soil.surface_level_mtaw:
                raise ValueError(
                    f"original_gwl_mtaw ({self._dewatering.original_gwl_mtaw}) "
                    f"cannot be above surface_level_mtaw ({self._soil.surface_level_mtaw})"
                )

    @property
    def soil(self) -> SoilProfile | None:
        return self._soil

    @soil.setter
    def soil(self, value: SoilProfile | None) -> None:
        old_val = self._soil
        try:
            self._soil = value
            self._validate_cross_dependencies()
            self._invalidate_results()
        except ValueError:
            self._soil = old_val
            raise

    @property
    def pit(self) -> ConstructionPit | None:
        return self._pit

    @pit.setter
    def pit(self, value: ConstructionPit | None) -> None:
        old_val = self._pit
        try:
            self._pit = value
            self._validate_cross_dependencies()
            self._invalidate_results()
        except ValueError:
            self._pit = old_val
            raise

    @property
    def dewatering(self) -> DewateringConfig | None:
        return self._dewatering

    @dewatering.setter
    def dewatering(self, value: DewateringConfig | None) -> None:
        old_val = self._dewatering
        try:
            self._dewatering = value
            self._validate_cross_dependencies()
            self._invalidate_results()
        except ValueError:
            self._dewatering = old_val
            raise

    @property
    def buildings(self) -> list[Building]:
        return self._buildings

    @buildings.setter
    def buildings(self, value: list[Building]) -> None:
        self._buildings = list(value)
        self._invalidate_results()

    @property
    def loads(self) -> list[LoadGeometry]:
        return self._loads

    @loads.setter
    def loads(self, value: list[LoadGeometry]) -> None:
        self._loads = list(value)
        self._invalidate_results()

    @property
    def settings(self) -> SolverSettings:
        return self._settings

    @settings.setter
    def settings(self, value: SolverSettings) -> None:
        self._settings = value
        self._invalidate_results()

    @property
    def results(self) -> ProjectResults | None:
        return self._results

    def to_dict(self) -> dict[str, Any]:
        """Convert Project input configuration to a dictionary."""
        model = ProjectDataModel(
            soil=self.soil,
            pit=self.pit,
            dewatering=self.dewatering,
            buildings=self.buildings,
            loads=self.loads,
            settings=self.settings,
        )
        return model.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Reconstruct a Project instance from a dictionary."""
        model = ProjectDataModel.model_validate(data)
        return cls(
            soil=model.soil,
            pit=model.pit,
            dewatering=model.dewatering,
            buildings=model.buildings,
            loads=model.loads,
            settings=model.settings,
        )

    def save(self, path: str | Path) -> None:
        """Save Project configuration to a JSON file."""
        p = Path(path)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        """Load Project configuration from a JSON file."""
        p = Path(path)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def export_pdf(self, path: str | Path) -> None:
        """Export project calculation report as a PDF document."""
        from settlewell.export import generate_pdf_report

        content = generate_pdf_report(self)
        Path(path).write_bytes(content)

    def export_dxf(self, path: str | Path) -> None:
        """Export project drawing as a CAD DXF file."""
        from settlewell.export import generate_dxf_drawing

        content = generate_dxf_drawing(self)
        Path(path).write_bytes(content)

    def export_excel(self, path: str | Path) -> None:
        """Export project calculation data as an Excel workbook (.xlsx)."""
        from settlewell.export import generate_excel_workbook

        content = generate_excel_workbook(self)
        Path(path).write_bytes(content)

    def export_csv(self, path: str | Path) -> None:
        """Export settlement profile data as a CSV file."""
        from settlewell.export import generate_csv_data

        content = generate_csv_data(self)
        Path(path).write_bytes(content)

    @classmethod
    def from_template(
        cls, template_name: str, gwl_mtaw: float, surface_level_mtaw: float
    ) -> "Project":
        """
        Create a Project instance populated with soil layers from a Flemish preset template.

        Parameters
        ----------
        template_name : str
            Name of the Flemish soil profile template (e.g. "Antwerp Boom Clay Formation").
        gwl_mtaw : float
            Groundwater elevation [mTAW].
        surface_level_mtaw : float
            Ground surface elevation [mTAW].

        Returns
        -------
        Project
            New Project initialized with the specified soil profile.
        """
        if template_name not in FLEMISH_PROFILE_TEMPLATES:
            valid = list(FLEMISH_PROFILE_TEMPLATES.keys())
            raise ValueError(
                f"Unknown template '{template_name}'. Valid templates: {valid}"
            )

        layers_data = FLEMISH_PROFILE_TEMPLATES[template_name]
        layers: list[SoilLayer] = []
        for name_override, flemish_type, thickness in layers_data:
            preset = FLEMISH_SOIL_PRESETS[flemish_type]
            layer = SoilLayer(
                name=name_override,
                thickness=thickness,
                gamma=preset["gamma_dry"],
                gamma_sat=preset["gamma_sat"],
                k_h=preset["k_h"],
                e0=preset["e0"],
                Cc=preset["Cc"],
                Cr=preset["Cr"],
                Eoed=preset["E_modulus"] * 1000.0,  # Convert MPa to kPa
                Cv=preset["Cv"],
                OCR=preset["ocr"],
                flemish_type=flemish_type,
            )
            layers.append(layer)

        profile = SoilProfile(
            layers=layers, gwl_mtaw=gwl_mtaw, surface_level_mtaw=surface_level_mtaw
        )
        return cls(soil=profile)

    def _validate_ready_to_solve(self) -> None:
        if self.soil is None or self.pit is None or self.dewatering is None:
            raise ValueError(
                "Soil profile, construction pit, and dewatering configuration "
                "must be set before calling solve()."
            )

    def _get_building_optional(self, building_idx: int) -> Building | None:
        """Get building by index. Returns None if project has no buildings."""
        if not self.buildings:
            return None
        if building_idx < 0 or building_idx >= len(self.buildings):
            raise IndexError(
                f"Building index {building_idx} out of range for {len(self.buildings)} buildings."
            )
        return self.buildings[building_idx]

    def _get_building_required(self, building_idx: int) -> Building:
        """Get building by index. Raises ValueError if project has no buildings."""
        b = self._get_building_optional(building_idx)
        if b is None:
            raise ValueError("This plot requires at least one building in the project.")
        return b

    def solve_hydraulics(self) -> HydraulicsResults:
        """Solve hydraulic drawdown distribution across the calculation domain."""
        self._validate_ready_to_solve()

        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None

        T = (
            self.dewatering.T
            if self.dewatering.T is not None
            else compute_transmissivity(self.soil, self.dewatering)
        )
        S = (
            self.dewatering.S
            if self.dewatering.S is not None
            else compute_storativity(self.soil, self.dewatering)
        )
        H0 = self.soil.total_depth - self.soil.gwl_depth
        R = (
            self.dewatering.R
            if self.dewatering.R is not None
            else compute_radius_of_influence(self.dewatering, T, H0)
        )

        x_min = -self.pit.length / 2.0 - self.settings.grid_padding
        x_max = self.pit.length / 2.0 + self.settings.grid_padding
        y_min = -self.pit.width / 2.0 - self.settings.grid_padding
        y_max = self.pit.width / 2.0 + self.settings.grid_padding

        mode = self.settings.hydraulics_solver.lower()
        if mode == "numerical":
            grid = create_grid((x_min, x_max), (y_min, y_max), dx=self.settings.grid_dx)
            solve_steady_state(grid, self.dewatering, self.soil, self.pit)
            X_grid, Y_grid = np.meshgrid(grid.x, grid.y)
            drawdown_grid = H0 - grid.head
        else:
            nx = max(10, int((x_max - x_min) / self.settings.grid_dx))
            ny = max(10, int((y_max - y_min) / self.settings.grid_dx))
            X_grid, Y_grid, drawdown_grid = compute_drawdown_grid(
                (x_min, x_max),
                (y_min, y_max),
                nx,
                ny,
                self.dewatering,
                self.soil,
            )

        return HydraulicsResults(
            T=T,
            S=S,
            R=R,
            drawdown_grid=drawdown_grid,
            X_grid=X_grid,
            Y_grid=Y_grid,
        )

    def solve_stress(self) -> StressResults:
        """Solve initial and secondary vertical stress profiles under surface loads."""
        self._validate_ready_to_solve()
        assert self.soil is not None

        z_mids = []
        curr = 0.0
        for layer in self.soil.layers:
            z_mids.append(curr + layer.thickness / 2.0)
            curr += layer.thickness
        z_arr = np.array(z_mids, dtype=np.float64)

        _, sigma_v0_eff, _ = compute_initial_stress_profile(self.soil, z_points=z_arr)

        if self.loads:
            delta_sigma_v = compute_stress_profile_under_loads(
                self.loads, z_arr, x_eval=0.0, method=self.settings.stress_method
            )
        else:
            delta_sigma_v = np.zeros_like(z_arr, dtype=np.float64)

        return StressResults(
            z=z_arr, sigma_v0_eff=sigma_v0_eff, delta_sigma_v=delta_sigma_v
        )

    def solve_settlement(
        self, hyd_res: HydraulicsResults, str_res: StressResults
    ) -> SettlementResults:
        """Solve ultimate primary consolidation settlement and time-settlement curves."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.dewatering is not None

        drawdown_center = compute_drawdown_at_points(
            np.array([[0.0, 0.0]]),
            self.dewatering,
            self.soil,
        )[0]

        total_primary, per_layer_primary = compute_total_settlement(
            self.soil,
            drawdown_center,
            method=self.settings.settlement_method,
            additional_stress=str_res.delta_sigma_v,
        )

        s_elastic, per_layer_elastic = compute_elastic_settlement(
            self.soil, str_res.delta_sigma_v
        )

        per_layer_creep = []
        if self.settings.calculate_creep:
            times_days = np.linspace(
                self.settings.t_start_days,
                self.settings.t_end_years * 365.0,
                50,
                dtype=np.float64,
            )
            cv_eq = compute_equivalent_cv(self.soil)
            h_dr = (
                self.soil.total_depth / 2.0
                if self.settings.drainage == DrainageType.DOUBLE
                else self.soil.total_depth
            )
            time_curve, u_curve = compute_full_consolidation_curve(
                s_elastic, total_primary, cv_eq, h_dr, times_days
            )
            total_creep = compute_secondary_creep(
                total_primary, 0.05, self.settings.t_end_years * 365.0
            )
            for s_prim in per_layer_primary:
                per_layer_creep.append(
                    compute_secondary_creep(
                        s_prim, 0.05, self.settings.t_end_years * 365.0
                    )
                )
        else:
            time_curve = None
            u_curve = None
            times_days = None
            total_creep = 0.0
            per_layer_creep = [0.0] * len(per_layer_primary)

        total_settlement = s_elastic + total_primary + total_creep

        return SettlementResults(
            total_settlement=total_settlement,
            per_layer_settlements=per_layer_primary,
            elastic_settlement=s_elastic,
            primary_settlement=total_primary,
            creep_settlement=total_creep,
            per_layer_elastic=per_layer_elastic,
            per_layer_creep=per_layer_creep,
            time_settlement_curve=time_curve,
            degree_of_consolidation_curve=u_curve,
            times_days=times_days,
        )

    def solve_damage(
        self, hyd_res: HydraulicsResults, set_res: SettlementResults
    ) -> DamageResults:
        """Solve building damage assessments for all neighboring buildings."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.dewatering is not None

        assessments: dict[str, DamageAssessment] = {}

        def dd_func(points: Any) -> np.ndarray:
            return compute_drawdown_at_points(points, self.dewatering, self.soil)

        for idx, building in enumerate(self.buildings):
            b_key = building.id if building.id else building.name or f"Building_{idx}"
            assessment = assess_building_damage(
                building,
                self.soil,
                self.dewatering,
                dd_func,
                settlement_method=self.settings.settlement_method,
            )
            assessments[b_key] = assessment

        return DamageResults(assessments=assessments)

    def solve(self) -> ProjectResults:
        """
        Execute full analysis workflow across hydraulics, stress, settlement, and damage models.

        Returns
        -------
        ProjectResults
            Aggregated frozen results container.
        """
        self._validate_ready_to_solve()

        hyd = self.solve_hydraulics()
        str_res = self.solve_stress()
        set_res = self.solve_settlement(hyd, str_res)
        dam_res = self.solve_damage(hyd, set_res)

        self._results = ProjectResults(
            hydraulics=hyd, stress=str_res, settlement=set_res, damage=dam_res
        )
        return self._results

    def plot_cross_section(self, building_idx: int = 0, **kwargs: Any) -> Any:
        """Generate cross-section visualization plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None
        b = self._get_building_required(building_idx)
        dd_b = compute_drawdown_at_points(
            np.array([[b.x, b.y]]), self.dewatering, self.soil
        )[0]
        return plotting.plot_cross_section(
            self.soil, self.pit, self.dewatering, b, dd_b, **kwargs
        )

    def plot_plan_view(self, building_idx: int = 0, **kwargs: Any) -> Any:
        """Generate plan-view visualization plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None

        if not self.results or not self.results.hydraulics or not self.results.damage:
            self.solve()

        assert self.results is not None
        assert self.results.hydraulics is not None
        assert self.results.damage is not None

        b = self._get_building_optional(building_idx)
        if b is not None:
            b_key = b.id if b.id else b.name or f"Building_{building_idx}"
            assessment = self.results.damage.assessments.get(
                b_key,
                list(self.results.damage.assessments.values())[0]
                if self.results.damage.assessments
                else None,
            )
        else:
            assessment = None

        return plotting.plot_plan_view(
            self.pit,
            self.dewatering,
            b,
            self.results.hydraulics.X_grid,
            self.results.hydraulics.Y_grid,
            self.results.hydraulics.drawdown_grid,
            assessment,
            **kwargs,
        )

    def plot_settlement_trough(self, building_idx: int = 0, **kwargs: Any) -> Any:
        """Generate 1D settlement trough visualization plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None

        b = self._get_building_required(building_idx)
        x_transect = np.linspace(-self.pit.length, b.x + b.length, 50)
        pts = np.column_stack((x_transect, np.zeros_like(x_transect)))
        drawdowns = compute_drawdown_at_points(pts, self.dewatering, self.soil)
        settlements = np.array(
            [
                compute_total_settlement(
                    self.soil, dd, method=self.settings.settlement_method
                )[0]
                for dd in drawdowns
            ]
        )
        return plotting.plot_settlement_trough(
            self.soil, self.dewatering, self.pit, b, x_transect, settlements, **kwargs
        )

    def plot_time_settlement(self, **kwargs: Any) -> Any:
        """Generate time-dependent consolidation settlement plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.dewatering is not None

        if (
            not self.results
            or not self.results.settlement
            or self.results.settlement.time_settlement_curve is None
        ):
            self.solve()

        assert self.results is not None
        assert self.results.settlement is not None
        assert self.results.settlement.times_days is not None
        assert self.results.settlement.time_settlement_curve is not None

        dict_corners = {"Center": self.results.settlement.time_settlement_curve}
        return plotting.plot_time_settlement(
            self.results.settlement.times_days,
            dict_corners,
            self.dewatering.pumping_duration_days,
            **kwargs,
        )

    def plot_effective_stress_profile(self, **kwargs: Any) -> Any:
        """Generate initial and final effective vertical stress profile plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None

        if not self.results or not self.results.stress:
            self.solve()

        assert self.results is not None
        assert self.results.stress is not None

        z = self.results.stress.z
        sig_0 = self.results.stress.sigma_v0_eff
        sig_final = sig_0 + self.results.stress.delta_sigma_v
        return plotting.plot_effective_stress_profile(
            self.soil, z, sig_0, sig_final, **kwargs
        )

    def plot_3d_drawdown(self, building_idx: int = 0, **kwargs: Any) -> Any:
        """Generate 3D drawdown surface plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None

        if not self.results or not self.results.hydraulics:
            self.solve()

        assert self.results is not None
        assert self.results.hydraulics is not None

        b = self._get_building_optional(building_idx)
        return plotting.plot_3d_drawdown(
            self.results.hydraulics.X_grid,
            self.results.hydraulics.Y_grid,
            self.results.hydraulics.drawdown_grid,
            self.pit,
            b,
            **kwargs,
        )

    def plot_3d_drawdown_mpl(self, **kwargs: Any) -> Any:
        """Generate Matplotlib 3D drawdown surface plot."""
        self._validate_ready_to_solve()
        assert self.soil is not None
        assert self.pit is not None
        assert self.dewatering is not None

        if not self.results or not self.results.hydraulics:
            self.solve()

        assert self.results is not None
        assert self.results.hydraulics is not None

        return plotting.plot_3d_drawdown_mpl(
            self.results.hydraulics.X_grid,
            self.results.hydraulics.Y_grid,
            self.results.hydraulics.drawdown_grid,
            self.pit,
            **kwargs,
        )

    def plot_damage_summary(self, building_idx: int = 0, **kwargs: Any) -> Any:
        """Generate building damage assessment summary plot."""
        self._validate_ready_to_solve()
        if not self.results or not self.results.damage:
            self.solve()

        assert self.results is not None
        assert self.results.damage is not None
        b = self._get_building_required(building_idx)
        b_key = b.id if b.id else b.name or f"Building_{building_idx}"
        assessment = self.results.damage.assessments.get(
            b_key,
            list(self.results.damage.assessments.values())[0]
            if self.results.damage.assessments
            else None,
        )
        if assessment is None:
            raise ValueError(f"No damage assessment found for building {b_key}.")

        return plotting.plot_damage_summary(assessment, **kwargs)
