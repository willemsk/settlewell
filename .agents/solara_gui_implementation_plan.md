# `settlewell` Interactive Web GUI — Technical Specification Sheet

## 1. System Overview & Domain Context

* **Package Name:** `settlewell`
* **Domain:** Geotechnical Soil Mechanics, Groundwater Dewatering Hydraulics, Stress Distribution, Primary/Secondary Settlement & Consolidation Analysis, and Building Damage Assessment.
* **Objective:** Replace the existing linear wizard interface with a modern, dynamic, non-wizard web GUI featuring persistent side-by-side textual input and interactive graphical preview/analysis.
* **Target Audience:** Geotechnical engineers, dewatering contractors, foundation design consultants, and civil engineering researchers.

---

## 2. Technology Stack & Execution Architecture

```
+-----------------------------------------------------------------------------------+
|                            Solara Application Shell                               |
|                                                                                   |
|  +-----------------------------------+   +-------------------------------------+  |
|  |  Persistent Left Drawer           |   |  Right Multi-Tab Viewport           |  |
|  |  (Accordion Forms, Tables, Cards) |   |  (2D Canvas, Plots, Hydraulics, PDF)|  |
|  +-----------------+-----------------+   +------------------+------------------+  |
|                    |                                        |                     |
|                    +------------------+---------------------+                     |
|                                       |                                           |
|                            solara.reactive Store                                  |
|                                       |                                           |
+---------------------------------------+-------------------------------------------+
                                        |
                                        v
                 +-------------------------------------------+
                 |       FastAPI / Python Backend Core       |
                 |  (settlewell.hydraulics, settlement,      |
                 |   damage, plotting, models modules)       |
                 +-------------------------------------------+
                                        |
             +--------------------------+--------------------------+
             |                          |                          |
             v                          v                          v
      ReportLab (PDF)            ezdxf (DXF CAD)            pandas (CSV/XLSX)
```

* **Frontend & UI Framework:** **Solara** (v1.20+) running on **FastAPI / Starlette** with `ipyvuetify` / Quasar UI components.
* **Reactivity Model:** Pure Python `solara.reactive()` state management with fine-grained component re-rendering.
* **Interactive 2D Canvas Engine:** Plotly hybrid canvas with client-side mouse event hooks for vertex dragging, selection, and coordinate snapping.
* **Plotting Library:** `Plotly Python` (for stress profiles, settlement surface bowls, groundwater drawdown contours, logarithmic time-consolidation curves, and building damage risk graphs).
* **Export Engines:** `ReportLab` (automated PDF report generation), `ezdxf` (DXF CAD vector export), `pandas` / `openpyxl` (CSV/XLSX raw data export).
* **Execution Modes:**
  1. **Standalone Web Server:** Launched via `solara run app.py` (accessible locally at `http://localhost:8765`).
  2. **Jupyter Notebook Integration:** Renderable directly inside a Jupyter cell via `display(app.Page())`.

---

## 3. Workspace Layout & UI Component Hierarchy

The application follows **Persistent Left Accordion Drawer (480px) + Right Multi-Tab Viewport (Flex 1)** layout.

```
+--------------------------------------------------------------------------------------------------------+
| [LOGO] settlewell v2.0 | Scenario: [Baseline v] | Datum: [ Depth (m) | Elevation (mTAW) ] | [Dark/Light]|
+------------------------------------+-------------------------------------------------------------------+
| LEFT DRAWER (Width: 480px)         | RIGHT VIEWPORT (Flex 1)                                           |
|                                    | +---------------------------------------------------------------+ |
| v Project Metadata & Water Table   | | [ 2D Canvas ][ Stress ][ Settlement ][ Dewatering ][ Damage ] | |
|   - Project Title / Site ID        | +---------------------------------------------------------------+ |
|   - Groundwater Level z_gw (m)     |                                                                   |
| > Soil Stratigraphy Table          |  [ Interactive Multi-Tab Dashboard / Plotly Viewport ]            |
|   - Layer Name, h, γ, e0, E, Cc... |   +---------------------------------------------------------+     |
| > Surface & Foundation Loads       |   |                                                         |     |
|   - Coordinates, Width B, Stress q |   | Subsoil Strata / Stress Profiles / Drawdown Contours    |     |
| > Dewatering Pit & Well Array      |   |                                                         |     |
|   - Pit Length, Width, Depth       |   +---------------------------------------------------------+     |
|   - Wells (x, y, Q, Screen top/bot)|                                                                   |
| > Neighboring Building Assessment  |  Status Bar: Real-time Elastic Settlement: s_e = 41.2 mm          |
|   - Location, Foundation depth, Type|  [ ▶ Run Full Consolidation Solve ]                              |
+------------------------------------+-------------------------------------------------------------------+
```

