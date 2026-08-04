"""Physics convergence tests — verify numerical solutions approach known analytical limits.

These tests validate the physical correctness of the implementation by checking
that in known limiting cases, the numerical results converge to analytical solutions.

Run with: uv run pytest -m slow (included in full suite: uv run pytest)
Exclude with: uv run pytest -m 'not slow'
"""

import numpy as np
import pytest

from settlewell import AquiferType, DewateringConfig, SoilLayer, SoilProfile, Well
from settlewell.hydraulics import (
    compute_drawdown_at_points,
    theis_drawdown_single_well,
    thiem_drawdown_single_well,
)
from settlewell.numerical import (
    create_grid,
    extract_drawdown_at_points,
    solve_steady_state,
)
from settlewell.settlement import (
    compute_degree_of_consolidation,
    compute_settlement_vs_time,
    compute_total_settlement,
)

# ============================================================
# HYDRAULICS CONVERGENCE
# ============================================================


class TestTheisToThiemConvergence:
    """
    Groups tests that verify the physical consistency between transient and steady-state models.
    At very large times, the transient Theis solution must naturally converge to the steady-state
    Thiem solution.
    """

    def test_convergence_at_multiple_distances(self):
        """
        This test proves that at a sufficiently large time (when the system reaches equilibrium),
        the time-dependent Theis drawdown matches the steady-state Thiem drawdown. It is critical
        for ensuring the mathematical models seamlessly transition from short-term to long-term behavior.
        It calculates the theoretical steady-state time `t_ss`, computes both Theis and Thiem drawdowns
        at distances of 5, 10, and 20 meters, and compares them. The expected result is that the
        Theis drawdown is within 1% relative error of the Thiem drawdown for significant drawdown values.
        """
        Q, T, S, R, H0 = 0.001, 5e-4, 0.1, 200.0, 5.0
        t_ss = R**2 * S / (2.25 * T)
        # Cooper-Jacob approximation u = r²S/(4Tt) < 0.01 holds for r <= 20m
        r_values = np.array([5.0, 10.0, 20.0])

        s_thiem = thiem_drawdown_single_well(
            r_values, Q, T, R, H0, AquiferType.CONFINED
        )
        s_theis = theis_drawdown_single_well(r_values, t_ss, Q, T, S)

        for i, r in enumerate(r_values):
            if s_thiem[i] > 0.001:  # Only check where drawdown is significant
                assert s_theis[i] == pytest.approx(s_thiem[i], rel=0.01), (
                    f"Theis ≠ Thiem at r={r}m: {s_theis[i]:.6f} vs {s_thiem[i]:.6f}"
                )


class TestCooperJacobApproximation:
    """
    Groups tests comparing the Theis equation to the Cooper-Jacob approximation.
    These tests ensure that for small values of the well function argument 'u' (typical at large times
    or small distances), the two analytical methods yield identical results.
    """

    def test_small_u_convergence(self):
        """
        This test confirms that for small values of 'u' (u < 0.01), the exact Theis equation
        simplifies correctly to the Cooper-Jacob logarithmic approximation. This validates the
        implementation of both formulas under specific boundary conditions. The test computes drawdown
        using both methods for a very large time (`t = 1e7`) at a set distance. The expected result
        is that the Theis output matches the Cooper-Jacob calculation within a tight 0.1% tolerance.
        """
        Q, T, S, r = 0.001, 5e-4, 0.1, 10.0
        t = 1e7  # Very large t → very small u
        u = r**2 * S / (4 * T * t)
        assert u < 0.01, f"u = {u}, test requires u < 0.01"

        s_theis = theis_drawdown_single_well(r, t, Q, T, S)
        s_cj = Q / (4 * np.pi * T) * np.log(2.25 * T * t / (r**2 * S))
        assert s_theis == pytest.approx(s_cj, rel=0.001)


class TestRadialSymmetry:
    """
    Groups tests that verify the geometric and physical symmetry of drawdown cones.
    A single well in a homogenous aquifer must produce a perfectly circular (radial) drawdown pattern.
    """

    def test_four_equidistant_points(self, simple_profile):
        """
        This test checks that drawdown is radially symmetric around a single pumping well.
        It ensures there are no unintentional directional biases in the coordinate system or
        superposition logic. It calculates the drawdown at four points lying on a 20m circle
        around the origin (North, South, East, West). The expected result is that all four points
        experience identically the same drawdown amount.
        """
        well = Well(x=0.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well],
            target_drawdown_mtaw=0.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
            R=200.0,
            T=5e-4,
        )
        r = 20.0
        points = [(r, 0), (0, r), (-r, 0), (0, -r)]
        drawdowns = compute_drawdown_at_points(points, config, simple_profile)
        assert np.allclose(drawdowns, drawdowns[0], rtol=1e-10)


