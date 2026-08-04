# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
# ---

# %% [markdown]
# # Ground Settlement Calculation During Dewatering (`settlewell`)
# 
# **Worked Example Analysis — Dewatering of a Construction Pit in Flanders, Belgium**  
# *Author: Kherim Willems* | *Package: settlewell v2.0.0*
# 
# ---
# 
# ## Executive Summary
# This notebook demonstrates the complete end-to-end workflow for analyzing ground settlement (*zetting*) and neighboring building damage risk caused by construction pit dewatering (*settlewell*) using the unified `Project` orchestrator API.
# 
# ### Problem Scenario:
# - **Location**: Flemish lowland site (typical soil profile: fill, sand, compressible clay, deep sand).
# - **Excavation Pit**: $10\text{ m} \times 8\text{ m}$ rectangular excavation, $3.0\text{ m}$ depth below surface ($2.0\text{ mTAW}$).
# - **Groundwater Table**: Original GWL at $4.0\text{ mTAW}$ ($1.0\text{ m}$ below ground surface at $5.0\text{ mTAW}$).
# - **Dewatering System**: 6 peripheral extraction wells pumping down to target level $1.5\text{ mTAW}$ ($2.5\text{ m}$ total drawdown in pit).
# - **Neighboring Building**: Masonry residential structure located $12.0\text{ m}$ from pit center.

# %%
import matplotlib.pyplot as plt

from settlewell import (
    AquiferType,
    Building,
    BuildingType,
    ConstructionPit,
    DewateringConfig,
    Project,
    SoilLayer,
    SoilProfile,
    Well,
)

print("settlewell package and Project orchestrator API successfully loaded.")

# %% [markdown]
# ## §1 Input Parameters & Project Setup (Invoergegevens)

# %%
# === 1. Soil Profile (Grondopbouw) ===
profile = SoilProfile(
    surface_level_mtaw=5.0,  # mTAW
    gwl_mtaw=4.0,  # mTAW (1m below surface)
    layers=[
        SoilLayer(
            "Aanvulling (Fill)",
            thickness=0.5,
            gamma=17.0,
            gamma_sat=19.0,
            k_h=1e-5,
            e0=0.6,
            Cc=0.05,
            Cr=0.01,
            Eoed=15000,
            Cv=1e-4,
            OCR=3.0,
        ),
        SoilLayer(
            "Zand (Sand)",
            thickness=2.0,
            gamma=17.5,
            gamma_sat=20.0,
            k_h=1e-4,
            e0=0.5,
            Cc=0.02,
            Cr=0.005,
            Eoed=30000,
            Cv=1e-2,
            OCR=1.5,
        ),
        SoilLayer(
            "Klei (Clay)",
            thickness=3.0,
            gamma=16.0,
            gamma_sat=18.5,
            k_h=1e-9,
            e0=1.0,
            Cc=0.30,
            Cr=0.06,
            Eoed=3000,
            Cv=1e-7,
            OCR=1.5,
        ),
        SoilLayer(
            "Zand (Sand, deep)",
            thickness=4.5,
            gamma=18.0,
            gamma_sat=20.5,
            k_h=5e-4,
            e0=0.45,
            Cc=0.01,
            Cr=0.003,
            Eoed=40000,
            Cv=1e-2,
            OCR=1.0,
        ),
    ],
)

# === 2. Construction Pit (Bouwput) ===
pit = ConstructionPit(
    length=10.0, width=8.0, depth=3.0, center_x=0.0, center_y=0.0, bottom_mtaw=2.0
)

# === 3. Dewatering Wells (Bronnen) ===
wells = [
    Well(x=-5.5, y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=0.0, y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=5.5, y=-4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=-5.5, y=4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=0.0, y=4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
    Well(x=5.5, y=4.5, Q=0.0005, screen_top_mtaw=3.0, screen_bottom_mtaw=0.0),
]

dewatering = DewateringConfig(
    wells=wells,
    target_drawdown_mtaw=1.5,  # mTAW (pump down to 1.5 mTAW)
    original_gwl_mtaw=4.0,  # mTAW
    pumping_duration_days=90,
    aquifer_type=AquiferType.UNCONFINED,
)

# === 4. Neighboring Building (Naburig Gebouw) ===
building = Building(
    x=12.0,
    y=0.0,
    length=10.0,
    width=6.0,
    foundation_depth=0.6,
    building_type=BuildingType.MASONRY,
)

# === 5. Initialize Project Orchestrator ===
project = Project(
    soil=profile,
    pit=pit,
    dewatering=dewatering,
    buildings=[building],
)

print(f"Soil Profile Total Depth: {project.soil.total_depth:.1f} m")
print(f"GWL Depth Below Surface: {project.soil.gwl_depth:.1f} m")
print(f"Target Dewatering Drawdown: {project.dewatering.target_drawdown:.1f} m")

# %% [markdown]
# ## §2 Unified Calculation & Visualizations

# %%
# Execute full analysis via Project API
results = project.solve()

print(f"Transmissivity T: {results.hydraulics.T:.2e} m²/s")
print(f"Radius of Influence R: {results.hydraulics.R:.1f} m")
print(
    f"Total Settlement at Pit Center: {results.settlement.total_settlement * 1000.0:.2f} mm"
)

# %%
# Cross-section plot
fig_cs = project.plot_cross_section(building_idx=0)
plt.show()

# %%
# Plan-view drawdown & building location plot
fig_plan = project.plot_plan_view(building_idx=0)
plt.show()

# %%
# 3D Drawdown surface plot
fig_3d = project.plot_3d_drawdown(building_idx=0)
fig_3d.show()

# %% [markdown]
# ## §3 Stress & Settlement Profiles

# %%
# Effective vertical stress profile plot
fig_stress = project.plot_effective_stress_profile()
plt.show()

# %%
# Settlement trough profile plot
fig_trough = project.plot_settlement_trough(building_idx=0)
plt.show()

# %% [markdown]
# ## §4 Time-Dependent Consolidation

# %%
# Time-settlement consolidation plot
fig_time = project.plot_time_settlement()
plt.show()

# %% [markdown]
# ## §5 Neighboring Building Damage Assessment

# %%
assessment = (
    results.damage.assessments.get("Building")
    or list(results.damage.assessments.values())[0]
)
print(f"Max Settlement:             {assessment.max_settlement * 1000.0:.2f} mm")
print(f"Min Settlement:             {assessment.min_settlement * 1000.0:.2f} mm")
print(
    f"Differential Settlement:    {assessment.differential_settlement * 1000.0:.2f} mm"
)
print(
    f"Angular Distortion β:       1/{int(1.0 / max(assessment.angular_distortion, 1e-9))}"
)
print(
    f"Damage Category:            {assessment.damage_category} ({assessment.damage_description})"
)

fig_damage = project.plot_damage_summary(building_idx=0)
plt.show()

# %% [markdown]
# ## §6 Report Export

# %%
# Export calculation report to PDF
project.export_pdf("example_analysis_report.pdf")
print("Geotechnical calculation report exported to PDF successfully.")

# %% [markdown]
# ## §7 Verification & Sanity Checks

# %%
# Sanity check assertions using ProjectResults
assert results.hydraulics is not None
assert results.settlement is not None
assert results.damage is not None
assert results.settlement.total_settlement > 0.0
print("All worked example verification checks PASSED successfully!")


