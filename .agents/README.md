# .agents — Agent Reference Documents

This directory contains specification documents, design decisions, and reference
material for AI-assisted development of the `bronbemaling` package.

## Contents

| File | Purpose |
|---|---|
| `spec.md` | **Current specification** (v2) — includes the full test suite. All implementation must conform to this spec. |
| `spec_v1.md` | **Original specification** (v1) — frozen snapshot before tests were added. For historical reference only. |
| `phase3_plan.md` | **Phase 3 Plan Snapshot** — detailed technical design for Phase 3 (Settlement). |

## Usage Guidelines

- **For implementing agents**: Read `spec.md` first to understand the full design before writing any code. It contains function signatures, algorithms, formulas, data structures, visualization layouts, and the complete test suite specification.
- **For reviewing agents**: Compare implementation against `spec.md` to verify correctness and completeness.
- **Immutability**: Each spec version is a snapshot of the approved plan. If the design evolves, create a new versioned spec (e.g., `spec_v3.md`) and update `spec.md` to the latest version.

## Project Development Rules

<!-- phase_documentation -->
### Phase Documentation Requirement

For every implementation phase:
1. **NumPy Docstrings**: Write thorough NumPy-style docstrings for all new or modified classes, methods, functions, and module headers (including type annotations, unit specifications, formulas, and parameters).
2. **Autodoc Integration**: Add or update corresponding Markdown pages under `docs/api/` and `mkdocs.yml` navigation for newly introduced modules.
3. **Doc Build Verification**: Run `uv run --extra docs mkdocs build` alongside the phase verification gate to ensure zero documentation build warnings or syntax errors.
<!-- phase_documentation -->

## Version History

| Version | Date | Changes |
|---|---|---|
| v1 | 2026-07-20 | Initial spec: package structure, 6 modules, 7 visualizations, Flemish defaults |
| v2 | 2026-07-21 | Added comprehensive test suite: 7 test files (conftest + 6 modules + physics convergence), pytest config, `__post_init__` validation requirements |
| v3 | 2026-07-21 | Restructured into 8 phased implementation stages with dependency diagram, verification gates, and review protocol |
| v4 | 2026-07-21 | Added mandatory documentation requirement rule (NumPy docstrings + MkDocs autodoc build for every phase) |
