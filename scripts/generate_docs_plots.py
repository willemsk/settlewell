"""Generate vector SVG convergence plots for MkDocs validation page.

Computes limiting-case numerical convergence data and exports SVG graphs:
1. fd_grid_refinement.svg — 2D Finite-Difference grid refinement vs Thiem analytical solution.
2. theis_to_thiem_convergence.svg — Unsteady Theis drawdown converging to steady-state Thiem.
3. mesh_independence.svg — 1D consolidation settlement vs sublayer count N.
4. cooper_jacob_approximation.svg — Cooper-Jacob approximation error vs Boltzmann u.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import exp1

from settlewell import (
    AquiferType,
    ConstructionPit,
    DewateringConfig,
    SoilLayer,
    SoilProfile,
    Well,
    create_grid,
    extract_drawdown_at_points,
    solve_steady_state,
    theis_drawdown_single_well,
    thiem_drawdown_single_well,
)
from settlewell.settlement import compute_total_settlement

# Output directory for documentation SVG assets
OUTPUT_DIR = Path("docs/assets/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Set clean matplotlib styling for documentation
plt.style.use(
    "seaborn-v0_8-whitegrid"
    if "seaborn-v0_8-whitegrid" in plt.style.available
    else "default"
)
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 14,
        "svg.fonttype": "none",  # Retain clean editable text in SVG
    }
)


def generate_fd_grid_refinement_plot():
    """Plot 1: FD Grid refinement vs Thiem analytical drawdown curve."""
    Q, T, R_val, H0 = 0.001, 5e-4, 200.0, 5.0
    well = Well(x=0.0, y=0.0, Q=Q)
    config = DewateringConfig(
        wells=[well],
        target_drawdown_mtaw=3.0,
        original_gwl_mtaw=H0,
        pumping_duration_days=1,
        aquifer_type=AquiferType.CONFINED,
    )
    layer = SoilLayer(
        "Sand",
        thickness=10.0,
        gamma=17.5,
        gamma_sat=20.0,
        k_h=T / 10.0,
        e0=0.5,
        Cc=0.02,
        Cr=0.005,
        Eoed=30000,
        Cv=1e-2,
    )
    profile = SoilProfile(layers=[layer], gwl_mtaw=H0, surface_level_mtaw=H0 + 1.0)
    pit = ConstructionPit(length=10.0, width=8.0, depth=3.0)

    x_analytical = np.linspace(1.0, 150.0, 300)
    s_analytical = thiem_drawdown_single_well(
        x_analytical, Q=Q, T=T, R=R_val, H0=H0, aquifer_type=AquiferType.CONFINED
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        x_analytical,
        s_analytical,
        color="black",
        linewidth=2.5,
        label="Thiem Analytical Solution",
    )

    dx_list = [10.0, 5.0, 2.0, 1.0]
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71"]
    markers = ["o", "s", "^", "D"]

    for dx, color, marker in zip(dx_list, colors, markers):
        grid = create_grid(x_range=(-R_val, R_val), y_range=(-R_val, R_val), dx=dx)
        grid = solve_steady_state(grid, config, profile, pit)
        eval_x = np.arange(dx, 150.0, max(dx, 5.0))
        eval_pts = [(x, 0.0) for x in eval_x]
        s_num = extract_drawdown_at_points(grid, eval_pts, H0)
        ax.plot(
            eval_x,
            s_num,
            marker=marker,
            linestyle="--",
            color=color,
            alpha=0.85,
            label=f"FD Grid (Δx = {dx}m)",
        )

    ax.set_xlabel("Distance from Well r [m]")
    ax.set_ylabel("Drawdown s [m]")
    ax.set_title(
        "2D Finite-Difference Grid Refinement Convergence (Δx → 0)", weight="bold"
    )
    ax.set_xlim(0, 150)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fd_grid_refinement.svg", format="svg")
    plt.close(fig)
    print("Saved docs/assets/images/fd_grid_refinement.svg")


def generate_theis_to_thiem_plot():
    """Plot 2: Unsteady Theis drawdown converging to steady-state Thiem curve."""
    Q, T, S, R, H0 = 0.001, 5e-4, 0.1, 200.0, 5.0
    r_vals = np.linspace(1.0, 150.0, 300)
    s_thiem = thiem_drawdown_single_well(r_vals, Q, T, R, H0, AquiferType.CONFINED)

    t_ss_days = (R**2 * S / (2.25 * T)) / 86400.0  # ≈ 41.15 days
    test_days = [1.0, 5.0, 15.0, t_ss_days]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        r_vals,
        s_thiem,
        color="black",
        linewidth=2.5,
        linestyle="-",
        label=f"Thiem Steady-State (R={R:.0f}m)",
    )

    colors = ["#3498db", "#9b59b6", "#e67e22", "#27ae60"]
    for t_d, color in zip(test_days, colors):
        t_sec = t_d * 86400.0
        s_theis = theis_drawdown_single_well(r_vals, t_sec, Q, T, S)
        lbl = (
            f"Theis t = {t_d:.1f} days"
            if t_d == t_ss_days
            else f"Theis t = {t_d:.0f} days"
        )
        ax.plot(r_vals, s_theis, color=color, linewidth=1.8, linestyle="--", label=lbl)

    ax.set_xlabel("Distance from Well r [m]")
    ax.set_ylabel("Drawdown s [m]")
    ax.set_title(
        "Unsteady Theis Drawdown Converging to Steady-State Thiem (t → ∞)",
        weight="bold",
    )
    ax.set_xlim(0, 150)
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "theis_to_thiem_convergence.svg", format="svg")
    plt.close(fig)
    print("Saved docs/assets/images/theis_to_thiem_convergence.svg")


def generate_mesh_independence_plot():
    """Plot 3: Total 1D settlement vs sublayer count N demonstrating spatial mesh independence."""
    n_sub_list = [1, 2, 4, 8, 16, 32, 64]
    settlements = []

    for n_sub in n_sub_list:
        thickness = 3.0 / n_sub
        layers = [
            SoilLayer(
                name=f"Klei_{i}",
                thickness=thickness,
                gamma=16.0,
                gamma_sat=18.5,
                k_h=1e-9,
                e0=1.0,
                Cc=0.30,
                Cr=0.06,
                Eoed=3000,
                Cv=1e-7,
                OCR=1.0,
            )
            for i in range(n_sub)
        ]
        profile = SoilProfile(layers=layers, gwl_mtaw=4.0, surface_level_mtaw=5.0)
        s, _ = compute_total_settlement(profile, drawdown=2.0)
        settlements.append(s * 1000.0)  # in mm

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        n_sub_list,
        settlements,
        marker="o",
        linewidth=2,
        color="#2980b9",
        markersize=7,
        label="1D Primary Settlement",
    )
    ax.axhline(
        settlements[-1],
        color="#e74c3c",
        linestyle="--",
        linewidth=1.5,
        label=f"Asymptotic Value ({settlements[-1]:.2f} mm)",
    )

    ax.set_xlabel("Number of Sublayer Discretizations (N)")
    ax.set_ylabel("Total Surface Settlement [mm]")
    ax.set_title("1D Consolidation Spatial Mesh Independence (N → ∞)", weight="bold")
    ax.set_xscale("log")
    ax.set_xticks(n_sub_list)
    ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "mesh_independence.svg", format="svg")
    plt.close(fig)
    print("Saved docs/assets/images/mesh_independence.svg")


def generate_cooper_jacob_plot():
    """Plot 4: Relative error of Cooper-Jacob logarithmic approximation vs u."""
    u_vals = np.logspace(-4, 0, 200)
    w_exact = exp1(u_vals)
    w_cj = -0.5772156649 - np.log(u_vals)  # Cooper-Jacob approximation ln(2.25/u)
    rel_error = np.abs(w_cj - w_exact) / w_exact * 100.0

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)

    ax1.plot(
        u_vals,
        w_exact,
        color="#2c3e50",
        linewidth=2.2,
        label="Exact Well Function W(u)",
    )
    ax1.plot(
        u_vals,
        w_cj,
        color="#e67e22",
        linewidth=2.0,
        linestyle="--",
        label="Cooper-Jacob Approx ln(2.25/u)",
    )
    ax1.set_ylabel("Well Function Value [-]")
    ax1.set_title("Cooper-Jacob Logarithmic Approximation (u → 0)", weight="bold")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle=":", alpha=0.6)

    ax2.plot(
        u_vals, rel_error, color="#c0392b", linewidth=2.0, label="Relative Error [%]"
    )
    ax2.axvline(
        0.01,
        color="#27ae60",
        linestyle=":",
        linewidth=1.8,
        label="Standard Threshold u = 0.01 (Error ≈ 0.25%)",
    )
    ax2.set_xlabel("Boltzmann Parameter u = r²S / (4Tt) [-]")
    ax2.set_ylabel("Relative Error [%]")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_ylim(0.01, 100)
    ax2.legend(loc="upper left", frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "cooper_jacob_approximation.svg", format="svg")
    plt.close(fig)
    print("Saved docs/assets/images/cooper_jacob_approximation.svg")


def main():
    print("Generating vector SVG convergence plots for MkDocs validation page...")
    generate_fd_grid_refinement_plot()
    generate_theis_to_thiem_plot()
    generate_mesh_independence_plot()
    generate_cooper_jacob_plot()
    print("All 4 SVG vector convergence plots successfully generated.")


if __name__ == "__main__":
    main()
