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

## 2024-11-20 - Vectorized Dense 2D Grid Evaluations in Stress Module
**Learning:** A double python loop over scalar physics functions (like Fadum/Boussinesq equations) to compute stress heatmaps was causing a massive performance bottleneck.
**Action:** When computing 2D grids (like stress heatmaps), eliminate python loops entirely by vectorizing the underlying mathematical functions to accept `np.meshgrid` arrays. Use `np.broadcast_shapes`/`np.broadcast_arrays` to align dimensions, and use `np.where` or mask arrays for conditional logic. Maintain a fast execution path at the top of these functions checking `not isinstance(var, np.ndarray)` to avoid numpy overhead for individual scalar calls, ensuring backward compatibility with existing public APIs.
