import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty import SIMP, load_airport
import subprocess

# Do this to have the plotting work with nohup
import matplotlib

matplotlib.use("Agg")
plt.ioff()

cur_dir = os.path.abspath(os.path.dirname(__file__))
cmap_white = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#ffffffff", "#ffffff00"])
cmap_run = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#00000000", "#00000055"])
cmap_taxi = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#b3b3b300", "#b3b3b3ff"])
cmap_build = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#00000000", "#000000ff"])


def callback_plot(x, fname=None):
    # Only save a plot every X major iterations
    if x["nMajor"] % 1 != 0:
        return

    print("plotting")

    T = prob.get_val("temp").reshape(nx, ny)
    density = prob.get_val("density").reshape(nx - 1, ny - 1)

    if airport is None:
        fig, axs = plt.subplots(2, 1, figsize=(5, 8))
        c = axs[0].contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm")
        axs[0].pcolorfast(mesh_x, mesh_y, density, cmap=cmap_white, vmin=0.0, vmax=1.0, zorder=10)
        cbar = fig.colorbar(c, ax=axs[0])
        cbar.set_label("Temperature (K?)")
        axs[0].set_aspect("equal")

        c = axs[1].pcolorfast(mesh_x, mesh_y, density, cmap="Blues", vmin=0.0, vmax=1.0)
        cbar = fig.colorbar(c, ax=axs[1])
        cbar.set_label("Density")
        axs[1].set_aspect("equal")
    else:
        fig, ax = plt.subplots(figsize=(xlim[1] * 10, ylim[1] * 10))
        c = ax.contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm", zorder=0)
        ax.pcolorfast(mesh_x, mesh_y, density, cmap=cmap_white, vmin=0.0, vmax=1.0, zorder=1)
        ax.pcolorfast(mesh_x, mesh_y, apt_data["runways"], cmap=cmap_run, vmin=0.0, vmax=1.0, zorder=2)
        ax.pcolorfast(mesh_x, mesh_y, apt_data["buildings"], cmap=cmap_build, vmin=0.0, vmax=1.0, zorder=2)
        cbar = fig.colorbar(c, ax=ax, fraction=0.02, pad=0.05)
        cbar.set_label("Temperature (K?)")
        ax.set_aspect("equal")
        ax.set_axis_off()

    if fname:
        fig.savefig(fname)
    else:
        fig.savefig(os.path.join(out_folder, f"opt_{x['nMajor']:04d}.png"), dpi=300)
    plt.close(fig)


# USER INPUTS
out_folder = os.path.join(cur_dir, "SAN_airport_300w")

use_snopt = False
min_compliance_problem = False
mass_frac = 0.1
airport = "SAN"  # set to None to do other problem
resolution = "300w"

# Proper SIMP for min compliance problem (required to make linear mass constraint)
# mass_density_in = "density_dv" if min_compliance_problem else "density"
mass_density_in = "density_dv"
min_density = 1e-3  # lower bound on density

