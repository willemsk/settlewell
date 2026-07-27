# Sprint 3 Outcome: Interactive 2D Subsoil Canvas Viewport

## Summary of Accomplishments
Sprint 3 successfully delivers the interactive 2D subsoil cross-section graphic viewport, complete with Plotly figure generation, USCS soil layer polygons, groundwater table line visualization, foundation load polygons with downward stress arrows, dimension annotations, stress bulb iso-contours, toolbar toggles, and side-by-side flex layout integration.

---

## Technical Details

### 1. 2D Subsoil Cross-Section Canvas Component
- **`build_subsoil_cross_section_fig()`** in [subsoil_canvas.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/canvas/subsoil_canvas.py):
  - Renders soil layer polygons with USCS color mapping (Sand Ochre `#f59e0b`, Clay Brown `#854d0e`, Gravel Slate `#64748b`, Peat Dark `#451a03`).
  - Displays groundwater table dashed cyan line ($z_{gw}$) with depth markers.
  - Draws red concrete footing block polygons with downward stress arrows for applied surface loads.
  - Renders Boussinesq stress bulb ratio contours ($\Delta\sigma_z / q = 0.8, 0.5, 0.2, 0.1$).
  - Configures rich hover tooltips in Read-Only Mode showing local soil parameters ($h, \gamma_{\text{dry}}, \gamma_{\text{sat}}, E, e_0, C_c, C_r, C_v$).

### 2. Canvas Toolbar & Layout Polish
- **`CanvasToolbar`** in [canvas_toolbar.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/canvas/canvas_toolbar.py): Multi-select toggle buttons for overlays and single-select toggle buttons for Edit Mode vs. Read-Only Mode.
- **Refactored Left Drawer Cards** in [components/drawer/](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/): Removed double card wrappers and redesigned stratigraphy and loads tables into structured, un-squished per-element cards.
- **App Entrypoint & Side-by-Side Flex Layout:** Updated [solara_app/app.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/app.py) and [solara_app/__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/__init__.py).

---

## Verification & Compliance
- **Unit Tests:** 116 passing tests in full test suite (`pytest tests/`).
- **DevTools Visual Inspection:** Screenshot verified clean layout rendering on `http://localhost:8766`.
- **Ruff Compliance:** Clean linting and formatting (`ruff check --fix`, `ruff format`).
