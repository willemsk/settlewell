# Implementation Plan - Sprint 1: Core Data Models & State Management for Solara Web GUI

This implementation plan details the implementation of **Sprint 1** for the modern Solara web GUI for `settlewell`. It establishes the foundational Pydantic v2 schemas, reactive state management store (`solara.reactive`), `.settle` JSON serialization/deserialization routines, domain dataclass conversion bridges, and dependency configuration.

## Resolved Architectural Decisions

During the initial design alignment, the following choices were confirmed:
1. **Package Placement:** Solara application code will live in `src/settlewell/solara_app/`.
2. **Schema Integration:** Pydantic v2 schemas in `src/settlewell/solara_app/schemas.py` with `to_domain()` and `from_domain()` methods for converting to/from `settlewell.models` dataclasses.
3. **File Format:** Direct `.settle` JSON specification with strict validation.
4. **Dependencies:** Added under `[project.optional-dependencies] web` in `pyproject.toml` alongside `settlewell-web` CLI entry point.
5. **State Architecture:** Unified `solara.reactive(ProjectState)` state store in `src/settlewell/solara_app/state.py`.

---

## Proposed Changes

### Configuration & Packaging

#### [MODIFY] [pyproject.toml](file:///d:/repos/bronbemaling/pyproject.toml)
* Add `web` optional dependencies:
  - `solara>=1.60.3`
  - `pydantic>=2.13.4`
  - `ipycanvas>=0.14.3`
  - `reportlab>=5.0.0`
  - `ezdxf>=1.4.4`
  - `openpyxl>=3.1.5`
* Add script entry point under `[project.gui-scripts]`:
  - `settlewell-web = "settlewell.solara_app:main"`

---

### Solara Web Application Core

#### [NEW] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/__init__.py)
* Expose package level entry points `Page` and `main()`.

#### [NEW] [schemas.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/schemas.py)
Contains complete Pydantic v2 data models for GUI state representation and domain mapping.

##### Data Model Specification:

```python
from enum import StrEnum
from typing import List, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator

class SoilTypeUSCS(StrEnum):
    SAND = "SAND"
    CLAY = "CLAY"
    GRAVEL = "GRAVEL"
    PEAT = "PEAT"

class LoadType(StrEnum):
    STRIP = "STRIP"
    RECTANGULAR = "RECTANGULAR"
    EMBANKMENT = "EMBANKMENT"
    POINT = "POINT"

class StressMethod(StrEnum):
    BOUSSINESQ = "BOUSSINESQ"
    WESTERGAARD = "WESTERGAARD"
    TWO_TO_ONE = "2:1"

class SoilLayerSchema(BaseModel):
    id: str = Field(description="Unique layer identifier")
    name: str = Field(default="New Layer", description="Descriptive layer name")
    thickness: float = Field(gt=0, default=3.0, description="Layer thickness in meters [m]")
    gamma_dry: float = Field(gt=0, default=17.0, description="Dry unit weight [kN/m³]")
    gamma_sat: float = Field(gt=0, default=19.0, description="Saturated unit weight [kN/m³]")
    e0: float = Field(ge=0, default=0.65, description="Initial void ratio [-]")
    E_modulus: float = Field(gt=0, default=15.0, description="Elastic modulus [MPa]")
    Cc: float = Field(ge=0, default=0.15, description="Compression index [-]")
    Cr: float = Field(ge=0, default=0.03, description="Recompression index [-]")
    Cv: float = Field(ge=0, default=5.0, description="Coefficient of consolidation [m²/yr]")
    uscs_type: SoilTypeUSCS = Field(default=SoilTypeUSCS.SAND, description="USCS soil classification")
    color: str = Field(default="#f59e0b", description="Hex color code for visualization")

    @field_validator("gamma_sat")
    def validate_gamma_sat(cls, v: float, info: ValidationInfo) -> float:
        gamma_dry = info.data.get("gamma_dry", 0.0)
        if v < gamma_dry:
            raise ValueError(f"Saturated unit weight ({v}) cannot be less than dry unit weight ({gamma_dry})")
        return v

class LoadGeometrySchema(BaseModel):
    id: str = Field(description="Unique load identifier")
    name: str = Field(default="Footing Load", description="Load name")
    type: LoadType = Field(default=LoadType.RECTANGULAR)
    x_center: float = Field(default=0.0, description="X coordinate of load center [m]")
    z_surface_offset: float = Field(default=0.0, description="Depth offset from surface [m]")
    width_B: float = Field(gt=0, default=4.0, description="Footing width B [m]")
    length_L: float = Field(gt=0, default=8.0, description="Footing length L [m]")
    stress_q: float = Field(gt=0, default=100.0, description="Applied uniform stress q [kPa]")

class SolverSettingsSchema(BaseModel):
    stress_method: StressMethod = Field(default=StressMethod.BOUSSINESQ)
    z_max: float = Field(gt=0, default=20.0, description="Maximum calculation depth [m]")
    delta_z: float = Field(gt=0, default=0.25, description="Vertical mesh step size [m]")
    x_min: float = Field(default=-15.0, description="Left grid boundary [m]")
    x_max: float = Field(default=15.0, description="Right grid boundary [m]")
    t_start_days: float = Field(ge=1.0, default=1.0, description="Start time for consolidation [days]")
    t_end_years: float = Field(gt=0, default=50.0, description="End time for consolidation [years]")
    calculate_creep: bool = Field(default=True, description="Enable secondary creep C_alpha calculation")

class ProjectMetadataSchema(BaseModel):
    title: str = Field(default="Untitled Settlement Analysis")
    engineer: str = Field(default="Geotechnical Engineer")
    date: str = Field(default="2026-07-24")
    units: str = Field(default="metric")
    comments: Optional[str] = Field(default=None)

class WaterTableSchema(BaseModel):
    depth_z: float = Field(ge=0, default=2.0, description="Groundwater depth below surface [m]")

class ScenarioSchema(BaseModel):
    id: str = Field(description="Unique scenario ID")
    name: str = Field(default="Baseline Scenario")
    is_active: bool = Field(default=True)
    water_table: WaterTableSchema = Field(default_factory=WaterTableSchema)
    stratigraphy: List[SoilLayerSchema] = Field(default_factory=list)
    loads: List[LoadGeometrySchema] = Field(default_factory=list)
    solver_settings: SolverSettingsSchema = Field(default_factory=SolverSettingsSchema)

class ProjectState(BaseModel):
    version: str = Field(default="2.0")
    metadata: ProjectMetadataSchema = Field(default_factory=ProjectMetadataSchema)
    scenarios: List[ScenarioSchema] = Field(default_factory=list)
    active_scenario_id: str = Field(default="baseline")
    edit_mode: bool = Field(default=True, description="Toggle canvas edit vs read-only mode")
    dark_mode: bool = Field(default=False, description="UI dark mode toggle")

    def get_active_scenario(self) -> ScenarioSchema:
        for s in self.scenarios:
            if s.id == self.active_scenario_id:
                return s
        if self.scenarios:
            return self.scenarios[0]
        # Return default scenario if list empty
        default_sc = ScenarioSchema(id="baseline", name="Baseline Model")
        self.scenarios.append(default_sc)
        return default_sc
```

