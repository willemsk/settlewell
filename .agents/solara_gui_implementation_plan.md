# `settlewell` Interactive Web GUI — Technical Specification Sheet

## 1. System Overview & Domain Context

* **Package Name:** `settlewell`
* **Domain:** Geotechnical Soil Mechanics, Stress Distribution, and Primary/Secondary Settlement & Consolidation Analysis.
* **Objective:** Replace the existing linear wizard interface with a modern, dynamic, non-wizard web GUI featuring persistent side-by-side textual input and interactive graphical preview/analysis.
* **Target Audience:** Geotechnical engineers, foundation design consultants, and civil engineering researchers.

---

## 2. Technology Stack & Execution Architecture

```
+-----------------------------------------------------------------------+
|                         Solara Application Shell                      |
|                                                                       |
|  +------------------------------+   +------------------------------+  |
|  |  Persistent Left Drawer      |   |  Right Multi-Tab Viewport    |  |
|  |  (Accordion Forms & Tables)  |   |  (2D Canvas, Plots, PDF)     |  |
|  +--------------+---------------+   +--------------+---------------+  |
|                 |                                  |                  |
|                 +----------------+-----------------+                  |
|                                  |                                    |
|                        solara.reactive Store                          |
|                                  |                                    |
+----------------------------------+------------------------------------+
                                   |
                                   v
             +-------------------------------------------+
             |       FastAPI / Python Backend Core       |
             |   (settlewell.core, solver, io modules)   |
             +-------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
  ReportLab (PDF)           ezdxf (DXF CAD)            pandas (CSV/XLSX)
```

* **Frontend & UI Framework:** **Solara** (v1.20+) running on **FastAPI / Starlette** with `ipyvuetify` / Quasar UI components.
* **Reactivity Model:** Pure Python `solara.reactive()` state management with fine-grained component re-rendering.
* **Interactive 2D Canvas Engine:** `ipycanvas` / Plotly hybrid canvas with client-side mouse event hooks for vertex dragging, selection, and coordinate snapping.
* **Plotting Library:** `Plotly Python` (for stress profiles, settlement surface bowls, and logarithmic time-consolidation curves).
* **Export Engines:** `ReportLab` (automated PDF report generation), `ezdxf` (DXF CAD vector export), `pandas` / `openpyxl` (CSV/XLSX raw data export).
* **Execution Modes:**
  1. **Standalone Web Server:** Launched via `solara run app.py` (accessible locally at `http://localhost:8765`).
  2. **Jupyter Notebook Integration:** Renderable directly inside a Jupyter cell via `display(app.Page())`.

---

## 3. Workspace Layout & UI Component Hierarchy

The application follows **Option B (Persistent Left Accordion Drawer + Right Multi-Tab Viewport)** with a draggable horizontal split bar.

```
+------------------------------------------------------------------------------------------------+
| [LOGO] settlewell v2.0 | Scenario: [Baseline v] | Mode: [Edit/Read-Only Toggle] | [Dark/Light] |
+------------------------------------+-----------------------------------------------------------+
| LEFT DRAWER (Width: 35%, Min: 300px)| RIGHT VIEWPORT (Width: 65%)                               |
|                                    | +-------------------------------------------------------+ |
| v Project Metadata & Water Table   | | [ 2D Canvas ] [ Stress ] [ Settlement ] [ Scenarios ] | |
|   - Project Title / Site ID        | +-------------------------------------------------------+ |
|   - Groundwater Level z_gw (m)     |                                                           |
|                                    |  [ Interactive 2D Subsoil Canvas / Plotly Viewport ]      |
| > Soil Stratigraphy Table (Editable) |                                                         |
|   - [ + Add Layer ]                |   +-------------------------------------------------+     |
|   - Layer Name, h, γ, e0, E, Cc... |   |                                                 |     |
|                                    |   | Soil Layer 1 (Sand) - h=3m                      |     |
| > Surface & Foundation Loads       |   | ~~~~~~~~~~~~~~~~~~~~~ Groundwater Line ~~~~~~~~ |     |
|   - Footing/Embankment Type        |   | Soil Layer 2 (Clay) - h=5m                      |     |
|   - Coordinates, Width B, Stress q |   |                                                 |     |
|                                    |   +-------------------------------------------------+     |
| > Calculation Grid & Method        |                                                           |
|   - Boussinesq / Westergaard / 2:1 |  Status Bar: Real-time Elastic Settlement: s = 14.2 mm    |
|   - Grid z_max, dz, Creep toggle   |  [ ▶ Run Full Consolidation Solve ]                        |
+------------------------------------+-----------------------------------------------------------+
```

