import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty.FEM_comp import FEM
from toasty.FEM_comp_sparse import FEM as FEM_sparse
import subprocess

cur_dir = os.path.dirname(__file__)

class Mass(om.ExplicitComponent):
    def initialize(self):
        self.options.declare("mesh_size", types=tuple, default=(2, 2), desc="Tuple of mesh size in (nx, ny)")
    
    def setup(self):
        nx, ny = self.options["mesh_size"]
        self.add_input("density", shape=((nx - 1) * (ny - 1),))
        self.add_output("mass")

        self.declare_partials("mass", "density", val=1.0)
    
    def compute(self, inputs, outputs):
        outputs["mass"] = np.sum(inputs["density"])


def callback_plot(x, fname=None):
    T = x["funcs"]["fem.temp"].reshape(nx, ny)
    density = x["xuser"]["density"].reshape(nx - 1, ny - 1)

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
        fig.savefig(os.path.join(cur_dir, "opt", f"opt_{x['nMajor']:04d}.png"), dpi=300)
    plt.close(fig)

nx = 31
ny = 31
x_linspace = np.linspace(0, 1.0, nx)
y_linspace = np.linspace(0, 1.0, ny)
mesh_x, mesh_y = np.meshgrid(x_linspace, y_linspace, indexing="ij")

T_set = np.full((nx, ny), np.inf)
T_set[:, 0] = 200.0

q = np.zeros((nx - 1, ny - 1), dtype=float)
q[0, -1] = 2e5 / x_linspace[1]**1.5
q[nx // 2, -1] = 5e5 / x_linspace[1]**1.5
q[-1, -1] = 2e5 / x_linspace[1]**1.5

prob = om.Problem()

# Pick if you want dense or sparse
# fem = prob.model.add_subsystem("fem", FEM(mesh_x=mesh_x, mesh_y=mesh_y, T_set=T_set, q=q), promotes=["*"])
fem = prob.model.add_subsystem("fem", FEM_sparse(mesh_x=mesh_x, mesh_y=mesh_y, T_set=T_set, q=q), promotes=["*"])

prob.model.add_subsystem("mass", Mass(mesh_size=(nx, ny)), promotes=["*"])

prob.model.add_objective("mass")
prob.model.add_design_var("density", lower=1e-6, upper=1.0)
prob.model.add_constraint("temp", upper=600)

prob.model.linear_solver = om.DirectSolver()

prob.driver = om.pyOptSparseDriver(optimizer="SNOPT")
os.makedirs(os.path.join(cur_dir, "opt"), exist_ok=True)
prob.driver.hist_file = os.path.join(cur_dir, "opt", "opt.hst")
prob.driver.options["debug_print"] = ["objs"]  # desvars, nl_cons, ln_cons, objs, totals
prob.driver.opt_settings["Iterations limit"] = 1e7
prob.driver.opt_settings["Major iterations limit"] = 500
prob.driver.opt_settings["Major optimality tolerance"] = 1e-6
prob.driver.opt_settings["Major feasibility tolerance"] = 1e-8
prob.driver.opt_settings["Print file"] = os.path.join(cur_dir, "opt", "SNOPT_print.out")
prob.driver.opt_settings["Summary file"] = os.path.join(cur_dir, "opt", "SNOPT_summary.out")
prob.driver.opt_settings["snSTOP function handle"] = callback_plot
prob.driver.opt_settings["Verify level"] = 0

prob.setup()

# prob.run_model()
# prob.check_partials()
prob.run_driver()

callback_plot({"funcs": {"fem.temp": prob.get_val("temp")}, "xuser": {"density": prob.get_val("density")}}, fname=os.path.join(cur_dir, "opt", f"opt_final.pdf"))

# Create video
subprocess.run(
    [
        "ffmpeg",
        "-framerate",
        "10",
        "-pattern_type",
        "glob",
        "-i",
        os.path.join(cur_dir, "opt", f"opt_*.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        os.path.join(cur_dir, "opt", "opt_movie.mp4"),
    ]
)

# # Smooth video
# subprocess.run(
#     [
#         "ffmpeg",
#         "-i",
#         os.path.join(cur_dir, "opt", "opt_move.mp4"),
#         "-filter:v",
#         "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
#         os.path.join(cur_dir, "opt", "opt_movie_smoothed.mp4"),
#     ]
# )
