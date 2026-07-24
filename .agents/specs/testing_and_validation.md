# Testing & Physics Validation Specification

This document specifies the pytest test suite structure (`tests/`), physics convergence testing (`tests/test_physics_convergence.py`), and documentation plot generation scripts (`scripts/generate_docs_plots.py`).

---

## Test Suite Structure (`tests/`)

The test suite is structured into Pytest test classes across 9 test modules:

```
tests/
├── conftest.py                          # Shared pytest fixtures (soil profiles, pits, wells, buildings)
├── test_models.py                       # Dataclass validation & corner rotation tests
├── test_hydraulics.py                   # Analytical drawdown & transmissivity tests
├── test_settlement.py                   # Terzaghi stress & consolidation settlement tests
├── test_damage.py                       # Burland/Wroth & SBR damage classification tests
├── test_numerical.py                    # 2D Finite-Difference groundwater solver tests
├── test_plotting.py                     # Plotting suite figure generation tests
├── test_physics_convergence.py          # Physics convergence & limiting-case tests (@slow)
└── test_gui.py                          # PySide6 Desktop GUI import & project I/O tests
```

---

## Test Organization & Class Structure

### 1. Model Validation Tests (`tests/test_models.py`)
- **`TestSoilLayerValidation`**: Rejects invalid values (negative thickness, `gamma_sat < gamma`).
- **`TestSoilProfile`**: Rejects `gwl_mtaw > surface_level_mtaw` and empty layer lists; tests elevation/depth conversions (`mtaw_to_depth`).
- **`TestBuilding`**: Verifies 4 corner coordinates at $0^\circ$ and $90^\circ$ rotation angles.
- **`TestModelsEdgeCases`**: Edge-case validation for `SoilLayer` and `SoilProfile`.

### 2. Analytical Hydraulics Tests (`tests/test_hydraulics.py`)
- **`TestTransmissivity`**: Verifies equivalent transmissivity $T = \sum k_i d_i$.
- **`TestThiemDrawdown`**: Hand-calculated steady-state drawdown vs radial distance $r$.
- **`TestTheisDrawdown`**: Hand-calculated transient drawdown using `exp1(u)`.
- **`TestSuperposition`**: Verifies 2-well linear/quadratic head superposition at midpoint.

### 3. Settlement Tests (`tests/test_settlement.py`)
- **`TestStressProfile`**: Initial effective vertical stress profiles with depth $\sigma'_v(z)$.
- **`TestStressIncrease`**: Effective stress increase $\Delta \sigma' = \gamma_w \cdot s$.
- **`TestSettlementCcCr`**: Normally vs overconsolidated settlement ($C_c$ vs $C_r$).
- **`TestSettlementEoed`**: Linear oedometer modulus settlement method ($E_{oed}$).
- **`TestConsolidationTime`**: Terzaghi degree of consolidation $U(T_v)$ approximations.
- **`TestSettlementVsTime`**: Time-dependent settlement progression $s(t)$.
- **`TestSettlementEdgeCases`**: Single vs double drainage conditions and zero drawdown edge cases.

### 4. Building Damage Tests (`tests/test_damage.py`)
- **`TestClassifyDamage`**: Translates angular distortion $\beta$ into SBR damage categories 0–5 and risk colors.
- **`TestAssessBuildingDamage`**: Full building assessment (`differential_settlement`, $\beta$, $\Delta / L$, concrete frame discount).

### 5. Numerical Solver Tests (`tests/test_numerical.py`)
- **`TestCreateGrid`**: Verifies regular 2D mesh grid creation dimensions $(nx, ny)$.
- **`TestSolveSteadyState`**: Solves sparse system $A h = b$ for steady-state groundwater head.
- **`TestExtractDrawdown`**: Extracts interpolated non-negative drawdown at points.

### 6. Plotting Smoke Tests (`tests/test_plotting.py`)
- **`TestPlottingFunctions`**: Verifies functions return valid Matplotlib `plt.Figure` or Plotly `go.Figure` objects without crashing.

### 7. Physics Convergence Tests (`tests/test_physics_convergence.py`)
- **`TestFDToThiemConvergence`** (`@pytest.mark.slow`): Confirms 2D FD grid refinement converges to analytical Thiem steady-state solution within $10\%$ as grid spacing $\Delta x \to 0$.
- **`TestThinLayerConvergence`** (`@pytest.mark.slow`): Confirms mesh independence as thick clay layers are subdivided into $N \in [1, 30]$ sublayers (relative diff $< 1\%$).
- **`TestTheisToThiemConvergence`**: Confirms unsteady-state Theis drawdown $s(r, t)$ converges to steady-state Thiem drawdown as $t \to \infty$.
- **`TestCooperJacobApproximation`**: Verifies Cooper-Jacob logarithmic approximation error vs exact Theis $W(u)$ is $< 0.1\%$ for small $u < 0.01$.

### 8. GUI Tests (`tests/test_gui.py`)
- **`TestGUIImport`**: Uses top-level `pytest.skip(allow_module_level=True)` guard to skip gracefully if PySide6 is uninstalled.
- **`TestProjectIO`**: Tests saving and loading `.settlewell` JSON project state envelope.

---

## Validation Plot Generator Script (`scripts/generate_docs_plots.py`)

Generates 4 vector SVG validation plots and saves them to `docs/assets/images/`:

1. `fd_grid_refinement.svg`: 2D FD vs Thiem drawdown grid refinement convergence.
2. `theis_to_thiem_convergence.svg`: Unsteady-state Theis drawdown converging to Thiem as $t \to \infty$.
3. `mesh_independence.svg`: Sublayering mesh independence convergence curve.
4. `cooper_jacob_approximation.svg`: Relative error scan of Cooper-Jacob approximation vs Theis $W(u)$.

---

## Verification Commands & Protocol

1. **Fast Unit Tests**:
   ```bash
   uv run pytest -m "not slow"
   ```
2. **Full Test Suite (Including Slow Physics Tests)**:
   ```bash
   uv run pytest -v
   ```
3. **GUI Tests Only**:
   ```bash
   uv run pytest tests/test_gui.py -v
   ```
4. **Validation SVG Plot Generation**:
   ```bash
   uv run python scripts/generate_docs_plots.py
   ```
5. **Documentation Build Gate**:
   ```bash
   uv run --extra docs mkdocs build
   ```
