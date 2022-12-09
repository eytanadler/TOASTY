import matplotlib.pyplot as plt
import matplotlib
import os
from .utils import gen_mesh

def debug_plots(apt_data, out_dir):
    # ==================== Bounds debug plot ====================
    lower, upper = (apt_data["density_lower"], apt_data["density_upper"])

    # Create the default mesh corresponding to indexing of nodal rows/cols
    nx, ny = lower.shape
    nx += 1
    ny += 1
    mesh_x, mesh_y = gen_mesh(nx, ny, (0, nx - 1), (0, ny - 1))

    fig, axs = plt.subplots(1, 2, figsize=(12, 8))

    # Plot data
    axs[0].pcolorfast(
        mesh_x, mesh_y, lower, cmap="binary", vmin=0.0, vmax=1.0
    )
    axs[0].set_title("Lower bound")
    axs[1].pcolorfast(
        mesh_x, mesh_y, upper, cmap="binary", vmin=0.0, vmax=1.0
    )
    axs[1].set_title("Upper bound")

    fig.suptitle("White = 0, black = 1")

    for i in range(2):
        axs[i].set_xlabel("Nodal row index")
        axs[i].set_ylabel("Nodal column index")
        axs[i].set_aspect("equal")

    fig.savefig(os.path.join(out_dir, "debug_plot_bounds.png"), dpi=300)
    plt.close(fig)

    # ==================== Heat debug plot ====================
    n_cases = len(list(apt_data["q_elem"].keys()))
    fig, axs = plt.subplots(1, n_cases, figsize=(6*n_cases, 8))
    if n_cases == 1:
        axs = [axs]
    red_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#ffffff", "#ff0000"])

    for i_case, case in enumerate(apt_data["q_elem"].keys()):
        axs[i_case].pcolorfast(
            mesh_x, mesh_y, apt_data["q_elem"][case], cmap=red_cmap, vmin=0.0, vmax=1.0
        )
        axs[i_case].set_xlabel("Nodal row index")
        axs[i_case].set_ylabel("Nodal column index")
        axs[i_case].set_aspect("equal")
        axs[i_case].set_title(case)

    fig.savefig(os.path.join(out_dir, "debug_plot_heat.png"), dpi=300)
    plt.close(fig)

    # ==================== Temp debug plot ====================
    fig, axs = plt.subplots(1, n_cases, figsize=(6*n_cases, 8))
    if n_cases == 1:
        axs = [axs]
    blue_cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#ffffff", "#0000ff"])

    for i_case, case in enumerate(apt_data["T_set_node"].keys()):
        axs[i_case].contourf(
            mesh_x, mesh_y, apt_data["T_set_node"][case], cmap=blue_cmap, vmin=0.0, vmax=1.0
        )
        axs[i_case].set_xlabel("Nodal row index")
        axs[i_case].set_ylabel("Nodal column index")
        axs[i_case].set_aspect("equal")
        axs[i_case].set_title(case)

    fig.savefig(os.path.join(out_dir, "debug_plot_temp.png"), dpi=300)
    plt.close(fig)
