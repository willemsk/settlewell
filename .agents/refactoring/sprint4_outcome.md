# Sprint 4 Outcome: Settlewell Project Orchestrator

## 1. Overview
Sprint 4 implemented the top-level `Project` orchestrator class in `src/settlewell/project.py`. The `Project` class unifies all domain models, hydraulic and settlement physics solvers, building damage evaluation, visualization, preset soil template loading, and JSON file serialization into a clean, object-oriented API.

## 2. Key Accomplishments

### 2.1 Result Models & Data Model (`src/settlewell/project.py`)
- Created frozen Pydantic result containers (`BaseModelFrozen`):
  - `HydraulicsResults`: Transmissivity ($T$), storativity ($S$), radius of influence ($R$), 2D grid mesh $(X, Y)$ and drawdown array.
  - `StressResults`: Depths ($z$), initial effective vertical stress profile ($\sigma_{v0}'$), and load stress increments ($\Delta \sigma_v$).
  - `SettlementResults`: Total primary settlement, per-layer breakdown, time array, and time-settlement consolidation curves.
  - `DamageResults`: Dictionary mapping building identifiers to `DamageAssessment` objects.
  - `ProjectResults`: Top-level aggregated container holding all component calculation results.
- Created `ProjectDataModel`: Pydantic model for JSON dictionary serialization.

### 2.2 `Project` Orchestrator Class (`src/settlewell/project.py`)
- **Properties & Validation**: Getter/setter properties for `soil`, `pit`, `dewatering`, `buildings`, `loads`, and `settings`. Automatically invalidates cached results (`_results = None`) and enforces cross-dependency validation (raising `ValueError` if `dewatering.original_gwl_mtaw > soil.surface_level_mtaw`).
- **Serialization**: Added `to_dict()`, `from_dict()`, `save(path)`, and `load(path)` for saving and restoring project state to/from JSON files.
- **Flemish Template Loader**: Added `Project.from_template(template_name, gwl_mtaw, surface_level_mtaw)` classmethod initializing Flemish soil profiles from standard geological presets.
- **Solver Orchestration**: Added `solve_hydraulics()`, `solve_stress()`, `solve_settlement()`, `solve_damage()`, and `solve()`.
- **Plotting Wrappers**: Added plot wrappers delegating directly to `settlewell.plotting`: `plot_cross_section()`, `plot_plan_view()`, `plot_settlement_trough()`, `plot_time_settlement()`, `plot_effective_stress_profile()`, `plot_3d_drawdown()`, `plot_3d_drawdown_mpl()`, and `plot_damage_summary()`.

### 2.3 Package Exports & Documentation
- Updated [`src/settlewell/__init__.py`](file:///d:/repos/bronbemaling/src/settlewell/__init__.py) to re-export `Project`, `ProjectResults`, `HydraulicsResults`, `StressResults`, `SettlementResults`, and `DamageResults`.
- Created [`docs/api/project.md`](file:///d:/repos/bronbemaling/docs/api/project.md) and updated `mkdocs.yml` navigation.

### 2.4 Test Suite & Verification (`tests/test_project.py`)
- Added 10 new comprehensive unit tests in `tests/test_project.py`:
  - `test_empty_init`
  - `test_property_setters_and_invalidation`
  - `test_cross_dependency_validation`
  - `test_solve_ready_check`
  - `test_full_solve_workflow`
  - `test_to_dict_and_from_dict`
  - `test_save_and_load_file`
  - `test_from_template_antwerp_boom_clay`
  - `test_from_template_invalid_raises`
  - `test_plotting_methods_run_without_error`
- Total project tests passing: **171 / 171** (`171 passed in 15.45s`).
