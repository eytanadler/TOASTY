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
out_folder = os.path.join(cur_dir, "DTW_250w_multipoint")
use_snopt = True
airport = "DTW"  # set to None to do other problem
resolution = "250w"
min_density = 1e-3  # lower bound on density

apt_data = load_airport(airport, resolution)

# Get rid of the case where all the terminals are sinks at once
del apt_data["T_set_node"]["dumb"]
del apt_data["q_elem"]["dumb"]

cases = apt_data["q_elem"].keys()
nx, ny, xlim, ylim = (apt_data["num_x"], apt_data["num_y"], apt_data["x_lim"], apt_data["y_lim"])
n_elem = (nx - 1) * (ny - 1)

# Set up the temperatures and heat generation to the desired amounts
for case_name in cases:
    apt_data["T_set_node"][case_name] *= 200.0
    apt_data["T_set_node"][case_name][apt_data["T_set_node"][case_name] == 0] = np.inf
    apt_data["q_elem"][case_name] *= 1e7

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
        T_set=apt_data["T_set_node"],
        q=apt_data["q_elem"],
        plot=None if use_snopt else [out_folder, 5],
        airport_data=apt_data,
        r=4e-3,
        p=3.0,
        ks_rho=10.0,
        use_smoothstep=False,
    ),
    promotes=["*"],
)

prob.model.add_objective("mass")
prob.model.add_design_var("density_dv", lower=density_lower, upper=1.0)
prob.model.add_constraint("max_temp_evans", upper=900)
prob.model.add_constraint("max_temp_macnamera", upper=600)
prob.model.add_constraint("max_temp_macnamera_satellite", upper=800)

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
            os.path.join(out_folder, case_name, "opt_movie.mp4"),
        ]
    )