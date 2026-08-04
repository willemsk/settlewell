# Complex Analysis Example

## Overview

This case study demonstrates the use of the `settlewell` calculation engine in a generic complex testing scenario (`test_scenario_complex`). The scenario illustrates the superposition of multiple dewatering wells, complex soil strata, multiple building loads, and the generation of multi-format exports.

## Python Implementation

The following Python code outlines the scenario:

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


def test_scenario_complex():
    # === 1. Complex Soil Strata ===
    # A multi-layered soil profile representing a complex geotechnical environment.
    profile = SoilProfile(
        surface_level_mtaw=5.0,
        gwl_mtaw=4.0,
        layers=[
            SoilLayer(
                name="Fill",
                thickness=1.0,
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
                name="Upper Sand",
                thickness=3.0,
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
                name="Consolidated Clay",
                thickness=4.0,
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
                name="Deep Aquifer Sand",
                thickness=6.0,
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

    # === 2. Construction Pit ===
    pit = ConstructionPit(
        length=20.0, width=15.0, depth=4.0, center_x=0.0, center_y=0.0, bottom_mtaw=1.0
    )

    # === 3. Dewatering System (Superposition of 4 Wells) ===
    wells = [
        Well(x=-10.0, y=-7.5, Q=0.0015, screen_top_mtaw=2.0, screen_bottom_mtaw=-2.0),
        Well(x=10.0, y=-7.5, Q=0.0015, screen_top_mtaw=2.0, screen_bottom_mtaw=-2.0),
        Well(x=10.0, y=7.5, Q=0.0015, screen_top_mtaw=2.0, screen_bottom_mtaw=-2.0),
        Well(x=-10.0, y=7.5, Q=0.0015, screen_top_mtaw=2.0, screen_bottom_mtaw=-2.0),
    ]

    dewatering = DewateringConfig(
        wells=wells,
        target_drawdown_mtaw=0.5,
        original_gwl_mtaw=4.0,
        pumping_duration_days=90,
        aquifer_type=AquiferType.SEMI_CONFINED,
    )

    # === 4. Multiple Building Loads ===
    buildings = [
        Building(
            id="B1",
            name="Historic Masonry Building",
            x=15.0,
            y=0.0,
            length=12.0,
            width=8.0,
            foundation_depth=1.0,
            building_type=BuildingType.MASONRY,
        ),
        Building(
            id="B2",
            name="Modern Concrete Structure",
            x=-20.0,
            y=10.0,
            length=20.0,
            width=15.0,
            foundation_depth=2.5,
            building_type=BuildingType.CONCRETE_FRAME,
        ),
        Building(
            id="B3",
            name="Light Timber Structure",
            x=0.0,
            y=-20.0,
            length=10.0,
            width=6.0,
            foundation_depth=0.5,
            building_type=BuildingType.TIMBER_FRAME,
        ),
    ]

    # === 5. Initialize Project and Solve ===
    project = Project(
        soil=profile,
        pit=pit,
        dewatering=dewatering,
        buildings=buildings,
    )

    results = project.solve()
    print("Project solved successfully.")

    # === 6. Multi-Format Exports ===
    project.export_pdf("complex_scenario_report.pdf")
    project.export_dxf("complex_scenario_drawing.dxf")
    project.export_excel("complex_scenario_data.xlsx")
    project.export_csv("complex_scenario_data.csv")

    print("Multi-format exports completed successfully.")


if __name__ == "__main__":
    test_scenario_complex()
```

## Highlights

* **Superposition:** The scenario models the combined drawdown effects of 4 individual wells working in tandem, testing the superposition logic of the calculation engine.
* **Complex Strata:** The soil profile consists of four layers with drastically different hydraulic conductivities ($k_h$) and stiffnesses, creating a realistic, challenging numerical environment.
* **Building Assessments:** Multiple building types are placed at varying distances from the pit, allowing `settlewell` to calculate individualized damage risks based on their respective foundation depths and structure types.
* **Exports:** The final step demonstrates the automated generation of comprehensive deliverables: a PDF report, a CAD DXF drawing, an Excel workbook, and raw CSV data.
