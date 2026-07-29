# Sprint 4 Implementation Plan: Settlewell Project Orchestrator

## 1. Goal
Build the `Project` orchestrator class that ties together all models, physics, plotting, and serialization into a single top-level API in `src/settlewell/project.py`.

## 2. Deliverables
1. `src/settlewell/project.py`
2. Update `src/settlewell/__init__.py`
3. `tests/test_project.py`
4. Adaptations in `src/settlewell/plotting.py` (if any are strictly required, though `Project` will mostly just wrap them)

---

## 3. Implementation Details

### 3.1 Frozen Pydantic Models for Results (`project.py`)

Add the following Pydantic models to encapsulate results. They must be `frozen=True`.

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any
import numpy as np

# We may need a custom config to allow arbitrary types like numpy arrays
class BaseModelFrozen(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

class HydraulicsResults(BaseModelFrozen):
    T: float
    S: float
    R: float
    # Arrays can be stored, though typically we might store grid shapes or flat arrays
    drawdown_grid: Optional[np.ndarray] = None
    X_grid: Optional[np.ndarray] = None
    Y_grid: Optional[np.ndarray] = None

class StressResults(BaseModelFrozen):
    # Placeholders for Sprint 2 load results
    z: np.ndarray
    sigma_v0_eff: np.ndarray
    delta_sigma_v: np.ndarray

class SettlementResults(BaseModelFrozen):
    total_settlement: float
    per_layer_settlements: list[float]
    time_settlement_curve: Optional[np.ndarray] = None
    times_days: Optional[np.ndarray] = None

class DamageResults(BaseModelFrozen):
    # From DamageAssessment
    assessments: dict[str, Any]  # map building ID or index to DamageAssessment

class ProjectResults(BaseModelFrozen):
    hydraulics: Optional[HydraulicsResults] = None
    stress: Optional[StressResults] = None
    settlement: Optional[SettlementResults] = None
    damage: Optional[DamageResults] = None
```

### 3.2 Helper Model for Serialization (`project.py`)

```python
from .models import SoilProfile, ConstructionPit, DewateringConfig, Building

class ProjectDataModel(BaseModel):
    """Pydantic model for JSON serialization of Project inputs."""
    soil: Optional[SoilProfile] = None
    pit: Optional[ConstructionPit] = None
    dewatering: Optional[DewateringConfig] = None
    buildings: list[Building] = Field(default_factory=list)
    loads: list[Any] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
```

### 3.3 The `Project` Class (`project.py`)

#### 3.3.1 Initialization and Properties

```python
import json
from .models import SoilProfile, ConstructionPit, DewateringConfig, Building
from .soils import FLEMISH_PROFILE_TEMPLATES, FLEMISH_SOIL_PRESETS, SoilLayer

class Project:
    def __init__(
        self,
        soil: Optional[SoilProfile] = None,
        pit: Optional[ConstructionPit] = None,
        dewatering: Optional[DewateringConfig] = None,
        buildings: Optional[list[Building]] = None,
        loads: Optional[list[Any]] = None,
        settings: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the Project.
        """
        self._soil = soil
        self._pit = pit
        self._dewatering = dewatering
        self._buildings = buildings or []
        self._loads = loads or []
        self._settings = settings or {}
        self._results: Optional[ProjectResults] = None

        self._validate_cross_dependencies()

    def _invalidate_results(self):
        """Algorithm: Set self._results = None."""
        self._results = None

    def _validate_cross_dependencies(self):
        """
        Algorithm:
        1. If self._soil and self._dewatering are both set:
           Assert self._dewatering.original_gwl_mtaw <= self._soil.surface_level_mtaw
        """
        if self._soil and self._dewatering:
            if self._dewatering.original_gwl_mtaw > self._soil.surface_level_mtaw:
                raise ValueError("original_gwl_mtaw cannot be above surface_level_mtaw")

    @property
    def soil(self) -> Optional[SoilProfile]:
        return self._soil

    @soil.setter
    def soil(self, value: Optional[SoilProfile]):
        self._soil = value
        self._validate_cross_dependencies()
        self._invalidate_results()

    # Repeat properties with setters for pit, dewatering, buildings, loads, settings
    # All setters must call self._invalidate_results() and self._validate_cross_dependencies()

    @property
    def results(self) -> Optional[ProjectResults]:
        return self._results
```

#### 3.3.2 Serialization Methods

```python
    def to_dict(self) -> dict:
        """
        Algorithm:
        1. Create ProjectDataModel with current properties.
        2. Return model_dump(mode='json').
        """
        model = ProjectDataModel(
            soil=self.soil,
            pit=self.pit,
            dewatering=self.dewatering,
            buildings=self.buildings,
            loads=self.loads,
            settings=self.settings
        )
        return model.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """
        Algorithm:
        1. Parse dict using ProjectDataModel.model_validate(data).
        2. Return cls(soil=model.soil, pit=model.pit, ...)
        """
        model = ProjectDataModel.model_validate(data)
        return cls(
            soil=model.soil,
            pit=model.pit,
            dewatering=model.dewatering,
            buildings=model.buildings,
            loads=model.loads,
            settings=model.settings
        )

    def save(self, path: str):
        """
        Algorithm:
        1. Write json.dumps(self.to_dict()) to path.
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'Project':
        """
        Algorithm:
        1. Read JSON from path.
        2. Return cls.from_dict(data)
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_template(cls, template_name: str, gwl_mtaw: float, surface_level_mtaw: float) -> 'Project':
        """
        Algorithm:
        1. Lookup template_name in FLEMISH_PROFILE_TEMPLATES.
        2. Build list of SoilLayer using FLEMISH_SOIL_PRESETS.
        3. Create SoilProfile(layers, gwl_mtaw, surface_level_mtaw).
        4. Return cls(soil=profile).
        """
        layers_data = FLEMISH_PROFILE_TEMPLATES[template_name]
        layers = []
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
                Eoed=preset["E_modulus"] * 1000, # MPa to kPa
                Cv=preset["Cv"],
                OCR=preset["ocr"]
            )
            layers.append(layer)
        profile = SoilProfile(layers=layers, gwl_mtaw=gwl_mtaw, surface_level_mtaw=surface_level_mtaw)
        return cls(soil=profile)
```

#### 3.3.3 Solve Methods

```python
    def _validate_ready_to_solve(self):
        """Algorithm: raise ValueError if soil, pit, or dewatering are None."""
        if not self.soil or not self.pit or not self.dewatering:
            raise ValueError("Soil, pit, and dewatering must be set before solving.")

    def solve_hydraulics(self) -> HydraulicsResults:
        """
        Algorithm:
        1. Extract mode from self.settings.get('hydraulics_mode', 'analytical').
        2. T = compute_transmissivity(self.soil, self.dewatering)
        3. S = compute_storativity(self.soil, self.dewatering)
        4. H0 = self.soil.total_depth - self.soil.gwl_depth
        5. R = compute_radius_of_influence(self.dewatering, T, H0)
        6. Compute grid drawdown:
           If mode == 'analytical':
               call compute_drawdown_grid(...)
           If mode == 'numerical':
               grid = create_grid(...)
               solve_steady_state(grid, self.dewatering, self.soil, self.pit)
               X_grid, Y_grid = np.meshgrid(grid.x, grid.y)
               drawdown_grid = H0 - grid.head
        7. Return HydraulicsResults(T=T, S=S, R=R, drawdown_grid, X_grid, Y_grid)
        """
        pass

    def solve_stress(self) -> StressResults:
        """
        Algorithm: placeholder for sprint 2.
        """
        return StressResults(z=np.array([]), sigma_v0_eff=np.array([]), delta_sigma_v=np.array([]))

    def solve_settlement(self, hyd_res: HydraulicsResults, str_res: StressResults) -> SettlementResults:
        """
        Algorithm:
        1. Calculate total settlement at pit center based on drawdown (and loads if any).
           drawdown = hyd_res.drawdown_grid at center (interpolate or use compute_drawdown_at_points).
        2. total, per_layer = compute_total_settlement(self.soil, drawdown, method='cc_cr')
        3. Return SettlementResults(total_settlement=total, per_layer_settlements=per_layer)
        """
        pass

    def solve_damage(self, hyd_res: HydraulicsResults, set_res: SettlementResults) -> DamageResults:
        """
        Algorithm:
        1. Iterate over self.buildings.
        2. For each, call assess_building_damage(...)
           Note: Need a drawdown_func wrapper that uses compute_drawdown_at_points (analytical) 
           or extract_drawdown_at_points (numerical).
        3. Return DamageResults with the dict of assessments.
        """
        pass

    def solve(self):
        """
        Algorithm:
        1. _validate_ready_to_solve()
        2. hyd = solve_hydraulics()
        3. str_res = solve_stress()
        4. set_res = solve_settlement(hyd, str_res)
        5. dam_res = solve_damage(hyd, set_res)
        6. self._results = ProjectResults(hydraulics=hyd, stress=str_res, settlement=set_res, damage=dam_res)
        """
        pass
```

#### 3.3.4 Plotting Wrappers

```python
    def plot_cross_section(self, building_idx: int = 0) -> Any:
        """
        Algorithm:
        1. Ensure self._results is not None.
        2. Check if building_idx is valid.
        3. Get drawdown at building.
        4. Call plotting.plot_cross_section(...)
        """
        pass
    
    # Similarly define plot_plan_view, plot_settlement_trough, plot_time_settlement, 
    # plot_effective_stress_profile, plot_3d_drawdown, plot_3d_drawdown_mpl, plot_damage_summary
```


### 3.4 Update `__init__.py`

```python
# In src/settlewell/__init__.py
# Add:
from .project import Project, ProjectResults, HydraulicsResults, SettlementResults, DamageResults, StressResults

__all__ = [
    "Project",
    "ProjectResults",
    "HydraulicsResults",
    "SettlementResults",
    "DamageResults",
    "StressResults",
    "AquiferType",
    "Building",
    "BuildingType",
    "ConstructionPit",
    "DewateringConfig",
    "SoilLayer",
    "SoilProfile",
    "Well",
    "__version__"
]
```


### 3.5 Test Plan (`tests/test_project.py`)

- **test_project_init_and_validation:** Test constructor with/without args. Test that setting `soil` after init triggers `_invalidate_results`. Test cross-validation error if `dewatering.gwl > soil.surface`.
- **test_solve_lifecycle:** Setup a mock soil, pit, dewatering. Call `solve()`. Assert `project.results` is populated. Modify `project.dewatering`. Assert `project.results is None`.
- **test_serialization:** Create project. Save to dict. Load from dict. Assert models match. Save to JSON file, load from JSON file.
- **test_from_template:** Call `Project.from_template("Antwerp Boom Clay Formation", 5.0, 10.0)`. Assert layers are populated correctly.
- **test_plotting_smoke:** Setup project, call `solve()`. Call `plot_cross_section()`, assert a figure object is returned (mock plotting internals if necessary to avoid slow tests, or just run them and assert type).

## 4. Verification
- `pytest tests/test_project.py -v`
- `ruff check src/settlewell/project.py`
- Check type hints with `mypy src/settlewell/project.py` (if mypy is used).
