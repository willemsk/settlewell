# Implementation Plan - Sprint 5: Dewatering Hydraulics, Construction Pit & Building Damage Analysis

Connect `settlewell.hydraulics` (Dupuit-Thiem, Theis well drawdown, Sichardt radius of influence $R$) and `settlewell.damage` (differential settlement $\Delta s$, angular distortion $\beta$, deflection ratio $\Delta/L$, Burland / Boscardin & Cording damage category) to the Solara reactive store (`project_state`) and build Left Drawer Cards (Card 4: Dewatering & Wells, Card 5: Buildings) and Right Viewport Tabs (Tab 4: Dewatering Hydraulics, Tab 5: Building Damage).

---

## User Review Required

> [!IMPORTANT]
> **Dewatering & Building Models Integration**
> Adds Pydantic schemas for `WellSchema`, `ConstructionPitSchema`, `DewateringConfigSchema`, and `BuildingSchema` into `schemas.py`, and integrates hydraulic drawdown and building damage solvers into `state.py`.

> [!NOTE]
> **Multi-Tab Dashboard Expansion**
> Expands Right Viewport to 5 active workspace tabs:
> 1. `📐 2D Subsoil Canvas`
> 2. `📊 Stress Profiles & Bulbs`
> 3. `📉 Settlement & Consolidation`
> 4. `💧 Dewatering Hydraulics & Drawdown`
> 5. `🏚️ Building Damage Assessment`

---

## Proposed Changes

### 1. Pydantic Schemas & State Management Bridge

#### [MODIFY] [schemas.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/schemas.py)
- Add `AquiferType` and `BuildingType` enums.
- Add `WellSchema`, `ConstructionPitSchema`, `DewateringConfigSchema`, and `BuildingSchema`.
- Extend `ScenarioSchema` to include `construction_pit`, `dewatering`, and `buildings`.

#### [MODIFY] [state.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/state.py)
- Add state helper functions: `add_well()`, `update_well()`, `delete_well()`, `duplicate_well()`, `update_construction_pit()`, `add_building()`, `update_building()`, `delete_building()`.
- Add hydraulic drawdown solver helper `run_hydraulics_solve(scenario)`.
- Add building damage solver helper `run_building_damage_solve(scenario)`.

---

### 2. Left Accordion Drawer Input Cards

#### [NEW] [dewatering_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/dewatering_card.py)
- Implement `DewateringCard()`:
  - Construction Pit Geometry ($L_{\text{pit}}, W_{\text{pit}}, d_{\text{pit}}$, bottom level mTAW).
  - Aquifer Parameters (`AquiferType.UNCONFINED` vs `CONFINED`, $k_h$, pumping duration).
  - Well Array Cards: Dynamic per-well card (`X`, `Y`, `Q` [m³/h], casing $r_w$, screen top/bottom mTAW) with `[➕ Add Well]`, `[📋 Duplicate]`, `[🗑️ Delete]`.

#### [NEW] [building_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/building_card.py)
- Implement `BuildingCard()`:
  - Multi-building array cards (`Building Name`, $X_{\text{center}}$, foundation depth $z_{\text{fnd}}$, length $L_{\text{bldg}}$, structural type: Masonry vs Concrete Frame) with `[➕ Add Building]`, `[📋 Duplicate]`, `[🗑️ Delete]`.

#### [MODIFY] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/__init__.py)
- Integrate `DewateringCard()` and `BuildingCard()` into `DrawerContainer()` as Cards 4 and 5.

---

### 3. Viewport Components & Visualizations

#### [NEW] [hydraulics_plots.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/hydraulics_plots.py)
- Implement `build_2d_drawdown_heatmap_fig()`: Plotly 2D spatial groundwater drawdown contour heatmap ($s(x, y)$) with well symbols ($\bullet$) and pit boundary.
- Implement `build_radial_drawdown_fig()`: Radial drawdown profile $s(r)$ vs. distance $r$ with Sichardt radius of influence $R$.
- Implement `@solara.component def HydraulicsPlotsView()`: Renders side-by-side dual plot layout.

#### [NEW] [damage_plots.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/damage_plots.py)
- Implement `build_burland_risk_chart_fig()`: Burland / Boscardin & Cording Risk Severity Scatter Chart (Angular distortion $\beta$ vs. Deflection ratio $\Delta/L$ with color-coded risk severity zones).
- Implement `build_building_settlement_profile_fig()`: Settlement profile under building foundation ($s(x_{\text{bldg}})$).
- Implement `@solara.component def DamagePlotsView()`: Renders side-by-side chart and Building Risk Summary Metric Cards.

#### [MODIFY] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/__init__.py)
- Update `ViewportContainer()` to include 5 tabs (`📐 2D Canvas`, `📊 Stress Profiles`, `📉 Settlement`, `💧 Dewatering Hydraulics`, `🏚️ Building Damage`).

---

## Verification Plan

### Automated Tests
- Create `tests/test_dewatering_damage_components.py`:
  - `test_run_hydraulics_solve()`: Verify steady-state Dupuit-Thiem drawdown calculations for well array.
  - `test_run_building_damage_solve()`: Verify differential settlement $\Delta s$, angular distortion $\beta$, and damage rating category.
  - `test_hydraulics_plots_fig_generation()`: Verify 2D drawdown contour and radial profile figure creation.
  - `test_damage_plots_fig_generation()`: Verify Burland risk chart and building settlement profile figure creation.
  - `test_dewatering_and_building_cards_rendering()`: Verify `DewateringCard()` and `BuildingCard()` rendering.
- Execute full test suite:
  ```bash
  uv run --extra web --extra gui --extra test pytest tests/
  ```

### Manual Verification & Visual Inspection
- Launch Solara dev server:
  ```bash
  uv run --extra web solara run settlewell.solara_app.app --port 8767
  ```
- Use `chrome-devtools-mcp` to navigate to `http://localhost:8767`, test switching to `💧 Dewatering Hydraulics` and `🏚️ Building Damage` tabs, and capture full-page screenshot verification.