### 3.1 Global Top Header Bar
* **App Branding:** `settlewell` logo & version badge.
* **Scenario Switcher Dropdown:** `[ Scenario: Baseline Model v ]` with `[+ New Scenario]` and `[ Duplicate ]` buttons.
* **Canvas Interactivity Mode Toggle:** `[ Edit Mode (Interactive) | Read-Only Mode (Locked) ]`.
* **Project File Controls:** `[ Open .settle ]`, `[ Save .settle ]`, `[ Quick Export v ]`.
* **Theme Toggle:** Dark Mode / Light Mode switch.

### 3.2 Persistent Left Accordion Drawer (35% Width)
Contains 4 collapsible accordion cards with dense, engineering-styled input fields:

1. **Card 1: Project Metadata & Groundwater**
   - Project Name, Engineer ID, Site Location, Calculation Date.
   - **Groundwater Table ($z_{gw}$):** Numeric input (meters depth below ground surface) with slider sync.
2. **Card 2: Subsoil Stratigraphy Table**
   - Dynamic data table with editable inline rows: `Layer Name`, `Thickness h (m)`, `Unit Weight γ (kN/m³)`, `Saturated Unit Weight γ_sat (kN/m³)`, `Initial Void Ratio e0`, `Modulus of Elasticity E (MPa)`, `Compression Index Cc`, `Recompression Index Cr`, `Consolidation Coeff Cv (m²/yr)`, `USCS Classification` (Sand, Clay, Gravel, Peat).
   - Actions: `[+ Add Soil Layer Above/Below]`, `[ Delete Layer ]`, `[ Reorder Drag Handles ]`.
3. **Card 3: Surface & Foundation Loads Table**
   - Load Type dropdown: `Strip Footing`, `Rectangular Scribe`, `Trapezoidal Embankment`, `Point Load`.
   - Parameters: `X-center (m)`, `Z-surface offset (m)`, `Width B (m)`, `Length L (m)`, `Applied Stress q (kPa)`.
   - Actions: `[+ Add Load]`, `[ Duplicate Load ]`, `[ Delete Load ]`.
4. **Card 4: Calculation Mesh & Solver Parameters**
   - Stress Distribution Method: Dropdown `[ Boussinesq (Elastic Half-Space) | Westergaard | 2:1 Method ]`.
   - Mesh Parameters: Maximum calculation depth $z_{\text{max}}$ (m), vertical step size $\Delta z$ (m), horizontal grid extent $x_{\text{min}}, x_{\text{max}}$.
   - Time-Consolidation Range: $t_{\text{start}}$ (1 day) to $t_{\text{end}}$ (50 years).
   - Secondary Compression Toggle: `[x] Calculate Creep (C_alpha)`.

### 3.3 Right Multi-Tab Viewport (65% Width)
Contains 5 workspace tabs displaying live graphical visualizations and outputs:

* **Tab 1: 2D Geometry Cross-Section Canvas**
  - Renders 2D subsoil geometry, layered strata, soil hatch patterns, water level line, and load geometries.
  - Controls overlay: `[x] Show Dimension Lines`, `[x] Show USCS Soil Hatches`, `[x] Show Stress Bulb Overlay (Iso-contours)`.
* **Tab 2: Stress Profiles & Bulbs**
  - Plot 1: Vertical Depth $z$ vs. Effective Overburden Stress $\sigma'_{v0}$ and Delta Induced Stress $\Delta\sigma_z$.
  - Plot 2: 2D Contour Heatmap of Stress Ratio $\Delta\sigma_z / q = 0.1, 0.2, 0.5, 0.8$.
