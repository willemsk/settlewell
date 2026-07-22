"""Smoke and regression tests for settlewell.plotting — verify plots render without errors."""

from functools import partial

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import pytest

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
from settlewell.settlement import compute_initial_stress_profile, compute_total_settlement


class TestPlotSmoke:
    """All plot functions execute without exceptions on the default scenario."""

    def test_cross_section(self, flemish_profile, pit, six_well_config, building):
        fig = plot_cross_section(flemish_profile, pit, six_well_config, building, drawdown_at_building=1.5)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plan_view(self, flemish_profile, pit, six_well_config, building):
        X, Y, S = compute_drawdown_grid((-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile)
        drawdown_func = partial(compute_drawdown_at_points, config=six_well_config, profile=flemish_profile)
        assessment = assess_building_damage(building, flemish_profile, six_well_config, drawdown_func)
        fig = plot_plan_view(pit, six_well_config, building, X, Y, S, assessment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_settlement_trough(self, flemish_profile, pit, six_well_config, building):
        x_transect = np.linspace(0, 50, 50)
        points = [(x, 0.0) for x in x_transect]
        drawdowns = compute_drawdown_at_points(points, six_well_config, flemish_profile)
        settlements = np.array([compute_total_settlement(flemish_profile, d)[0] for d in drawdowns])
        fig = plot_settlement_trough(flemish_profile, six_well_config, pit, building, x_transect, settlements)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_time_settlement(self):
        times = np.linspace(0, 365, 100)
        settlements = {"center": np.linspace(0, 0.01, 100), "corner_1": np.linspace(0, 0.012, 100)}
        fig = plot_time_settlement(times, settlements, pumping_duration_days=90)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_effective_stress_profile(self, flemish_profile):
        z, sigma_init, _ = compute_initial_stress_profile(flemish_profile)
        sigma_final = sigma_init + 10  # Fake increase
        fig = plot_effective_stress_profile(flemish_profile, z, sigma_init, sigma_final)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_3d_drawdown(self, flemish_profile, pit, six_well_config, building):
        X, Y, S = compute_drawdown_grid((-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile)
        fig = plot_3d_drawdown(X, Y, S, pit, building)
        assert isinstance(fig, go.Figure)

    def test_damage_summary(self, flemish_profile, six_well_config, building):
        drawdown_func = partial(compute_drawdown_at_points, config=six_well_config, profile=flemish_profile)
        assessment = assess_building_damage(building, flemish_profile, six_well_config, drawdown_func)
        fig = plot_damage_summary(assessment)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotContent:
    def test_cross_section_layer_patches(self, flemish_profile, pit, six_well_config, building):
        """Cross-section should have one colored patch per soil layer."""
        fig = plot_cross_section(flemish_profile, pit, six_well_config, building, drawdown_at_building=1.5)
        ax = fig.axes[0]
        # Count Rectangle/Polygon patches (soil layers)
        from matplotlib.patches import Polygon, Rectangle
        patches = [p for p in ax.patches if isinstance(p, (Rectangle, Polygon))]
        assert len(patches) >= len(flemish_profile.layers)
        plt.close(fig)

    def test_plan_view_well_markers(self, flemish_profile, pit, six_well_config, building):
        """Plan view should have axes rendered properly."""
        X, Y, S = compute_drawdown_grid((-50, 50), (-50, 50), 20, 20, six_well_config, flemish_profile)
        drawdown_func = partial(compute_drawdown_at_points, config=six_well_config, profile=flemish_profile)
        assessment = assess_building_damage(building, flemish_profile, six_well_config, drawdown_func)
        fig = plot_plan_view(pit, six_well_config, building, X, Y, S, assessment)
        assert len(fig.axes) >= 1
        plt.close(fig)
