# Getting Started

## Installation

Install `settlewell` with optional export capabilities (PDF, DXF, Excel):

```bash
pip install settlewell[export]
```

Or for local development using [`uv`](https://github.com/astral-sh/uv):

```bash
git clone https://github.com/willemsk/settlewell.git
cd settlewell

# Install with all extras (web, testing, export, documentation)
uv sync --all-extras
```

### Running Tests

```bash
uv run pytest -v
```

### Building Documentation

```bash
uv run --extra docs mkdocs build
```

To serve documentation locally:

```bash
uv run --extra docs mkdocs serve
```

## Quick Example

The `Project` orchestrator class unifies soil profiles, construction pit geometry, dewatering system configurations, neighboring building assessments, and export utilities under a single clean API.

```python
from settlewell import Building, ConstructionPit, DewateringConfig, Project, Well

# 1. Initialize project from a Flemish soil profile preset template
project = Project.from_template(
    template_name="Antwerp Boom Clay Formation",
    gwl_mtaw=4.0,
    surface_level_mtaw=5.0,
)

# 2. Define construction pit excavation
project.pit = ConstructionPit(
    length=20.0,
    width=15.0,
    depth=3.5,
)

# 3. Configure dewatering system layout and target groundwater level
project.dewatering = DewateringConfig(
    wells=[
        Well(name="W1", x=-10.0, y=-7.5, Q=5.0),
        Well(name="W2", x=10.0, y=-7.5, Q=5.0),
        Well(name="W3", x=10.0, y=7.5, Q=5.0),
        Well(name="W4", x=-10.0, y=7.5, Q=5.0),
    ],
    target_drawdown_mtaw=1.5,
    original_gwl_mtaw=4.0,
    pumping_duration_days=90,
)

# 4. Add neighboring buildings for structural damage assessment
project.buildings = [
    Building(
        name="Residence 1",
        x=25.0,
        y=0.0,
        length=12.0,
        width=8.0,
        foundation_depth=1.5,
    )
]

# 5. Execute unified geotechnical and hydraulic calculation
results = project.solve()

print(f"Radius of Influence R: {results.hydraulics.R:.1f} m")
print(
    f"Total Pit Center Settlement: {results.settlement.total_settlement * 1000:.1f} mm"
)

# 6. Export calculation report to PDF
project.export_pdf("report.pdf")
```