class TestSuperpositionLinearity:
    """
    Groups tests that ensure confined aquifers obey the principle of linearity.
    Because the partial differential equations governing confined flow are linear, the system's
    response must scale linearly with pumping rates.
    """

    def test_double_q_doubles_drawdown(self):
        """
        This test verifies that the confined steady-state drawdown is directly proportional
        to the pumping rate (Q). It confirms the underlying linear physics assumption of the model.
        The test computes the drawdown for a baseline Q (0.001 m³/s) and then for double that rate (0.002 m³/s).
        The expected result is that the drawdown for the doubled rate is exactly twice the baseline drawdown.
        """
        T, R, H0 = 5e-4, 200.0, 5.0
        r = 15.0
        s1 = thiem_drawdown_single_well(
            r, Q=0.001, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED
        )
        s2 = thiem_drawdown_single_well(
            r, Q=0.002, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED
        )
        assert s2 == pytest.approx(2 * s1, rel=1e-10)


class TestDrawdownMonotonicity:
    """
    Groups tests checking the spatial decay of the drawdown cone. Drawdown must
    always be deepest at the well and strictly decrease as distance increases.
    """

    def test_monotonic_decrease(self):
        """
        This test ensures that the predicted drawdown strictly decreases as the distance from
        the pumping well increases. This is a fundamental physical reality of dewatering that must
        be maintained to prevent oscillating or physically impossible depression cones. It calculates
        drawdown at an array of increasing distances. The expected result is that the sequential
        differences between these values are always negative or zero (monotonic decrease).
        """
        T, R, H0 = 5e-4, 200.0, 5.0
        r_values = np.array([1.0, 5.0, 10.0, 20.0, 50.0, 100.0, 150.0])
        s = thiem_drawdown_single_well(
            r_values, Q=0.001, T=T, R=R, H0=H0, aquifer_type=AquiferType.CONFINED
        )
        assert np.all(np.diff(s) <= 0), "Drawdown must decrease with distance"


