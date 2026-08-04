# Sprint 7 Implementation Plan: Core Library Export Engine & Final Cleanup

## Execution Strategy: Parallel Subagents
This sprint will be executed by dispatching two parallel subagents to ensure deep focus.

---

## Subagent 1: Export Engine Core

**Target Files:**
- `pyproject.toml`
- `src/settlewell/project.py`
- `src/settlewell/export.py`

### ❌ Strict Deletions & Removals Checklist
- [ ] Delete the `src/settlewell/solara_app/export/` directory and all its contents completely using CLI commands (`rm -rf`). Do not leave it behind.
- [ ] Remove any unused imports in `solara_app/state.py` relating to the old export engine.

### 🔨 Implementation Details
1. **`pyproject.toml`**: Add an `export` optional dependency group (`reportlab>=5.0.0`, `ezdxf>=1.4.4`, `openpyxl>=3.1.5`, `pandas>=2.0.0`). Update `web` group to depend on `settlewell[export]`.
2. **`src/settlewell/project.py`**: Create the `Project` facade methods (`export_pdf`, `export_dxf`, `export_excel`, `export_csv`) that delegate to `settlewell.export`.
```python
    def export_pdf(self, path: str) -> None:
        from .export import generate_pdf_report
        with open(path, "wb") as f:
            f.write(generate_pdf_report(self))
```
3. **`src/settlewell/export.py`**: Consolidate old export functions into this single module. 
   - Wrap third-party imports in a `_check_dependencies()` function to fail gracefully if not installed.
   - Update function signatures to take a `Project` instance rather than `ScenarioSchema`.
   - Replace `scenario.stratigraphy` with `project.profile.layers`, `scenario.water_table.depth_z` with `project.profile.gwl_depth`, etc.

---

## Subagent 2: Documentation & Examples

**Target Files:**
- `docs/getting-started.md`
- `mkdocs.yml`
- `docs/api/project.md` (New)
- `docs/api/export.md` (New)
- `notebooks/example_analysis.ipynb`
- `scripts/generate_docs_plots.py`

### ❌ Strict Deletions & Removals Checklist
- [ ] Replace any old instances in notebooks/docs where raw functions like `run_fast_elastic_solve` are used for project-level exports. Ensure old export patterns are completely deleted from examples.

### 🔨 Implementation Details
1. **Docs**: 
   - Update `getting-started.md` to show `pip install settlewell[export]`.
   - Update `mkdocs.yml` with `api/project.md` and `api/export.md`. Use `mkdocstrings` format.
2. **Notebooks**: 
   - Update `example_analysis.ipynb` to wrap raw models into a `Project` and demonstrate `project.export_pdf(...)`.
3. **Scripts**: 
   - Ensure `generate_docs_plots.py` runs cleanly with the new `__init__.py` structure.

---

## Final Verification (Run after subagents merge)
1. Run `ruff format src/settlewell tests scripts` and `ruff check --fix src/settlewell`.
2. Ensure `solara_app/export` directory is truly gone.
3. Verify tests pass.
