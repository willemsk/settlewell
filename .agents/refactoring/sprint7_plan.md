# Sprint 7 Implementation Plan: Core Library Export Engine & Final Cleanup

## 1. `pyproject.toml`
**File:** `d:\repos\bronbemaling\pyproject.toml`
**Action:** Add an `export` optional dependency group and update `web` if necessary.

```toml
[project.optional-dependencies]
notebook = ["jupyter>=1.0", "ipykernel>=6.0"]
test = ["pytest>=7.0"]
export = [
    "reportlab>=5.0.0",
    "ezdxf>=1.4.4",
    "openpyxl>=3.1.5",
    "pandas>=2.0.0",
]
web = [
    "solara>=1.60.3",
    "pydantic>=2.13.4",
    "ipycanvas>=0.14.3",
    "anywidget>=0.9.0",
    "settlewell[export]",
]
```

## 2. `src/settlewell/project.py`
**File:** `d:\repos\bronbemaling\src\settlewell\project.py`
**Action:** Create (or update) the `Project` facade class to include the export methods.

```python
from dataclasses import dataclass, field
from typing import List, Optional, Any

from .models import SoilProfile, ConstructionPit, DewateringConfig, Building

@dataclass
class Project:
    """Main facade class for managing a settlewell geotechnical analysis project."""
    name: str = "Untitled Project"
    profile: Optional[SoilProfile] = None
    pit: Optional[ConstructionPit] = None
    dewatering: Optional[DewateringConfig] = None
    buildings: List[Building] = field(default_factory=list)
    loads: List[Any] = field(default_factory=list)
    
    def export_pdf(self, path: str) -> None:
        """Export the project calculation report to a PDF file."""
        from .export import generate_pdf_report
        with open(path, "wb") as f:
            f.write(generate_pdf_report(self))

    def export_dxf(self, path: str) -> None:
        """Export the project geometry and results to a DXF CAD file."""
        from .export import generate_dxf_drawing
        with open(path, "wb") as f:
            f.write(generate_dxf_drawing(self))

    def export_excel(self, path: str) -> None:
        """Export the project data to an Excel workbook."""
        from .export import generate_excel_workbook
        with open(path, "wb") as f:
            f.write(generate_excel_workbook(self))

    def export_csv(self, path: str) -> None:
        """Export the settlement profiles to a CSV file."""
        from .export import generate_csv_data
        with open(path, "wb") as f:
            f.write(generate_csv_data(self))
```

*(Also, be sure to export `Project` in `src/settlewell/__init__.py`)*

## 3. `src/settlewell/export.py`
**File:** `d:\repos\bronbemaling\src\settlewell\export.py`
**Action:** Consolidate `solara_app/export/*` into this single module. Wrap the third-party imports in a `_check_dependencies()` function. Update the function signatures to take a `Project` instance rather than a `ScenarioSchema`. Replace `scenario.stratigraphy` with `project.profile.layers`, `scenario.water_table.depth_z` with `project.profile.gwl_depth`, etc. Use core functions instead of `run_fast_elastic_solve` (which was tied to Solara state).

```python
"""Optional export engine for settlewell."""
from io import BytesIO

def _check_dependencies():
    try:
        import reportlab
        import ezdxf
        import pandas as pd
        import openpyxl
    except ImportError as e:
        raise ImportError(
            "Export dependencies are missing. Install them with: "
            "`pip install settlewell[export]` or `uv pip install settlewell[export]`"
        ) from e

def generate_pdf_report(project: "Project") -> bytes:
    _check_dependencies()
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from datetime import datetime

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#0284c7"))
    body_style = styles["BodyText"]
    h1_style = styles["Heading1"]
    
    story = []
    story.append(Paragraph("settlewell v2.0 — Geotechnical Calculation Report", title_style))
    story.append(Paragraph(f"<b>Project:</b> {project.name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style))
    story.append(Spacer(1, 16))
    
    # ... Continue porting the ReportLab logic from pdf_generator.py ...
    # Substitute `scenario.stratigraphy` -> `project.profile.layers`
    # Substitute `scenario.construction_pit` -> `project.pit`
    # Substitute `scenario.dewatering` -> `project.dewatering`
    
    doc.build(story)
    return buffer.getvalue()

def generate_dxf_drawing(project: "Project") -> bytes:
    _check_dependencies()
    import ezdxf
    import numpy as np
    from io import StringIO
    
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    
    # ... Port ezdxf logic from dxf_generator.py ...
    # Substitute `scenario.stratigraphy` -> `project.profile.layers`
    
    s_io = StringIO()
    doc.write(s_io)
    return s_io.getvalue().encode("utf-8")

def generate_excel_workbook(project: "Project") -> bytes:
    _check_dependencies()
    import pandas as pd
    
    buffer = BytesIO()
    
    # ... Port openpyxl/pandas logic from data_exporter.py ...
    # Calculate stresses using core functions instead of `run_fast_elastic_solve`
    # e.g., compute_initial_stress_profile(project.profile)
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame([{"Project": project.name}]).to_excel(writer, sheet_name="Summary", index=False)
    
    return buffer.getvalue()

def generate_csv_data(project: "Project") -> bytes:
    _check_dependencies()
    import pandas as pd
    
    buffer = BytesIO()
    buffer.write(b"# Settlewell Results\n")
    # ... Port csv logic ...
    
    return buffer.getvalue()
```
*(After this, delete `src/settlewell/solara_app/export/` directory completely).*

## 4. Docs
**Actions:**
1. Update `docs/getting-started.md` to show the `pip install settlewell[export]` command and demonstrate the new `Project` usage for exports.
2. Update `mkdocs.yml` to include a new API page `docs/api/project.md` and `docs/api/export.md`.
3. Create `docs/api/project.md` and `docs/api/export.md` using `mkdocstrings` format:
   ```markdown
   # Project API
   ::: settlewell.project
   ```

## 5. Notebooks & Scripts
**Action:** Refactor notebooks and scripts to wrap the raw core models into a `Project` and use the export methods.

**`notebooks/example_analysis.ipynb`:**
Insert a new cell at the end of the notebook or update existing cells:
```python
from settlewell.project import Project

# Create a project wrapper for the current analysis
project = Project(
    name="Flanders Construction Pit",
    profile=profile,
    pit=pit,
    dewatering=dewatering,
    buildings=[building]
)

# Export the results
project.export_pdf("settlement_report.pdf")
project.export_excel("results.xlsx")
project.export_dxf("geometry.dxf")

print("Project successfully exported to PDF, Excel, and DXF!")
```

**`scripts/generate_docs_plots.py`:**
Ensure imports for `solve_steady_state` and other functions are still correct. The script is mostly analytical/FD verification, so it may not strictly need the `Project` class, but update it if you wish to showcase the `Project` API, or simply verify that it runs cleanly with the new `__init__.py` structure.

## 6. Cleanup
1. Run `ruff format src/settlewell tests scripts` and `ruff check --fix src/settlewell`.
2. Delete `solara_app/export` directory.
3. Remove any unused imports in `solara_app/state.py` or elsewhere relating to the old export engine.
4. Verify tests pass (or update tests for the new `export.py` mock dependencies).
