## 2024-05-15 - Vectorized Drawdown Calculation Bottleneck
**Learning:** The `compute_drawdown_at_points` function in `src/settlewell/hydraulics.py` originally used a python `for` loop to compute the steady-state or transient drawdown over many grid points (often hundreds of thousands in tests or production use cases). This caused a massive CPU bottleneck.
**Action:** When calculating distances, distances relative to extraction wells, and applying analytical formulas (Dupuit/Thiem/Theis) over a dense mesh of spatial points, always use NumPy vectorization (`np.hypot`, array operations) to eliminate python loop overhead.

## 2024-05-24 - Vectorized Laplacian Assembly & Sink Term Accumulation
*   **Bottleneck:** Constructing large 2D sparse Laplacian matrices cell-by-cell using Python `for` loops and `scipy.sparse.lil_matrix` is exceptionally slow for high-resolution grids.
*   **Solution:** Replaced inner loops with `scipy.sparse.diags`. Boundary conditions were mapped to a 1D boolean array (`is_boundary`) to efficiently zero out matrix connections across Dirichlet boundaries without loop iteration.
*   **Edge Case:** When vectorizing source/sink additions (wells), multiple sinks can map to the exact same grid node. A naive slice assignment `b[kws] += Q` results in a "lost update" bug due to how NumPy handles repeated indices during array slicing.
*   **Fix:** Always use `np.add.at(array, indices, values)` for safely accumulating overlapping values in unbuffered operations.

## 2026-07-26 - Vectorized Grid Points Generation
**Learning:** `compute_drawdown_grid` used `list(zip(X.ravel(), Y.ravel()))` to generate `points`. This operation was creating a list of tuples which was exceedingly slow for large meshes (e.g. 500x500 grid taking 1.5 seconds instead of 0.1 seconds), and `compute_drawdown_at_points` was converting it back into a NumPy array immediately.
**Action:** When passing data between grid generation and vectorized numerical computation functions, avoid generating large standard Python lists (such as `list(zip(...))`). Instead, use NumPy stack/concatenation functions like `np.column_stack` and type hint downstream functions to accept `np.ndarray` types.

## 2024-08-01 - Vectorized Grid Point Generation Bottleneck
*   **Bottleneck:** Using `list(zip(X.ravel(), Y.ravel()))` to convert large meshgrid arrays into pairs of coordinate points is extremely slow and causes unnecessary memory allocations and python loop overhead for high-resolution grids.
*   **Solution:** Replace with `np.column_stack((X.ravel(), Y.ravel()))` which is heavily optimized natively in C by NumPy.
*   **Action:** When passing points to vectorized numerical computations from large multi-dimensional arrays, avoid generating large standard Python lists using `zip` and instead use NumPy stack/concatenation functions like `np.column_stack`.

## 2024-11-20 - Vectorized Stress Heatmap Generation
*   **Bottleneck:** Evaluating complex scalar equations (e.g. `fadum_corner_stress`, `boussinesq_rectangular_stress`) iteratively in double `for` loops across large depth/distance grids scales terribly. Testing indicated ~0.3s just for a 200x200 grid point stress heatmap generation.
*   **Solution:** Removed Python loops in `compute_stress_profile_under_loads` and `compute_stress_heatmap`, processing multi-dimensional inputs with `np.meshgrid` arrays. Modified math functions to branch conditionally and process arrays natively, dropping execution time to ~0.02s (10x faster).
*   **Action:** When vectorizing multi-dimensional inputs in numerical equations to accept NumPy grids, maintain a scalar fast path using explicit scalar type checks (`not isinstance(val, np.ndarray)`), explicitly handle shape broadcasting (`np.broadcast_shapes`), suppress runtime warnings (`with np.errstate`), conditionally index via boolean masks, and preserve dimensionality upon exit (`if out.ndim == 1: ...`).
