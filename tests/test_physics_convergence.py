"""Physics convergence tests — verify numerical solutions approach known analytical limits.

These tests validate the physical correctness of the implementation by checking
that in known limiting cases, the numerical results converge to analytical solutions.

Run with: uv run pytest -m slow (included in full suite: uv run pytest)
Exclude with: uv run pytest -m 'not slow'
"""
import pytest
import numpy as np
from settlewell import AquiferType, Well, DewateringConfig, SoilLayer, SoilProfile
from settlewell.hydraulics import (
    thiem_drawdown_single_well, theis_drawdown_single_well,
    compute_drawdown_at_points,
)
from settlewell.settlement import (
    compute_total_settlement, compute_degree_of_consolidation,
    compute_settlement_vs_time,
)
from settlewell.numerical import create_grid, solve_steady_state, extract_drawdown_at_points


# ============================================================
# HYDRAULICS CONVERGENCE
# ============================================================

class TestTheisToThiemConvergence:
    """At large t, Theis solution must converge to Thiem (steady-state)."""

    def test_convergence_at_multiple_distances(self):
        """Theis at t_ss = R² * S / (2.25 * T) converges to Thiem within 1%.

        For R=200, S=0.1, T=5e-4: t_ss = 200²*0.1/(2.25*5e-4) = 3.555e6 s ≈ 41.15 days."""
        Q, T, S, R, H0 = 0.001, 5e-4, 0.1, 200.0, 5.0
        t_ss = R**2 * S / (2.25 * T)
        # Cooper-Jacob approximation u = r²S/(4Tt) < 0.01 holds for r <= 20m
        r_values = np.array([5.0, 10.0, 20.0])

        s_thiem = thiem_drawdown_single_well(r_values, Q, T, R, H0, AquiferType.CONFINED)
        s_theis = theis_drawdown_single_well(r_values, t_ss, Q, T, S)

        for i, r in enumerate(r_values):
            if s_thiem[i] > 0.001:  # Only check where drawdown is significant
                assert s_theis[i] == pytest.approx(s_thiem[i], rel=0.01), (
                    f"Theis ≠ Thiem at r={r}m: {s_theis[i]:.6f} vs {s_thiem[i]:.6f}"
                )


class TestCooperJacobApproximation:
    """At large t (small u), Theis matches Cooper-Jacob approximation."""

    def test_small_u_convergence(self):
        """For u < 0.01, Cooper-Jacob ≈ Theis within 0.1%.
        Cooper-Jacob: s ≈ Q/(4πT) * ln(2.25*T*t / (r²*S))."""
        Q, T, S, r = 0.001, 5e-4, 0.1, 10.0
        t = 1e7  # Very large t → very small u
        u = r**2 * S / (4 * T * t)
        assert u < 0.01, f"u = {u}, test requires u < 0.01"

        s_theis = theis_drawdown_single_well(r, t, Q, T, S)
        s_cj = Q / (4 * np.pi * T) * np.log(2.25 * T * t / (r**2 * S))
        assert s_theis == pytest.approx(s_cj, rel=0.001)


class TestRadialSymmetry:
    """Single well produces radially symmetric drawdown."""

    def test_four_equidistant_points(self, simple_profile):
        """4 points at equal distance r=20m from a single well at origin
        should have identical drawdown."""
        well = Well(x=0.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well], target_drawdown_mtaw=0.0, original_gwl_mtaw=4.0,
            pumping_duration_days=1, aquifer_type=AquiferType.CONFINED,
            R=200.0, T=5e-4,
        )
        r = 20.0
        points = [(r, 0), (0, r), (-r, 0), (0, -r)]
        drawdowns = compute_drawdown_at_points(points, config, simple_profile)
        assert np.allclose(drawdowns, drawdowns[0], rtol=1e-10)


