import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty import SIMP, load_airport, debug_plots
import subprocess
from pyoptsparse.pyOpt_history import History

# Do this to have the plotting work with nohup
import matplotlib

matplotlib.use("Agg")
plt.ioff()

cur_dir = os.path.abspath(os.path.dirname(__file__))

# USER INPUTS
out_folder = os.path.join(cur_dir, "title_slide_fun")
os.makedirs(out_folder, exist_ok=True)

min_density = 1e-3  # lower bound on density
filter_radius = 1.6e-3
penalty_exponent = 3.0
ks_rho = 10.0
use_smoothstep = False

max_temp = 400
set_temp = 200.0
q_elem = 1e7

d = 700
nx = 2 * d + 1
ny = d + 1
n_elem = (nx - 1) * (ny - 1)
xlim = (0.0, 2.0)
ylim = (0.0, 1.0)

T_set = np.full((nx, ny), np.inf)
T_set[nx // 3 : 2 * nx // 3 + 1, 14 * ny // 15] = set_temp

q = np.zeros((nx - 1, ny - 1), dtype=float)
q[nx // 30, ny // 15 : ny // 2] = q_elem
q[nx // 30 : 29 * nx // 30, ny // 15] = q_elem
q[29 * nx // 30, ny // 15 : ny // 2] = q_elem

density_lower = min_density

postprocess_video_only = False  # skip running the problem and just make the video for the current setup

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
        plot=[out_folder, 5],
        # clim={case_name: [set_temp, max_temps[case_name]] for case_name in cases},
        r=filter_radius,
        p=penalty_exponent,
        ks_rho=ks_rho,
        use_smoothstep=use_smoothstep,
    ),
    promotes=["*"],
)

prob.model.add_objective("mass")
prob.model.add_design_var("density_dv", lower=min_density, upper=1.0)
prob.model.add_constraint(f"max_temp", upper=max_temp)

prob.driver = om.pyOptSparseDriver(optimizer="IPOPT")
prob.driver.hist_file = os.path.join(out_folder, "opt.hst")
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
prob.driver.opt_settings["limited_memory_max_history"] = 1000
prob.driver.opt_settings["corrector_type"] = "primal-dual"
prob.driver.opt_settings["hessian_approximation"] = "limited-memory"
prob.driver.opt_settings["linear_solver"] = "ma77"

prob.setup(mode="rev")

om.n2(prob, outfile=os.path.join(out_folder, "n2.html"), show_browser=False)

mesh_x, mesh_y = simp.get_mesh()

dens_init = np.ones(n_elem, dtype=float) * 0.01
prob.set_val("density_dv", dens_init)

if not postprocess_video_only:
    # prob.run_model()
    prob.run_driver()

# Create better images
hist = History(prob.driver.hist_file)
dv_vals = hist.getValues(names=["density_dv"])["density_dv"]
plot_folder = os.path.join(out_folder, "postprocess")
os.makedirs(plot_folder, exist_ok=True)

for i, density in enumerate(dv_vals):
    if i % 2 != 0:
        continue

    print(f"Plotting iteration {i}             ", end="\r")

    density = density.reshape(nx - 1, ny - 1)
    fname = os.path.join(plot_folder, f"plot_{i:05d}.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.pcolorfast(mesh_x, mesh_y, density, cmap="inferno", vmin=min_density, vmax=1.0)
    plt.axis("off")
    ax.set_aspect("equal")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(fname, dpi=300)
    plt.close(fig)

print("")

# Create video
subprocess.run(
    [
        "ffmpeg",
        "-framerate",
        "30",
        "-pattern_type",
        "glob",
        "-i",
        os.path.join(plot_folder, f"plot_*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # handle divisble by 2 errors
        os.path.join(plot_folder, "opt_movie.mp4"),
    ]
)