if airport is None:
    d = 101
    nx = d
    ny = d
    n_elem = (nx - 1) * (ny - 1)
    xlim = (0.0, 1.0)
    ylim = xlim

    T_set = np.full((nx, ny), np.inf)
    T_set[[nx // 3, 2 * nx // 3], 0] = 200.0

    q = np.zeros((nx - 1, ny - 1), dtype=float)
    q[0, -1] = 2e5 / ((xlim[1] - xlim[0]) / (nx - 1)) ** 1.5
    q[nx // 2, -1] = 5e5 / ((xlim[1] - xlim[0]) / (nx - 1)) ** 1.5
    q[-1, -1] = 2e5 / ((xlim[1] - xlim[0]) / (nx - 1)) ** 1.5

    density_lower = min_density
else:
    apt_data = load_airport(airport, resolution)
    nx, ny, xlim, ylim = (apt_data["num_x"], apt_data["num_y"], apt_data["x_lim"], apt_data["y_lim"])
    n_elem = (nx - 1) * (ny - 1)

    T_set = 200.0 * apt_data["T_set_node"]["27"]
    T_set[T_set == 0] = np.inf
    q = 5e7 * apt_data["q_elem"]["27"]
    q[np.arange(2 * nx // 3), :] *= 20

    density_lower = apt_data["runways"].flatten()
    density_lower[density_lower < min_density] = min_density

prob = om.Problem()
simp = prob.model.add_subsystem(
    "simp",
    SIMP(
        num_x=nx,
        num_y=ny,
        x_lim=xlim,
        y_lim=ylim,
        T_set=T_set,
        q=q,
        plot=None if use_snopt else [out_folder, 5],
        airport_data=apt_data if airport else None,
        r=1e-2,
        p=3.0,
        ks_rho=10.0,
        use_smoothstep=False,
    ),
    promotes=["*"],
)

if min_compliance_problem:
    prob.model.add_objective("max_temp")
    prob.model.add_design_var("density_dv", lower=density_lower, upper=1.0)
    prob.model.add_constraint("mass", upper=mass_frac * n_elem, linear=True)
else:
    prob.model.add_objective("mass")
    prob.model.add_design_var("density_dv", lower=density_lower, upper=1.0)
    prob.model.add_constraint("max_temp", upper=1000)

os.makedirs(out_folder, exist_ok=True)

if use_snopt:
    prob.driver = om.pyOptSparseDriver(optimizer="SNOPT")
    prob.driver.hist_file = os.path.join(out_folder, "opt.hst")
    prob.driver.options["debug_print"] = ["objs", "nl_cons", "ln_cons"]  # desvars, nl_cons, ln_cons, objs, totals
    prob.driver.opt_settings["Iterations limit"] = 1e9
    prob.driver.opt_settings["Minor iterations limit"] = 30_000
    prob.driver.opt_settings["New superbasics limit"] = 5_000
    prob.driver.opt_settings["Major iterations limit"] = 5_000
    prob.driver.opt_settings["Violation limit"] = 1e4
    prob.driver.opt_settings["Major optimality tolerance"] = 1e-5
    prob.driver.opt_settings["Major feasibility tolerance"] = 1e-7
    prob.driver.opt_settings["Print file"] = os.path.join(out_folder, "SNOPT_print.out")
    prob.driver.opt_settings["Summary file"] = os.path.join(out_folder, "SNOPT_summary.out")
    prob.driver.opt_settings["snSTOP function handle"] = callback_plot
    prob.driver.opt_settings["Hessian updates"] = 50
    prob.driver.opt_settings["Verify level"] = 0
    prob.driver.opt_settings["Penalty"] = 1
else:
    prob.driver = om.pyOptSparseDriver(optimizer="IPOPT")
    prob.driver.options["debug_print"] = ["objs", "nl_cons", "ln_cons"]  # desvars, nl_cons, ln_cons, objs, totals
    prob.driver.opt_settings["output_file"] = os.path.join(out_folder, "IPOPT.out")
    prob.driver.opt_settings["max_iter"] = 5000
    prob.driver.opt_settings["constr_viol_tol"] = 1e-6
    prob.driver.opt_settings["nlp_scaling_method"] = "gradient-based"
    prob.driver.opt_settings["acceptable_tol"] = 1e-5
    prob.driver.opt_settings["acceptable_iter"] = 0
    prob.driver.opt_settings["tol"] = 1e-5
    prob.driver.opt_settings["mu_strategy"] = "adaptive"
    prob.driver.opt_settings["corrector_type"] = "affine"
    prob.driver.opt_settings["limited_memory_max_history"] = 100
    prob.driver.opt_settings["corrector_type"] = "primal-dual"
    prob.driver.opt_settings["hessian_approximation"] = "limited-memory"

prob.setup(mode="rev")

# prob.set_val("density_dv", 0.5**(1/3))  # initialize density to 0.5

mesh_x, mesh_y = simp.get_mesh()

# om.n2(prob, show_browser=True, outfile=os.path.join(out_folder, "opt_n2.html"))

prob.run_driver()

callback_plot({"nMajor": 0}, fname=os.path.join(out_folder, f"opt_final.pdf"))

# Create video
subprocess.run(
    [
        "ffmpeg",
        "-framerate",
        "24",
        "-pattern_type",
        "glob",
        "-i",
        os.path.join(out_folder, f"opt_*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        os.path.join(out_folder, "opt_movie.mp4"),
    ]
)

# # Smooth video
# subprocess.run(
#     [
#         "ffmpeg",
#         "-i",
#         os.path.join(out_folder, "opt_move.mp4"),
#         "-filter:v",
#         "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
#         os.path.join(out_folder, "opt_movie_smoothed.mp4"),
#     ]
# )