##### Conversion Routines (`schemas.py`):
- `to_domain_soil_layer(schema: SoilLayerSchema) -> SoilLayer`
  Maps `SoilLayerSchema` fields to `settlewell.models.SoilLayer` (with unit conversions e.g. `E_modulus` MPa to kPa `Eoed = E_modulus * 1000.0`, `Cv` m²/yr to m²/s `Cv_sec = Cv / (365.25 * 86400)`).
- `from_domain_soil_layer(layer: SoilLayer) -> SoilLayerSchema`
  Converts `settlewell.models.SoilLayer` back into `SoilLayerSchema`.

---

#### [NEW] [state.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/state.py)
Implements reactive state management and serialization.

##### Key Functions & Variables:

```python
import json
from pathlib import Path
import solara
from .schemas import ProjectState, ScenarioSchema, SoilLayerSchema, LoadGeometrySchema

# Global Reactive State
project_state: solara.Reactive[ProjectState] = solara.reactive(create_default_project_state())

def create_default_project_state() -> ProjectState:
    """Instantiate default initial ProjectState with Baseline scenario."""
    ...

def load_project_from_file(file_path: Path | str) -> None:
    """Read .settle JSON file, parse into ProjectState, and update reactive store.
    
    Algorithm:
    1. Read JSON file content UTF-8.
    2. Parse into ProjectState via ProjectState.model_validate_json(content).
    3. Update project_state.set(new_state).
    """
    ...

def save_project_to_file(file_path: Path | str) -> None:
    """Serialize current reactive project_state to .settle JSON file.
    
    Algorithm:
    1. json_data = project_state.value.model_dump_json(indent=2)
    2. Write json_data to file_path.
    """
    ...

def add_soil_layer(layer: Optional[SoilLayerSchema] = None) -> None:
    """Add a new soil layer to active scenario in project_state."""
    ...

def update_soil_layer(layer_id: str, updated_layer: SoilLayerSchema) -> None:
    """Update an existing soil layer by ID in active scenario."""
    ...

def delete_soil_layer(layer_id: str) -> None:
    """Delete soil layer by ID from active scenario."""
    ...

def add_load(load: Optional[LoadGeometrySchema] = None) -> None:
    """Add a new load definition to active scenario."""
    ...

def delete_load(load_id: str) -> None:
    """Delete a load definition by ID."""
    ...

def add_scenario(name: str) -> str:
    """Duplicate active scenario as a new scenario and set as active."""
    ...
```

---

### Automated Verification

#### [NEW] [test_solara_state.py](file:///d:/repos/bronbemaling/tests/test_solara_state.py)
Automated unit tests using `pytest` verifying:
1. `ProjectState` default initialization and schema validation rules.
2. Soil layer saturated unit weight validation constraint (`gamma_sat >= gamma_dry`).
3. Conversion of `SoilLayerSchema` to/from `settlewell.models.SoilLayer`.
4. `.settle` JSON serialization and deserialization cycle (`save_project_to_file` and `load_project_from_file`).
5. Reactive state helper methods (`add_soil_layer`, `update_soil_layer`, `delete_soil_layer`, `add_scenario`).

---

## Verification Plan

### Automated Tests
- Run `uv run pytest tests/test_solara_state.py` to verify schema validation, JSON serialization/deserialization, and state modification helpers.
- Run `uv run pytest tests/` to confirm no regression in existing domain model tests.
- Run `uv run --with ruff ruff check --fix .` and `uv run --with ruff ruff format .` for linting and formatting compliance.

### Manual Verification
- Verify importability of `from settlewell.solara_app.schemas import ProjectState` and `from settlewell.solara_app.state import project_state`.
