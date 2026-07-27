# Implementation Plan - Sprint 2: Persistent Left Accordion Drawer UI

This implementation plan details **Sprint 2** for the modern Solara web GUI for `settlewell`. It covers the design, component architecture, and implementation of the 4 persistent left drawer accordion cards:
1. **Metadata & Groundwater Card** (`metadata_card.py`)
2. **Subsoil Stratigraphy Table** (`stratigraphy_table.py`)
3. **Surface & Foundation Loads Table** (`loads_table.py`)
4. **Calculation Mesh & Solver Settings Card** (`solver_mesh_card.py`)
5. **Drawer Assembly & Container** (`components/drawer/__init__.py`)

---

## Resolved Architectural Decisions

During the initial design alignment, the following choices were confirmed:
1. **UI Component Library:** Standard `solara` native components (`solara.Card`, `solara.InputFloat`, `solara.InputText`, `solara.Select`) and Vuetify expansion panels (`solara.v.ExpansionPanels`) styled with dense engineering layout tokens.
2. **File Organization:** Modular component breakdown under `src/settlewell/solara_app/components/drawer/`.
3. **Reactivity Model:** Direct live two-way reactive binding to `solara_app.state.project_state` for instant preview updates.
4. **Table UX:** Inline dense table editing with compact cell controls and direct row action buttons (`[+ Add Layer]`, `[ 📋 Copy ]`, `[ 🗑️ Delete ]`).

---

## Proposed Changes

### Solara Web Application Drawer Components

#### [NEW] [metadata_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/metadata_card.py)
Card 1: Project Metadata & Groundwater Table input controls.

#### [NEW] [stratigraphy_table.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/stratigraphy_table.py)
Card 2: Subsoil Stratigraphy editable table.

#### [NEW] [loads_table.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/loads_table.py)
Card 3: Surface & Foundation Loads editable table.

#### [NEW] [solver_mesh_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/solver_mesh_card.py)
Card 4: Calculation Mesh & Solver Parameters card.

#### [NEW] [drawer_container.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/__init__.py)
Assembles all 4 accordion cards into a unified drawer container using `solara.v.ExpansionPanels`.

---

### Automated Verification

#### [NEW] [test_drawer_components.py](file:///d:/repos/bronbemaling/tests/test_drawer_components.py)
Automated unit tests using `pytest` verifying component rendering and state updates.
