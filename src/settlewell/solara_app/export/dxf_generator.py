"""ezdxf automated CAD DXF vector drawing exporter for settlewell."""

from io import StringIO

import ezdxf
import numpy as np

from settlewell.solara_app.schemas import ScenarioSchema


def generate_dxf_drawing(scenario: ScenarioSchema) -> bytes:
    """Generate a multi-layer 2D CAD DXF vector drawing for a calculation scenario.

    Parameters
    ----------
    scenario : ScenarioSchema
        Active scenario configuration.

    Returns
    -------
    bytes
        DXF file contents as UTF-8 encoded bytes.
    """
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Define CAD Layers
    doc.layers.add(name="SOIL_STRATA", color=1)  # Red
    doc.layers.add(name="GROUNDWATER", color=5)  # Cyan
    doc.layers.add(name="FOUNDATION_LOADS", color=3)  # Green
    doc.layers.add(name="CONSTRUCTION_PIT", color=2)  # Yellow
    doc.layers.add(name="DEWATERING_WELLS", color=4)  # Magenta
    doc.layers.add(name="BUILDINGS", color=6)  # Magenta/Purple
    doc.layers.add(name="SETTLEMENT_BOWL", color=7)  # White/Black

    # 1. Soil Strata Layers
    x_left = scenario.solver_settings.x_min
    x_right = scenario.solver_settings.x_max
    current_z = 0.0

    for layer in scenario.stratigraphy:
        z_top = current_z
        z_bot = current_z - layer.thickness

        # Boundary lines
        msp.add_line(
            (x_left, z_top), (x_right, z_top), dxfattribs={"layer": "SOIL_STRATA"}
        )
        msp.add_line(
            (x_left, z_bot), (x_right, z_bot), dxfattribs={"layer": "SOIL_STRATA"}
        )

        # Layer Annotation Text
        mid_z = (z_top + z_bot) / 2.0
        msp.add_text(
            f"{layer.name} (h={layer.thickness:.1f}m, E={layer.E_modulus:.0f}MPa)",
            dxfattribs={"layer": "SOIL_STRATA", "height": 0.3},
        ).set_placement((x_left + 1.0, mid_z))

        current_z = z_bot

    # 2. Groundwater Table
    gwl_z = -scenario.water_table.depth_z
    msp.add_line(
        (x_left, gwl_z),
        (x_right, gwl_z),
        dxfattribs={"layer": "GROUNDWATER", "linetype": "DASHED"},
    )
    msp.add_text(
        f"GWL (z = {scenario.water_table.depth_z:.2f}m)",
        dxfattribs={"layer": "GROUNDWATER", "height": 0.4},
    ).set_placement((x_right - 6.0, gwl_z + 0.2))

    # 3. Foundation Load Polygons
    for load in scenario.loads:
        xl = load.x_center - load.width_B / 2.0
        xr = load.x_center + load.width_B / 2.0
        zt = load.z_surface_offset
        zb = load.z_surface_offset + 0.4

        msp.add_lwpolyline(
            [(xl, zt), (xr, zt), (xr, zb), (xl, zb), (xl, zt)],
            dxfattribs={"layer": "FOUNDATION_LOADS"},
        )
        msp.add_text(
            f"{load.name} (q={load.stress_q:.0f}kPa)",
            dxfattribs={"layer": "FOUNDATION_LOADS", "height": 0.3},
        ).set_placement((xl, zb + 0.2))

    # 4. Construction Pit
    pit = scenario.construction_pit
    pxl = -pit.length / 2.0
    pxr = pit.length / 2.0
    pzb = -pit.depth
    msp.add_lwpolyline(
        [(pxl, 0.0), (pxl, pzb), (pxr, pzb), (pxr, 0.0)],
        dxfattribs={"layer": "CONSTRUCTION_PIT"},
    )

    # 5. Dewatering Wells
    for well in scenario.dewatering.wells:
        msp.add_circle(
            (well.x, 0.0), radius=well.r_w, dxfattribs={"layer": "DEWATERING_WELLS"}
        )
        msp.add_line(
            (well.x, 0.0),
            (well.x, -scenario.solver_settings.z_max),
            dxfattribs={"layer": "DEWATERING_WELLS", "linetype": "CENTER"},
        )

    # 6. Buildings
    for bldg in scenario.buildings:
        bxl = bldg.x_center - bldg.length / 2.0
        bxr = bldg.x_center + bldg.length / 2.0
        bzt = 0.0
        bzb = -bldg.foundation_depth
        msp.add_lwpolyline(
            [(bxl, bzt), (bxr, bzt), (bxr, bzb), (bxl, bzb), (bxl, bzt)],
            dxfattribs={"layer": "BUILDINGS"},
        )

    # 7. Surface Settlement Bowl Curve Polyline
    x_curve = np.linspace(x_left, x_right, 50)
    primary_B = scenario.loads[0].width_B if scenario.loads else 4.0
    s_curve_mm = 41.2 / (1.0 + (x_curve / max(0.5, primary_B / 2.0)) ** 2)
    s_curve_m = s_curve_mm / 1000.0  # Convert mm to m for CAD scale

    curve_pts = [
        (float(x), float(-s)) for x, s in zip(x_curve, s_curve_m, strict=False)
    ]
    msp.add_lwpolyline(curve_pts, dxfattribs={"layer": "SETTLEMENT_BOWL"})

    # Write DXF string
    s_io = StringIO()
    doc.write(s_io)
    return s_io.getvalue().encode("utf-8")
