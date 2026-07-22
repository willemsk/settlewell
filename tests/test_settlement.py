"""Unit tests for settlewell.settlement — Terzaghi consolidation."""
import pytest
import numpy as np
from settlewell import SoilLayer
from settlewell.settlement import (
    compute_initial_stress_profile,
    compute_stress_increase_from_drawdown,
    compute_layer_settlement_cc_cr,
    compute_layer_settlement_eoed,
    compute_total_settlement,
    compute_degree_of_consolidation,
)

GAMMA_W = 9.81


class TestInitialStressProfile:
    def test_increases_with_depth(self, flemish_profile):
        """Effective stress must increase monotonically with depth."""
        z, sigma_eff, _ = compute_initial_stress_profile(flemish_profile)
        assert np.all(np.diff(sigma_eff) > 0)

    def test_correct_switch_at_gwl(self, simple_profile):
        """Above GWL: uses γ_dry. Below GWL: uses γ_sat with buoyancy.
        For a single 5m sand layer with GWL at 1m depth:
        At z=0.5m (above GWL): σ'_v = 17.5 * 0.5 = 8.75 kPa
        At z=1.5m (below GWL): σ'_v = 17.5*1.0 + (20.0-9.81)*0.5 = 17.5 + 5.095 = 22.595 kPa."""
        z_pts = np.array([0.5, 1.5])
        z, sigma_eff, _ = compute_initial_stress_profile(simple_profile, z_points=z_pts)
        assert sigma_eff[0] == pytest.approx(17.5 * 0.5, rel=0.01)
        assert sigma_eff[1] == pytest.approx(17.5 * 1.0 + (20.0 - GAMMA_W) * 0.5, rel=0.01)


class TestStressIncrease:
    def test_zero_above_gwl(self, simple_profile):
        """No stress increase above original water table."""
        z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile, drawdown=2.0, z_points=np.array([0.5]),
        )
        assert dsigma[0] == pytest.approx(0.0)

    def test_full_drawdown_below_new_gwl(self, simple_profile):
        """Below new GWL: Δσ' = γ_w * drawdown.
        GWL at 1m, drawdown = 2m → new GWL at 3m.
        At z=4m: Δσ' = 9.81 * 2.0 = 19.62 kPa."""
        z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile, drawdown=2.0, z_points=np.array([4.0]),
        )
        assert dsigma[0] == pytest.approx(GAMMA_W * 2.0, rel=0.01)

    def test_linear_in_transition_zone(self, simple_profile):
        """Between original and new GWL: linear interpolation.
        GWL at 1m, drawdown=2m → new GWL at 3m.
        At z=2m: Δσ' = γ_w * (2 - 1) = 9.81 kPa."""
        z, dsigma = compute_stress_increase_from_drawdown(
            simple_profile, drawdown=2.0, z_points=np.array([2.0]),
        )
        assert dsigma[0] == pytest.approx(GAMMA_W * 1.0, rel=0.01)


