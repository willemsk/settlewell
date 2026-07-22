# .agents — Agent Reference Documents

This directory contains specification documents, design decisions, and reference
material for AI-assisted development of the `settlewell` package.

## Contents

| File | Purpose |
|---|---|
| `spec.md` | **Current specification** (v8) — renamed package to `settlewell` |
| `spec_v7.md` | **Specification v7** — frozen snapshot after complete spec with 8 phased implementation stages, test suite, documentation infrastructure, and numerical convergence validation graphs. All implementation must conform to this spec. |
| `spec_v6.md` | **Specification v6** — frozen snapshot after Phase 8 verification before SVG convergence graphs addition. |
| `spec_v3.md` | **Specification v3** — frozen snapshot before docs integration. For reference if needed. |
| `spec_v1.md` | **Original specification** (v1) — frozen snapshot before tests were added. For historical reference only. |
| `phase3_plan.md` | **Phase 3 Plan Snapshot** — detailed technical design for Phase 3 (Settlement). |

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
