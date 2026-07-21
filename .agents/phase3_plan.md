# Implementation Plan - Phase 3: Settlement (Consolidation)

Saved snapshot of Phase 3 implementation plan prior to Documentation setup.

Phase 2 has been completed and verified (all 24 unit tests passing).
Phase 3 implements the 1D Terzaghi consolidation and settlement engine in `src/bronbemaling/settlement.py` and unit tests in `tests/test_settlement.py`.

## Status of Previous Phases
- **Phase 1 (Scaffolding & Data Models)**: Completed & Verified (16/16 tests passing).
- **Phase 2 (Hydraulics - Drawdown)**: Completed & Verified (8/8 tests passing, total 24/24 passing).

---

## Detailed Technical Design for Phase 3

### 1. Data Flow & Module Architecture

```
[SoilProfile] + Drawdown [m]
          │
          ├──> compute_initial_stress_profile() ─────────> σ'_v0 per layer midpoint [kPa]
          ├──> compute_stress_increase_from_drawdown() ──> Δσ'_v per layer midpoint [kPa]
          │
          ├──> compute_total_settlement()
          │         │
          │         ├──> compute_layer_settlement_cc_cr()  [Logarithmic Cc/Cr model]
          │         └──> compute_layer_settlement_eoed()   [Linear Eoed model]
          │         │
          │         └──> (total_settlement, per_layer_settlements)
          │
          └──> compute_settlement_vs_time()
                    │
                    ├──> compute_degree_of_consolidation(Tv) [Terzaghi U(Tv) approximation]
                    └──> Settlement curve s(t) [m] vs time [days]
```

---

### 2. Mathematical Formulas & Algorithms

#### A. Initial Effective Stress Profile (`compute_initial_stress_profile`)
- **Signature**: `compute_initial_stress_profile(profile: SoilProfile, z_points: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]`
- **Logic**:
  - Groundwater depth $z_{\text{gw}} = \text{profile.gwl\_depth}$.
  - At depth $z$:
    - For $z \le z_{\text{gw}}$: $\sigma_v(z) = \sum \gamma_{\text{dry}} \cdot \Delta z$, $u = 0$, $\sigma'_v(z) = \sigma_v(z)$.
    - For $z > z_{\text{gw}}$: $\sigma_v(z) = \sigma_v(z_{\text{gw}}) + \sum \gamma_{\text{sat}} \cdot \Delta z$, $u(z) = \gamma_w \cdot (z - z_{\text{gw}})$, $\sigma'_v(z) = \sigma_v(z) - u(z)$.
  - Returns `(z, sigma_v_eff, sigma_v_total)`.

#### B. Stress Increase from Drawdown (`compute_stress_increase_from_drawdown`)
- **Signature**: `compute_stress_increase_from_drawdown(profile: SoilProfile, drawdown: float, z_points: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]`
- **Logic**:
  - $z_{\text{gw}} = \text{profile.gwl\_depth}$, $z_{\text{gw\_new}} = z_{\text{gw}} + \text{drawdown}$.
  - At depth $z$:
    - If $z < z_{\text{gw}}$: $\Delta \sigma'_v = 0$.
    - If $z_{\text{gw}} \le z < z_{\text{gw\_new}}$: $\Delta \sigma'_v = \gamma_w \cdot (z - z_{\text{gw}})$.
    - If $z \ge z_{\text{gw\_new}}$: $\Delta \sigma'_v = \gamma_w \cdot \text{drawdown}$.
  - Returns `(z, delta_sigma_eff)`.

