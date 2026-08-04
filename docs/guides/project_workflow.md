# Project Workflows

This guide covers the core Python workflow for performing a ground settlement analysis using Settlewell's Project API.

## Defining a New Project

Settlewell uses a unified `Project` object to manage soil stratigraphy, dewatering parameters, loading configurations, and results. You can define a project from scratch or use built-in Flemish soil presets.

### Using Flemish Soil Presets

A common workflow in Belgium uses the provided templates (e.g., Antwerp Boom Clay, Brussels Sand).

```python
from settlewell import Project

# Initialize a project from a Flemish template
project = Project.from_template(
    template_name="Antwerp Boom Clay Formation",
    gwl_mtaw=4.0,           # Groundwater level (mTAW)
    surface_level_mtaw=6.0  # Ground surface level (mTAW)
)
```

### Adding Pit and Dewatering Configuration

Next, specify the dimensions of your construction pit and the dewatering system configuration.

```python
from settlewell import ConstructionPit, DewateringConfig, Well, AquiferType

# Add excavation pit
project.pit = ConstructionPit(
    length=30.0,
    width=20.0,
    depth=5.0
)

# Add dewatering configuration with a well array
project.dewatering = DewateringConfig(
    original_gwl_mtaw=4.0,
    target_drawdown_mtaw=0.0,
    pumping_duration_days=60.0,
    aquifer_type=AquiferType.UNCONFINED,
    wells=[
        Well(x=-15.0, y=-10.0, Q=15.0),
        Well(x=15.0, y=-10.0, Q=15.0),
        Well(x=15.0, y=10.0, Q=15.0),
        Well(x=-15.0, y=10.0, Q=15.0),
    ]
)
```

### Adding Neighboring Buildings and Loads

Include adjacent structures and any additional surface loads to evaluate potential damage risks.

```python
from settlewell import Building, BuildingType, LoadGeometry, LoadType

# Add neighboring buildings
project.buildings = [
    Building(
        name="Historical Masonry House",
        x=25.0,
        y=0.0,
        length=12.0,
        width=8.0,
        building_type=BuildingType.MASONRY
    )
]

# Add additional surface loads (e.g., equipment or material storage)
project.loads = [
    LoadGeometry(
        name="Crane Load",
        type=LoadType.RECTANGULAR,
        x_center=20.0,
        width_B=5.0,
        length_L=5.0,
        stress_q=150.0  # kPa
    )
]
```

## Running the Analysis

With the project configured, you can execute the full analysis pipeline—hydraulics, stress, settlement, and damage assessment—using a single method:

```python
# Execute the solver
results = project.solve()

# Access results
print(f"Total Settlement: {results.settlement.total_settlement * 1000:.1f} mm")
print(f"Max Drawdown: {results.hydraulics.drawdown_grid.max():.2f} m")

damage = results.damage.assessments["Historical Masonry House"]
print(f"Damage Category: {damage.damage_category.name}")
```

## Visualizing Results

Settlewell provides built-in plotting routines through the `Project` API. 

```python
# View 2D settlement cross section
project.plot_cross_section(building_idx=0)

# View 3D drawdown cone
project.plot_3d_drawdown()

# Plot consolidation settlement over time
project.plot_time_settlement()

# Summary damage assessment for a specific building
project.plot_damage_summary(building_idx=0)
```