### 3.1 Global Top Header Bar
* **App Branding:** `settlewell` logo & version badge.
* **Scenario Switcher Dropdown:** `[ Scenario: Baseline Model v ]` with `[+ New Scenario]` and `[ Duplicate ]` buttons.
* **Elevation Datum Unit Switcher:** Toggle `[ Depth Z (m) | Elevation (mTAW) ]`.
* **Canvas Interactivity Mode Toggle:** `[ Edit Mode (Interactive) | Read-Only Mode (Locked) ]`.
* **Project File Controls:** `[ Open .settle ]`, `[ Save .settle ]`.
* **Theme Toggle:** Dark Mode / Light Mode switch.

### 3.2 Persistent Left Accordion Drawer (480px Width)
Contains 6 collapsible accordion cards with dense, engineering-styled input fields:

1. **Card 1: Project Metadata & Groundwater**
   - Project Name, Engineer ID, Site Location, Calculation Date.
   - **Groundwater Table ($z_{gw}$):** Numeric input (meters depth below surface or mTAW elevation) with slider sync.
2. **Card 2: Subsoil Stratigraphy Cards**
   - Dynamic per-layer input cards: `Layer Name`, `Thickness h (m)`, `Unit Weight γ (kN/m³)`, `Saturated Unit Weight γ_sat (kN/m³)`, `Initial Void Ratio e0`, `Modulus of Elasticity E (MPa)`, `Compression Index Cc`, `Recompression Index Cr`, `Consolidation Coeff Cv (m²/yr)`, `USCS Classification` (Sand, Clay, Gravel, Peat).
   - Actions: `[+ Add Soil Layer]`, `[ 📋 Duplicate Layer ]`, `[ 🗑️ Delete Layer ]`.
3. **Card 3: Surface & Foundation Load Cards**
   - Load Type dropdown: `Strip Footing`, `Rectangular Load`, `Trapezoidal Embankment`, `Point Load`.
   - Parameters: `X-center (m)`, `Z-surface offset (m)`, `Width B (m)`, `Length L (m)`, `Applied Stress q (kPa)`.
   - Actions: `[+ Add Load]`, `[ 📋 Duplicate Load ]`, `[ 🗑️ Delete Load ]`.
4. **Card 4: Dewatering Pit & Well Array (Hydraulics)**
   - **Construction Pit Geometry:** Excavation length $L_{\text{pit}}$ (m), width $W_{\text{pit}}$ (m), excavation depth $d_{\text{pit}}$ (m), pit bottom level (mTAW).
   - **Aquifer Hydraulics:** Dropdown `[ Confined Aquifer | Unconfined Phreatic Aquifer ]`, hydraulic conductivity $k_h$ (m/s), pumping duration (days).
   - **Well Array Table:** Well location ($x, y$), pumping rate $Q$ ($m^3/h$ or $L/s$), casing radius $r_w$ (m), screen top & bottom (mTAW).
5. **Card 5: Neighboring Building Damage Assessment**
   - Building Name, distance to excavation $X_{\text{bldg}}$ (m), foundation depth $z_{\text{fnd}}$ (m), building length $L_{\text{bldg}}$ (m).
   - Structural Type dropdown: `[ Masonry Structure (Metselwerk) | Concrete Frame (Betonskelet) ]`.
   - Sensitivity Class: `[ High Sensitivity | Normal | Low Sensitivity ]`.
6. **Card 6: Calculation Mesh & Solver Parameters**
   - Stress Distribution Method: Dropdown `[ Boussinesq (Elastic Half-Space) | Westergaard | 2:1 Method ]`.
   - Mesh Parameters: Maximum calculation depth $z_{\text{max}}$ (m), vertical step size $\Delta z$ (m), horizontal grid extent $x_{\text{min}}, x_{\text{max}}$.
   - Time-Consolidation Range: $t_{\text{start}}$ (1 day) to $t_{\text{end}}$ (50 years).
   - Secondary Compression Toggle: `[x] Calculate Creep (C_alpha)`.

### 3.3 Right Multi-Tab Viewport (Flex 1)
Contains 6 workspace tabs displaying live graphical visualizations and outputs:

* **Tab 1: 2D Geometry Cross-Section Canvas (`SubsoilCanvasContainer`)**
  - Renders 2D subsoil geometry, layered strata, soil USCS fill colors, water level line, and footing load geometries.
  - Controls overlay: `[x] Dimensions`, `[x] USCS Colors`, `[x] Stress Bulbs`, `[x] Water Table`.
* **Tab 2: Stress Profiles & Bulbs (`StressPlotsView`)**
  - Plot 1: Vertical Depth $z$ vs. Effective Overburden Stress $\sigma'_{v0}$, Total Stress $\sigma_v$, and Delta Induced Stress $\Delta\sigma_z$.
  - Plot 2: 2D Contour Heatmap of Stress Ratio $\Delta\sigma_z / q = 0.1, 0.2, 0.5, 0.8$.
