import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty import SIMP, load_airport, debug_plots
import subprocess

# Do this to have the plotting work with nohup
import matplotlib

matplotlib.use("Agg")
plt.ioff()

cur_dir = os.path.abspath(os.path.dirname(__file__))

# USER INPUTS
out_folder = os.path.join(cur_dir, "ORD_1000w")
os.makedirs(out_folder, exist_ok=True)
airport = "ORD"  # set to None to do other problem
resolution = "1000w"
min_density = 1e-3  # lower bound on density
filter_radius = 2e-3
penalty_exponent = 3.0
ks_rho = 10.0
use_smoothstep = False

set_temp = 200.0
q_elem = 1e8
max_temps = {
    "dumb": 3000,
    "arrivals": 600,
    "departures": 350,
    "arr_and_dep": 800,
}

only_postprocess_video = False  # skip running the problem and just make the video for the current setup

apt_data = load_airport(airport, resolution, min_density=min_density, ignore_cases=["dumb", "arrivals", "departures"])

# Plot the bounds it generated
debug_plots(apt_data, out_folder)

cases = apt_data["q_elem"].keys()
nx, ny, xlim, ylim = (apt_data["num_x"], apt_data["num_y"], apt_data["x_lim"], apt_data["y_lim"])
n_elem = (nx - 1) * (ny - 1)

# Set up the temperatures and heat generation to the desired amounts
for case_name in cases:
    apt_data["T_set_node"][case_name] *= set_temp
    apt_data["T_set_node"][case_name][apt_data["T_set_node"][case_name] == 0] = np.inf
    apt_data["q_elem"][case_name] *= q_elem

# ========== Initial condition options ==========
init = "uniform"  # can be "uniform", "taxiways", or "circle"

if not only_postprocess_video:
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
            keep_out=apt_data["keep_out"],
            plot=[out_folder, 5],
            # clim={case_name: [set_temp, max_temps[case_name]] for case_name in cases},
            airport_data=apt_data,
            r=filter_radius,
            p=penalty_exponent,
            ks_rho=ks_rho,
            use_smoothstep=use_smoothstep,
        ),
        promotes=["*"],
    )

    prob.model.add_objective("mass")
    prob.model.add_design_var("density_dv", lower=apt_data["density_lower"], upper=apt_data["density_upper"])
    for case_name in cases:
        prob.model.add_constraint(f"max_temp_{case_name}", upper=max_temps[case_name])

    prob.driver = om.pyOptSparseDriver(optimizer="IPOPT")
    prob.driver.options["debug_print"] = ["objs", "nl_cons", "ln_cons"]  # desvars, nl_cons, ln_cons, objs, totals
    prob.driver.hist_file = os.path.join(out_folder, "opt.hst")
    prob.driver.opt_settings["output_file"] = os.path.join(out_folder, "IPOPT.out")
    prob.driver.opt_settings["max_iter"] = 99999
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
    prob.driver.opt_settings["gamma_theta"] = 1e-2
    prob.driver.opt_settings["gamma_phi"] = 1e-2

    # Write data about problem setup to file for reproducibility
    write_vars = [
        "out_folder",
        "airport",
        "resolution",
        "min_density",
        "filter_radius",
        "penalty_exponent",
        "ks_rho",
        "use_smoothstep",
        "set_temp",
        "q_elem",
        "max_temps",
        "cases",
        "init",
    ]
    with open(os.path.join(out_folder, "problem_variable_values.txt"), "w") as f:
        f.write("==================================================================\n")
        f.write("                    RUNSCRIPT VARIABLE VALUES                     \n")
        f.write("==================================================================\n\n")
        for var in write_vars:
            f.write(f"{var}: {globals()[var]}\n")
        
        # Optimizer settings
        f.write(f"\n-------- {prob.driver.options['optimizer']} settings --------\n")
        for opt_setting in prob.driver.opt_settings.keys():
            f.write(f"{opt_setting}: {prob.driver.opt_settings[opt_setting]}\n")

    prob.setup(mode="rev")

    om.n2(prob, outfile=os.path.join(out_folder, "n2.html"), show_browser=False)

    mesh_x, mesh_y = simp.get_mesh()

    # Set the initial condition
    if init == "circle":
        x_mid = (xlim[0] + xlim[1]) / 2
        y_mid = (ylim[0] + ylim[1]) / 2
        r_circ = min(xlim[1] - xlim[0], ylim[1] - ylim[0]) / 2

        x_centroid = mesh_x[:-1, :-1] + mesh_x[1, 1] / 2
        y_centroid = mesh_y[:-1, :-1] + mesh_y[1, 1] / 2
        dens_init = ((x_centroid - x_mid)**2 + (y_centroid - y_mid)**2) < r_circ**2
        dens_init = dens_init.astype(float)
        dens_init[dens_init < min_density] = min_density
    elif init == "uniform":
        dens_init = np.ones(n_elem, dtype=float)
    elif init == "taxiways":
        dens_init = apt_data["runways"].flatten()
        dens_init += apt_data["taxiways"].flatten()
        dens_init[dens_init < min_density] = min_density
        dens_init[dens_init > 1.0] = 1.0
    else:
        raise ValueError(f"Initial condition \"{init}\" unknown, must be \"uniform\", \"taxiways\", or \"circle\"")
    prob.set_val("density_dv", dens_init)

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
