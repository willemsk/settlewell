# Implementation Plan - Eurocode 7 Flemish Soil Library & Belgian ANB Design Approach

Implement a dedicated backend Eurocode 7 Flemish Soil Library (`src/settlewell/soils.py`) conforming to Belgian NBN EN 1997-1 ANB standards, add Flemish stratigraphy profile templates, integrate EC7 soil type dropdowns with auto-population in the Solara Web GUI, and support Eurocode 7 Design Limit State safety factors.

---

## User Review Required

> [!IMPORTANT]
> **Eurocode 7 & Flemish Geotechnical Compliance**
> - **NBN EN 1997-1 ANB Flemish Soils:** Adds 10 standard Flemish soil types (Boomse Klei, Ieperse Klei, Alluviale Klei, Brabantse Leem, Pleistoceen Zand, Diestiaan Zand, Brusseliaan Zand, Maasgrind, Holoceen Veen, Antropogeen).
> - **Flemish Profile Templates:** Quick-loader templates for *Antwerp Boom Clay Formation*, *Flemish Coastal Plain*, and *Brabant Loam & Sand*.
> - **Eurocode 7 Design Approaches:** Toggle between SLS Characteristic (unfactored) and ULS Eurocode 7 DA1-1 / GEO Set M1 & Set M2 design states.

---

## Proposed Changes

### 1. Backend Eurocode 7 Flemish Soil Library

#### [NEW] [soils.py](file:///d:/repos/bronbemaling/src/settlewell/soils.py)
- Create `FlemishSoilType` StrEnum:
  - `BOOMSE_KLEI`, `IEPERSE_KLEI`, `ALLUVIALE_KLEI`, `BRABANTSE_LEEM`, `PLEISTOCEEN_ZAND`, `DIESTIAAN_ZAND`, `BRUSSELIAAN_ZAND`, `MAASGRIND`, `HOLOCEEN_VEEN`, `ANTROPOGEEN`.
- Define `FLEMISH_SOIL_PRESETS` dictionary containing characteristic Belgian ANB parameters ($\gamma_{dry}, \gamma_{sat}, e_0, E_{\text{oed}}, C_c, C_r, C_v, k_h, \text{OCR}$, USCS mapping, display color).
- Define `FLEMISH_PROFILE_TEMPLATES` (e.g. Antwerp Boom Clay Formation, Flemish Coastal Plain, Brabant Silt & Sand).
- Define Eurocode 7 Belgian ANB partial safety factors ($\gamma_{M1}, \gamma_{M2}$).

---

### 2. Pydantic Schemas & State Store

#### [MODIFY] [schemas.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/schemas.py)
- Add `DesignApproach` enum (`SLS_CHARACTERISTIC = "SLS_CHARACTERISTIC"`, `EC7_DA1_M1 = "EC7_DA1_M1"`, `EC7_DA1_M2 = "EC7_DA1_M2"`).
- Extend `SoilLayerSchema`:
  - `flemish_type: FlemishSoilType = Field(default=FlemishSoilType.PLEISTOCEEN_ZAND)`
- Extend `SolverSettingsSchema`:
  - `design_approach: DesignApproach = Field(default=DesignApproach.SLS_CHARACTERISTIC)`

#### [MODIFY] [state.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/state.py)
- Add helper `load_flemish_profile_template(template_name)`.
- Apply Eurocode 7 partial safety factor scaling in `run_fast_elastic_solve()` and `run_full_consolidation_solve()` when ULS design approach is active.

---

### 3. Left Accordion Drawer Cards & UI Integration

#### [MODIFY] [stratigraphy_table.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/stratigraphy_table.py)
- Expose `Flemish Soil Type (Eurocode 7)` select dropdown in `StratigraphyLayerCard()`.
- Auto-populate characteristic properties when Flemish soil type is selected (with manual user override).
- Add `[ 🇧🇪 Load Flemish Soil Template ]` action button in `StratigraphyTable()`.

#### [MODIFY] [solver_mesh_card.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/drawer/solver_mesh_card.py)
- Add `Eurocode 7 Design Limit State` select dropdown (`SLS Characteristic (Unfactored)`, `ULS Eurocode 7 DA1-1 / GEO M1`, `ULS Eurocode 7 DA1-2 / GEO M2`).

---

### 4. PDF Deliverables & Data Exporters

#### [MODIFY] [pdf_generator.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/pdf_generator.py)
- Include Flemish Soil Classification (Eurocode 7 NBN EN 1997-1 ANB) and Design Limit State in PDF report.

---

## Verification Plan

### Automated Tests
- Create `tests/test_flemish_soils.py`:
  - Test `FLEMISH_SOIL_PRESETS` parameter lookup and validation.
  - Test loading Flemish profile templates (Antwerp Boom Clay, Coastal Plain).
  - Test Eurocode 7 partial safety factor scaling under ULS DA1-1 / GEO M1 and M2 design modes.
- Execute full test suite:
  ```bash
  uv run --extra web --extra gui --extra test pytest tests/
  ```

### Manual Verification & Visual Inspection
- Launch Solara dev server on port 8773:
  ```bash
  uv run --extra web solara run settlewell.solara_app.app --port 8773
  ```
- Inspect Flemish soil type dropdown, profile template loader, and EC7 design limit state toggle in Chrome DevTools.
