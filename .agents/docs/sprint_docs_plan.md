# Sprint Documentation Implementation Plan: Complete Documentation Overhaul (v0.2.0)

> **Goal**: Update and expand the `settlewell` documentation to align with the `Project`-centric v0.2.0 architecture, introducing User Guides, Eurocode 7 & Flemish standards theory, Case Studies, and complete API reference documentation.

---

## 1. Documentation Structure & Navigation (`mkdocs.yml`)

Update `mkdocs.yml` navigation (`nav`) to organize content into 5 main sections:

```yaml
nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - User Guides:
      - Project Workflows: guides/project_workflow.md
      - Solara Web Application: guides/solara_gui.md
      - Exporting Deliverables: guides/exporting.md
  - Theory & Eurocode 7:
      - Mechanics Overview: theory/index.md
      - Eurocode 7 & Flemish ANB: theory/eurocode7.md
      - Building Damage Risk: theory/building_damage.md
      - Physics Validation: validation.md
  - Case Studies:
      - Kauwereelstraat 31 Ghent: case_studies/kauwereelstraat.md
      - Bridge Abutment Settlement: case_studies/example_analysis.md
  - API Reference:
      - Overview: api/index.md
      - Project Orchestrator: api/project.md
      - Export Engine: api/export.md
      - Domain Models: api/models.md
      - Stress Distribution: api/stress.md
      - Hydraulics & Drawdown: api/hydraulics.md
      - Settlement & Creep: api/settlement.md
      - Eurocode 7 Factors: api/eurocode.md
      - Building Damage: api/damage.md
      - Numerical Solver: api/numerical.md
      - Plotting & Visualizations: api/plotting.md
```

---

## 2. Page Specifications & Content Outline

### Home & Getting Started
- **`docs/index.md`**: Highlight v0.2.0 features (`Project` orchestrator, Pydantic models, Boussinesq stress distribution, Eurocode 7 partial factors, Burland damage assessment, and multi-format exports).
- **`docs/getting-started.md`**: Quickstart guide with `pip install settlewell[export]` and copy-pasteable 5-minute `Project` API example.

### User Guides (`docs/guides/`)
- **`docs/guides/project_workflow.md`**: Complete step-by-step python workflow (defining soil strata, loading Flemish presets, adding excavation pit, wells, loads, buildings, solving, and plotting).
- **`docs/guides/solara_gui.md`**: Guide for the Solara interactive web app (`solara run settlewell.solara_app`), managing scenarios, drawing canvas, live viewport plots, and downloading reports.
- **`docs/guides/exporting.md`**: Detailed guide covering all 4 deliverable exports (`export_pdf`, `export_dxf`, `export_excel`, `export_csv`).

### Theory & Eurocode 7 (`docs/theory/`)
- **`docs/theory/index.md`**: Theoretical foundation of 1D Terzaghi consolidation, Boussinesq & Fadum stress distribution, Sichardt/Thiem/Dupuit/Theis hydraulics, elastic settlement, secondary creep, and equivalent $C_v$.
- **`docs/theory/eurocode7.md`**: Eurocode 7 (EN 1997-1) and Belgian NBN EN 1997-1 ANB partial material safety factor scaling (`apply_partial_factors`, `DesignApproach.EC7_DA1_M2`).
- **`docs/theory/building_damage.md`**: Neighboring building damage evaluation: Burland & Wroth / Boscardin & Cording angular distortion ($\beta$), deflection ratio ($\Delta / L$), SBR damage categories 0-5, and risk color codes.
- **`docs/validation.md`**: Verification of `settlewell` algorithms against analytical closed-form solutions and finite-difference benchmarks.

### Case Studies (`docs/case_studies/`)
- **`docs/case_studies/kauwereelstraat.md`**: Rendered case study for Kauwereelstraat 31 (Ghent) construction dewatering and building settlement evaluation with code blocks and downloadable link to `notebooks/kauwereelstraat_31_analysis.ipynb`.
- **`docs/case_studies/example_analysis.md`**: Rendered case study for Bridge Abutment & Multi-Layer Settlement analysis with code blocks and downloadable link to `notebooks/example_analysis.ipynb`.

### API Reference (`docs/api/`)
- **`docs/api/index.md`**: Architectural landing page for the API reference section.
- **`docs/api/*.md`**: 10 module pages (`project.md`, `export.md`, `models.md`, `stress.md`, `hydraulics.md`, `settlement.md`, `eurocode.md`, `damage.md`, `numerical.md`, `plotting.md`) containing overviews, code snippets, and `mkdocstrings` directives (`::: settlewell.module_name`).

---

## 3. Verification Commands

1. **Build documentation site**:
   ```bash
   uv run --extra docs mkdocs build
   ```
2. **Lint and format code**:
   ```bash
   uv run --with ruff ruff check --fix .
   uv run --with ruff ruff format .
   ```
3. **Run test suite**:
   ```bash
   uv run pytest -v
   ```
