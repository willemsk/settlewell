# Sprint 5 Outcome: Test Suite Migration to `Project` API

## 1. Overview
Sprint 5 migrated the existing `settlewell` test suite to use the top-level `Project` orchestrator API, resolving legacy dependencies on internal calculation functions and GUI state schemas.

## 2. Key Accomplishments

### 2.1 Fixture Extension (`tests/conftest.py`)
- Added `standard_project` fixture initializing a complete `Project` with Flemish soil stratigraphy, 6-well dewatering configuration, construction pit, and neighboring building.

### 2.2 Test Suite Migrations
- **`tests/test_hydraulics.py`**: Rewrote grid computations, superposition, and edge-case tests to instantiate `Project` models and use `solve_hydraulics()`. Mathematical unit tests (`theis`, `thiem`) were preserved.
- **`tests/test_settlement.py`**: Replaced standalone calculations with `solve_settlement(hyd_res, str_res)`. Handled frozen Pydantic instances correctly by migrating from direct mutations (`well.Q = 0`) to `model_copy(update=...)`.
- **`tests/test_numerical.py`**: Migrated `solve_steady_state` calls to use `Project.solve_hydraulics` with `settings.hydraulics_solver='numerical'`.
- **`tests/test_damage.py`**: Replaced standalone `assess_building_damage` usages with `project.solve_damage()` and queried results from `project.results.damage.assessments`.
- **`tests/test_plotting.py`**: Replaced all standalone plot functions with `project.plot_*` equivalents.
- **`tests/test_physics_convergence.py`**: Removed extraction functions and replaced them with `Project` implementations, utilizing `scipy.interpolate.RegularGridInterpolator` for validations.
- **`tests/test_remediation_physics.py`**: Eliminated all `ScenarioSchema` and GUI state dependencies. Migrated to core `SoilProfile` and `DewateringConfig` models, unblocking Sprint 6.
- **`tests/test_flemish_soils.py`**: Added `test_project_from_template()` validating `Project.from_template()`.

## 3. Verification & Compliance
- **Total Tests Passing**: **180 / 180**
- **Linting & Formatting**: Clean (`ruff check` & `ruff format`).
