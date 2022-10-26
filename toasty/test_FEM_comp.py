import openmdao.api as om
import matplotlib.pyplot as plt
import os
import numpy as np
from toasty.FEM_comp import FEM

p = om.Problem()
fem = p.model = FEM()
mesh_x, mesh_y = fem.get_mesh()
nx = mesh_x.shape[0]
ny = mesh_x.shape[1]

p.model.nonlinear_solver = om.NewtonSolver(iprint=2, solve_subsystems=True)
p.model.linear_solver = om.DirectSolver()

p.setup()

q = np.zeros((nx - 1, ny - 1), dtype=float)
q[nx // 2, ny - 2] = 20.0 * nx * ny
q[-2, nx // 3 : 2 * nx // 3] = -2e5
fem.set_element_heat(q)
density = np.ones((nx - 1, ny - 1))
density[np.ix_(np.arange(nx // 3, 2 * nx // 3), np.arange(ny // 6, 5 * ny // 6))] = 0.00001
density[np.ix_(np.arange(0, nx // 3), np.arange(ny // 6, 5 * ny // 6))] = 0.2
p.set_val("density", density.flatten())

p.run_model()

T = p.get_val("temp").reshape(nx, ny)

fig, axs = plt.subplots(2, 1, figsize=(5, 8))
c = axs[0].contourf(mesh_x, mesh_y, T, 100, cmap="coolwarm")
fig.colorbar(c, ax=axs[0])
axs[0].set_aspect("equal")

c = axs[1].pcolorfast(mesh_x, mesh_y, density, cmap="Blues", vmin=0.0, vmax=1.0)
fig.colorbar(c, ax=axs[1])
axs[1].set_aspect("equal")

cur_dir = os.path.dirname(__file__)
fig.savefig(os.path.join(cur_dir, "test.pdf"))
