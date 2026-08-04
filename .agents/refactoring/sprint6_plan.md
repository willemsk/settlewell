# Sprint 6 Implementation Plan: GUI Rewiring to Core API

## Execution Strategy: Parallel Subagents
This sprint will be executed by dispatching three parallel subagents to ensure deep focus and prevent model fatigue.

---

## Subagent 1: State & Schema Refactor

**Target Files:**
- `src/settlewell/solara_app/schemas.py`
- `src/settlewell/solara_app/state.py`

### ❌ Strict Deletions & Removals Checklist
- [ ] Delete duplicated enums: `LoadType`, `StressMethod`, `DrainageType`, `DesignApproach`, `AquiferType`, `BuildingType` from `schemas.py`.
- [ ] Delete duplicated schemas: `SoilLayerSchema`, `LoadGeometrySchema`, `SolverSettingsSchema`, `ProjectMetadataSchema`, `WaterTableSchema`, `WellSchema`, `ConstructionPitSchema`, `DewateringConfigSchema`, `BuildingSchema` from `schemas.py`.
- [ ] Delete conversion functions: `to_domain_soil_layer`, `from_domain_soil_layer` from `schemas.py`.
- [ ] Delete `SECONDS_PER_YEAR` from `schemas.py`.
- [ ] Delete `run_fast_elastic_solve`, `run_full_consolidation_solve`, `run_hydraulics_solve`, `run_building_damage_solve`, `_fadum_corner`, `_compute_load_delta_sigma` completely from `state.py`. Do not leave them behind.

### 🔨 Implementation Details

**`schemas.py`:**
Update `ScenarioSchema` and `ProjectState` to use the new core models.
```python
from pydantic import BaseModel, Field
from settlewell.project import Project

class ProjectState(BaseModel):
    """Root Pydantic schema for full GUI state representation."""
    version: str = Field(default="3.0")
    project: Project = Field(default_factory=Project)
    active_scenario_id: str = Field(default="baseline")
    edit_mode: bool = Field(default=True, description="Toggle canvas edit vs read-only mode")
    dark_mode: bool = Field(default=False, description="UI dark mode toggle")

    def get_active_scenario(self):
        """Return the currently active scenario from the core Project."""
        return self.project.get_scenario(self.active_scenario_id)
```
*(Note: `ScenarioSchema` is kept only if needed for specific GUI state, otherwise we rely directly on the core Project scenarios.)*

**`state.py`:**
Update `create_default_project_state` to initialize a core `Project`.
Update serialization to delegate to `Project`:
```python
def save_project_json() -> str:
    state = project_state.value
    return state.project.to_json()

def load_project_json(json_content: str) -> bool:
    try:
        from settlewell.project import Project
        loaded_project = Project.from_json(json_content)
        new_state = project_state.value.model_copy(deep=True)
        new_state.project = loaded_project
        new_state.active_scenario_id = loaded_project.scenarios[0].id if loaded_project.scenarios else "baseline"
        project_state.set(new_state)
        return True
    except Exception:
        import logging
        logging.exception("Failed to parse .settle project JSON content")
        return False
```
Update CRUD helpers (like `add_soil_layer`) to operate on `current_state.get_active_scenario()`.

---

## Subagent 2: Viewport Components Rewire

**Target Files:**
- `src/settlewell/solara_app/components/viewport/settlement_plots.py`
- `src/settlewell/solara_app/components/viewport/damage_plots.py`
- `src/settlewell/solara_app/components/viewport/hydraulics_plots.py`
- `src/settlewell/solara_app/components/viewport/stress_plots.py`

### ❌ Strict Deletions & Removals Checklist
- [ ] Delete all direct imports and calls to `run_fast_elastic_solve`, `run_full_consolidation_solve`, `run_hydraulics_solve`, and `run_building_damage_solve` in all plot components.
- [ ] Do not leave any legacy standalone solving logic in the viewport components.

### 🔨 Implementation Details
Replace direct calls to `run_*_solve()` with calls to `Project` methods. For `settlement_plots.py`:
```python
@solara.component
def SettlementPlotsView() -> solara.Element:
    state = project_state.value
    project = state.project
    
    # Run the core API solvers
    elastic_res = project.solve_elastic_settlement(scenario_id=state.active_scenario_id)
    consolidation_res = project.solve_consolidation(scenario_id=state.active_scenario_id)

    # Use the results dictionaries/objects returned by the core API
    fig_bowl = build_surface_settlement_bowl_fig(project.get_scenario(state.active_scenario_id), elastic_res)
    fig_breakdown = build_layer_breakdown_fig(project.get_scenario(state.active_scenario_id), consolidation_res)
    fig_time = build_time_consolidation_fig(project.get_scenario(state.active_scenario_id), consolidation_res)
```

---

## Subagent 3: GUI Tests Migration

**Target Files:**
- `tests/test_solara_state.py`
- `tests/test_e2e_solara_app.py`
- `tests/test_dewatering_damage_components.py`
- `tests/test_drawer_components.py`
- `tests/test_viewport_components.py`
- `tests/test_subsoil_canvas.py`

### ❌ Strict Deletions & Removals Checklist
- [ ] Delete `test_soil_layer_schema_validation` and `test_domain_soil_layer_conversion` from `test_solara_state.py`.
- [ ] Remove all mocks of `run_fast_elastic_solve` and legacy standalone functions across all test files.

### 🔨 Implementation Details
1. **`test_solara_state.py`**: Update `test_default_project_state_creation` and `test_state_modification_helpers` to verify changes through the core `Project` API.
2. **Component Tests**: Replace mocks with `Project.solve_elastic_settlement` etc. Update fixture data to use core models instead of GUI schemas.
3. **E2E Tests**: Ensure the initial state injection uses the updated `ProjectState` containing a core `Project`. Verify that UI interactions correctly trigger `Project.solve_*` methods.
