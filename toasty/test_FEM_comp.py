import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty.FEM_comp import FEM as FEM_dense
from toasty import FEM, Mass, gen_mesh, AvgTemp
import subprocess

cur_dir = os.path.dirname(__file__)

def callback_plot(x, fname=None):
    # Only save a plot every 10 major iterations
    if x["nMajor"] % 10 != 0:
        return

    T = prob.get_val("temp").reshape(nx, ny)
    density = prob.get_val("density").reshape(nx - 1, ny - 1)

    fig, axs = plt.subplots(2, 1, figsize=(5, 8))
    c = axs[0].contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm")
    cbar = fig.colorbar(c, ax=axs[0])
    cbar.set_label("Temperature (K?)")
    axs[0].set_aspect("equal")

    c = axs[1].pcolorfast(mesh_x, mesh_y, density, cmap="Blues", vmin=0.0, vmax=1.0)
    cbar = fig.colorbar(c, ax=axs[1])
    cbar.set_label("Density")
    axs[1].set_aspect("equal")

    if fname:
        fig.savefig(fname)
    else:
        fig.savefig(os.path.join(out_folder, f"opt_{x['nMajor']:04d}.png"), dpi=300)
    plt.close(fig)

out_folder = os.path.join(cur_dir, "opt")

nx = 51
ny = 51
n_elem = (nx - 1) * (ny - 1)
xlim = (0.0, 1.0)
ylim = xlim

T_set = np.full((nx, ny), np.inf)
T_set[[nx // 3, 2 * nx // 3], 0] = 200.0

q = np.zeros((nx - 1, ny - 1), dtype=float)
q[0, -1] = 2e5 / ((xlim[1] - xlim[0]) / (nx - 1))**1.5
q[nx // 2, -1] = 5e5 / ((xlim[1] - xlim[0]) / (nx - 1))**1.5
q[-1, -1] = 2e5 / ((xlim[1] - xlim[0]) / (nx - 1))**1.5

prob = om.Problem()

# Pick if you want dense or sparse
# fem = prob.model.add_subsystem("fem", FEM_dense(num_x=nx, num_y=ny, x_lim=xlim, y_lim=ylim, T_set=T_set, q=q), promotes=["*"])
fem = prob.model.add_subsystem("fem", FEM(num_x=nx, num_y=ny, x_lim=xlim, y_lim=ylim, T_set=T_set, q=q), promotes=["*"])

prob.model.add_subsystem("mass", Mass(num_x=nx, num_y=ny), promotes=["*"])
# prob.model.add_subsystem("element_avg_temp", AvgTemp(num_x=nx, num_y=ny), promotes=["*"])
# prob.model.add_subsystem("max_temp", om.KSComp(width=n_elem, rho=50.0), promotes_inputs=[("g", "avg_temp")], promotes_outputs=[("KS", "max_temp")])
prob.model.add_subsystem("max_temp", om.KSComp(width=nx * ny, rho=50.0), promotes_inputs=[("g", "temp")], promotes_outputs=[("KS", "max_temp")])

prob.model.add_objective("mass")
prob.model.add_design_var("density", lower=1e-6, upper=1.0)
prob.model.add_constraint("max_temp", upper=600)

prob.model.linear_solver = om.DirectSolver()

prob.driver = om.pyOptSparseDriver(optimizer="SNOPT")
os.makedirs(out_folder, exist_ok=True)
prob.driver.hist_file = os.path.join(out_folder, "opt.hst")
prob.driver.options["debug_print"] = ["objs", "nl_cons"]  # desvars, nl_cons, ln_cons, objs, totals
prob.driver.opt_settings["Iterations limit"] = 1e7
prob.driver.opt_settings["Major iterations limit"] = 5000
prob.driver.opt_settings["Major optimality tolerance"] = 1e-6
prob.driver.opt_settings["Major feasibility tolerance"] = 1e-8
prob.driver.opt_settings["Print file"] = os.path.join(out_folder, "SNOPT_print.out")
prob.driver.opt_settings["Summary file"] = os.path.join(out_folder, "SNOPT_summary.out")
prob.driver.opt_settings["snSTOP function handle"] = callback_plot
prob.driver.opt_settings["Hessian"] = "full memory"
prob.driver.opt_settings["Verify level"] = 0

prob.setup()

mesh_x, mesh_y = fem.get_mesh()

# prob.set_val("density", np.random.rand((nx - 1) * (ny - 1)))

# prob.run_model()
# prob.check_partials(includes=["element_avg_temp"])
prob.run_driver()

# om.n2(prob, show_browser=False, outfile=os.path.join(out_folder, "opt_n2.html"))
callback_plot({"funcs": {"fem.temp": prob.get_val("temp")}, "xuser": {"density": prob.get_val("density")}, "nMajor": 0}, fname=os.path.join(out_folder, f"opt_final.pdf"))

# Create video
subprocess.run(
    [
        "ffmpeg",
        "-framerate",
        "30",
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