class TestLayerSettlement:
    def test_nc_layer_cc_cr(self, single_clay_layer):
        """Normally consolidated (OCR=1): Δs = Cc/(1+e0) * H * log10((σ0+Δσ)/σ0).
        Cc=0.30, e0=1.0, H=3.0, σ0=50 kPa, Δσ=20 kPa.
        Δs = 0.30/2.0 * 3.0 * log10(70/50) = 0.15 * 3 * 0.1461 = 0.06574 m."""
        single_clay_layer_nc = SoilLayer(
            name="Klei", thickness=3.0, gamma=16.0, gamma_sat=18.5,
            k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=3000, Cv=1e-7, OCR=1.0,
        )
        s = compute_layer_settlement_cc_cr(single_clay_layer_nc, sigma_v0_eff=50.0, delta_sigma_v=20.0)
        expected = (0.30 / 2.0) * 3.0 * np.log10(70 / 50)
        assert s == pytest.approx(expected, rel=0.01)

    def test_oc_layer_uses_cr(self, single_clay_layer):
        """Overconsolidated (OCR=1.5, σ0=50): σ_p=75.
        If Δσ=20 → σ0+Δσ=70 < σ_p=75 → fully OC, uses Cr.
        Δs = Cr/(1+e0) * H * log10(70/50) = 0.06/2.0 * 3.0 * 0.1461 = 0.01315 m."""
        s = compute_layer_settlement_cc_cr(single_clay_layer, sigma_v0_eff=50.0, delta_sigma_v=20.0)
        expected = (0.06 / 2.0) * 3.0 * np.log10(70 / 50)
        assert s == pytest.approx(expected, rel=0.01)

    def test_transitional_splits_correctly(self, single_clay_layer):
        """OCR=1.5, σ0=50 → σ_p=75. Δσ=40 → σ0+Δσ=90 > σ_p.
        Splits: Cr part (50→75) + Cc part (75→90).
        Δs = Cr/(1+e0)*H*log10(75/50) + Cc/(1+e0)*H*log10(90/75)."""
        s = compute_layer_settlement_cc_cr(single_clay_layer, sigma_v0_eff=50.0, delta_sigma_v=40.0)
        cr_part = (0.06 / 2.0) * 3.0 * np.log10(75 / 50)
        cc_part = (0.30 / 2.0) * 3.0 * np.log10(90 / 75)
        assert s == pytest.approx(cr_part + cc_part, rel=0.01)

    def test_eoed_settlement(self, single_clay_layer):
        """Eoed approach: Δs = Δσ/Eoed * H = 20/3000 * 3.0 = 0.020 m."""
        s = compute_layer_settlement_eoed(single_clay_layer, delta_sigma_v=20.0)
        assert s == pytest.approx(20.0 / 3000 * 3.0, rel=0.01)


class TestTotalSettlement:
    def test_zero_drawdown_zero_settlement(self, flemish_profile):
        """No drawdown → no settlement."""
        total, per_layer = compute_total_settlement(flemish_profile, drawdown=0.0)
        assert total == pytest.approx(0.0, abs=1e-12)
        assert all(s == pytest.approx(0.0, abs=1e-12) for s in per_layer)

    def test_sum_matches_total(self, flemish_profile):
        """Sum of per-layer settlements equals returned total."""
        total, per_layer = compute_total_settlement(flemish_profile, drawdown=2.0)
        assert total == pytest.approx(sum(per_layer), rel=1e-10)


class TestDegreeOfConsolidation:
    def test_zero_at_t0(self):
        """U(Tv=0) = 0."""
        assert compute_degree_of_consolidation(0.0) == pytest.approx(0.0)

    def test_converges_to_one(self):
        """U(Tv→∞) → 1."""
        assert compute_degree_of_consolidation(100.0) == pytest.approx(1.0, abs=1e-6)

    def test_known_value_at_tv_05(self):
        """At Tv=0.5, U ≈ 0.764 (standard Terzaghi table value)."""
        U = compute_degree_of_consolidation(0.5)
        assert U == pytest.approx(0.764, abs=0.005)


class TestSettlementVsTime:
    def test_settlement_vs_time_monotonic(self, flemish_profile):
        """Settlement increases monotonically over time toward ultimate value."""
        from settlewell.settlement import compute_settlement_vs_time
        times = np.array([0, 1, 10, 30, 90, 365, 3650])
        s_t = compute_settlement_vs_time(flemish_profile, drawdown=1.5, times_days=times)
        assert s_t[0] >= 0
        assert np.all(np.diff(s_t) >= 0)

    def test_settlement_vs_time_eoed(self, flemish_profile):
        """Time settlement works under eoed method without Cc specified."""
        from settlewell.settlement import compute_settlement_vs_time
        times = np.array([0, 10, 100, 1000])
        s_t = compute_settlement_vs_time(flemish_profile, drawdown=1.5, times_days=times, method="eoed")
        assert s_t[0] >= 0
        assert np.all(np.diff(s_t) >= 0)
        total_eoed, _ = compute_total_settlement(flemish_profile, drawdown=1.5, method="eoed")
        assert s_t[-1] == pytest.approx(total_eoed, rel=0.05)