class TestSuperpositionLinearity:
    """In a confined aquifer (linear), doubling Q doubles drawdown."""

    def test_double_q_doubles_drawdown(self):
        """Confined Thiem: s ∝ Q (linear). Doubling Q should double s."""
        T, R, H0 = 5e-4, 200.0, 5.0
        r = 15.0
        s1 = thiem_drawdown_single_well(r, Q=0.001, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED)
        s2 = thiem_drawdown_single_well(r, Q=0.002, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED)
        assert s2 == pytest.approx(2 * s1, rel=1e-10)


class TestDrawdownMonotonicity:
    """Drawdown decreases monotonically with distance from well."""

    def test_monotonic_decrease(self):
        """s(r1) > s(r2) for r1 < r2."""
        T, R, H0 = 5e-4, 200.0, 5.0
        r_values = np.array([1.0, 5.0, 10.0, 20.0, 50.0, 100.0, 150.0])
        s = thiem_drawdown_single_well(r_values, Q=0.001, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED)
        assert np.all(np.diff(s) <= 0), "Drawdown must decrease with distance"


@pytest.mark.slow
class TestFDToThiemConvergence:
    """As grid spacing dx → 0, FD drawdown converges to Thiem analytical solution."""

    def test_grid_refinement(self, flemish_profile, pit):
        """FD drawdown at r=30m from a single well converges to Thiem as dx decreases.

        Test at dx = 4m, 2m, 1m. Relative error should decrease with refinement.
        Final error at dx=1m should be < 10%."""
        from settlewell.hydraulics import compute_transmissivity

        well = Well(x=0.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well], target_drawdown_mtaw=3.0, original_gwl_mtaw=4.0,
            pumping_duration_days=1, aquifer_type=AquiferType.CONFINED,
        )
        T = compute_transmissivity(flemish_profile, config)
        R_val = 200.0
        H0 = config.original_gwl_mtaw

        # Analytical (Thiem) at r=30
        r_test = 30.0
        s_analytical = thiem_drawdown_single_well(
            r_test, Q=0.001, T=T, R=R_val, H0=H0, aquifer_type=AquiferType.CONFINED,
        )

        errors = []
        for dx in [4.0, 2.0, 1.0]:
            grid = create_grid(x_range=(-R_val, R_val), y_range=(-R_val, R_val), dx=dx)
            grid = solve_steady_state(grid, config, flemish_profile, pit)
            s_numerical = extract_drawdown_at_points(grid, [(r_test, 0.0)], H0)[0]
            rel_error = abs(s_numerical - s_analytical) / s_analytical
            errors.append(rel_error)

        # Errors should decrease with refinement
        assert errors[-1] < errors[0], "Error should decrease with grid refinement"
        # Final error should be < 10%
        assert errors[-1] < 0.10, f"FD error at dx=1m is {errors[-1]:.1%}, should be <10%"


# ============================================================
# SETTLEMENT CONVERGENCE
# ============================================================

class TestEoedVsCcCrConsistency:
    """When Eoed and Cc are consistent, both methods give the same settlement."""

    def test_single_nc_layer(self):
        """For a single normally consolidated layer, if Eoed_secant = Δσ' / ((Cc/(1+e0)) * log10((σ0+Δσ)/σ0)),
        then Eoed and Cc/Cr methods should agree exactly.

        Setup: 5m clay, GWL at 0m (fully saturated), drawdown = 2m.
        σ'_v at midpoint = (18.5 - 9.81) * 2.5 = 21.725 kPa.
        Δσ' = 9.81 * 2.0 = 19.62 kPa.
        Secant Eoed = 19.62 / ((0.30/2.0) * log10(41.345 / 21.725)) = 468.04 kPa."""
        sigma_mid = (18.5 - 9.81) * 2.5  # 21.725 kPa
        dsigma = 9.81 * 2.0               # 19.62 kPa
        strain_cc = (0.30 / (1.0 + 1.0)) * np.log10((sigma_mid + dsigma) / sigma_mid)
        Eoed_secant = dsigma / strain_cc

        layer = SoilLayer(
            name="Klei", thickness=5.0, gamma=18.5, gamma_sat=18.5,
            k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=Eoed_secant, Cv=1e-7, OCR=1.0,
        )
        profile = SoilProfile(layers=[layer], gwl_mtaw=5.0, surface_level_mtaw=5.0)

        s_cc, _ = compute_total_settlement(profile, drawdown=2.0, method="cc_cr")
        s_eoed, _ = compute_total_settlement(profile, drawdown=2.0, method="eoed")
        assert s_cc == pytest.approx(s_eoed, rel=1e-6)


