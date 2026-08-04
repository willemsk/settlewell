"""Script to generate the complete notebooks/kauwereelstraat_31_analysis.ipynb notebook."""

import nbformat as nbf


def build_notebook():
    nb = nbf.v4.new_notebook()

    # Title & Metadata
    title_md = r"""# Bronbemaling & Zettingsanalyse: Kauwereelstraat 31, Oud-Heverlee

**Project**: Nieuwbouw Eengezinswoning met kelder  
**Locatie**: Kauwereelstraat 31, 3051 Oud-Heverlee  
**Opdrachtgever**: Dhr. Kherim Willems  
**Geotechnisch Rapport**: Sonderingsrapport 26010068-001 (Sonderingen S01, S02, S03)  

---

### Referentiepeilen (mTAW Benchmark Hierarchy)
* **Pas 0.00 (Vloerpeil woning)**: `30.30 mTAW`
* **Maaiveld vooraan (Referentie $z=0$)**: `29.76 mTAW`
* **Maaiveld achteraan**: `28.81 mTAW` (terrein daalt ~1.0 m over de eerste 20 m)
* **Oorspronkelijke Grondwaterstand (juli 2026)**: `27.28 mTAW` ($2.48\text{ m}$ onder maaiveld vooraan)
* **Bouwputbodem ($13.0\text{ m} \times 14.0\text{ m}$)**: `26.72 mTAW` ($3.58\text{ m}$ onder pas / $3.04\text{ m}$ onder maaiveld vooraan)
* **Pompputbodem**: `26.62 mTAW` ($3.68\text{ m}$ onder pas / $3.14\text{ m}$ onder maaiveld vooraan)
* **Doelniveau Grondwaterstand**: `26.12 mTAW` ($0.50\text{ m}$ droogstand onder pompput)
* **Vereiste Netto Aflaging ($\Delta s$)**: $27.28 - 26.12 = \mathbf{1.16\text{ m}}$ netto grondwaterverlaging
"""

    imports_code = """import matplotlib.pyplot as plt
import numpy as np

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

print("Alle settlewell modules en Project API succesvol geïmporteerd.")
"""

    sec1_md = """## §1 Input Parameters (Invoergegevens)

In deze sectie worden de fysieke parameters gedefinieerd op basis van het sonderingsrapport `26010068-001` en de werfgegevens voor Kauwereelstraat 31.
"""

    sec1_code = """# === 1. Soil Profile (Grondopbouw op basis van Sondering 26010068-001) ===
profile = SoilProfile(
    surface_level_mtaw=29.76,
    gwl_mtaw=27.28,
    layers=[
        SoilLayer(
            name="Leem (Toplaag)",
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
            name="Zandige Leem",
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
            name="Zand (Dicht)",
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
            name="Klei",
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
            name="Diep Zand met Grind",
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

# === 2. Construction Pit (Bouwput Geometrie: 13m x 14m) ===
pit = ConstructionPit(
    length=13.0,
    width=14.0,
    depth=3.04,
    center_x=0.0,
    center_y=0.0,
    bottom_mtaw=26.72,
)

# === 3. Dewatering System (8 Filterputten rondom bouwput) ===
well_coords = [
    (-7.0, -7.5), (7.0, -7.5), (7.0, 7.5), (-7.0, 7.5),
    (0.0, -7.5), (7.0, 0.0), (0.0, 7.5), (-7.0, 0.0)
]
q_per_well = 1.2e-3  # ~4.32 m³/h per put
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

# === 4. Neighboring Buildings (Omliggende Bebouwing) ===
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

b38 = Building(
    id="Building_38",
    name="Kauwereelstraat 38",
    x=0.0,
    y=38.0,
    length=10.0,
    width=10.0,
    foundation_depth=2.4,
    building_type=BuildingType.CONCRETE_FRAME,
)

buildings = [b29, b33, b38]

# === 5. Initialize Project Orchestrator ===
project = Project(
    soil=profile,
    pit=pit,
    dewatering=dewatering,
    buildings=buildings,
)

print(f"Bodemprofiel tot. dikte: {project.soil.total_depth:.1f} m")
print(f"Oorspronkelijke GWL:    {project.soil.gwl_mtaw:.2f} mTAW ({project.soil.gwl_depth:.2f} m onder MV vooraan)")
print(f"Vereiste aflaging:       {project.dewatering.target_drawdown:.2f} m")
print(f"Totaal debiet (8 putten): {sum(w.Q for w in wells)*3600:.2f} m³/h")
"""

    sec2_md = """## §2 Unified Calculation & Visualizations (Analyse & Grafieken)

Berekening van hydraulica, spanningen, zettingen en schade via `project.solve()`.
"""

    sec2_code = """# Execute unified calculation workflow
results = project.solve()

print(f"Berekende hydraulische straal R: {results.hydraulics.R:.1f} m")
print(f"Transmissiviteit T: {results.hydraulics.T:.2e} m²/s")
print(f"Totale zetting centrum bouwput: {results.settlement.total_settlement * 1000:.2f} mm")

# Dwarsprofiel (Cross-Section) voor Buurman #29
fig_cs = project.plot_cross_section(building_idx=0)
plt.show()

# Situatieplan (Plan View) voor Buurman #29
fig_pv = project.plot_plan_view(building_idx=0)
plt.show()

# 3D Oppervlakte van de Grondwaterverlaging
fig_3d = project.plot_3d_drawdown(building_idx=0)
fig_3d.show()
"""

    sec3_md = """## §3 Stress & Settlement Profiles (Spanningsverloop & Zettingskom)
"""

    sec3_code = """fig_stress = project.plot_effective_stress_profile()
plt.show()

fig_trough = project.plot_settlement_trough(building_idx=0)
plt.show()
"""

    sec4_md = """## §4 Time-Dependent Consolidation (Tijdsafhankelijke Consolidatie)
"""

    sec4_code = """fig_time = project.plot_time_settlement()
plt.show()
"""

    sec5_md = """## §5 Neighboring Building Damage Assessment (Schadebeoordeling)
"""

    sec5_code = """for b_key, asm in results.damage.assessments.items():
    print(f"=== {b_key} ===")
    print(f"  Max zetting:        {asm.max_settlement*1000:.2f} mm")
    print(f"  Diff zetting:       {asm.differential_settlement*1000:.2f} mm")
    print(f"  Hoekverdraaiing:    1/{int(1.0/max(asm.angular_distortion, 1e-9))}")
    print(f"  Schadeklasse:       Klasse {asm.damage_category} ({asm.damage_description})")
    print(f"  Scheurwijdte:       {asm.expected_crack_width}")
    print()

fig_damage = project.plot_damage_summary(building_idx=0)
plt.show()
"""

    sec6_md = """## §6 PDF Report Export (Rapportage)
"""

    sec6_code = """project.export_pdf("kauwereelstraat_31_report.pdf")
print("PDF berekeningsrapport succesvol geëxporteerd via project.export_pdf().")
"""

    sec7_md = """## §7 Verification & Sanity Checks (Verificatie)
"""

    sec7_code = """assert results.hydraulics is not None
assert results.settlement is not None
assert results.damage is not None

assert results.settlement.total_settlement * 1000 > 1.0

for asm in results.damage.assessments.values():
    assert asm.max_settlement < 0.025, "Zetting overschrijdt 25 mm!"
    assert asm.damage_category <= 1, "Schadeklasse is te hoog!"

print("✓ ALLE SANITY CHECKS SUCCESVOL GESLAAGD!")
"""

    # Add cells to notebook
    cells = [
        nbf.v4.new_markdown_cell(title_md),
        nbf.v4.new_code_cell(imports_code),
        nbf.v4.new_markdown_cell(sec1_md),
        nbf.v4.new_code_cell(sec1_code),
        nbf.v4.new_markdown_cell(sec2_md),
        nbf.v4.new_code_cell(sec2_code),
        nbf.v4.new_markdown_cell(sec3_md),
        nbf.v4.new_code_cell(sec3_code),
        nbf.v4.new_markdown_cell(sec4_md),
        nbf.v4.new_code_cell(sec4_code),
        nbf.v4.new_markdown_cell(sec5_md),
        nbf.v4.new_code_cell(sec5_code),
        nbf.v4.new_markdown_cell(sec6_md),
        nbf.v4.new_code_cell(sec6_code),
        nbf.v4.new_markdown_cell(sec7_md),
        nbf.v4.new_code_cell(sec7_code),
    ]

    nb["cells"] = cells

    output_path = "notebooks/kauwereelstraat_31_analysis.ipynb"
    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Notebook generated successfully at: {output_path}")


if __name__ == "__main__":
    build_notebook()
