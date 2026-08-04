# Solara Web Application

Settlewell includes an interactive, browser-based graphical user interface built with [Solara](https://solara.dev/). This GUI is designed for rapid prototyping, real-time visualization, and easy report generation without requiring Python scripts.

## Launching the Application

Start the web application from your terminal:

```bash
solara run settlewell.solara_app
```

The application will launch in your default web browser (typically at `http://localhost:8765`).

## User Interface Overview

The GUI is divided into several main components:

### 1. Sidebar Controls (Left)
- **Global Settings:** Configure solver settings, groundwater levels, and simulation time.
- **Project Export:** Download project data and reports as PDF, Excel, DXF, or CSV.
- **Scenario Management:** Save, load, and switch between different configuration states.

### 2. Main Canvas (Center)
The central workspace where you construct your model. It includes tabs for different components:

- **Soil Stratigraphy:** Define soil layers interactively. Adjust thicknesses, edit geotechnical properties, or load predefined Flemish soil templates.
- **Dewatering & Pit:** Specify the dimensions of the construction pit and configure the dewatering parameters (target drawdown, aquifer type). You can add wells visually.
- **Loads & Buildings:** Place and dimension surface loads and neighboring buildings to assess damage risks.

### 3. Live Viewport Plots (Right)
As you modify the project configuration, the results in the right panel update in real-time. Available views include:

- **Plan View:** A 2D overhead view showing the pit, wells, buildings, and the hydraulic drawdown contours.
- **Cross-Section:** A 1D vertical slice showing soil layers, the excavation pit, the groundwater table, and the drawdown curve.
- **Stress Profile:** Vertical plots of effective stress before and after loading/dewatering.
- **Time-Settlement:** A graph of the primary consolidation and secondary creep settlement over time.
- **Damage Assessment:** Visualization of the risk category for selected buildings (e.g., using SBR or Boscarding & Cording methods).

## Interactive Features

- **Real-Time Feedback:** The solvers run efficiently in the background, updating plots almost instantly as you drag a slider or change a value.
- **Template Integration:** Quickly populate complex soil models by selecting from the Flemish Soil Database directly in the GUI.

## Downloading Reports

Once your analysis is complete, use the **Export** buttons in the left sidebar to generate deliverables. The GUI leverages the `Project` API's export engine, allowing you to instantly download PDF calculation reports, DXF drawings, or raw data directly to your local machine.
