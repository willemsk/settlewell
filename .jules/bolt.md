## 2024-05-15 - Vectorized Drawdown Calculation Bottleneck
**Learning:** The `compute_drawdown_at_points` function in `src/settlewell/hydraulics.py` originally used a python `for` loop to compute the steady-state or transient drawdown over many grid points (often hundreds of thousands in tests or production use cases). This caused a massive CPU bottleneck.
**Action:** When calculating distances, distances relative to extraction wells, and applying analytical formulas (Dupuit/Thiem/Theis) over a dense mesh of spatial points, always use NumPy vectorization (`np.hypot`, array operations) to eliminate python loop overhead.
## 2024-05-24 - Vectorized Laplacian Assembly & Sink Term Accumulation

*   **Bottleneck:** Constructing large 2D sparse Laplacian matrices cell-by-cell using Python `for` loops and `scipy.sparse.lil_matrix` is exceptionally slow for high-resolution grids.
*   **Solution:** Replaced inner loops with `scipy.sparse.diags`. Boundary conditions were mapped to a 1D boolean array (`is_boundary`) to efficiently zero out matrix connections across Dirichlet boundaries without loop iteration.
*   **Edge Case:** When vectorizing source/sink additions (wells), multiple sinks can map to the exact same grid node. A naive slice assignment `b[kws] += Q` results in a "lost update" bug due to how NumPy handles repeated indices during array slicing.
*   **Fix:** Always use `np.add.at(array, indices, values)` for safely accumulating overlapping values in unbuffered operations.