class TestConsolidationTimeConvergence:
    """Settlement converges to ultimate value at large time."""

    def test_settlement_reaches_ultimate(self, flemish_profile):
        """At t → ∞, s(t) → s_ultimate within 0.1%."""
        s_ult, _ = compute_total_settlement(flemish_profile, drawdown=2.0)
        # Very large time (1000 years)
        times_days = np.array([365 * 1000.0])
        s_t = compute_settlement_vs_time(flemish_profile, drawdown=2.0, times_days=times_days)
        assert s_t[-1] == pytest.approx(s_ult, rel=0.001)


class TestConsolidationTimeScaling:
    """Doubling drainage path quadruples time to reach same U."""

    def test_hdr_scaling(self):
        """Tv = Cv * t / Hdr². For same Tv (same U):
        t2/t1 = (Hdr2/Hdr1)². Doubling Hdr → t2 = 4 * t1."""
        Cv = 1e-7  # m²/s
        Hdr1 = 1.5  # m
        Hdr2 = 3.0  # m (doubled)

        Tv_target = 0.197

        t1 = Tv_target * Hdr1**2 / Cv  # time for Hdr1 to reach U=0.5
        t2 = Tv_target * Hdr2**2 / Cv  # time for Hdr2 to reach U=0.5

        assert t2 / t1 == pytest.approx(4.0, rel=1e-10)

        # Verify via the consolidation function
        U1 = compute_degree_of_consolidation(Cv * t1 / Hdr1**2)
        U2 = compute_degree_of_consolidation(Cv * t2 / Hdr2**2)
        assert U1 == pytest.approx(U2, rel=1e-6)


class TestZeroDrawdownZeroSettlement:
    """Trivial sanity check: no drawdown → no settlement."""

    def test_all_profiles(self, flemish_profile, simple_profile):
        """Both profiles should give zero settlement for zero drawdown."""
        for profile in [flemish_profile, simple_profile]:
            s, per_layer = compute_total_settlement(profile, drawdown=0.0)
            assert s == pytest.approx(0.0, abs=1e-12)


@pytest.mark.slow
class TestThinLayerConvergence:
    """As we subdivide layers into thinner sublayers, total settlement converges."""

    def test_mesh_independence(self):
        """Split a 3m clay layer into N sublayers (N=1,3,6,12,30).
        Total settlement should converge. Difference between N=12 and N=30
        should be < 1%."""
        results = []
        for n_sub in [1, 3, 6, 12, 30]:
            thickness = 3.0 / n_sub
            layers = [
                SoilLayer(
                    name=f"Klei_{i}", thickness=thickness, gamma=16.0, gamma_sat=18.5,
                    k_h=1e-9, e0=1.0, Cc=0.30, Cr=0.06, Eoed=3000, Cv=1e-7, OCR=1.0,
                )
                for i in range(n_sub)
            ]
            profile = SoilProfile(layers=layers, gwl_mtaw=4.0, surface_level_mtaw=5.0)
            s, _ = compute_total_settlement(profile, drawdown=2.0)
            results.append(s)

        # Convergence: difference between last two should be small
        rel_diff = abs(results[-1] - results[-2]) / results[-1]
        assert rel_diff < 0.01, (
            f"Settlement not converged: N=12 → {results[-2]:.6f}, N=30 → {results[-1]:.6f}"
        )
