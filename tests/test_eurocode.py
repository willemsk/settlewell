import pytest

from settlewell.eurocode import apply_partial_factors
from settlewell.models import DesignApproach, SoilLayer, SoilProfile


@pytest.fixture
def sample_profile() -> SoilProfile:
    layer = SoilLayer(
        name="Test Layer",
        thickness=5.0,
        gamma=17.0,
        gamma_sat=19.0,
        k_h=1e-4,
        e0=0.7,
        Cc=0.20,
        Cr=0.04,
        Eoed=10000.0,
        Cv=2e-7,
    )
    return SoilProfile(layers=[layer], gwl_mtaw=0.0, surface_level_mtaw=5.0)


class TestEurocodePartialFactors:
    def test_sls_characteristic_no_change(self, sample_profile: SoilProfile):
        """Test SLS_CHARACTERISTIC approach does not alter soil parameters."""
        scaled = apply_partial_factors(
            sample_profile, DesignApproach.SLS_CHARACTERISTIC
        )
        assert scaled.layers[0].Eoed == sample_profile.layers[0].Eoed
        assert scaled.layers[0].Cc == sample_profile.layers[0].Cc
        assert scaled.layers[0].Cr == sample_profile.layers[0].Cr

    def test_ec7_da1_m1_no_change(self, sample_profile: SoilProfile):
        """Test EC7_DA1_M1 approach does not alter material soil parameters."""
        scaled = apply_partial_factors(sample_profile, DesignApproach.EC7_DA1_M1)
        assert scaled.layers[0].Eoed == sample_profile.layers[0].Eoed
        assert scaled.layers[0].Cc == sample_profile.layers[0].Cc
        assert scaled.layers[0].Cr == sample_profile.layers[0].Cr

    def test_ec7_da1_m2_scales_parameters(self, sample_profile: SoilProfile):
        """Test EC7_DA1_M2 divides Eoed by 1.25 and multiplies Cc/Cr by 1.25."""
        scaled = apply_partial_factors(sample_profile, DesignApproach.EC7_DA1_M2)
        orig_layer = sample_profile.layers[0]
        scaled_layer = scaled.layers[0]

        assert scaled_layer.Eoed == pytest.approx(orig_layer.Eoed / 1.25)
        assert scaled_layer.Cc == pytest.approx(orig_layer.Cc * 1.25)
        assert scaled_layer.Cr == pytest.approx(orig_layer.Cr * 1.25)
