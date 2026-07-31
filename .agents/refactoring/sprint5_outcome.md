# Sprint 5 Outcome: Test Suite Migration to `Project` API

## 1. Overview
Sprint 5 migrated and extended the `settlewell` test suite to use the top-level `Project` orchestrator API.

## 2. Key Accomplishments

### 2.1 Fixture Extension (`tests/conftest.py`)
- Added `standard_project` fixture initializing a complete `Project` with Flemish soil stratigraphy, 6-well dewatering configuration, construction pit, and neighboring building.

### 2.2 Integration Test Suite Migrations & Extensions
- **`tests/test_hydraulics.py`**: Added `TestProjectHydraulicsIntegration` verifying `solve_hydraulics()` grid shapes, transmissivity, storativity, and radius of influence.
- **`tests/test_settlement.py`**: Added `TestProjectSettlementIntegration` verifying `solve_settlement()` total settlement, per-layer breakdown, and time curves.
- **`tests/test_numerical.py`**: Added `TestProjectNumericalIntegration` verifying finite-difference numerical solving via `Project.settings.hydraulics_solver = "numerical"`.
- **`tests/test_damage.py`**: Added `TestProjectDamageIntegration` verifying `solve_damage()` building differential settlement, angular distortion, and SBR damage category.
- **`tests/test_plotting.py`**: Added `TestProjectPlottingIntegration` verifying all high-level `Project` plot wrappers (`plot_cross_section`, `plot_plan_view`, `plot_settlement_trough`, `plot_time_settlement`, `plot_effective_stress_profile`, `plot_3d_drawdown`, `plot_damage_summary`).
- **`tests/test_physics_convergence.py`**: Added `TestProjectConvergenceIntegration` testing numerical grid refinement convergence via `Project`.
- **`tests/test_remediation_physics.py`**: Added `test_project_remediation_physics_via_orchestrator()` validating soil layer permeability influence on Sichardt radius of influence.
- **`tests/test_flemish_soils.py`**: Added `test_project_from_template()` validating `Project.from_template()`.

## 3. Verification & Compliance
- **Total Tests Passing**: **181 / 181** (`181 passed in 17.66s`).
- **Linting & Formatting**: 100% clean (`ruff check` & `ruff format`).
