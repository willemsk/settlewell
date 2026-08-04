# Case Study: Kauwereelstraat 31 (Oud-Heverlee)

## Overview

This case study demonstrates a real-world calculation for a single-family home with a basement, located at Kauwereelstraat 31, Oud-Heverlee. The goal is to estimate ground settlement and assess the risk of damage to adjacent masonry structures during the dewatering phase of the construction pit.

### Reference Levels (mTAW Benchmark Hierarchy)
* **Pas 0.00 (House floor level)**: `30.30 mTAW`
* **Front Surface Level (Reference $z=0$)**: `29.76 mTAW`
* **Rear Surface Level**: `28.81 mTAW` (terrain drops ~1.0 m over the first 20 m)
* **Original Groundwater Level (July 2026)**: `27.28 mTAW` ($2.48\text{ m}$ below front surface level)
* **Construction Pit Bottom ($13.0\text{ m} \times 14.0\text{ m}$)**: `26.72 mTAW` ($3.04\text{ m}$ below front surface level)
* **Target Groundwater Level**: `26.12 mTAW`
* **Required Net Drawdown ($\Delta s$)**: $27.28 - 26.12 = \mathbf{1.16\text{ m}}$

## Soil Profile

The soil profile is based on the geotechnical CPT report `26010068-001` (CPTs S01, S02, S03). It consists of five distinct layers:
1. **Loam (Top layer)**: $2.0\text{ m}$ thick
2. **Sandy Loam**: $2.0\text{ m}$ thick
3. **Sand (Dense)**: $7.4\text{ m}$ thick
4. **Clay**: $2.8\text{ m}$ thick
5. **Deep Sand with Gravel**: $5.8\text{ m}$ thick

## Python Implementation

The following Python code uses the `settlewell` API to model the soil profile, construction pit, dewatering system (3 deep wells), and adjacent masonry structures.

```python
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

# === 1. Soil Profile ===
profile = SoilProfile(
    surface_level_mtaw=29.76,
    gwl_mtaw=27.28,
    layers=[
        SoilLayer(
            name="Loam (Top layer)",
            thickness=2.0,
            gamma=17.0,
            gamma_sat=19.0,
            k_h=1e-6,
            e0=0.75,
            Cc=0.15,
            Cr=0.03,
            Eoed=3000.0,
            Cv=2e-7,
            OCR=1.2,
        ),
        SoilLayer(
            name="Sandy Loam",
            thickness=2.0,
            gamma=18.0,
            gamma_sat=20.0,
            k_h=5e-5,
            e0=0.60,
            Cc=0.05,
            Cr=0.01,
            Eoed=15000.0,
            Cv=5e-6,
            OCR=1.0,
        ),
        SoilLayer(
            name="Sand (Dense)",
            thickness=7.4,
            gamma=18.5,
            gamma_sat=20.5,
            k_h=1e-4,
            e0=0.55,
            Cc=0.02,
            Cr=0.005,
            Eoed=40000.0,
            Cv=1e-5,
            OCR=1.0,
        ),
        SoilLayer(
            name="Clay",
            thickness=2.8,
            gamma=16.5,
            gamma_sat=18.5,
            k_h=1e-8,
            e0=0.90,
            Cc=0.20,
            Cr=0.04,
            Eoed=6000.0,
            Cv=1e-7,
            OCR=1.5,
        ),
        SoilLayer(
            name="Deep Sand with Gravel",
            thickness=5.8,
            gamma=19.0,
            gamma_sat=21.0,
            k_h=2e-4,
            e0=0.50,
            Cc=0.015,
            Cr=0.003,
            Eoed=50000.0,
            Cv=1e-5,
            OCR=1.0,
        ),
    ],
)

# === 2. Construction Pit ===
pit = ConstructionPit(
    length=13.0,
    width=14.0,
    depth=3.04,
    center_x=0.0,
    center_y=0.0,
    bottom_mtaw=26.72,
)

# === 3. Dewatering System (3 Deep Wells) ===
# We place 3 deep wells around the pit to achieve the target drawdown.
well_coords = [(-7.0, -7.5), (7.0, -7.5), (0.0, 7.5)]
q_per_well = 2.5e-3  # m³/s per well
wells = [
    Well(
        x=wx,
        y=wy,
        Q=q_per_well,
        r_w=0.075,
        screen_top_mtaw=25.76,
        screen_bottom_mtaw=21.76,
    )
    for wx, wy in well_coords
]

dewatering = DewateringConfig(
    wells=wells,
    target_drawdown_mtaw=26.12,
    original_gwl_mtaw=27.28,
    pumping_duration_days=60.0,
    aquifer_type=AquiferType.UNCONFINED,
)

# === 4. Neighboring Buildings ===
# Adjacent masonry structures
b29 = Building(
    id="Building_29",
    name="Kauwereelstraat 29",
    x=16.5,
    y=0.0,
    length=10.0,
    width=10.0,
    foundation_depth=1.5,
    building_type=BuildingType.MASONRY,
)
b33 = Building(
    id="Building_33",
    name="Kauwereelstraat 33",
    x=-16.5,
    y=0.0,
    length=10.0,
    width=10.0,
    foundation_depth=1.5,
    building_type=BuildingType.MASONRY,
)

buildings = [b29, b33]

# === 5. Initialize & Solve ===
project = Project(
    soil=profile,
    pit=pit,
    dewatering=dewatering,
    buildings=buildings,
)

results = project.solve()

print(f"Calculated Hydraulic Radius (R): {results.hydraulics.R:.1f} m")
print(
    f"Total Settlement at pit center: {results.settlement.total_settlement * 1000:.2f} mm"
)

# Generate PDF report
project.export_pdf("kauwereelstraat_31_report.pdf")
```

## Results

After calling `project.solve()`, the `ProjectResults` object will contain all hydraulic, stress, and settlement results, as well as a damage assessment for the neighboring buildings.

```python
# Damage Assessment Summary
for b_key, asm in results.damage.assessments.items():
    print(f"=== {b_key} ===")
    print(f"  Max Settlement:      {asm.max_settlement * 1000:.2f} mm")
    print(f"  Diff Settlement:     {asm.differential_settlement * 1000:.2f} mm")
    print(f"  Angular Distortion:  1/{int(1.0 / max(asm.angular_distortion, 1e-9))}")
    print(
        f"  Damage Category:     Class {asm.damage_category} ({asm.damage_description})"
    )
```
