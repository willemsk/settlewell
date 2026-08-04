# Export & Reporting API Reference

The `settlewell.export` module provides export generators for generating multi-page engineering PDF reports, CAD DXF drawings, multi-tab Excel spreadsheets, and CSV numerical data.

## Overview

Export features require optional dependencies, which can be installed via:

```bash
pip install settlewell[export]
```

The primary export functions can also be invoked directly from `Project` instance methods:
- `project.export_pdf("report.pdf")`
- `project.export_dxf("drawing.dxf")`
- `project.export_excel("data.xlsx")`
- `project.export_csv("data.csv")`

::: settlewell.export
