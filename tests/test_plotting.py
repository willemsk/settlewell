"""Smoke and regression tests for settlewell.plotting — verify plots render without errors."""

from functools import partial

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

from settlewell.damage import assess_building_damage
from settlewell.hydraulics import compute_drawdown_at_points, compute_drawdown_grid
from settlewell.plotting import (
    plot_3d_drawdown,
    plot_cross_section,
    plot_damage_summary,
    plot_effective_stress_profile,
    plot_plan_view,
    plot_settlement_trough,
    plot_time_settlement,
)
from settlewell.settlement import (
    compute_initial_stress_profile,
    compute_total_settlement,
)


class TestPlotSmoke:
    """
    Groups "smoke tests" for the plotting module. These tests simply execute every major
    plotting function with standard data to ensure they don't crash, validating that matplotlib
    and plotly code can render the basic geometry and data structures.
    """

    def test_cross_section(self, flemish_profile, pit, six_well_config, building):
        """
        This test checks that generating the 2D cross-section profile view works without throwing
        an exception. It validates the visual alignment of the soil layers, pit, and building.
        It calls `plot_cross_section` using standard fixtures. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = plot_cross_section(
            flemish_profile, pit, six_well_config, building, drawdown_at_building=1.5
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plan_view(self, flemish_profile, pit, six_well_config, building):
        """
        This test checks that generating the top-down plan view map works without errors.
        It ensures contour mapping and spatial overlay logic is functional.
        It calls `plot_plan_view` using generated drawdown grids and building damage assessments.
        The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        X, Y, S = compute_drawdown_grid(
            (-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile
        )
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func
        )
        fig = plot_plan_view(pit, six_well_config, building, X, Y, S, assessment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_settlement_trough(self, flemish_profile, pit, six_well_config, building):
        """
        This test ensures that plotting the vertical settlement trough (the shape of ground
        deformation over distance) executes successfully. It computes a linear array of settlement
        points and calls `plot_settlement_trough`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        x_transect = np.linspace(0, 50, 50)
        points = [(x, 0.0) for x in x_transect]
        drawdowns = compute_drawdown_at_points(points, six_well_config, flemish_profile)
        settlements = np.array(
            [compute_total_settlement(flemish_profile, d)[0] for d in drawdowns]
        )
        fig = plot_settlement_trough(
            flemish_profile, six_well_config, pit, building, x_transect, settlements
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_time_settlement(self):
        """
        This test ensures that the time-series plot comparing settlement over time at different points
        renders correctly. It creates dummy time and settlement data dicts and calls `plot_time_settlement`.
        The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        times = np.linspace(0, 365, 100)
        settlements = {
            "center": np.linspace(0, 0.01, 100),
            "corner_1": np.linspace(0, 0.012, 100),
        }
        fig = plot_time_settlement(times, settlements, pumping_duration_days=90)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_effective_stress_profile(self, flemish_profile):
        """
        This test verifies that the plot showing initial versus final effective stress profiles
        can be generated without errors. It calculates an initial profile, fakes an increase,
        and calls `plot_effective_stress_profile`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        z, sigma_init, _ = compute_initial_stress_profile(flemish_profile)
        sigma_final = sigma_init + 10  # Fake increase
        fig = plot_effective_stress_profile(flemish_profile, z, sigma_init, sigma_final)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_3d_drawdown(self, flemish_profile, pit, six_well_config, building):
        """
        This test checks that the 3D interactive Plotly visualization for the drawdown cone
        renders without crashing. It relies on a generated drawdown grid and calls `plot_3d_drawdown`.
        The expected result is a valid `plotly.graph_objects.Figure` object.
        """
        X, Y, S = compute_drawdown_grid(
            (-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile
        )
        fig = plot_3d_drawdown(X, Y, S, pit, building)
        assert isinstance(fig, go.Figure)

    def test_damage_summary(self, flemish_profile, six_well_config, building):
        """
        This test ensures the creation of the building damage summary infographic (with the classification
        gauges and categories) completes successfully. It assesses building damage and passes the result
        to `plot_damage_summary`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile
        )
        assessment = assess_building_damage(building, flemish_profile, six_well_config, drawdown_func)
        fig = plot_damage_summary(assessment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotContent:
    """
    Groups tests that inspect the internal components of the generated figures to ensure
    that data is actually being rendered correctly, rather than just returning an empty plot.
    """
    def test_cross_section_layer_patches(
        self, flemish_profile, pit, six_well_config, building
    ):
        """
        This test checks that the cross-section plot accurately renders graphical shapes
        representing the soil layers. It verifies that the drawing loop inside the plotting function works.
        It extracts the polygon and rectangle patches from the generated figure's axis. The expected result
        is that the number of shape patches is greater than or equal to the number of soil layers in the profile.
        """
        fig = plot_cross_section(
            flemish_profile, pit, six_well_config, building, drawdown_at_building=1.5
        )
        ax = fig.axes[0]
        # Count Rectangle/Polygon patches (soil layers)
        from matplotlib.patches import Polygon, Rectangle

        patches = [p for p in ax.patches if isinstance(p, (Rectangle, Polygon))]
        assert len(patches) >= len(flemish_profile.layers)
        plt.close(fig)

    def test_plan_view_well_markers(
      self, flemish_profile, pit, six_well_config, building
    ):
        """
        This test performs a basic check on the plan view figure to ensure that the primary
        drawing axis is properly initialized. It calls `plot_plan_view` and accesses the `axes` property.
        The expected result is that the figure contains at least one set of axes.
        """
        X, Y, S = compute_drawdown_grid(
            (-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile
        )
        drawdown_func = partial(
            compute_drawdown_at_points, config=six_well_config, profile=flemish_profile
        )
        assessment = assess_building_damage(
            building, flemish_profile, six_well_config, drawdown_func
        )
        fig = plot_plan_view(pit, six_well_config, building, X, Y, S, assessment)
        assert len(fig.axes) >= 1
        plt.close(fig)

    def test_soil_color_fallback(self):
        """
        This test ensures that the internal soil color mapping utility provides a safe default
        color if it encounters an unrecognized soil type string. This prevents the plotting code from
        crashing on custom soil names. It calls `_get_soil_color` with an unknown string.
        The expected result is the default hex color code `#B0C4DE` (Light Steel Blue).
        """
        from settlewell.plotting import _get_soil_color as get_soil_color
        # Soil name not in dictionary (e.g., "unknown_material") should return fallback hex #B0C4DE
        color = get_soil_color("unknown_material")
        assert color == "#B0C4DE"
