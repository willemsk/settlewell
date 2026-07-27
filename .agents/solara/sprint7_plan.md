# Implementation Plan - Sprint 7: Main Application Shell & End-to-End Testing

Complete the `settlewell` Solara Web GUI by enhancing the main application shell header toolbar (Scenario dropdown switcher, mTAW elevation datum unit toggle, `.settle` project file save/open controls), registering the `settlewell-web` CLI entry point, and adding a comprehensive end-to-end automated test suite (`test_e2e_solara_app.py`).

---

## User Review Required

> [!IMPORTANT]
> **Final Sprint Completion**
> Sprint 7 is the final sprint in the Solara Web GUI 7-sprint roadmap. It completes the application shell integration and full end-to-end test verification.

---

## Proposed Changes

### 1. Main Application Shell Header Bar & State Enhancements

#### [MODIFY] [state.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/state.py)
- Add reactive state flags: `display_elevation_mtaw = solara.reactive(False)`.
- Add state helper functions: `create_new_scenario()`, `duplicate_scenario(scenario_id)`, `switch_active_scenario(scenario_id)`, `set_elevation_display_mode(mtaw_enabled)`.
- Add JSON file import/export helper functions: `save_project_json()` and `load_project_json(json_content)`.

#### [MODIFY] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/__init__.py)
- Update `Page()` header bar:
  - Scenario Selector dropdown with `[➕ New Scenario]` and `[📋 Duplicate]` buttons.
  - Elevation Datum Unit Toggle: `[ Depth Z (m) | Elevation (mTAW) ]`.
  - Project Persistence Controls: `[ 📂 Open .settle ]` and `[ 💾 Save .settle ]`.
- Update `main()` to launch `solara.server.app.run(app_script="settlewell.solara_app.app:Page")`.

#### [MODIFY] [pyproject.toml](file:///d:/repos/bronbemaling/pyproject.toml)
- Ensure `settlewell-web = "settlewell.solara_app:main"` is registered in `[project.gui-scripts]`.

---

### 2. End-to-End Automated Testing

#### [NEW] [test_e2e_solara_app.py](file:///d:/repos/bronbemaling/tests/test_e2e_solara_app.py)
- Create comprehensive end-to-end user flow test:
  - `test_e2e_full_workflow()`: Validates initial project state, scenario creation & duplication, card updates (stratigraphy, loads, wells, buildings), elastic & consolidation solver execution, PDF/DXF/Excel file exports, and `.settle` JSON project state save/load serialization.

---

## Verification Plan

### Automated Tests
- Execute full test suite across all 13 test modules:
  ```bash
  uv run --extra web --extra gui --extra test pytest tests/
  ```

### Manual Verification & Visual Inspection
- Launch Solara dev server on port 8770:
  ```bash
  uv run --extra web solara run settlewell.solara_app.app --port 8770
  ```
- Use `chrome-devtools-mcp` to navigate to `http://localhost:8770`, test scenario switcher dropdown, toggle elevation datum units (Depth vs mTAW), click `Save .settle`, and take full-page screenshot verification.
