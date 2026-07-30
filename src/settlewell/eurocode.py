"""Eurocode 7 partial factor application for geotechnical soil profiles."""

from settlewell.models import DesignApproach, SoilLayer, SoilProfile


def apply_partial_factors(
    profile: SoilProfile, approach: DesignApproach = DesignApproach.SLS_CHARACTERISTIC
) -> SoilProfile:
    """
    Apply Eurocode 7 partial material safety factors to a soil profile.

    Parameters
    ----------
    profile : SoilProfile
        The original soil profile.
    approach : DesignApproach, optional
        The design approach to apply. Default is DesignApproach.SLS_CHARACTERISTIC.

    Returns
    -------
    SoilProfile
        A new SoilProfile with scaled soil parameters.

    Raises
    ------
    ValueError
        If `approach` is not a recognized `DesignApproach`.
    """
    if (
        approach == DesignApproach.SLS_CHARACTERISTIC
        or approach == DesignApproach.EC7_DA1_M1
    ):
        return profile.model_copy(deep=True)

    if approach == DesignApproach.EC7_DA1_M2:
        new_layers: list[SoilLayer] = []
        for layer in profile.layers:
            scaled_layer = layer.model_copy(
                update={
                    "Eoed": layer.Eoed / 1.25,
                    "Cc": layer.Cc * 1.25,
                    "Cr": layer.Cr * 1.25,
                }
            )
            new_layers.append(scaled_layer)

        return profile.model_copy(update={"layers": new_layers}, deep=True)

    raise ValueError(f"Unsupported design approach: {approach}")
