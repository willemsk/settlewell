# Architecture & Project Structure Specification

This document defines the high-level architecture, deterministic repository layout, configuration files, package dependencies, documentation setup, and development guidelines for `settlewell`.

## Project Overview

- **Package Name**: `settlewell`
- **Description**: Ground settlement calculation for dewatering of construction pits.
- **Target Context**: Flanders, Belgium — residential basement excavation.
- **Language**: English with Dutch geotechnical terms in parentheses (e.g., "Settlement (zetting)", "Groundwater level (grondwaterstand - mTAW)").
- **Python Version**: `>=3.11` (Environment pinned to `3.14` in `.python-version`)
- **Package Manager**: `uv`
- **Build Backend**: `hatchling`

---

## Deterministic Repository Structure

```
d:\repos\bronbemaling\
├── .agents/
│   ├── README.md                            # Master index for AI agent specs
│   ├── gui_implementation_plan.md           # GUI implementation plan reference
│   └── specs/                               # Modular specification documents
│       ├── architecture.md                  # Structure, pyproject.toml, mkdocs.yml, rules
│       ├── hydraulics_and_models.md         # Dataclasses & analytical drawdown engines
│       ├── settlement_and_damage.md         # Terzaghi consolidation & Burland/SBR damage
│       ├── numerical_solver.md              # 2D Finite-Difference groundwater solver
│       ├── plotting.md                      # Matplotlib & Plotly visualization suite
│       ├── gui.md                           # PySide6 QWizard Desktop Application
│       └── testing_and_validation.md        # Test suite, physics convergence, validation
├── .github/
│   └── workflows/
│       ├── docs.yml                         # MkDocs GitHub Pages deployment
│       ├── publish.yml                      # PyPI and GitHub release publishing
│       └── tests.yml                        # Pytest & Ruff CI matrix
├── .gitignore
├── .jules/
│   └── bolt.md                              # Jules AI memory/context
├── .python-version                          # Python 3.14 version pin
├── LICENSE                                  # MIT License
├── README.md                                # Root package README
├── pyproject.toml                           # Package build & dependency metadata
├── mkdocs.yml                               # MkDocs documentation configuration
├── uv.lock                                  # Lockfile for deterministic environment
├── docs/
│   ├── index.md                             # Site landing page & overview
│   ├── getting-started.md                   # Installation & quick start guide
│   ├── theory.md                            # Geotechnical & hydraulic background theory
│   ├── validation.md                        # Physics convergence & verification page
│   ├── gui.md                               # Desktop GUI user manual
│   ├── api/                                 # Auto-generated API reference pages
│   │   ├── models.md
│   │   ├── hydraulics.md
│   │   ├── settlement.md
│   │   ├── damage.md
│   │   ├── numerical.md
│   │   ├── plotting.md
│   │   └── gui.md
│   └── assets/
│       └── images/                          # Generated SVG validation figures
├── notebooks/
│   ├── example_analysis.ipynb              # Worked example notebook
│   └── kauwereelstraat_31_analysis.ipynb    # Real-world case study notebook
├── scripts/
│   ├── generate_docs_plots.py               # Generates validation SVG plots
│   └── generate_kauwereelstraat_notebook.py # Notebook generator script
├── src/
│   └── settlewell/
│       ├── __init__.py                      # Package exports (__all__)
│       ├── py.typed                         # PEP 561 type marker
│       ├── models.py                        # Core input dataclasses
│       ├── hydraulics.py                    # Analytical hydraulics calculations
│       ├── settlement.py                    # 1D consolidation settlement calculations
│       ├── damage.py                        # Building damage classification
│       ├── numerical.py                     # 2D finite-difference flow solver
│       ├── plotting.py                      # Visualization functions
│       └── gui/                             # PySide6 Desktop GUI sub-package
│           ├── __init__.py
│           ├── __main__.py                  # python -m settlewell.gui support
│           ├── app.py                       # QApplication entry point & theme
│           ├── main_window.py               # QMainWindow shell & menu bar
│           ├── wizard.py                    # QWizard 6-page workflow orchestrator
│           ├── theme.py                     # Dark QSS stylesheet constant
│           ├── worker.py                    # QThread background analysis worker
│           ├── project_io.py                # .settlewell JSON project save/load
│           ├── pages/                       # QWizardPage step implementations
│           │   ├── __init__.py
│           │   ├── soil_profile.py
│           │   ├── construction_pit.py
│           │   ├── wells.py
│           │   ├── dewatering.py
│           │   ├── buildings.py
│           │   └── results.py
│           └── widgets/                     # Reusable Qt widgets & canvases
│               ├── __init__.py
│               ├── soil_table.py
│               ├── well_table.py
│               ├── building_table.py
│               ├── plot_canvas.py
│               └── validated_input.py
└── tests/
    ├── conftest.py                          # Shared pytest fixtures
    ├── test_models.py                       # Dataclass unit tests
    ├── test_hydraulics.py                   # Drawdown unit tests
    ├── test_settlement.py                   # Consolidation unit tests
    ├── test_damage.py                       # Damage classification unit tests
    ├── test_numerical.py                    # Finite-difference solver unit tests
    ├── test_plotting.py                     # Plot smoke unit tests
    ├── test_physics_convergence.py          # Physics convergence tests (@slow)
    └── test_gui.py                          # PySide6 GUI unit tests
```

