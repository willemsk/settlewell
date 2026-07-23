"""Background QThread worker for executing the settlement analysis calculation pipeline."""

import numpy as np
from PySide6.QtCore import QObject, Signal

from settlewell.damage import assess_building_damage
from settlewell.hydraulics import (
    compute_drawdown_at_points,
    compute_drawdown_grid,
    compute_radius_of_influence,
    compute_storativity,
    compute_transmissivity,
)
from settlewell.models import (
    AquiferType,
    Building,
    BuildingType,
    ConstructionPit,
    DewateringConfig,
    SoilLayer,
    SoilProfile,
    Well,
)
from settlewell.plotting import (
    plot_3d_drawdown_mpl,
    plot_cross_section,
    plot_damage_summary,
    plot_effective_stress_profile,
    plot_plan_view,
    plot_settlement_trough,
    plot_time_settlement,
)
from settlewell.settlement import (
    compute_initial_stress_profile,
    compute_settlement_vs_time,
    compute_stress_increase_from_drawdown,
    compute_total_settlement,
)


class AnalysisWorker(QObject):
    """Worker object for running the settlement calculation pipeline in a background thread."""

    progress = Signal(int, str)  # (percentage 0-100, step_description)
    finished = Signal(dict)  # (results dictionary)
    error = Signal(str)  # (error message)

    def __init__(self, state: dict, parent=None):
        super().__init__(parent)
        self.state = state

    def run(self) -> None:
        """Main execution entry point for background thread."""
        try:
            # 1. Parse domain objects
            self.progress.emit(5, "Constructing domain data models...")
            prof_data = self.state.get("soil_profile", {})
            layers = [
                SoilLayer(
                    name=layer_dict["name"],
                    thickness=layer_dict["thickness"],
                    gamma=layer_dict["gamma"],
                    gamma_sat=layer_dict["gamma_sat"],
                    k_h=layer_dict["k_h"],
                    e0=layer_dict["e0"],
                    Cc=layer_dict["Cc"],
                    Cr=layer_dict["Cr"],
                    Eoed=layer_dict["Eoed"],
                    Cv=layer_dict["Cv"],
                    OCR=layer_dict["OCR"],
                )
                for layer_dict in prof_data.get("layers", [])
            ]
            profile = SoilProfile(
                surface_level_mtaw=prof_data.get("surface_level_mtaw", 5.0),
                gwl_mtaw=prof_data.get("gwl_mtaw", 4.0),
                layers=layers,
            )

            pit_data = self.state.get("construction_pit", {})
            pit = ConstructionPit(
                length=pit_data.get("length", 8.0),
                width=pit_data.get("width", 6.0),
                depth=pit_data.get("depth", 3.0),
                center_x=pit_data.get("center_x", 0.0),
                center_y=pit_data.get("center_y", 0.0),
                bottom_mtaw=pit_data.get("bottom_mtaw", 2.0),
            )

            wells_data = self.state.get("wells", [])
            wells = [
                Well(
                    x=w["x"],
                    y=w["y"],
                    Q=w["Q"],
                    r_w=w["r_w"],
                    screen_top_mtaw=w.get("screen_top_mtaw", w.get("screen_top", 2.0)),
                    screen_bottom_mtaw=w.get(
                        "screen_bottom_mtaw", w.get("screen_bottom", -3.0)
                    ),
                )
                for w in wells_data
            ]

            dew_data = self.state.get("dewatering", {})
            a_type = AquiferType(dew_data.get("aquifer_type", "unconfined"))
            config = DewateringConfig(
                wells=wells,
                target_drawdown_mtaw=dew_data.get("target_drawdown_mtaw", 2.0),
                original_gwl_mtaw=dew_data.get("original_gwl_mtaw", 4.0),
                pumping_duration_days=dew_data.get("pumping_duration_days", 90.0),
                aquifer_type=a_type,
                T=dew_data.get("T_override"),
                S=dew_data.get("S_override"),
                R=dew_data.get("R_override"),
            )

            buildings_data = self.state.get("buildings", [])
            buildings = [
                Building(
                    x=b["x"],
                    y=b["y"],
                    length=b["length"],
                    width=b["width"],
                    orientation_deg=b["orientation_deg"],
                    foundation_depth=b["foundation_depth"],
                    building_type=BuildingType(b["building_type"]),
                )
                for b in buildings_data
            ]

            # 2. Hydraulic calculations
            self.progress.emit(
                20, "Computing aquifer parameters & radius of influence..."
            )
            T = config.T if config.T else compute_transmissivity(profile, config)
            S = config.S if config.S else compute_storativity(profile, config)
            R = config.R if config.R else compute_radius_of_influence(config, T)

            # 3. Drawdown grid
            self.progress.emit(40, "Generating 2D drawdown grid...")
            grid_extent = max(R, 50.0)
            X_grid, Y_grid, s_grid = compute_drawdown_grid(
                x_range=(-grid_extent, grid_extent),
                y_range=(-grid_extent, grid_extent),
                nx=50,
                ny=50,
                config=config,
                profile=profile,
            )

            # 4. Damage assessment & settlement metrics
            self.progress.emit(60, "Assessing building damage and settlements...")
            primary_building = (
                buildings[0] if buildings else Building(15.0, 0.0, 10.0, 8.0)
            )

            def drawdown_func(pts):
                return compute_drawdown_at_points(pts, config, profile)

            assessment = assess_building_damage(
                primary_building, profile, config, drawdown_func
            )

            # 5. Plot figures generation
            self.progress.emit(80, "Generating result visualization plots...")

            # Cross section
            s_b_center = float(
                drawdown_func([(primary_building.x, primary_building.y)])[0]
            )
            fig_cross = plot_cross_section(
                profile, pit, config, primary_building, drawdown_at_building=s_b_center
            )

            # Plan view
            fig_plan = plot_plan_view(
                pit, config, primary_building, X_grid, Y_grid, s_grid, assessment
            )

            # Settlement trough
            x_transect = np.linspace(0, 50, 50)
            pts_transect = [(x, 0.0) for x in x_transect]
            drawdowns_trough = drawdown_func(pts_transect)
            settlements_trough = np.array(
                [
                    compute_total_settlement(profile, max(0.0, float(d)))[0]
                    for d in drawdowns_trough
                ]
            )
            fig_trough = plot_settlement_trough(
                profile, config, pit, primary_building, x_transect, settlements_trough
            )

            # Time settlement
            times = np.linspace(0, config.pumping_duration_days, 100)
            s_max = float(np.max(s_grid))
            s_b_max = float(assessment.max_settlement)
            settlements_dict = {
                "Grootste verlaging": compute_settlement_vs_time(profile, s_max, times),
                "Gebouw (max)": compute_settlement_vs_time(profile, s_b_max, times),
            }
            fig_time = plot_time_settlement(
                times,
                settlements_dict,
                pumping_duration_days=config.pumping_duration_days,
            )

            # Stress profile
            z_nodes, sigma_eff_0, _ = compute_initial_stress_profile(profile)
            _, delta_sigma = compute_stress_increase_from_drawdown(
                profile, s_max, z_points=z_nodes
            )
            sigma_eff_f = sigma_eff_0 + delta_sigma
            fig_stress = plot_effective_stress_profile(
                profile, z_nodes, sigma_eff_0, sigma_eff_f
            )

            # 3D surface
            fig_3d = plot_3d_drawdown_mpl(X_grid, Y_grid, s_grid, pit)

            # Damage summary
            fig_damage = plot_damage_summary(assessment)

            self.progress.emit(100, "Analysis complete.")

            results = {
                "profile": profile,
                "pit": pit,
                "wells": wells,
                "config": config,
                "buildings": buildings,
                "assessment": assessment,
                "transmissivity": T,
                "storativity": S,
                "radius_of_influence": R,
                "figures": [
                    ("Dwarsdoorsnede (Cross Section)", fig_cross),
                    ("Grondplan (Plan View)", fig_plan),
                    ("Zettingskom (Settlement Trough)", fig_trough),
                    ("Tijd-Zetting (Time-Settlement)", fig_time),
                    ("Spanningsverloop (Stress Profile)", fig_stress),
                    ("3D Bemalingskegel (3D Drawdown)", fig_3d),
                    ("Schadesamenvatting (Damage Summary)", fig_damage),
                ],
            }

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))
