import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
# from toasty.FEM_comp import FEM
from toasty.FEM_comp_sparse import FEM

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

nx = 31
ny = 31
x_linspace = np.linspace(0, 1.0, nx)
y_linspace = np.linspace(0, 1.0, ny)
mesh_x, mesh_y = np.meshgrid(x_linspace, y_linspace, indexing="ij")

T_set = np.full((nx, ny), np.inf)
T_set[:, 0] = 200.0

q = np.zeros((nx - 1, ny - 1), dtype=float)
q[0, -1] = 2e7
q[nx // 2, -1] = 5e7
q[-1, -1] = 2e7

p = om.Problem()
fem = p.model.add_subsystem("fem", FEM(mesh_x=mesh_x, mesh_y=mesh_y, T_set=T_set, q=q), promotes=["*"])
p.model.add_subsystem("mass", Mass(mesh_size=(nx, ny)), promotes=["*"])

p.model.nonlinear_solver = om.NewtonSolver(iprint=2, solve_subsystems=False, atol=1e-8)
p.model.linear_solver = om.DirectSolver()

p.model.add_objective("mass")
p.model.add_design_var("density", lower=1e-6, upper=1.0)
p.model.add_constraint("temp", upper=360)

p.driver = om.pyOptSparseDriver(optimizer='SNOPT')
p.driver.opt_settings['Major iterations limit'] = 20
p.driver.opt_settings['Major optimality tolerance'] = 1e-6
p.driver.opt_settings['Major feasibility tolerance'] = 1e-8
# p.driver.opt_settings["Verify level"] = 3

p.setup()

# om.n2(p)

density = np.ones((nx - 1, ny - 1))
p.set_val("density", density.flatten())

# p.check_partials()
p.run_model()
# p.run_driver()

T = p.get_val("temp").reshape(nx, ny)
density = p.get_val("density").reshape(nx - 1, ny - 1)
print(T)

fig, axs = plt.subplots(2, 1, figsize=(5, 8))
c = axs[0].contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm")
fig.colorbar(c, ax=axs[0])
axs[0].set_aspect("equal")

c = axs[1].pcolorfast(mesh_x, mesh_y, density, cmap="Blues", vmin=0.0, vmax=1.0)
fig.colorbar(c, ax=axs[1])
axs[1].set_aspect("equal")

cur_dir = os.path.dirname(__file__)
fig.savefig(os.path.join(cur_dir, "test.pdf"))
