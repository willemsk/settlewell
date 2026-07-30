import numpy as np
import pytest

from settlewell.models import SoilLayer, SoilProfile
from settlewell.settlement import (
    compute_elastic_settlement,
    compute_equivalent_cv,
    compute_full_consolidation_curve,
    compute_secondary_creep,
)


@pytest.fixture
def sample_profile() -> SoilProfile:
    layer1 = SoilLayer(
        name="Sand",
        thickness=2.0,
        gamma=17.0,
        gamma_sat=19.0,
        k_h=1e-4,
        e0=0.6,
        Cc=0.05,
        Cr=0.01,
        Eoed=10000.0,
        Cv=1e-7,
    )
    layer2 = SoilLayer(
        name="Clay",
        thickness=3.0,
        gamma=16.0,
        gamma_sat=18.0,
        k_h=1e-8,
        e0=0.9,
        Cc=0.3,
        Cr=0.05,
        Eoed=15000.0,
        Cv=4e-7,
    )
    return SoilProfile(layers=[layer1, layer2], gwl_mtaw=0.0, surface_level_mtaw=5.0)


class TestElasticSettlement:
    def test_elastic_settlement_calculation(self, sample_profile: SoilProfile):
        """Test elastic settlement s_e = sum(dsigma * H / Eoed)."""
        delta_sigma_z = np.array([20.0, 30.0])
        s_e = compute_elastic_settlement(sample_profile, delta_sigma_z)
        # Expected: (20*2/10000) + (30*3/15000) = 0.004 + 0.006 = 0.010 m
        assert s_e == pytest.approx(0.010)

    def test_zero_stress_gives_zero_settlement(self, sample_profile: SoilProfile):
        """Test zero stress increment yields zero elastic settlement."""
        delta_sigma_z = np.array([0.0, 0.0])
        s_e = compute_elastic_settlement(sample_profile, delta_sigma_z)
        assert s_e == 0.0


class TestSecondaryCreep:
    def test_creep_before_primary_completion(self):
        """Test creep settlement is zero before t_p."""
        s_creep = compute_secondary_creep(
            s_primary=0.1, c_alpha_to_cc=0.05, t_days=50.0, t_p_days=100.0
        )
        assert s_creep == 0.0

    def test_creep_after_primary_completion(self):
        """Test creep settlement calculation s_creep = s_primary * C_alpha/Cc * log10(t/t_p)."""
        s_creep = compute_secondary_creep(
            s_primary=0.1, c_alpha_to_cc=0.05, t_days=1000.0, t_p_days=100.0
        )
        # Expected: 0.1 * 0.05 * log10(1000/100) = 0.005 m
        assert s_creep == pytest.approx(0.005)


class TestEquivalentCv:
    def test_equivalent_cv_calculation(self):
        """Test equivalent Cv calculation for layered profile."""
        l1 = SoilLayer(
            name="Layer1",
            thickness=2.0,
            gamma=17.0,
            gamma_sat=19.0,
            k_h=1e-4,
            e0=0.6,
            Cc=0.05,
            Cr=0.01,
            Eoed=10000.0,
            Cv=1e-7,
        )
        l2 = SoilLayer(
            name="Layer2",
            thickness=8.0,
            gamma=16.0,
            gamma_sat=18.0,
            k_h=1e-8,
            e0=0.9,
            Cc=0.3,
            Cr=0.05,
            Eoed=15000.0,
            Cv=4e-7,
        )
        profile = SoilProfile(layers=[l1, l2], gwl_mtaw=0.0, surface_level_mtaw=10.0)

        cv_eq = compute_equivalent_cv(profile)
        # H_total = 10. Denom = 2/sqrt(1e-7) + 8/sqrt(4e-7) = 6324.555 + 12649.111 = 18973.666
        # Cv_eq = 100 / (18973.666)^2 = 2.777777e-7 m^2/s
        assert cv_eq == pytest.approx(2.77777777e-7, rel=1e-4)


class TestFullConsolidationCurve:
    def test_full_consolidation_curve(self):
        """Test time-dependent consolidation curve combining elastic, primary, and creep."""
        times_days = np.array([0.0, 365.0, 3650.0])
        curve = compute_full_consolidation_curve(
            s_elastic=0.01,
            s_primary_ult=0.1,
            cv_eq=1e-7,
            h_dr=5.0,
            times_days=times_days,
            c_alpha_to_cc=0.05,
            t_p_days=365.0,
        )

        assert len(curve) == 3
        # At t=0, settlement equals instant elastic settlement
        assert curve[0] == pytest.approx(0.01)
        # Settlement strictly increases over time
        assert curve[1] > curve[0]
        assert curve[2] > curve[1]
