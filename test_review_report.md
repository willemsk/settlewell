# Comprehensive Unit Test Review Report: `settlewell` Package

## 1. Current Status & Failing Tests
Overall baseline coverage across the codebase is **~93%** (measured against the `src/settlewell` package). While high, it falls short of the target 100%.
During the initial run, **2 tests failed**, both inside `test_hydraulics.py` / `test_physics_convergence.py`.
* **Failing Tests:**
    * `TestSuperposition.test_two_symmetric_wells_at_midpoint`
    * `TestRadialSymmetry.test_four_equidistant_points`
* **Root Cause:** A `NameError: name 'Well' is not defined` on line 286 in `src/settlewell/hydraulics.py`. The `Well` class is referenced within inner functions inside `compute_drawdown_at_points` but it is not imported into the file. The implementation is bugged due to this missing import (`from .models import Well`).

---

## 2. Missing Coverage & Edge Cases Identified by Module

### A. `models.py` (Current Coverage: ~85-87%)
The missing coverage in this file entirely consists of untested branches in the validation checks inside the `__post_init__` methods of the various dataclasses. To reach 100%, tests need to trigger these specific `ValueError` conditions:
* **`SoilLayer`:**
  * `e0 < 0` (initial void ratio)
  * `Cc < 0` (compression index)
  * `Cr < 0` (recompression index)
  * `Cr > Cc` (recompression exceeding virgin compression)
* **`SoilProfile`:**
  * Converting custom elevations/depths using `mtaw_to_depth` and `depth_to_mtaw` explicitly.
* **`Well`:**
  * `r_w <= 0` (well radius)
  * `screen_top_mtaw < screen_bottom_mtaw` (inverted well screen)
* **`ConstructionPit`:**
  * `length <= 0`, `width <= 0`, and `depth <= 0`
* **`DewateringConfig`:**
  * `target_drawdown_mtaw > original_gwl_mtaw`
  * `pumping_duration_days <= 0`
  * Explicitly provided `R <= 0`, `T <= 0`, and `S <= 0`
* **`Building`:**
  * `length <= 0`, `width <= 0`
  * `foundation_depth < 0`

### B. `hydraulics.py` (Current Coverage: ~85-89%)
A few critical logic branches and analytical paths are untested:
* **Confined layer filtering (`compute_transmissivity`, lines 58-63):** Logic that filters out clay/aquitards to determine the transmissivity of the main aquifer is not being explicitly tested by a profile layout that triggers the `if not confined_layers` and fallback filtering mechanism.
* **Transient & Steady-State confined superposition paths (`compute_drawdown_at_points`, lines 287-302):** The inner logic for looping over wells in confined and unconfined transient states (and steady-state linear superposition paths) are not being successfully run (because of the `NameError` crash and missing distinct aquifer tests).
* **Missing Import Bug:** Fix the missing import for `Well`.

### C. `settlement.py` (Current Coverage: ~94%)
Generally well-tested, but misses a few key logical edges:
* **Grid Node / Depth Node Override (`compute_stress_increase_from_drawdown`, lines 122-127):** The fallback logic where evaluation depth nodes (`z_eval`) are generated at the center of each layer when not explicitly provided by the user is untested.
* **Unknown Settlement Method Fallback (`compute_total_settlement`, line 277):** The `ValueError` exception raised when an invalid `method` string (not `'cc_cr'` or `'eoed'`) is passed.
* **Single Drainage Condition (`compute_settlement_vs_time`, line 352):** The logic evaluating consolidation times checks adjacent layer permeability (`k_h`) to determine if a layer undergoes single or double drainage. The single drainage branch (`Hdr = layer.thickness`) is currently untested.

### D. `damage.py` (Current Coverage: ~96%)
Coverage is near perfect. The only gap:
* **Max Damage Category Fallback (lines 106-107):** A loop matches settlement limits to an `SBR_THRESHOLDS` category. The fallback that occurs if the settlement exceeds all predefined finite limits isn't hit (though practically difficult because the final threshold limit is infinity).

### E. `numerical.py` (Current Coverage: ~97%)
* **Well on Grid Boundary Warning (lines 148-150):** The sparse linear finite-difference solver expects wells to be placed on interior nodes. A specific `warnings.warn` is emitted if a well is mapped exactly on the 0-th or N-th grid boundary. This warning edge case is untested.

### F. `plotting.py` (Current Coverage: ~99%)
* **Default Soil Color (line 33):** The `get_soil_color` helper function iterates over predefined strings (like "clay", "sand", etc.). If an unknown soil name is provided, it falls back to a default `"#B0C4DE"` color. This unknown soil edge case is untested.

---

## 3. Summary of Actions Required
To hit **100% coverage**, we must:
1. Fix the `NameError` implementation bug in `hydraulics.py`.
2. Add a robust test suite focusing heavily on `models.py` validation edge cases.
3. Construct specific test fixtures (e.g., an unknown soil string, single-drainage profile, out-of-bounds well placement) to hit the missing conditional branches in the other modules.
