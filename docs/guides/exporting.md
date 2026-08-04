# Exporting Deliverables

Settlewell allows you to export your analysis results into multiple industry-standard formats. Deliverables are generated using the `Project` API.

## Supported Export Formats

You can export project data to:
- **PDF (.pdf):** Comprehensive engineering calculation report.
- **DXF (.dxf):** 2D CAD vector drawing for integration into design software.
- **Excel (.xlsx):** Multi-sheet workbook containing all tabular data and results.
- **CSV (.csv):** Raw numerical data for further custom analysis.

## Usage

Assuming you have a configured `Project` instance (named `project`), you can use the built-in export methods. The export engine automatically runs the solver if it hasn't been run yet.

```python
from settlewell import Project
# ... project initialization ...

# Generate a PDF calculation report
project.export_pdf("calculation_report.pdf")

# Generate a 2D CAD drawing
project.export_dxf("site_plan.dxf")

# Generate an Excel workbook containing tabular results
project.export_excel("results_data.xlsx")

# Generate a raw CSV for further data processing
project.export_csv("settlement_profile.csv")
```

## Details on Exported Content

### 1. PDF Report (`export_pdf`)
The PDF report is built using ReportLab and includes:
- An Executive Summary.
- Subsoil stratigraphy and geotechnical parameters table.
- A summary of surface and foundation loads.
- Dewatering pit and well array configurations.
- Neighboring building structural damage assessments.
- An engineering sign-off and verification block.

### 2. DXF CAD Drawing (`export_dxf`)
The DXF export (created via `ezdxf`) generates a 2D cross-sectional drawing containing:
- Layered soil strata with annotations.
- The groundwater table.
- Foundation load polygons.
- Construction pit dimensions.
- Dewatering wells.
- Building foundations.
- A scaled settlement bowl curve.

### 3. Excel Workbook (`export_excel`)
The Excel document is composed of multiple tabs:
- **Project Summary:** High-level scenario parameters.
- **Soil Stratigraphy:** Detailed list of layers and properties.
- **Stress & Settlement Profile:** Depth-dependent vertical stresses.
- **Dewatering Drawdown:** Transmissivity, storativity, and radius of influence.
- **Building Damage Results:** Detailed damage assessment per building.

### 4. CSV Data (`export_csv`)
Provides raw tabular data suitable for custom plotting or importing into other analysis tools. It includes the vertical stress profile and the 1D surface settlement bowl profile.
