"""Excel (.xlsx) and CSV raw data exporter for settlewell."""

from io import BytesIO

import numpy as np
import pandas as pd

from settlewell.solara_app.schemas import ScenarioSchema


def generate_excel_workbook(scenario: ScenarioSchema) -> bytes:
    """Generate a multi-tab Excel workbook (.xlsx) for a calculation scenario."""
    buffer = BytesIO()
    project = scenario.to_project()
    res = project.solve()

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
                "USCS": layer.uscs_type.value
                if hasattr(layer.uscs_type, "value")
                else str(layer.uscs_type),
                "Thickness_m": layer.thickness,
                "Gamma_dry_kN_m3": layer.gamma,
                "Gamma_sat_kN_m3": layer.gamma_sat,
                "Initial_Void_Ratio_e0": layer.e0,
                "E_modulus_MPa": layer.Eoed / 1000.0,
                "Cc": layer.Cc,
                "Cr": layer.Cr,
                "Cv_m2_s": layer.Cv,
            }
            for layer in scenario.stratigraphy
        ]
    )

    # 3. Stress & Settlement Profile Sheet
    if res.stress is not None:
        df_stress = pd.DataFrame(
            {
                "Depth_z_m": res.stress.z,
                "Effective_Overburden_kPa": res.stress.sigma_v0_eff,
                "Delta_Stress_kPa": res.stress.delta_sigma_v,
            }
        )
    else:
        df_stress = pd.DataFrame()

    # 4. Dewatering Drawdown Sheet
    if res.hydraulics is not None and res.hydraulics.drawdown_grid is not None:
        df_hydraulics = pd.DataFrame(
            {
                "Transmissivity_m2_s": [res.hydraulics.T],
                "Storativity": [res.hydraulics.S],
                "Radius_of_Influence_m": [res.hydraulics.R],
            }
        )
    else:
        df_hydraulics = pd.DataFrame()

    import dataclasses

    # 5. Building Damage Results Sheet
    if res.damage and res.damage.assessments:
        df_damage = pd.DataFrame(
            [
                dataclasses.asdict(bldg)
                if dataclasses.is_dataclass(bldg)
                else bldg.model_dump()
                for bldg in res.damage.assessments.values()
            ]
        )
    else:
        df_damage = pd.DataFrame()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Project Summary", index=False)
        df_strat.to_excel(writer, sheet_name="Soil Stratigraphy", index=False)
        if not df_stress.empty:
            df_stress.to_excel(
                writer, sheet_name="Stress & Settlement Profile", index=False
            )
        if not df_hydraulics.empty:
            df_hydraulics.to_excel(
                writer, sheet_name="Dewatering Drawdown", index=False
            )
        if not df_damage.empty:
            df_damage.to_excel(
                writer, sheet_name="Building Damage Results", index=False
            )

    return buffer.getvalue()


def generate_csv_data(scenario: ScenarioSchema) -> bytes:
    """Generate raw numerical settlement profile CSV data."""
    project = scenario.to_project()
    res = project.solve()

    if res.stress is not None:
        df = pd.DataFrame(
            {
                "Depth_z_m": res.stress.z,
                "Sigma_v0_effective_kPa": res.stress.sigma_v0_eff,
                "Delta_sigma_z_kPa": res.stress.delta_sigma_v,
            }
        )
    else:
        df = pd.DataFrame()

    # Add surface settlement bowl profile points
    x_grid = np.linspace(
        scenario.solver_settings.x_min, scenario.solver_settings.x_max, 50
    )
    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0
    s_max_mm = (res.settlement.total_settlement * 1000.0) if res.settlement else 0.0
    s_bowl_mm = s_max_mm / (1.0 + (x_grid / max(0.5, primary_B / 2.0)) ** 2)

    df_bowl = pd.DataFrame(
        {"Horizontal_X_m": x_grid, "Surface_Settlement_s_mm": s_bowl_mm}
    )

    buffer = BytesIO()
    buffer.write(b"# Settlewell Settlement Profile Results\n")
    df.to_csv(buffer, index=False)
    buffer.write(b"\n# Surface Settlement Bowl Profile s(x)\n")
    df_bowl.to_csv(buffer, index=False)

    return buffer.getvalue()
