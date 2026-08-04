# Sprint 6 Implementation Outcome

This document summarizes the changes made to fix the regressions discovered in Sprint 6.

## 1. Domain Model Purity & Validation
*   Removed GUI-specific alias fields (`x_center`, `structural_type`) and `_remap_gui_fields` logic from the core domain `Building` model in `src/settlewell/models.py`.
*   Introduced `BuildingSchema` in `src/settlewell/solara_app/schemas.py` that inherits from the core `Building` model but implements the necessary GUI-specific field aliases using a `@model_validator(mode="before")`. 
*   Updated `ScenarioSchema` to use `list[BuildingSchema]` and initialized UI state elements with `BuildingSchema` explicitly to prevent Pydantic validation errors during serialization and UI updates.

## 2. UI Plots Restoration
*   Expanded `SettlementResults` in `src/settlewell/project.py` to include `elastic_settlement`, `primary_settlement`, `creep_settlement`, `per_layer_elastic`, `per_layer_creep`, and `degree_of_consolidation_curve`.
*   Updated `solve_settlement()` inside `project.py` to calculate these missing elements by invoking `compute_elastic_settlement`, `compute_total_settlement`, `compute_full_consolidation_curve`, and `compute_secondary_creep`.
*   Updated `build_layer_breakdown_fig` in `settlement_plots.py` to correctly utilize `per_layer_elastic`, `per_layer_settlements` (primary consolidation), and `per_layer_creep` to restore the stacked bar charts breakdown per layer.
*   Updated `build_time_consolidation_fig` to plot the `degree_of_consolidation_curve` ($U$) against a secondary Y-axis, bringing back the crucial consolidation percentage curve to the time-dependent plots.

## 3. File Interoperability (.settle File Export)
*   Refactored the `.settle` export functionality inside `src/settlewell/solara_app/state.py`. 
*   `save_project_json()` now calls `active_sc.to_project()` and initializes a `ProjectDataModel` with the active project's fields, ensuring only the core domain model arrays (e.g. `dewatering`, `soil`, `pit`, `buildings`) are stored without any UI metadata or multiple unused scenarios. 
*   `load_project_json()` reconstructs the `ScenarioSchema` using the imported `ProjectDataModel` and accurately applies `BuildingSchema` parsing to the imported buildings collection, making older and newer `.settle` files completely interoperable.
*   Updated the tests in `test_solara_state.py` to assert against default metadata since GUI metadata is no longer preserved inside `.settle` exports.

## Verification
*   Tests in `test_elastic_settlement.py`, `test_settlement.py`, `test_solara_state.py`, and `test_e2e_solara_app.py` were modernized to support these API changes.
*   Full `pytest` suite passes with `0` failures!
