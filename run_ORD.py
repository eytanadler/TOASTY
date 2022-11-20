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

    for case in cases:
        T = prob.get_val(f"temp_{case}").reshape(nx, ny)
        density = prob.get_val("density").reshape(nx - 1, ny - 1)

        fig, ax = plt.subplots(figsize=(xlim[1] * 10, ylim[1] * 10))
        c = ax.contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm", zorder=0)
        ax.pcolorfast(mesh_x, mesh_y, density, cmap=cmap_white, vmin=0.0, vmax=1.0, zorder=1)
        ax.pcolorfast(mesh_x, mesh_y, apt_data["runways"], cmap=cmap_run, vmin=0.0, vmax=1.0, zorder=2)
        ax.pcolorfast(mesh_x, mesh_y, apt_data["buildings"], cmap=cmap_build, vmin=0.0, vmax=1.0, zorder=2)
        cbar = fig.colorbar(c, ax=ax, fraction=0.02, pad=0.05)
        cbar.set_label("Temperature (K?)")
        ax.set_aspect("equal")
        ax.set_axis_off()

        os.makedirs(os.path.join(out_folder, case), exist_ok=True)
        if fname:
            fig.savefig(fname)
        else:
            fig.savefig(os.path.join(out_folder, case, f"opt_{x['nMajor']:04d}.png"), dpi=300)
        plt.close(fig)


# USER INPUTS
out_folder = os.path.join(cur_dir, "ORD_250w_temp400")
use_snopt = False
airport = "ORD"  # set to None to do other problem
resolution = "250w"
min_density = 1e-3  # lower bound on density

apt_data = load_airport(airport, resolution)

cases = apt_data["q_elem"].keys()
nx, ny, xlim, ylim = (apt_data["num_x"], apt_data["num_y"], apt_data["x_lim"], apt_data["y_lim"])
n_elem = (nx - 1) * (ny - 1)

# Set up the temperatures and heat generation to the desired amounts
for case_name in cases:
    apt_data["T_set_node"][case_name] *= 200.0
    apt_data["T_set_node"][case_name][apt_data["T_set_node"][case_name] == 0] = np.inf
    apt_data["q_elem"][case_name] *= 6e6

# Runways must stay
density_lower = apt_data["runways"].flatten()
density_lower[density_lower < min_density] = min_density

# Taxiways cannot go through buildings
density_upper = 1 - apt_data["buildings"].flatten()
density_upper[density_upper < min_density] = min_density

prob = om.Problem()
simp = prob.model.add_subsystem(
    "simp",
    SIMP(
        num_x=nx,
        num_y=ny,
        x_lim=xlim,
        y_lim=ylim,
        T_set=apt_data["T_set_node"],
        q=apt_data["q_elem"],
        plot=None if use_snopt else [out_folder, 5],
        airport_data=apt_data,
        r=2e-3,
        p=3.0,
        ks_rho=10.0,
        use_smoothstep=False,
    ),
    promotes=["*"],
)

prob.model.add_objective("mass")
prob.model.add_design_var("density_dv", lower=density_lower, upper=density_upper)
prob.model.add_constraint("max_temp_dumb", upper=400)

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
    prob.driver.opt_settings["linear_solver"] = "ma86"

prob.setup(mode="rev")

mesh_x, mesh_y = simp.get_mesh()

# # Start with a circle for the meme
# x_mid = (xlim[0] + xlim[1]) / 2
# y_mid = (ylim[0] + ylim[1]) / 2
# r_circ = min(xlim[1] - xlim[0], ylim[1] - ylim[0]) / 2

# x_centroid = mesh_x[:-1, :-1] + mesh_x[1, 1] / 2
# y_centroid = mesh_y[:-1, :-1] + mesh_y[1, 1] / 2
# dens_circ = ((x_centroid - x_mid)**2 + (y_centroid - y_mid)**2) < r_circ**2
# dens_circ = dens_circ.astype(float)
# dens_circ[dens_circ < min_density] = min_density
# prob.set_val("density_dv", dens_circ.flatten())

# prob.run_model()
prob.run_driver()

# Create video
for case_name in cases:
    subprocess.run(
        [
            "ffmpeg",
            "-framerate",
            "24",
            "-pattern_type",
            "glob",
            "-i",
            os.path.join(out_folder, case_name, f"opt_*.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # handle divisble by 2 errors
            os.path.join(out_folder, case_name, "opt_movie.mp4"),
        ]
    )
