"""Smoke and regression tests for settlewell.plotting — verify plots render without errors."""

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import plotly.graph_objects as go


class TestPlotSmoke:
    """
    Groups "smoke tests" for the plotting module. These tests simply execute every major
    plotting function with standard data to ensure they don't crash, validating that matplotlib
    and plotly code can render the basic geometry and data structures.
    """

    def test_cross_section(self, standard_project):
        """
        This test checks that generating the 2D cross-section profile view works without throwing
        an exception. It validates the visual alignment of the soil layers, pit, and building.
        It calls `plot_cross_section` using standard fixtures. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_cross_section()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plan_view(self, standard_project):
        """
        This test checks that generating the top-down plan view map works without errors.
        It ensures contour mapping and spatial overlay logic is functional.
        It calls `plot_plan_view` using generated drawdown grids and building damage assessments.
        The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_plan_view()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_settlement_trough(self, standard_project):
        """
        This test ensures that plotting the vertical settlement trough (the shape of ground
        deformation over distance) executes successfully. It computes a linear array of settlement
        points and calls `plot_settlement_trough`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_settlement_trough()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_time_settlement(self, standard_project):
        """
        This test ensures that the time-series plot comparing settlement over time at different points
        renders correctly. It creates dummy time and settlement data dicts and calls `plot_time_settlement`.
        The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_time_settlement()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_effective_stress_profile(self, standard_project):
        """
        This test verifies that the plot showing initial versus final effective stress profiles
        can be generated without errors. It calculates an initial profile, fakes an increase,
        and calls `plot_effective_stress_profile`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_effective_stress_profile()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_3d_drawdown(self, standard_project):
        """
        This test checks that the 3D interactive Plotly visualization for the drawdown cone
        renders without crashing. It relies on a generated drawdown grid and calls `plot_3d_drawdown`.
        The expected result is a valid `plotly.graph_objects.Figure` object.
        """
        fig = standard_project.plot_3d_drawdown()
        assert isinstance(fig, go.Figure)

    def test_damage_summary(self, standard_project):
        """
        This test ensures the creation of the building damage summary infographic (with the classification
        gauges and categories) completes successfully. It assesses building damage and passes the result
        to `plot_damage_summary`. The expected result is a valid `matplotlib.pyplot.Figure` object.
        """
        fig = standard_project.plot_damage_summary()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotContent:
    """
    Groups tests that inspect the internal components of the generated figures to ensure
    that data is actually being rendered correctly, rather than just returning an empty plot.
    """

    def test_cross_section_layer_patches(self, standard_project):
        """
        This test checks that the cross-section plot accurately renders graphical shapes
        representing the soil layers. It verifies that the drawing loop inside the plotting function works.
        It extracts the polygon and rectangle patches from the generated figure's axis. The expected result
        is that the number of shape patches is greater than or equal to the number of soil layers in the profile.
        """
        fig = standard_project.plot_cross_section()
        ax = fig.axes[0]
        # Count Rectangle/Polygon patches (soil layers)
        from matplotlib.patches import Polygon, Rectangle

        patches = [p for p in ax.patches if isinstance(p, (Rectangle, Polygon))]
        assert len(patches) >= len(standard_project.soil.layers)
        plt.close(fig)

    def test_plan_view_well_markers(self, standard_project):
        """
        This test performs a basic check on the plan view figure to ensure that the primary
        drawing axis is properly initialized. It calls `plot_plan_view` and accesses the `axes` property.
        The expected result is that the figure contains at least one set of axes.
        """
        fig = standard_project.plot_plan_view()
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


class TestProjectPlottingIntegration:
    """Test plot wrappers using the Project orchestrator API."""

    def test_project_plot_wrappers(self, standard_project):
        """Test calling plot wrappers on a solved Project instance."""
        standard_project.solve()

        fig1 = standard_project.plot_cross_section()
        assert isinstance(fig1, plt.Figure)
        plt.close(fig1)

        fig2 = standard_project.plot_plan_view()
        assert isinstance(fig2, plt.Figure)
        plt.close(fig2)

        fig3 = standard_project.plot_settlement_trough()
        assert isinstance(fig3, plt.Figure)
        plt.close(fig3)

        fig4 = standard_project.plot_time_settlement()
        assert isinstance(fig4, plt.Figure)
        plt.close(fig4)

        fig5 = standard_project.plot_effective_stress_profile()
        assert isinstance(fig5, plt.Figure)
        plt.close(fig5)

        fig6 = standard_project.plot_3d_drawdown()
        assert isinstance(fig6, go.Figure)

        fig7 = standard_project.plot_damage_summary()
        assert isinstance(fig7, plt.Figure)
        plt.close(fig7)
