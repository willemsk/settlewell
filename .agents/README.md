# .agents — Agent Reference Documents

This directory contains specification documents, design decisions, and reference
material for AI-assisted development of the `settlewell` package.

## Contents

| File | Purpose |
|---|---|
| `spec.md` | **Current specification** (v8) — renamed package to `settlewell` |
| `gui_implementation_plan.md` | **GUI Implementation Plan** — technical specifications for the PySide6 wizard GUI |

## Usage Guidelines

- **For implementing agents**: Read `spec.md` first to understand the full design before writing any code. It contains function signatures, algorithms, formulas, data structures, visualization layouts, and the complete test suite specification.
- **For reviewing agents**: Compare implementation against `spec.md` to verify correctness and completeness.
- **Immutability**: Each spec version is a snapshot of the approved plan. If the design evolves, create a new versioned spec (e.g., `spec_v6.md`) and update `spec.md` to the latest version.

## Project Development Rules

<!-- phase_documentation -->
### Phase Documentation Requirement

For every implementation phase:
1. **NumPy Docstrings**: Write thorough NumPy-style docstrings for all new or modified classes, methods, functions, and module headers (including type annotations, unit specifications, formulas, and parameters).
2. **Autodoc Integration**: Add or update corresponding Markdown pages under `docs/api/` and `mkdocs.yml` navigation for newly introduced modules.
3. **Doc Build Verification**: Run `uv run --extra docs mkdocs build` alongside the phase verification gate to ensure zero documentation build warnings or syntax errors.
<!-- phase_documentation -->

<!-- specification_first_updates -->
### Specification-First Feature Rule

When new features, design changes, or architectural additions are requested:
1. **Snapshot Current Spec**: Copy `.agents/spec.md` to a versioned snapshot (e.g., `spec_v<N>.md`).
2. **Update `.agents/README.md`**: Update the Contents table and append a new entry to the Version History table with the version number, date, and summary of changes.
3. **Update `.agents/spec.md`**: Formally add complete technical specifications (signatures, algorithms, file paths, visual formats, and test/verification requirements) to `.agents/spec.md` **before** writing implementation code.
4. **Obtain Plan Approval**: Present the updated implementation plan referencing `spec.md` to the user for approval.
<!-- specification_first_updates -->

<!-- optional_dependency_testing -->
### Optional Dependency Testing & Pytest Guardrails

1. **Top-Level Module Import Guard**: When writing tests for optional dependency packages (e.g., `PySide6`, `plotly`, `jupyter`), add `pytest.importorskip("<package>")` at the top of the test module before importing the optional package. This ensures `pytest` collection skips the test file gracefully without crashing when optional dependencies are omitted.
2. **CI Workflow Synchronization**: Whenever adding a new `[project.optional-dependencies]` extra group in `pyproject.toml`, update the CI workflow files (e.g., `.github/workflows/tests.yml`) to include `--extra <group>` in the `uv sync` step so CI exercises the new functionality.
<!-- optional_dependency_testing -->

<!-- ruff_variable_naming -->
### Variable Naming & Ruff E741 Compliance

Avoid single-letter variable names `l`, `O`, or `I` (especially in loops, lambdas, and list comprehensions) to comply with Ruff `E741` ambiguous variable name rules. Prefer descriptive names like `layer_dict`, `item`, or `elem`.
<!-- ruff_variable_naming -->

## Version History

| Version | Date | Changes |
|---|---|---|
| v1 | 2026-07-20 | Initial spec: package structure, 6 modules, 7 visualizations, Flemish defaults |
| v2 | 2026-07-21 | Added comprehensive test suite: 7 test files (conftest + 6 modules + physics convergence), pytest config, `__post_init__` validation requirements |
| v3 | 2026-07-21 | Restructured into 8 phased implementation stages with dependency diagram, verification gates, and review protocol |
| v4 | 2026-07-21 | Added mandatory documentation requirement rule (NumPy docstrings + MkDocs autodoc build for every phase) |
| v5 | 2026-07-21 | Integrated docs into spec: mkdocs.yml, docs/ structure, per-phase doc deliverables, doc build in verification gates, __all__ in __init__.py, py.typed, fixed docs/index.md nav |
| v6 | 2026-07-21 | Reviewed and verified Phases 4–6 (Damage, Numerical, Plotting); updated spec.md with complete exported symbols list and docs/index.md overview |
| v7 | 2026-07-21 | Added Numerical Convergence Graphs & Validation Docs specification (`scripts/generate_docs_plots.py`, SVG vector output, `docs/validation.md`, `mkdocs.yml` nav) |
| v8 | 2026-07-22 | Renamed package to `settlewell` |
