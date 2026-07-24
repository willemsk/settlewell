# Desktop GUI Application Specification

This document specifies the architecture, UI component structure, wizard steps, project state serialization, background calculation threading, and PDF report export for the PySide6 Desktop GUI application (`src/settlewell/gui/`).

---

## Overview

- **Entry Point**: `settlewell-gui` CLI command (`settlewell.gui:main` -> `app.py`)
- **Framework**: PySide6 (Qt for Python 6.5+)
- **Theme**: Dark QSS Theme (`theme.py` stylesheet with custom palette, tab styling, and form inputs)

---

## Sub-package Architecture (`src/settlewell/gui/`)

```
src/settlewell/gui/
├── __init__.py          # Exports main() entry point
├── __main__.py          # CLI runner: python -m settlewell.gui
├── app.py               # QApplication setup, font loading, dark theme initialization
├── main_window.py       # QMainWindow shell, QMenuBar, QStatusBar, project action routing
├── wizard.py            # QWizard container orchestrating 6 sequential workflow steps
├── theme.py             # Dark QSS stylesheet string constant (DARK_THEME_QSS)
├── worker.py            # QThread AnalysisWorker running calculations & rendering plots
├── project_io.py        # .settlewell JSON project save/load serializer
├── pages/               # QWizardPage step implementations
│   ├── soil_profile.py       # Step 1: SoilProfilePage
│   ├── construction_pit.py   # Step 2: ConstructionPitPage
│   ├── wells.py              # Step 3: WellsPage
│   ├── dewatering.py         # Step 4: DewateringConfigPage
│   ├── buildings.py          # Step 5: BuildingsPage
│   └── results.py            # Step 6: ResultsPage
└── widgets/             # Reusable Qt widgets
    ├── soil_table.py         # SoilLayerTable QTableWidget
    ├── well_table.py         # WellTable QTableWidget (Q in m³/s)
    ├── building_table.py     # BuildingTable QTableWidget
    ├── plot_canvas.py        # Matplotlib FigureCanvasQTAgg wrapper
    └── validated_input.py    # Form line edits with regex validation
```

---

## QWizard 6-Step Workflow (`wizard.py`)

| Page ID | Page Class | Module Path | Purpose / Description |
|:---:|---|---|---|
| **0** | `SoilProfilePage` | `pages/soil_profile.py` | Configure soil layers (`SoilLayerTable`) and GWL/surface levels [mTAW]. |
| **1** | `ConstructionPitPage` | `pages/construction_pit.py` | Input excavation pit geometry (length, width, depth, center x/y, bottom mTAW). |
| **2** | `WellsPage` | `pages/wells.py` | Add/edit extraction wells (`WellTable`) with discharge $Q$ [m³/s] and coordinates. |
| **3** | `DewateringConfigPage` | `pages/dewatering.py` | Target water level [mTAW], pumping duration [days], and aquifer type. |
| **4** | `BuildingsPage` | `pages/buildings.py` | Define neighboring buildings (`BuildingTable`) with dimensions & `BuildingType`. |
| **5** | `ResultsPage` | `pages/results.py` | View background analysis status, 7 tabbed figures, and export PDF report. |

---

## Background Worker Thread (`worker.py`)

To maintain UI responsiveness during heavy calculation loops and plot rendering, `AnalysisWorker(QThread)` runs off the main thread:

- **Signals**:
  - `progress = Signal(int, str)`: Emits completion percentage (0–100%) and current status text.
  - `finished = Signal(dict)`: Emits results payload containing drawdown grid, settlements, damage assessments, and 7 Matplotlib figures.
  - `error = Signal(str)`: Emits error message string if calculation fails.

---

## Project Serialization (`project_io.py`)

Projects are saved to disk with `.settlewell` file extension using a versioned JSON envelope:

```json
{
  "settlewell_version": "0.1.0",
  "created": "2026-07-24T18:57:45+00:00",
  "state": {
    "soil_profile": {
      "gwl_mtaw": 3.0,
      "surface_level_mtaw": 5.0,
      "layers": [
        {
          "name": "Klei",
          "thickness": 3.0,
          "gamma": 16.0,
          "gamma_sat": 18.0,
          "k_h": 1e-7,
          "e0": 0.8,
          "Cc": 0.15,
          "Cr": 0.03,
          "Eoed": 5000.0,
          "Cv": 1e-7,
          "OCR": 1.0
        }
      ]
    },
    "construction_pit": {
      "length": 20.0,
      "width": 15.0,
      "depth": 4.0,
      "center_x": 0.0,
      "center_y": 0.0,
      "bottom_mtaw": 1.0
    },
    "wells": [
      {
        "x": -10.0,
        "y": -7.5,
        "Q": 0.002,
        "r_w": 0.075,
        "screen_top_mtaw": 0.0,
        "screen_bottom_mtaw": -5.0
      }
    ],
    "dewatering": {
      "target_drawdown_mtaw": 1.0,
      "original_gwl_mtaw": 3.0,
      "pumping_duration_days": 30.0,
      "aquifer_type": "unconfined"
    },
    "buildings": [
      {
        "x": 25.0,
        "y": 0.0,
        "length": 12.0,
        "width": 8.0,
        "orientation_deg": 0.0,
        "foundation_depth": 0.6,
        "building_type": "masonry"
      }
    ]
  }
}
```

---

## PDF Report Export (`pages/results.py`)

The PDF export feature saves a multipage PDF report using Matplotlib's `backend_pdf.PdfPages`:
- Generates and writes all **7** engineering figures to PDF pages:
  1. Dwarsdoorsnede (Cross Section)
  2. Grondplan (Plan View)
  3. Zettingskom (Settlement Trough)
  4. Tijd-Zetting (Time-Settlement)
  5. Spanningsverloop (Stress Profile)
  6. 3D Bemalingskegel (3D Drawdown Surface)
  7. Schadesamenvatting (Damage Assessment Summary)
