"""Excel (.xlsx) and CSV raw data exporter for settlewell."""

from io import BytesIO

import numpy as np
import pandas as pd

from settlewell.solara_app.schemas import ScenarioSchema
from settlewell.solara_app.state import (
    run_building_damage_solve,
    run_fast_elastic_solve,
    run_hydraulics_solve,
)


def generate_excel_workbook(scenario: ScenarioSchema) -> bytes:
    """Generate a multi-tab Excel workbook (.xlsx) for a calculation scenario.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    bytes
        Excel workbook contents as bytes.
    """
    buffer = BytesIO()

    # 1. Project Summary Sheet
    df_summary = pd.DataFrame(
        [
            {"Parameter": "Scenario Name", "Value": scenario.name},
            {
                "Parameter": "Groundwater Depth (z_gw)",
                "Value": f"{scenario.water_table.depth_z} m",
            },
            {
                "Parameter": "Excavation Pit Length",
                "Value": f"{scenario.construction_pit.length} m",
            },
            {
                "Parameter": "Excavation Pit Width",
                "Value": f"{scenario.construction_pit.width} m",
            },
            {
                "Parameter": "Excavation Pit Depth",
                "Value": f"{scenario.construction_pit.depth} m",
            },
            {
                "Parameter": "Active Dewatering Wells",
                "Value": len(scenario.dewatering.wells),
            },
            {
                "Parameter": "Stress Calculation Method",
                "Value": scenario.solver_settings.stress_method.value,
            },
            {
                "Parameter": "Max Depth (z_max)",
                "Value": f"{scenario.solver_settings.z_max} m",
            },
        ]
    )

    # 2. Soil Stratigraphy Sheet
    df_strat = pd.DataFrame(
        [
            {
                "Layer Name": layer.name,
                "USCS": layer.uscs_type.value,
                "Thickness_m": layer.thickness,
                "Gamma_dry_kN_m3": layer.gamma_dry,
                "Gamma_sat_kN_m3": layer.gamma_sat,
                "Initial_Void_Ratio_e0": layer.e0,
                "E_modulus_MPa": layer.E_modulus,
                "Cc": layer.Cc,
                "Cr": layer.Cr,
                "Cv_m2_yr": layer.Cv,
            }
            for layer in scenario.stratigraphy
        ]
    )

    # 3. Stress & Settlement Profile Sheet
    elastic_res = run_fast_elastic_solve(scenario)
    df_stress = pd.DataFrame(
        {
            "Depth_z_m": elastic_res["z_grid"],
            "Effective_Overburden_kPa": elastic_res["sigma_v0_eff"],
            "Delta_Stress_kPa": elastic_res["delta_sigma_z"],
        }
    )

    # 4. Dewatering Drawdown Sheet
    hydraulics_res = run_hydraulics_solve(scenario)
    df_hydraulics = pd.DataFrame(
        {
            "Distance_r_m": hydraulics_res["r_grid"],
            "Drawdown_s_m": hydraulics_res["drawdown_radial"],
        }
    )

    # 5. Building Damage Results Sheet
    damage_res = run_building_damage_solve(scenario)
    df_damage = pd.DataFrame(damage_res["buildings"])

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Project Summary", index=False)
        df_strat.to_excel(writer, sheet_name="Soil Stratigraphy", index=False)
        df_stress.to_excel(
            writer, sheet_name="Stress & Settlement Profile", index=False
        )
        df_hydraulics.to_excel(writer, sheet_name="Dewatering Drawdown", index=False)
        if not df_damage.empty:
            df_damage.to_excel(
                writer, sheet_name="Building Damage Results", index=False
            )

    return buffer.getvalue()


def generate_csv_data(scenario: ScenarioSchema) -> bytes:
    """Generate raw numerical settlement profile CSV data.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    bytes
        CSV file contents as UTF-8 encoded bytes.
    """
    elastic_res = run_fast_elastic_solve(scenario)
    df = pd.DataFrame(
        {
            "Depth_z_m": elastic_res["z_grid"],
            "Sigma_v0_effective_kPa": elastic_res["sigma_v0_eff"],
            "Delta_sigma_z_kPa": elastic_res["delta_sigma_z"],
        }
    )

    # Add surface settlement bowl profile points
    x_grid = np.linspace(
        scenario.solver_settings.x_min, scenario.solver_settings.x_max, 50
    )
    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0
    s_bowl_mm = elastic_res["elastic_settlement_mm"] / (
        1.0 + (x_grid / max(0.5, primary_B / 2.0)) ** 2
    )

    df_bowl = pd.DataFrame(
        {"Horizontal_X_m": x_grid, "Surface_Settlement_s_mm": s_bowl_mm}
    )

    buffer = BytesIO()
    buffer.write(b"# Settlewell Settlement Profile Results\n")
    df.to_csv(buffer, index=False)
    buffer.write(b"\n# Surface Settlement Bowl Profile s(x)\n")
    df_bowl.to_csv(buffer, index=False)

    return buffer.getvalue()