* **Tab 3: Settlement Profiles & Time Development (`SettlementPlotsView`)**
  - Plot 1: Surface Settlement Bowl ($s(x)$ vs $x$).
  - Plot 2: Layer-by-layer Settlement Breakdown (Stacked Bar Chart: Elastic $s_e$, Primary Consolidation $s_c$, Creep $s_s$).
  - Plot 3: Settlement vs Logarithmic Time ($s$ vs $\log t$ from 1 day to 50 years) with Degree of Consolidation $U(t)$.
* **Tab 4: Dewatering Hydraulics & Drawdown (`HydraulicsPlotsView`)**
  - Plot 1: 2D Groundwater Drawdown Contour Heatmap ($s(x, y)$ over excavation grid).
  - Plot 2: Radial Drawdown Profile $s(r)$ vs Distance from Wells with Sichardt Radius of Influence $R$.
* **Tab 5: Building Damage Assessment (`DamagePlotsView`)**
  - Plot 1: Settlement Profile under Building Foundation ($s(x_{\text{bldg}})$).
  - Plot 2: **Burland / Boscardin & Cording Damage Category Chart:** Visual scatter plot mapping Angular Distortion $\beta$ vs Horizontal Strain $\epsilon_h$, highlighting damage severity (Category 0: Negligible $\to$ Category 5: Very Severe).
* **Tab 6: Multi-Scenario Benchmarking & Overlays (`ScenarioBenchmarkView`)**
  - Comparative plot overlaying up to 4 saved scenarios.
  - Delta Settlement Table ($\Delta s = s_{\text{Scenario B}} - s_{\text{Baseline}}$).
* **Tab 7: PDF Calculation Report & Export Engine (`ExportView`)**
  - Live preview of generated PDF report.
  - Action Buttons: `[ Download PDF Report ]`, `[ Export .DXF CAD File ]`, `[ Export Raw Data (.CSV / .XLSX) ]`.

---

## 4. Bi-Directional State Synchronization & Interaction Rules

### 4.1 Reactivity Matrix
1. **Text Inputs $\rightarrow$ Canvas & Fast Solver Preview:** 
   - Modifying any numeric value in the left drawer triggers a **300ms debounced auto-solve loop** using lightweight elastic/Boussinesq approximations and steady-state well drawdown.
   - The 2D Canvas and instant settlement status bar (`Real-Time Elastic Settlement: s_e = 41.2 mm`) update immediately.
2. **Canvas $\rightarrow$ Text Inputs (Edit Mode Enabled):**
   - **Groundwater Table Handle:** Dragging the blue dashed water table line vertically updates $z_{gw}$ in Card 1.
   - **Load Handles:** Dragging footing edges horizontally updates load width $B$ and center coordinate $X$ in Card 3.
   - **Well Handles:** Dragging well markers in the 2D layout updates well $x, y$ coordinates in Card 4.
