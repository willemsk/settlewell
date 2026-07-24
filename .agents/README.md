# .agents — Agent Reference Documents & Specifications

This directory contains specification documents, design decisions, system architecture, and reference material for AI-assisted development of the `settlewell` package.

---

## Master Specification Index

All technical specifications are organized into modular documents under `.agents/specs/`:

| Specification Document | Subsystem / Focus | Key Topics |
|---|---|---|
| [Architecture & Structure](specs/architecture.md) | Package Layout & Environment | Repository structure, `pyproject.toml`, `mkdocs.yml`, dependencies, coding standards |
| [Hydraulics & Data Models](specs/hydraulics_and_models.md) | Models & Analytical Hydraulics | Dataclasses (`SoilProfile`, `Well`, `ConstructionPit`, `DewateringConfig`, `Building`), Thiem, Theis, Sichardt |
| [Settlement & Damage](specs/settlement_and_damage.md) | Consolidation & Damage Classification | Terzaghi 1D consolidation (`cc_cr`, `eoed`), effective stress, time factor $T_v$, Burland & Wroth / SBR damage categories |
| [Numerical Solver](specs/numerical_solver.md) | 2D Finite-Difference Groundwater Solver | `FDGrid`, 5-point Laplacian matrix assembly, boundary conditions, SciPy sparse solver |
| [Plotting Suite](specs/plotting.md) | Matplotlib & Plotly Visualizations | 8 visualization functions (cross-section, plan view, 3D drawdown, settlement trough, time-settlement, stress profile, summary card) |
| [Desktop GUI](specs/gui.md) | PySide6 Desktop Application | Standalone wizard GUI (`settlewell-gui`), 6 `QWizardPage` steps, dark QSS theme, `QThread` worker, `.settlewell` JSON project I/O, PDF export |
| [Testing & Validation](specs/testing_and_validation.md) | Test Suite & Physics Convergence | Unit test specifications, `@slow` physics convergence tests, `scripts/generate_docs_plots.py`, verification gates |

---

## Usage Guidelines for AI Agents

1. **For Implementing & Refactoring Agents**: Read the relevant specification document in `specs/` before modifying code. All implementations must strictly conform to these specifications.
2. **For Reviewing & Testing Agents**: Compare code implementations against `specs/` to verify correctness, parameter validation bounds, and test coverage.
3. **Immutability**: Specification documents serve as authoritative technical benchmarks. When evolving design requirements, update the corresponding document in `.agents/specs/` and log the change in the Version History table below.

---

## Development & Verification Protocol

### Running Unit Tests
```bash
# Run all fast unit tests:
uv run pytest -m 'not slow'

# Run complete test suite (including slow physics convergence tests):
uv run pytest -v

# Run GUI unit tests:
uv run pytest tests/test_gui.py -v
```

### Documentation Verification
```bash
# Build documentation locally with zero warnings:
uv run --extra docs mkdocs build

# Serve documentation:
uv run --extra docs mkdocs serve
```

---

## Version History

| Version | Date | Summary of Specification Changes |
|---|---|---|
| v1 | 2026-07-20 | Initial spec: package structure, 6 core modules, 7 visualizations, Flemish defaults |
| v2 | 2026-07-21 | Added comprehensive test suite: 7 test files, pytest config, `__post_init__` validation requirements |
| v3 | 2026-07-21 | Restructured into phased implementation stages with dependency diagram and verification gates |
| v4 | 2026-07-21 | Added mandatory documentation requirement rule (NumPy docstrings + MkDocs autodoc build) |
| v5 | 2026-07-21 | Integrated docs into spec: `mkdocs.yml`, `docs/` structure, per-phase doc deliverables |
| v6 | 2026-07-21 | Verified Phases 4–6 (Damage, Numerical, Plotting); updated exported symbols list |
| v7 | 2026-07-21 | Added Numerical Convergence Graphs & Validation Docs specification (`scripts/generate_docs_plots.py`) |
| v8 | 2026-07-22 | Renamed package to `settlewell` |
| v9 | 2026-07-24 | Integrated PySide6 Desktop GUI specification (`settlewell.gui`) |
| v10 | 2026-07-24 | Refactored monolithic specification into modular documents under `.agents/specs/` with `.agents/README.md` as sole master index |
| v11 | 2026-07-24 | Aligned all 7 specification documents with actual Python implementation in `src/settlewell/`, `tests/`, and `mkdocs.yml` |
