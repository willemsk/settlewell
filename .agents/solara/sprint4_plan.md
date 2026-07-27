# Implementation Plan - Sprint 4: Solver Integration & Plotly Results Views

## Goal Description
Implement Sprint 4 of the Solara Web GUI for `settlewell`: Connect `settlewell.settlement` and `settlewell.models` solver routines to the Solara reactive store (`project_state`) and build the Right Viewport multi-tab results dashboard featuring 1D depth stress profiles, 2D Boussinesq stress ratio heatmaps, surface settlement bowls, layer settlement breakdown stacked bar charts, time-consolidation curves, and multi-scenario comparative overlays.

## Components & Files Created / Modified
- `src/settlewell/solara_app/state.py`: Implemented `run_fast_elastic_solve()` for 300ms debounced real-time preview and `run_full_consolidation_solve()` for deep numerical time-consolidation integration.
- `src/settlewell/solara_app/components/viewport/stress_plots.py`: `build_1d_stress_profile_fig` and `build_2d_stress_heatmap_fig` Plotly charts.
- `src/settlewell/solara_app/components/viewport/settlement_plots.py`: `build_surface_settlement_bowl_fig`, `build_layer_breakdown_fig`, and `build_time_consolidation_fig` Plotly charts in a 2x2 dashboard grid.
- `src/settlewell/solara_app/components/viewport/scenario_benchmark.py`: `build_scenario_comparison_fig` Plotly overlay chart and Delta Settlement Comparison Table.
- `src/settlewell/solara_app/components/viewport/__init__.py`: `ViewportContainer` assembling top Vuetify icon tabs (`📐 2D Canvas`, `📊 Stress`, `📉 Settlement`, `🔀 Benchmarks`), `solara.ProgressLinear`, and status bar solve triggers.
- `src/settlewell/solara_app/__init__.py`: Updated `Page()` layout to render `ViewportContainer()` in the right flex column.
- `tests/test_viewport_components.py`: TDD unit test suite.

## Verification Plan
- Unit tests: `uv run --extra web --extra gui --extra test pytest tests/test_viewport_components.py`
- Full test suite: `uv run --extra web --extra gui --extra test pytest tests/`
- Ruff linting & formatting: `uv run --with ruff ruff check --fix .` and `uv run --with ruff ruff format .`
- Chrome DevTools visual inspection: Verified multi-tab dashboard layout on `http://localhost:8767`.
