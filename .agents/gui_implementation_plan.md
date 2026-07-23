# Settlewell Desktop GUI — PySide6 Implementation Plan (MVP)

A standalone desktop application using PySide6 that provides a full workflow GUI for ground settlement analysis: define inputs → run analysis → view results → export.

## Design Decisions Summary

| Decision | Choice |
|---|---|
| Framework | PySide6 (Qt for Python) |
| Navigation | 6-step wizard (`QWizard` / `QWizardPage`) |
| Charts | Matplotlib via `FigureCanvasQTAgg` + `NavigationToolbar2QT` |
| Persistence | JSON project files (`.settlewell` extension) |
| Soil editor | `QTableWidget` with Add/Remove, inline validation |
| Results | `QTabWidget` with 7 sub-tabs (one per plot) |
| Export | Individual PNG/SVG from toolbar + combined PDF report |
| Validation | Inline field validation with red borders, blocks "Next" |
| Computation | `QThread` worker-object pattern with progress bar |
| Theme | Custom dark QSS stylesheet |
| Entry point | `settlewell-gui` via `[project.gui-scripts]` |
| Architecture | `src/settlewell/gui/` sub-package |

---

## Proposed Changes

### Configuration & Dependencies

#### [MODIFY] [pyproject.toml](file:///d:/repos/bronbemaling/pyproject.toml)

Add a `gui` optional dependency group and a `gui-scripts` entry point:

```toml
[project.optional-dependencies]
gui = ["PySide6>=6.5"]
# ... existing groups unchanged ...

[project.gui-scripts]
settlewell-gui = "settlewell.gui:main"
```

PySide6 is the only new dependency. Matplotlib is already a core dependency.

---

### GUI Sub-package Structure

All new files live under `src/settlewell/gui/`:

```
src/settlewell/gui/
├── __init__.py          # Package init, exports main()
├── __main__.py          # python -m settlewell.gui support
├── app.py               # QApplication setup, dark theme, entry point
├── main_window.py       # QMainWindow shell with menu bar (File > Open/Save/Export)
├── wizard.py            # QWizard subclass orchestrating the 6 pages
├── theme.py             # Dark QSS stylesheet string constant
├── worker.py            # QThread worker for background analysis
├── project_io.py        # Save/load .settlewell JSON files
├── pages/
│   ├── __init__.py
│   ├── soil_profile.py  # Step 1: Soil profile + layer table
│   ├── construction_pit.py  # Step 2: Pit geometry form
│   ├── wells.py         # Step 3: Wells table
│   ├── dewatering.py    # Step 4: Dewatering config form
│   ├── buildings.py     # Step 5: Buildings table
│   └── results.py       # Step 6: Run analysis + tabbed results
└── widgets/
    ├── __init__.py
    ├── soil_table.py    # Reusable QTableWidget for soil layers
    ├── well_table.py    # Reusable QTableWidget for wells
    ├── building_table.py # Reusable QTableWidget for buildings
    ├── plot_canvas.py   # FigureCanvasQTAgg + NavigationToolbar wrapper
    └── validated_input.py  # QLineEdit subclass with validation styling
```

---

### Implementation Phases

The implementation proceeds in 4 sub-phases, each producing a testable increment:

### Phase A: Skeleton & Theme
1. Create `gui/` sub-package structure (all `__init__.py` files)
2. Implement `theme.py` (dark QSS constant)
3. Implement `app.py` (entry point)
4. Implement `main_window.py` (menu bar shell, no functionality yet)
5. Implement `wizard.py` with 6 empty placeholder pages
6. Update `pyproject.toml` with `gui` extra and `gui-scripts`
7. **Verify**: `uv sync --extra gui && settlewell-gui` launches a dark-themed wizard window

### Phase B: Input Pages
1. Implement `widgets/validated_input.py`
2. Implement `widgets/soil_table.py`
3. Implement `pages/soil_profile.py` — fully functional with validation
4. Implement `pages/construction_pit.py`
5. Implement `widgets/well_table.py`
6. Implement `pages/wells.py`
7. Implement `pages/dewatering.py`
8. Implement `widgets/building_table.py`
9. Implement `pages/buildings.py`
10. **Verify**: Can navigate through all 5 input pages, validation blocks invalid data

### Phase C: Results & Computation
1. Implement `widgets/plot_canvas.py`
2. Implement `worker.py` (analysis pipeline in QThread)
3. Implement `pages/results.py` (run button, progress bar, 6 tabbed plots)
4. **Verify**: End-to-end: fill inputs → run → view plots

### Phase D: Persistence & Export
1. Implement `project_io.py` (save/load JSON)
2. Wire `main_window.py` menu actions (New, Open, Save, Save As)
3. Implement PDF export (File > Export PDF Report)
4. **Verify**: Save project, close, reopen, verify all fields restored. Export PDF contains all plots.