3. **Canvas Lock Switch (Read-Only Mode Enabled):**
   - Canvas mouse drag event listeners are disabled (`pointer-events: none` or state guard).
   - Hovering displays rich inspection tooltips showing point parameters ($z$, $\sigma'_{v0}$, $\Delta\sigma_z$, $E$, $e_0$, drawdown $s_w$) without risking accidental geometry alterations.

---

## 5. Geotechnical Design System & Aesthetic Specifications

### 5.1 Color Palette & Geotechnical Hatching (USCS Compliant)

| Element / Soil Type | Light Mode Color | Dark Mode Color | Pattern / Hatch |
| :--- | :--- | :--- | :--- |
| **Sand / Gravelly Sand** | `#f59e0b` (Ochre) | `#d97706` | Stipple / Fine Dots pattern |
| **Clay / Silty Clay** | `#854d0e` (Brown) | `#a16207` | 45-degree diagonal line hatches |
| **Gravel / Cobbles** | `#64748b` (Slate Grey) | `#475569` | Pebble outline pattern |
| **Peat / Organic Soil** | `#451a03` (Dark Brown) | `#292524` | Horizontal stripe pattern |
| **Groundwater Table** | `#0284c7` (Cyan Blue) | `#38bdf8` | Dashed blue line with triangle markers |
| **Applied Surface Loads** | `#dc2626` (Red) | `#ef4444` | Solid red polygon with downward arrows |
| **Dewatering Wells** | `#059669` (Emerald Green) | `#10b981` | Well casing circle with extraction arrow |
| **Neighboring Building** | `#7c3aed` (Purple) | `#8b5cf6` | Structure outline with foundation beam |

---

## 6. Data Models, Schemas, & Export Contracts

### 6.1 Native Project File Schema (`.settle` / JSON)

```json
{
  "project_metadata": {
    "title": "Main Bridge Abutment Settlement Study",
    "engineer": "J. Doe, PE",
    "date": "2026-07-24",
    "units": "metric"
  },
  "water_table": {
    "depth_z": 2.5
  },
  "stratigraphy": [
    {
      "id": "layer_1",
      "name": "Medium Dense Sand",
      "thickness": 3.0,
      "gamma_dry": 17.5,
      "gamma_sat": 19.5,
      "e0": 0.65,
      "E_modulus": 25.0,
      "Cc": 0.05,
      "Cr": 0.01,
      "Cv": 12.0,
      "uscs_type": "SAND",
      "color": "#f59e0b"
    }
  ],
  "loads": [
    {
      "id": "load_1",
      "name": "Strip Footing Load",
      "type": "RECTANGULAR",
      "x_center": 0.0,
      "width_B": 4.0,
      "length_L": 8.0,
      "stress_q": 120.0
    }
  ],
  "construction_pit": {
    "length": 20.0,
    "width": 15.0,
    "depth": 4.0,
    "bottom_mtaw": -1.5
  },
  "dewatering": {
    "aquifer_type": "UNCONFINED",
    "target_drawdown_mtaw": -2.0,
    "pumping_duration_days": 30.0,
    "wells": [
      {
        "id": "well_1",
        "x": -8.0,
        "y": 0.0,
        "Q": 25.0,
        "r_w": 0.075,
        "screen_top_mtaw": -1.0,
        "screen_bottom_mtaw": -6.0
      }
    ]
  },
  "buildings": [
    {
      "id": "bldg_1",
      "name": "Adjacent Masonry Residence",
      "x_center": 18.0,
      "foundation_depth": 1.5,
      "length": 12.0,
      "structural_type": "MASONRY"
    }
  ],
  "solver_settings": {
    "stress_method": "BOUSSINESQ",
    "z_max": 20.0,
    "delta_z": 0.25,
    "calculate_creep": true
  }
}
```

---

## 7. Agentic Coding Framework Task Roadmap

An agentic framework should implement the project in **7 modular sprints**:

### Sprint 1: Core Data Models & State Management [COMPLETED]
* Define Pydantic schema models for `ProjectState`, `SoilLayer`, `LoadGeometry`, `SolverSettings`, and `Scenario`.
* Implement `app/state.py` containing `solara.reactive` state management routines and serialization for `.settle` JSON files.

### Sprint 2: Persistent Left Accordion Drawer UI [COMPLETED]
* Build `app/components/drawer/metadata_card.py`.
* Build `app/components/drawer/stratigraphy_table.py` with structured per-layer cards.
* Build `app/components/drawer/loads_table.py` and `solver_mesh_card.py`.

### Sprint 3: Interactive 2D Subsoil Canvas Viewport [COMPLETED]
* Build `app/components/canvas/subsoil_canvas.py` using Plotly.
* Render layered soil rectangles, groundwater blue dashed line, footing loads, and USCS soil fill colors.
* Add canvas toolbar toggles (`Dimensions`, `USCS Colors`, `Stress Bulbs`, `Water Table`).

### Sprint 4: Solver Integration & Plotly Results Views [COMPLETED]
* Connect `settlewell.settlement` and `settlewell.models` routines to the Solara reactive store.
* Build `app/components/viewport/stress_plots.py` ($\sigma'_{v0}$ and $\Delta\sigma_z$ profile curves & stress bulb heatmap).
* Build `app/components/viewport/settlement_plots.py` (Surface bowl $s(x)$, layer breakdown stacked bar chart, $s$ vs $\log t$).
* Build `app/components/viewport/scenario_benchmark.py` (Multi-scenario overlay plots and delta calculation tables).

### Sprint 5: Dewatering Hydraulics, Construction Pit & Building Damage Analysis [NEXT SPRINT]
* Build `app/components/drawer/dewatering_card.py` (Construction pit dimensions $L \times W \times d$, well array table $x, y, Q$, aquifer type).
* Build `app/components/drawer/building_card.py` (Neighboring building location, foundation depth, structural type).
* Build `app/components/viewport/hydraulics_plots.py` (2D groundwater drawdown contour map & radial drawdown profile $s(r)$).
* Build `app/components/viewport/damage_plots.py` (Building settlement profile $s(x_{\text{bldg}})$, angular distortion $\beta$, Boscardin/Burland damage severity classification chart).

### Sprint 6: PDF, DXF, and CSV Export Engine
* Implement `app/export/pdf_generator.py` using `ReportLab` (includes drawdown map & building damage summary).
* Implement `app/export/dxf_generator.py` using `ezdxf`.
* Implement `app/export/data_exporter.py` for CSV/XLSX generation.

### Sprint 7: Main Application Shell & End-to-End Testing
* Assemble complete `app.py` linking all drawer cards and 7 viewport tabs.
* Add automated end-to-end unit tests (`pytest`).