* **Tab 3: Settlement Profiles & Time Development**
  - Plot 1: Surface Settlement Bowl ($s$ vs $x$).
  - Plot 2: Layer-by-layer Settlement Breakdown (Stacked Bar Chart: Elastic $s_e$, Primary Consolidation $s_c$, Creep $s_s$).
  - Plot 3: Settlement vs Logarithmic Time ($s$ vs $\log t$ from 1 day to 50 years) with Degree of Consolidation $U(t)$.
* **Tab 4: Multi-Scenario Benchmarking & Overlays**
  - Comparative plot overlaying up to 4 saved scenarios (e.g., Baseline vs. Pre-loading Embankment vs. Ground Improvement).
  - Delta Settlement Table ($\Delta s = s_{\text{Scenario B}} - s_{\text{Baseline}}$).
* **Tab 5: PDF Calculation Report & Export Engine**
  - Live preview of generated PDF report.
  - Action Buttons: `[ Download PDF Report ]`, `[ Export .DXF CAD File ]`, `[ Export Raw Data (.CSV / .XLSX) ]`.

---

## 4. Bi-Directional State Synchronization & Interaction Rules

### 4.1 Reactivity Matrix
1. **Text Inputs $\rightarrow$ Canvas & Fast Solver Preview:** 
   - Modifying any numeric value in the left drawer triggers a **300ms debounced auto-solve loop** using lightweight elastic/Boussinesq approximations.
   - The 2D Canvas and instant settlement status bar (`Real-Time Elastic Settlement: s = 14.2 mm`) update immediately.
2. **Canvas $\rightarrow$ Text Inputs (Edit Mode Enabled):**
   - **Groundwater Table Handle:** Dragging the blue dashed water table line vertically updates $z_{gw}$ in Card 1.
   - **Soil Boundary Handles:** Dragging layer boundary handles updates layer thickness $h_i$ in Card 2.
   - **Load Handles:** Dragging footing edges horizontally updates load width $B$ and center coordinate $X$ in Card 3.
