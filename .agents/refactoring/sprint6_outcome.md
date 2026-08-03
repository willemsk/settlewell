# Sprint 6 Outcome: Solara GUI Rewire to Core Project API

## Summary of Accomplishments

Sprint 6 successfully rewired the Solara web application front-end (`src/settlewell/solara_app/`) to directly leverage the core `Project` orchestrator API (`settlewell.project.Project`), eliminating all duplicated Pydantic schema definitions and legacy wrapper solver functions.

### Key Changes
1. **Schema & State Refactoring (`src/settlewell/solara_app/schemas.py` & `state.py`)**:
   - Removed duplicated GUI model schemas (`SoilLayerSchema`, `BuildingSchema`, `WellSchema`, `LoadGeometrySchema`, `SolverSettingsSchema`, `WaterTableSchema`).
   - Re-exported core domain models directly from `settlewell.models` with alias compatibility.
   - Refactored `ScenarioSchema` as a clean wrapper around `Project` with a `.to_project()` factory method.
   - Deleted legacy solver functions (`run_fast_elastic_solve`, `run_full_consolidation_solve`, `run_hydraulics_solve`, `run_building_damage_solve`, `_fadum_corner`, `_compute_load_delta_sigma`).

2. **Viewport Components Rewire (`src/settlewell/solara_app/components/viewport/`)**:
   - `settlement_plots.py`: Switched calculations to `project.solve()`.
   - `damage_plots.py`: Switched damage classification and foundation settlement profile rendering to `project.solve()`.
   - `hydraulics_plots.py`: Switched drawdown contour heatmaps and radial profiles to `project.solve_hydraulics()`.
   - `stress_plots.py`: Switched vertical stress depth curves and Boussinesq heatmaps to `project.solve()`.
   - `scenario_benchmark.py`: Switched multi-scenario comparisons to `sc.to_project().solve()`.
   - `data_exporter.py`: Switched Excel (.xlsx) and CSV export generation to `scenario.to_project().solve()`.
   - `viewport/__init__.py`: Switched real-time status bar calculation to `active_sc.to_project().solve()`.

3. **Test Suite Migration & Verification**:
   - Migrated all Solara GUI unit tests (`test_solara_state.py`, `test_dewatering_damage_components.py`, `test_viewport_components.py`, `test_flemish_soils.py`, `test_export_engine.py`, `test_e2e_solara_app.py`) to use `Project` API.
   - Added backward compatibility aliases (`gamma_dry`, `E_modulus`, `ocr`, `x_center`, `structural_type`, `risk_category_name`).
   - Executed `ruff check --fix .` and `ruff format .`.
   - Verified that all 177 tests pass cleanly (`177 passed in 17.23s`).
