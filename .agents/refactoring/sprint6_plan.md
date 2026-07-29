# Sprint 6 Implementation Plan: GUI Rewiring to Core API

## 1. schemas.py
**File path:** `d:\repos\bronbemaling\src\settlewell\solara_app\schemas.py`

### What to Delete
- Delete duplicated enums: `LoadType`, `StressMethod`, `DrainageType`, `DesignApproach`, `AquiferType`, `BuildingType`.
- Delete duplicated schemas: `SoilLayerSchema`, `LoadGeometrySchema`, `SolverSettingsSchema`, `ProjectMetadataSchema`, `WaterTableSchema`, `WellSchema`, `ConstructionPitSchema`, `DewateringConfigSchema`, `BuildingSchema`.
- Delete conversion functions: `to_domain_soil_layer`, `from_domain_soil_layer`.
- Delete `SECONDS_PER_YEAR`.

### What to Add / Update
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

# Note: ScenarioSchema is kept only if needed for specific GUI state, 
# otherwise we rely directly on the core Project scenarios. 
# Based on the instructions, if we keep ScenarioSchema it wraps core models:
class ScenarioSchema(BaseModel):
    # This might be deprecated if Project handles scenarios internally.
    pass
```
*Note: Since `ProjectState` will now hold a `Project` instance which manages its own scenarios, the `scenarios` list in `ProjectState` should be delegated to `Project`. Adjust imports as necessary based on the core API structure.*

---

## 2. state.py
**File path:** `d:\repos\bronbemaling\src\settlewell\solara_app\state.py`

### What to Delete
Remove the following functions completely:
- `run_fast_elastic_solve`
- `run_full_consolidation_solve`
- `run_hydraulics_solve`
- `run_building_damage_solve`
- `_fadum_corner`
- `_compute_load_delta_sigma`

### What to Add / Update
Update `create_default_project_state` to initialize a core `Project`.
Update serialization to delegate to `Project`:

```python
def save_project_json() -> str:
    """Serialize project state to .settle JSON format string."""
    # Assuming Project has a to_json() or dump_json() method
    state = project_state.value
    return state.project.to_json()

def load_project_json(json_content: str) -> bool:
    """Load project state from .settle JSON string."""
    try:
        from settlewell.project import Project
        loaded_project = Project.from_json(json_content)
        new_state = project_state.value.model_copy(deep=True)
        new_state.project = loaded_project
        # Reset active scenario if needed
        new_state.active_scenario_id = loaded_project.scenarios[0].id if loaded_project.scenarios else "baseline"
        project_state.set(new_state)
        return True
    except Exception:
        import logging
        logging.exception("Failed to parse .settle project JSON content")
        return False
```

Update CRUD helpers to operate on `Project` properties.
Example for `add_soil_layer`:

```python
def add_soil_layer(layer=None) -> None:
    """Add a soil layer to the active scenario in project_state."""
    from settlewell.models import SoilLayer
    current_state = project_state.value.model_copy(deep=True)
    active_sc = current_state.get_active_scenario()
    
    if layer is None:
        new_idx = len(active_sc.stratigraphy) + 1
        layer = SoilLayer(
            id=f"layer_{new_idx}",
            name=f"Soil Layer {new_idx}",
            thickness=3.0,
            gamma=17.0,
            gamma_sat=19.0,
            e0=0.65,
            Eoed=15000.0,
            Cc=0.15,
            Cr=0.03,
            Cv=5.0 / (365.25 * 86400),
            k_h=1e-4,
            OCR=1.0
        )
    
    active_sc.add_soil_layer(layer)
    project_state.set(current_state)
```

---

## 3. Viewport components
**Files to update:** 
- `d:\repos\bronbemaling\src\settlewell\solara_app\components\viewport\settlement_plots.py`
- `damage_plots.py`, `hydraulics_plots.py`, `stress_plots.py` (similarly)

### Update Instructions
Replace direct calls to `run_*_solve()` with calls to `Project` methods.
For `settlement_plots.py`:

```python
# Remove imports for run_fast_elastic_solve, run_full_consolidation_solve
# Update SettlementPlotsView:

@solara.component
def SettlementPlotsView() -> solara.Element:
    """Render 2x2 dashboard grid for settlement bowl, layer breakdown, and time-consolidation."""
    state = project_state.value
    project = state.project
    
    # Run the core API solvers
    elastic_res = project.solve_elastic_settlement(scenario_id=state.active_scenario_id)
    consolidation_res = project.solve_consolidation(scenario_id=state.active_scenario_id)

    # Use the results dictionaries/objects returned by the core API
    # Note: ensure build_*_fig functions extract data from the new results structure.
    fig_bowl = build_surface_settlement_bowl_fig(project.get_scenario(state.active_scenario_id), elastic_res)
    fig_breakdown = build_layer_breakdown_fig(project.get_scenario(state.active_scenario_id), consolidation_res)
    fig_time = build_time_consolidation_fig(project.get_scenario(state.active_scenario_id), consolidation_res)

    # ... rest remains the same
```
*Note: Adjust `build_surface_settlement_bowl_fig` and others to read from the core API results structure (e.g. `elastic_res.elastic_settlement_mm` if it returns an object rather than a dict).*

---

## 4. GUI tests
**Files to update:**
- `d:\repos\bronbemaling\tests\test_solara_state.py`
- `d:\repos\bronbemaling\tests\test_e2e_solara_app.py`
- `d:\repos\bronbemaling\tests\test_dewatering_damage_components.py`
- `d:\repos\bronbemaling\tests\test_drawer_components.py`
- `d:\repos\bronbemaling\tests\test_viewport_components.py`
- `d:\repos\bronbemaling\tests\test_subsoil_canvas.py`

### Update Instructions
1. **test_solara_state.py**:
   - Remove `test_soil_layer_schema_validation` and `test_domain_soil_layer_conversion`.
   - Update `test_default_project_state_creation` to check the core `Project` instance.
   - Update `test_state_modification_helpers` to verify changes through the core `Project` API.
2. **Component Tests (`test_dewatering_damage_components.py`, `test_drawer_components.py`, `test_viewport_components.py`, `test_subsoil_canvas.py`)**:
   - Replace mocks of `run_fast_elastic_solve` and others with mocks of `Project.solve_elastic_settlement` etc.
   - Update fixture data to use core models instead of GUI schemas.
3. **E2E Tests (`test_e2e_solara_app.py`)**:
   - Ensure the initial state injection uses the updated `ProjectState` containing a core `Project`.
   - Verify that UI interactions correctly trigger `Project.solve_*` methods and update the canvas/plots.