#### C. Layer Settlement Logarithmic Model (`compute_layer_settlement_cc_cr`)
- **Signature**: `compute_layer_settlement_cc_cr(layer: SoilLayer, sigma_v0_eff: float, delta_sigma_v: float) -> float`
- **Logic**:
  - Preconsolidation stress: $\sigma'_p = \text{OCR} \cdot \sigma'_{v0}$.
  - Final stress: $\sigma'_f = \sigma'_{v0} + \Delta \sigma'_v$.
  - **Case 1**: Fully overconsolidated ($\sigma'_f \le \sigma'_p$):
    $$\Delta s = \frac{C_r}{1 + e_0} \cdot H \cdot \log_{10}\left(\frac{\sigma'_f}{\sigma'_{v0}}\right)$$
  - **Case 2**: Fully normally consolidated ($\sigma'_{v0} \ge \sigma'_p$):
    $$\Delta s = \frac{C_c}{1 + e_0} \cdot H \cdot \log_{10}\left(\frac{\sigma'_f}{\sigma'_{v0}}\right)$$
  - **Case 3**: Transitional ($\sigma'_{v0} < \sigma'_p < \sigma'_f$):
    $$\Delta s = \frac{C_r}{1 + e_0} \cdot H \cdot \log_{10}\left(\frac{\sigma'_p}{\sigma'_{v0}}\right) + \frac{C_c}{1 + e_0} \cdot H \cdot \log_{10}\left(\frac{\sigma'_f}{\sigma'_p}\right)$$

#### D. Layer Settlement Linear Model (`compute_layer_settlement_eoed`)
- **Signature**: `compute_layer_settlement_eoed(layer: SoilLayer, delta_sigma_v: float) -> float`
- **Logic**:
  $$\Delta s = \frac{\Delta \sigma'_v}{E_{\text{oed}}} \cdot H$$

#### E. Total Settlement (`compute_total_settlement`)
- **Signature**: `compute_total_settlement(profile: SoilProfile, drawdown: float, method: str = "cc_cr") -> tuple[float, list[float]]`
- **Logic**:
  - Evaluates $\sigma'_{v0, i}$ and $\Delta \sigma'_{v, i}$ at layer midpoints $z_{\text{mid}, i}$.
  - Calculates $\Delta s_i$ per layer using `cc_cr` or `eoed` method.
  - Returns `(sum(delta_s), delta_s_list)`.

#### F. Degree of Consolidation $U(T_v)$ (`compute_degree_of_consolidation`)
- **Signature**: `compute_degree_of_consolidation(Tv: float) -> float`
- **Logic**:
  - If $T_v \le 0.2827$: $U = \sqrt{\frac{4 T_v}{\pi}}$
  - If $T_v > 0.2827$: $U = 1 - \frac{8}{\pi^2} \exp\left(-\frac{\pi^2 T_v}{4}\right)$
  - Return $U \in [0, 1]$.

#### G. Time-Dependent Consolidation (`compute_settlement_vs_time`)
- **Signature**: `compute_settlement_vs_time(profile: SoilProfile, drawdown: float, times_days: np.ndarray, method: str = "cc_cr") -> np.ndarray`
- **Logic**:
  - Determines $H_{\text{dr}}$ for clay layers:
    - Double drainage (sand above and below): $H_{\text{dr}} = \frac{H}{2}$.
    - Single drainage (sand on one side only): $H_{\text{dr}} = H$.
  - Computes layer settlement over time $s_i(t) = U(T_v(t)) \cdot s_{i, \text{ult}}$.
  - Returns array $s(t)$ for all time steps.

---

## Proposed Changes

### [NEW] [settlement.py](file:///d:/repos/bronbemaling/src/bronbemaling/settlement.py)
Implement `compute_initial_stress_profile`, `compute_stress_increase_from_drawdown`, `compute_layer_settlement_cc_cr`, `compute_layer_settlement_eoed`, `compute_total_settlement`, `compute_degree_of_consolidation`, `compute_settlement_vs_time`.

### [MODIFY] [__init__.py](file:///d:/repos/bronbemaling/src/bronbemaling/__init__.py)
Re-export settlement calculation functions.

### [NEW] [test_settlement.py](file:///d:/repos/bronbemaling/tests/test_settlement.py)
Unit tests for initial stress profiles, stress increase from drawdown, layer settlement (NC, OC, transitional, Eoed), total settlement, and degree of consolidation.

---

## Verification Plan

### Automated Tests
```bash
uv run pytest tests/test_settlement.py -v
uv run pytest -v
```
