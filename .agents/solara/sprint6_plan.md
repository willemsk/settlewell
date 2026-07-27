# Implementation Plan - Sprint 6: PDF, DXF, and CSV Export Engine

Implement `pdf_generator.py` (ReportLab multi-page engineering report), `dxf_generator.py` (ezdxf multi-layer CAD drawing), and `data_exporter.py` (multi-tab Excel .xlsx and CSV exporter), and build Tab 7 (`ExportView`) in the Solara Right Viewport.

---

## User Review Required

> [!IMPORTANT]
> **Dependencies Check**
> Uses `reportlab`, `ezdxf`, `pandas`, and `openpyxl`, which are already specified in `pyproject.toml` under `[project.optional-dependencies] web`.

> [!NOTE]
> **Viewport Expansion**
> Adds Tab 7 (`📄 PDF, DXF & Data Export`) to the Right Viewport dashboard.

---

## Proposed Changes

### 1. Export Engines (`src/settlewell/solara_app/export/`)

#### [NEW] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/__init__.py)
- Package initializer exporting `generate_pdf_report`, `generate_dxf_drawing`, `generate_excel_workbook`, `generate_csv_data`.

#### [NEW] [pdf_generator.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/pdf_generator.py)
- Implement `generate_pdf_report(scenario: ScenarioSchema) -> bytes`:
  - Uses `reportlab.platypus` (SimpleDocTemplate, Paragraph, Table, Spacer, PageBreak, Image).
  - Cover page & Executive Summary.
  - Soil Stratigraphy table & Groundwater parameters.
  - Applied Surface & Foundation loads.
  - Dewatering pit & well array layout.
  - Stress distribution & Settlement consolidation results.
  - Dewatering drawdown & Neighboring building damage risk assessment summary.
  - Signature / Sign-off block.

#### [NEW] [dxf_generator.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/dxf_generator.py)
- Implement `generate_dxf_drawing(scenario: ScenarioSchema) -> bytes`:
  - Uses `ezdxf.new(dxfversion="R2010")`.
  - Creates CAD layers: `SOIL_STRATA`, `GROUNDWATER`, `FOUNDATION_LOADS`, `CONSTRUCTION_PIT`, `DEWATERING_WELLS`, `BUILDINGS`, `SETTLEMENT_BOWL`.
  - Adds lines, polylines, hatches, circles, and text entities.
  - Serializes to DXF string bytes.

#### [NEW] [data_exporter.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/export/data_exporter.py)
- Implement `generate_excel_workbook(scenario: ScenarioSchema) -> bytes`:
  - Uses `pandas` and `openpyxl`.
  - Worksheets: `Project Summary`, `Soil Stratigraphy`, `Stress & Settlement Profile`, `Dewatering Drawdown`, `Building Damage Results`.
- Implement `generate_csv_data(scenario: ScenarioSchema) -> bytes`:
  - Exports primary numerical settlement and stress results into a clean CSV format.

---

### 2. Export Viewport UI Tab

#### [NEW] [export_view.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/export_view.py)
- Implement `@solara.component def ExportView()`:
  - Left side: Report summary overview cards (Project Title, Date, Soil Layers count, Loads count, Well count, Buildings count, Solver status).
  - Right side: Action Cards with instant Solara FileDownload / FileDownloadButton triggers:
    - `📄 Download Full PDF Report`
    - `📐 Download DXF CAD Drawing`
    - `📊 Download Excel Workbook (.xlsx)`
    - `💾 Download Raw CSV Data (.csv)`

#### [MODIFY] [__init__.py](file:///d:/repos/bronbemaling/src/settlewell/solara_app/components/viewport/__init__.py)
- Add Tab 7 (`📄 PDF, DXF & Data Export`) rendering `ExportView()`.

---

## Verification Plan

### Automated Tests
- Create `tests/test_export_engine.py`:
  - `test_pdf_report_generation()`: Verify ReportLab PDF binary bytes creation (`len(bytes) > 0` and `%PDF` header).
  - `test_dxf_drawing_generation()`: Verify ezdxf DXF string bytes creation (`SECTION` and `HEADER` presence).
  - `test_excel_workbook_generation()`: Verify Excel `.xlsx` binary workbook structure.
  - `test_csv_data_generation()`: Verify CSV output string bytes.
  - `test_export_view_rendering()`: Verify Solara component tree rendering for `ExportView()`.
- Execute full test suite:
  ```bash
  uv run --extra web --extra gui --extra test pytest tests/
  ```

### Manual Verification & Visual Inspection
- Launch Solara dev server on port 8769:
  ```bash
  uv run --extra web solara run settlewell.solara_app.app --port 8769
  ```
- Use `chrome-devtools-mcp` to navigate to `http://localhost:8769`, switch to Tab 7 (`📄 PDF, DXF & Data Export`), and take full-page screenshot verification.
