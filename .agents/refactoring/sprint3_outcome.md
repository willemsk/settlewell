# Sprint 3 Outcome: Settlement & Consolidation Extension

## Summary
Sprint 3 extended the core `settlewell` settlement module by transplanting physics from the GUI layer into the core library, adding instant elastic settlement, secondary creep, equivalent $C_v$ for layered strata, full time-dependent consolidation curves, and Eurocode 7 partial material safety factor utilities.

## Completed Deliverables

1. **`src/settlewell/eurocode.py`**
   - Enum `DesignApproach` (`SLS_CHARACTERISTIC`, `EC7_DA1_M1`, `EC7_DA1_M2`).
   - Function `apply_partial_factors(profile, approach)`: Applies Eurocode 7 partial safety factors ($E_{\text{oed}} / 1.25$, $C_c \times 1.25$, $C_r \times 1.25$ for DA1-M2).

2. **`src/settlewell/settlement.py`**
   - `compute_elastic_settlement(profile, delta_sigma_z)`: Instant elastic settlement $s_e = \sum \frac{\Delta\sigma_z \cdot H}{E_{\text{oed}}}$.
   - `compute_secondary_creep(s_primary, c_alpha_to_cc, t_days, t_p_days)`: Secondary creep settlement $s_{\text{creep}} = s_{\text{primary}} \cdot \frac{C_\alpha}{C_c} \log_{10}(t / t_p)$.
   - `compute_equivalent_cv(profile)`: Stratified equivalent consolidation coefficient $C_{v,\text{eq}}$.
   - `compute_full_consolidation_curve(s_elastic, s_primary_ult, cv_eq, h_dr, times_days)`: Time-dependent consolidation curve combining elastic, primary, and creep components.

3. **`src/settlewell/__init__.py`**
   - Re-exported `apply_partial_factors`, `compute_elastic_settlement`, `compute_secondary_creep`, `compute_equivalent_cv`, and `compute_full_consolidation_curve` in `settlewell.__all__`.

4. **`tests/test_elastic_settlement.py` & `tests/test_eurocode.py`**
   - 9 unit tests verifying elastic settlement calculation, creep thresholds, equivalent $C_v$ formula, time consolidation curve monotonicity, and Eurocode partial factor scaling.

5. **`docs/api/eurocode.md` & `mkdocs.yml`**
   - Added API documentation reference page and updated MkDocs navigation.

## Verification Results
- `uv run pytest -v`: 160 / 160 tests passed.
- `uv run --with ruff ruff check --fix .`: All checks passed.
- `uv run --with ruff ruff format .`: All files formatted.