---

## Package Configuration (`pyproject.toml`)

```toml
[project]
name = "settlewell"
version = "0.1.0"
description = "Ground settlement calculation for dewatering of construction pits"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.7",
    "plotly>=5.15",
]

[project.optional-dependencies]
gui = ["PySide6>=6.5"]
notebook = ["jupyter>=1.0", "ipykernel>=6.0"]
test = ["pytest>=7.0"]
docs = [
    "mkdocs>=1.5",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.24",
]

[project.gui-scripts]
settlewell-gui = "settlewell.gui:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (grid refinement, convergence loops). Deselect with: pytest -m 'not slow'",
]

[tool.ruff]
target-version = "py311"
exclude = [".agents"]

[tool.ruff.lint]
select = ["E", "F", "UP"]
ignore = ["E501"]
```

---

## Documentation Setup (`mkdocs.yml`)

```yaml
site_name: Settlewell Documentation
site_description: Ground Settlement Calculation During Dewatering of Construction Pits
site_author: Kherim Willems

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.indexes
    - navigation.top
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: numpy
            show_source: true
            show_root_heading: true

markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences
  - pymdownx.arithmatex:
      generic: true

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Desktop GUI Guide: gui.md
  - Validation & Physics: validation.md
  - Theory: theory.md
  - API Reference:
      - Models: api/models.md
      - Hydraulics: api/hydraulics.md
      - Settlement: api/settlement.md
      - Damage: api/damage.md
      - Numerical: api/numerical.md
      - Plotting: api/plotting.md
      - GUI: api/gui.md
```

---

## Coding Guidelines & Conventions

1. **Modern Python 3.11+ Type Annotations**: Use `A | B` for unions, `A | None` for optional values, and built-in generic collections (`list[T]`, `dict[K, V]`, `tuple[...]`). Do not import `Union`, `Optional`, `List`, `Dict`, or `Tuple` from `typing`.
2. **NumPy Docstrings**: Write thorough NumPy-style docstrings (`docstring_style: numpy`) for all classes, methods, functions, and module headers. Format docstring types using modern lowercase generics (`list`, `dict`, `tuple`) and union pipes (`|`).
3. **Immutability & Input Validation**: Dataclass models must validate physical bounds inside `__post_init__` (e.g. thickness $> 0$, $E_{oed} > 0$).
4. **Linting & Formatting Compliance**: All Python code must satisfy `ruff check` and `ruff format` before completion (`exclude = [".agents"]`).
