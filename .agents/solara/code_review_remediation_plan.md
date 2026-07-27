# Implementation Plan - Code Review Remediation & Geotechnical Solver Refinement

Remediate ALL findings from the code review across geotechnical physics solvers, schema definitions, input debouncing, building damage coupling, PDF generation, and automated test assertions.

---

## User Review Required

> [!IMPORTANT]
> **Geotechnical Solver Enhancements**
> - **OCR & Preconsolidation:** Implements recompression index $C_r$ below preconsolidation stress $\sigma'_p = \text{OCR} \cdot \sigma'_{v0}$ and virgin compression $C_c$ above $\sigma'_p$.
> - **Explicit $k_h$ Hydraulic Conductivity:** Adds explicit $k_h$ [m/s] to `SoilLayerSchema` with USCS auto-defaults for Sichardt radius $R$ and transmissivity $T$.
> - **3D Rectangular Boussinesq Stress:** Implements Fadum's analytical corner integration formula for 3D rectangular loads ($B \times L$).
> - **Coupled Building Damage:** Samples actual calculated surface settlement trough $s(x)$ under building coordinates.
> - **Drainage Condition & Layered $C_v$:** Adds Double vs. Single drainage toggle and weighted harmonic mean $C_{v,\text{eq}}$.

---

## Proposed Changes

### 1. Pydantic Schemas & Data Models

#### [MODIFY] [schemas.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/schemas.py)
- Add `DrainageType` enum (`DOUBLE = "DOUBLE"`, `SINGLE = "SINGLE"`).
- Extend `SoilLayerSchema`:
  - `ocr: float = Field(ge=1.0, default=1.0, description="Overconsolidation ratio [-]")`
  - `k_h: float = Field(gt=0, default=1e-4, description="Hydraulic conductivity [m/s]")`
- Extend `SolverSettingsSchema`:
  - `drainage: DrainageType = Field(default=DrainageType.DOUBLE, description="Drainage boundary condition")`

---

### 2. State Management & Physics Solver Engine

#### [MODIFY] [state.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/state.py)
- **3D Boussinesq Stress (`run_fast_elastic_solve`):**
  - Implement `_boussinesq_rectangular_fadum(q, B, L, x, y, z)` using Fadum's corner integration.
  - Retain `_boussinesq_strip(q, B, x, z)` for 2D strip footings.
- **Overconsolidation Settlement (`run_full_consolidation_solve`):**
  - Compute $\sigma'_p = \text{OCR} \cdot \sigma'_{v0}$.
  - Calculate recompression settlement using $C_r$ when $\sigma'_f \le \sigma'_p$, and combined $C_r + C_c$ when $\sigma'_f > \sigma'_p$.
  - Calculate equivalent consolidation coefficient $C_{v,\text{eq}} = \frac{H_{\text{total}}^2}{\left( \sum_i \frac{h_i}{\sqrt{C_{v,i}}} \right)^2}$.
  - Apply $H_{dr} = H_{\text{total}} / 2$ for double drainage and $H_{dr} = H_{\text{total}}$ for single drainage.
- **Hydraulics Drawdown (`run_hydraulics_solve`):**
  - Use explicit layer $k_h$ for Sichardt radius $R = 3000 \cdot s \cdot \sqrt{k_h}$ and transmissivity $T = \sum k_{h,i} d_{\text{sat},i}$.
- **Coupled Building Damage (`run_building_damage_solve`):**
  - Interpolate actual calculated surface settlement bowl $s(x)$ at $x_{\text{left}} = x_{\text{bldg}} - L/2$ and $x_{\text{right}} = x_{\text{bldg}} + L/2$.
- **Error Logging (`load_project_json`):**
  - Add `logging.exception("Failed to load project JSON")`.

---

### 3. Left Accordion Drawer Cards & Debouncing

#### [MODIFY] [stratigraphy_table.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/stratigraphy_table.py)
- Expose `OCR [-]` and `k_h [m/s]` input fields.
- Auto-update default $k_h$ when USCS classification is changed (`SAND` $\to 10^{-4}$, `CLAY` $\to 10^{-8}$, `GRAVEL` $\to 10^{-2}$, `PEAT` $\to 10^{-5}$).

#### [MODIFY] [solver_mesh_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/solver_mesh_card.py)
- Expose Drainage Condition select dropdown (`Double Drainage` vs `Single Drainage`).

#### [MODIFY] [metadata_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/metadata_card.py)
- Add `continuous_update=False` to `solara.SliderFloat` to prevent continuous solver triggering during slider drag.

---

### 4. Viewport Components & Report Deliverables

#### [MODIFY] [damage_plots.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/damage_plots.py)
- Update `build_building_settlement_profile_fig` to plot actual calculated surface settlement profile $s(x)$ under the building foundation.

#### [MODIFY] [pdf_generator.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/pdf_generator.py)
- Replace hardcoded date string with dynamic date `scenario.metadata.date` or current date `datetime.now().strftime("%Y-%m-%d")`.
- Include OCR and $k_h$ columns in PDF stratigraphy table.

---

## Verification Plan

### Automated Tests
- Create / Update unit tests:
  - `test_ocr_consolidation_settlement()`: Verify $C_r$ recompression vs $C_c$ virgin consolidation calculations against hand-calculated benchmark values.
  - `test_3d_fadum_rectangular_stress()`: Verify Fadum corner stress coefficients against analytical benchmarks.
  - `test_explicit_kh_hydraulics()`: Verify Sichardt radius and transmissivity with explicit $k_h$.
  - `test_coupled_building_damage()`: Verify building settlement interpolation from calculated surface bowl.
- Execute full test suite:
  ```bash
  uv run --extra web --extra gui --extra test pytest tests/
  ```

### Manual Verification & Visual Inspection
- Launch Solara dev server on port 8771:
  ```bash
  uv run --extra web solara run settlewell.solara_app.app --port 8771
  ```
- Use `chrome-devtools-mcp` to inspect OCR, $k_h$, and coupled building damage visuals.