3. **Canvas Lock Switch (Read-Only Mode Enabled):**
   - Canvas mouse drag event listeners are disabled (`pointer-events: none` or state guard).
   - Hovering displays rich inspection tooltips showing point parameters ($z$, $\sigma'_{v0}$, $\Delta\sigma_z$, $E$, $e_0$) without risking accidental geometry alterations.

### 4.2 Dual Solver Execution Flow
* **Fast Real-Time Engine (Background):** Runs Boussinesq stress dispersion and elastic settlement calculations continuously as inputs change.
* **Deep Consolidation Solve Trigger:** Clicking `[ ▶ Run Full Consolidation Solve ]` executes numerical layer integration over time step intervals for primary consolidation ($s_c$) and secondary creep ($s_s$). Displays a progress bar during computation.

---

## 5. Geotechnical Design System & Aesthetic Specifications

### 5.1 UI Density & Typography
* **Density:** High-density compact technical UI (row height 32px in data tables, monospaced numerical inputs `font-family: 'JetBrains Mono', 'Fira Code', monospace`).
* **Components:** Resizable splitters between panes, collapsible drawer accordions, compact toggle buttons.

### 5.2 Color Palette & Geotechnical Hatching (USCS Compliant)

| Element / Soil Type | Light Mode Color | Dark Mode Color | Pattern / Hatch |
| :--- | :--- | :--- | :--- |
| **Sand / Gravelly Sand** | `#f59e0b` (Ochre) | `#d97706` | Stipple / Fine Dots pattern |
| **Clay / Silty Clay** | `#854d0e` (Brown/Teal) | `#a16207` | 45-degree diagonal line hatches |
| **Gravel / Cobbles** | `#64748b` (Slate Grey) | `#475569` | Pebble outline pattern |
| **Peat / Organic Soil** | `#451a03` (Dark Brown) | `#292524` | Horizontal stripe pattern |
| **Groundwater Table** | `#0284c7` (Cyan Blue) | `#38bdf8` | Dashed blue line with triangle markers |
| **Applied Surface Loads** | `#dc2626` (Red) | `#ef4444` | Solid red polygon with downward arrows |
| **Stress Bulb Heatmap** | Spectral / Viridis | Spectral / Viridis | Semi-transparent gradient overlay ($\alpha=0.45$) |

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
    },
    {
      "id": "layer_2",
      "name": "Soft Overconsolidated Clay",
      "thickness": 6.5,
      "gamma_dry": 15.0,
      "gamma_sat": 17.0,
      "e0": 1.10,
      "E_modulus": 8.0,
      "Cc": 0.35,
      "Cr": 0.06,
      "Cv": 1.5,
      "uscs_type": "CLAY",
      "color": "#854d0e"
    }
  ],
  "loads": [
    {
      "id": "load_1",
      "type": "RECTANGULAR",
      "x_center": 0.0,
      "width_B": 4.0,
      "length_L": 8.0,
      "stress_q": 120.0
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

### 6.2 Export Deliverables

1. **PDF Calculation Report (`ReportLab` engine):**
   - Professional branded cover block and project metadata summary.
   - Soil Stratigraphy Table & Load Definition Table.
   - High-resolution embedded 2D Cross-Section Diagram.
   - Stress distribution curves & Stress bulb heatmap charts.
   - Time-Settlement curves ($s$ vs $\log t$) and final settlement layer breakdown table.
   - Multi-scenario benchmark comparison summary table (if scenarios exist).
2. **AutoCAD Vector File (`ezdxf` engine):**
   - Layers: `SOIL_STRATA_BOUNDARIES`, `GROUNDWATER_LINE`, `FOUNDATION_LOADS`, `STRESS_BULB_CONTOURS`, `DIMENSION_LINES`.
3. **Raw Data Matrix Export (`pandas` engine):**
   - Multi-tab Excel file (`.xlsx`): Sheet 1 (`Stratigraphy`), Sheet 2 (`Depth_vs_Stress`), Sheet 3 (`Settlement_vs_Time`), Sheet 4 (`Scenario_Comparison`).

---

## 7. Agentic Coding Framework Task Roadmap

An agentic framework should implement the project in **6 modular sprints**:

### Sprint 1: Core Data Models & State Management
* Define Pydantic schema models for `ProjectState`, `SoilLayer`, `LoadGeometry`, `SolverSettings`, and `Scenario`.
* Implement `app/state.py` containing `solara.reactive` state management routines and serialization/deserialization for `.settle` JSON files.

### Sprint 2: Persistent Left Accordion Drawer UI
* Build `app/components/drawer/metadata_card.py`.
* Build `app/components/drawer/stratigraphy_table.py` with inline row addition, editing, and deletion.
* Build `app/components/drawer/loads_table.py` and `solver_mesh_card.py`.

### Sprint 3: Interactive 2D Subsoil Canvas Viewport
* Build `app/components/canvas/subsoil_canvas.py` using `ipycanvas` / Plotly.
* Render layered soil rectangles, groundwater blue dashed line, footing loads, and USCS soil hatch patterns.
* Implement CAD dimension lines and vertex drag handlers for groundwater and load width.
* Add the `[ Edit Mode / Read-Only Mode ]` state guard.

### Sprint 4: Solver Integration & Plotly Results Views
* Connect `settlewell.core` and `settlewell.solver` routines to the Solara reactive store.
* Build `app/components/viewport/stress_plots.py` ($\sigma'_{v0}$ and $\Delta\sigma_z$ profile curves & stress bulb heatmap).
* Build `app/components/viewport/settlement_plots.py` (Surface bowl $s(x)$, layer breakdown bar chart, time-consolidation $s$ vs $\log t$).
* Build `app/components/viewport/scenario_benchmark.py` (Multi-scenario overlay plots and delta calculation tables).

### Sprint 5: PDF, DXF, and CSV Export Engine
* Implement `app/export/pdf_generator.py` using `ReportLab`.
* Implement `app/export/dxf_generator.py` using `ezdxf`.
* Implement `app/export/data_exporter.py` for CSV/XLSX generation.

### Sprint 6: Main Application Shell & End-to-End Testing
* Assemble `app.py` linking the top header bar, left drawer splitter, right multi-tab viewport, and status bar.
* Add automated unit tests (`pytest`) covering JSON serialization, state reactivity, solver integration, and PDF export generation.
