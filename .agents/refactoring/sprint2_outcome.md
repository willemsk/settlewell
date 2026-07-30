# Sprint 2 Outcome: Stress Distribution Physics

## Summary
Sprint 2 extracted physical stress calculations (Fadum, Boussinesq, 2:1 method) from the GUI module into a pure, framework-agnostic core module `src/settlewell/stress.py`.

## Completed Deliverables

1. **`src/settlewell/stress.py`**
   - `fadum_corner_stress(b, l_dim, z)`: Fadum (1948) corner stress influence factor $I_z$.
   - `boussinesq_strip_stress(q, B, x_rel, z)`: Boussinesq (1885) strip load vertical stress increment.
   - `boussinesq_rectangular_stress(q, B, L, x_rel, z)`: Boussinesq rectangular load vertical stress increment.
   - `compute_load_stress_increment(load, x_rel, z, method)`: Unified stress increment solver for `BOUSSINESQ`, `2:1`, and `WESTERGAARD`.
   - `compute_stress_profile_under_loads(loads, z_points, x_eval, method)`: 1D stress increment profile array over depths.
   - `compute_stress_heatmap(loads, z_points, x_points, method)`: 2D stress ratio array ($z \times x$).

2. **`src/settlewell/__init__.py`**
   - Exported all stress functions and added to top-level `__all__`.

3. **`tests/test_stress.py`**
   - 12 comprehensive unit tests covering surface edge cases, published reference values (Poulos & Davis), Boussinesq strip & rectangular stress, symmetry, depth decay, 2:1 method calculations, and Westergaard error handling.

4. **`docs/api/stress.md` & `mkdocs.yml`**
   - Added API documentation reference page and updated MkDocs navigation.

## Verification Results
- `uv run pytest -v`: 151 / 151 tests passed.
- `uv run --with ruff ruff check --fix .`: All checks passed.
- `uv run --with ruff ruff format .`: All files formatted.