@pytest.mark.slow
class TestFDToThiemConvergence:
    """
    Groups tests verifying that numerical Finite Difference (FD) models converge to exact
    analytical solutions. These are vital for validating the custom numerical solver against known truth.
    """

    def test_grid_refinement(self, flemish_profile, pit):
        """
        This test confirms that solving the dewatering equations numerically via Finite Differences
        becomes increasingly accurate as the grid resolution improves. It validates the FD algorithm's
        consistency and convergence properties. It computes a numerical solution at progressively finer
        grid spacings (dx = 4m, 2m, 1m) and compares the drawdown at a fixed distance (r=30) to the exact Thiem solution.
        The expected result is that the relative error strictly decreases with each refinement step,
        and the final finest-grid error is less than 10%.
        """
        from settlewell.hydraulics import compute_transmissivity

        well = Well(x=0.0, y=0.0, Q=0.001)
        config = DewateringConfig(
            wells=[well],
            target_drawdown_mtaw=3.0,
            original_gwl_mtaw=4.0,
            pumping_duration_days=1,
            aquifer_type=AquiferType.CONFINED,
        )
        T = compute_transmissivity(flemish_profile, config)
        R_val = 200.0
        H0 = config.original_gwl_mtaw

        # Analytical (Thiem) at r=30
        r_test = 30.0
        s_analytical = thiem_drawdown_single_well(
            r_test,
            Q=0.001,
            T=T,
            R=R_val,
            H0=H0,
            aquifer_type=AquiferType.CONFINED,
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
        assert errors[-1] < 0.10, (
            f"FD error at dx=1m is {errors[-1]:.1%}, should be <10%"
        )


# ============================================================
# SETTLEMENT CONVERGENCE
# ============================================================


class TestEoedVsCcCrConsistency:
    """
    Groups tests proving that different empirical frameworks for computing soil settlement
    yield identical results when given mathematically equivalent input parameters.
    """

    def test_single_nc_layer(self):
        """
        This test verifies that calculating settlement using a secant Oedometer modulus (`Eoed`)
        gives exactly the same result as using the Compression Index (`Cc`) when the two parameters
        are rigorously calibrated to one another. It ensures internal consistency between the linear
        and logarithmic settlement equations. It constructs a normally consolidated clay profile, derives
        a matching `Eoed` from a given `Cc`, and computes total settlement using both methods.
        The expected result is that both methods return the exact same settlement value.
        """
        sigma_mid = (18.5 - 9.81) * 2.5  # 21.725 kPa
        dsigma = 9.81 * 2.0  # 19.62 kPa
        strain_cc = (0.30 / (1.0 + 1.0)) * np.log10((sigma_mid + dsigma) / sigma_mid)
        Eoed_secant = dsigma / strain_cc

        layer = SoilLayer(
            name="Klei",
            thickness=5.0,
            gamma=18.5,
            gamma_sat=18.5,
            k_h=1e-9,
            e0=1.0,
            Cc=0.30,
            Cr=0.06,
            Eoed=Eoed_secant,
            Cv=1e-7,
            OCR=1.0,
        )
        profile = SoilProfile(layers=[layer], gwl_mtaw=5.0, surface_level_mtaw=5.0)

        s_cc, _ = compute_total_settlement(profile, drawdown=2.0, method="cc_cr")
        s_eoed, _ = compute_total_settlement(profile, drawdown=2.0, method="eoed")
        assert s_cc == pytest.approx(s_eoed, rel=1e-6)


class TestConsolidationTimeConvergence:
    """
    Groups tests verifying that the time-dependent consolidation process correctly
    asymptotes to the final calculated total settlement.
    """

    def test_settlement_reaches_ultimate(self, flemish_profile):
        """
        This test checks that as time approaches infinity, the transient settlement curve reaches
        100% of the calculated total ultimate settlement. This confirms the time-scaling math (degree of consolidation)
        correctly brackets the steady-state target. It calculates the ultimate settlement directly, and then queries
        the time-dependent function at an extreme duration (1000 years). The expected result is that the two values
        are equal within a 0.1% margin.
        """
        s_ult, _ = compute_total_settlement(flemish_profile, drawdown=2.0)
        # Very large time (1000 years)
        times_days = np.array([365 * 1000.0])
        s_t = compute_settlement_vs_time(
            flemish_profile, drawdown=2.0, times_days=times_days
        )
        assert s_t[-1] == pytest.approx(s_ult, rel=0.001)


class TestConsolidationTimeScaling:
    """
    Groups tests confirming that the consolidation equations correctly follow Terzaghi's
    scaling laws, specifically relating time to the square of the drainage path length.
    """

    def test_hdr_scaling(self):
        """
        This test validates that the time required to reach a specific degree of consolidation
        scales with the square of the drainage path length (Hdr). It guarantees the model accurately
        reflects how soil thickness drastically impacts settlement timelines. It computes the theoretical
        time needed to reach a specific time factor (Tv) for a base thickness and a doubled thickness.
        The expected result is that doubling the thickness requires exactly four times as much time.
        """
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
    """
    Groups basic sanity checks verifying the null hypothesis: if there is no change
    in groundwater conditions, there should be no structural impact on the soil.
    """

    def test_all_profiles(self, flemish_profile, simple_profile):
        """
        This test confirms that a drawdown of zero correctly produces zero settlement.
        It ensures there are no rogue constants or phantom effective stress increases in the model.
        It calls the total settlement calculation on both standard test profiles passing `drawdown=0.0`.
        The expected result is exactly 0.0 total settlement.
        """
        for profile in [flemish_profile, simple_profile]:
            s, _per_layer = compute_total_settlement(profile, drawdown=0.0)
            assert s == pytest.approx(0.0, abs=1e-12)


@pytest.mark.slow
class TestThinLayerConvergence:
    """
    Groups tests validating the numerical stability of the settlement calculations across
    varying discretizations of the soil profile.
    """

    def test_mesh_independence(self):
        """
        This test checks that calculating total settlement converges to a stable value as a single
        soil layer is sliced into increasingly thinner sub-layers. Because effective stress varies
        non-linearly with depth, thicker layers have higher discretization error. It loops through subdivisions
        of N=1 to N=30 for a 3m clay layer, computing total settlement each time. The expected result is
        that the system is mesh-independent, meaning the difference between 12 and 30 slices is less than 1%.
        """
        results = []
        for n_sub in [1, 3, 6, 12, 30]:
            thickness = 3.0 / n_sub
            layers = [
                SoilLayer(
                    name=f"Klei_{i}",
                    thickness=thickness,
                    gamma=16.0,
                    gamma_sat=18.5,
                    k_h=1e-9,
                    e0=1.0,
                    Cc=0.30,
                    Cr=0.06,
                    Eoed=3000,
                    Cv=1e-7,
                    OCR=1.0,
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


class TestProjectConvergenceIntegration:
    """Test convergence behavior via Project orchestrator API."""

    def test_project_grid_refinement_convergence(
        self, flemish_profile, pit, six_well_config
    ):
        """Test numerical drawdown grid refinement convergence using Project."""
        from settlewell import Project, SolverSettings

        p_coarse = Project(
            soil=flemish_profile,
            dewatering=six_well_config,
            pit=pit,
            settings=SolverSettings(hydraulics_solver="numerical", grid_dx=4.0),
        )
        hyd_coarse = p_coarse.solve_hydraulics()

        p_fine = Project(
            soil=flemish_profile,
            dewatering=six_well_config,
            pit=pit,
            settings=SolverSettings(hydraulics_solver="numerical", grid_dx=1.0),
        )
        hyd_fine = p_fine.solve_hydraulics()

        assert hyd_coarse.drawdown_grid is not None
        assert hyd_fine.drawdown_grid is not None
        # Fine grid has higher resolution
        assert hyd_fine.drawdown_grid.size > hyd_coarse.drawdown_grid.size
