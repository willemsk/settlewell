# Implementation Plan - Sprint 3: Interactive 2D Subsoil Canvas Viewport

## Goal Description
Implement Sprint 3 of the Solara Web GUI for `settlewell`: an interactive 2D subsoil cross-section graphic viewport built using Plotly (`solara.FigurePlotly`), featuring USCS soil layer polygons, groundwater table dashed lines, foundation load polygons with downward stress arrows, ruler dimension annotations, Boussinesq stress bulb ratio contours, an overlay toolbar, and a side-by-side flex layout.

## Components & Files Created / Modified
- `src/settlewell/solara_app/components/canvas/canvas_toolbar.py`: Overlay toggle buttons (`Dimensions`, `USCS Colors`, `Stress Bulbs`, `Water Table`) and Mode toggle (`Edit Mode` vs. `Read-Only`).
- `src/settlewell/solara_app/components/canvas/subsoil_canvas.py`: `build_subsoil_cross_section_fig` Plotly figure construction and `@solara.component def SubsoilCanvas`.
- `src/settlewell/solara_app/components/canvas/__init__.py`: `SubsoilCanvasContainer` assembling toolbar and canvas.
- `src/settlewell/solara_app/app.py`: Standalone application runner script.
- `src/settlewell/solara_app/__init__.py`: Updated `Page()` layout side-by-side flex row.
- `src/settlewell/solara_app/components/drawer/`: Refactored `MetadataCard`, `StratigraphyTable`, `LoadsTable`, and `SolverMeshCard` to eliminate double card headers and squished row layouts.
- `pyproject.toml`: Added `anywidget>=0.9.0` optional web dependency.
- `tests/test_subsoil_canvas.py`: TDD unit test suite.

## Verification Plan
- Unit tests: `uv run --extra web --extra gui --extra test pytest tests/test_subsoil_canvas.py`
- Full test suite: `uv run --extra web --extra gui --extra test pytest tests/`
- Ruff linting & formatting: `uv run --with ruff ruff check --fix .` and `uv run --with ruff ruff format .`
- Chrome DevTools visual inspection: Verified layout on `http://localhost:8766`.
