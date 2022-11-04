import openmdao.api as om
import openmdao.utils.assert_utils as om_assert
import numpy as np
from toasty import PenalizeDensity, Mass, FEM
import unittest

class AssembledProblem(unittest.TestCase):
    def setUp(self):
        self.rand = np.random.default_rng(153)
        self.nx = nx = 9
        self.ny = ny = 13
        self.n_elem = (nx - 1) * (ny - 1)
        xlim = (0.0, 2.0)
        ylim = (-1.0, 3.0)

        # Set a corner, edge, and interior node
        T_set = np.full((nx, ny), np.inf)
        T_set[nx // 3, 0] = 200.0
        T_set[0, 0] = 100.0
        T_set[-1, -1] = 300.0
        T_set[nx // 3, ny // 2] = 140.0

        q = np.zeros((nx - 1, ny - 1), dtype=float)
        q[0, 0] = 1e6
        q[0, -1] = 2e5
        q[nx // 2, ny // 2] = 1e5
        q[nx // 2, -1] = 3e5
        q[-1, ny // 2] = 4e5

        self.p = prob = om.Problem()
        prob.model.add_subsystem(
            "simp", PenalizeDensity(num_x=nx, num_y=ny, p=3.0), promotes_inputs=[("density", "density_dv")], promotes_outputs=["density_penalized"]
        )
        prob.model.add_subsystem(
            "calc_mass", Mass(num_x=nx, num_y=ny), promotes_inputs=[("density", "density_dv")], promotes_outputs=["mass"]
        )
        prob.model.add_subsystem(
            "fem",
            FEM(num_x=nx, num_y=ny, x_lim=xlim, y_lim=ylim, T_set=T_set, q=q),
            promotes_inputs=[("density", "density_penalized")],
            promotes_outputs=["temp"],
        )
        prob.model.add_subsystem(
            "calc_max_temp",
            om.KSComp(width=nx * ny, rho=50.0),
            promotes_inputs=[("g", "temp")],
            promotes_outputs=[("KS", "max_temp")],
        )

        prob.setup()

    def test_values(self):
        """
        Do a regression test on some values
        """
        density = self.rand.random(self.n_elem)
        self.p.set_val("density_dv", density)
        self.p.run_model()

        np.testing.assert_allclose(np.sum(density), self.p.get_val("mass").item(), atol=1e-8, rtol=1e-8)
        np.testing.assert_allclose(1134.052863, self.p.get_val("max_temp").item(), atol=1e-8, rtol=1e-8)

    def test_partial_derivs(self):
        self.p.set_val("density_dv", self.rand.random(self.n_elem))
        self.p.run_model()

        om_assert.assert_check_partials(self.p.check_partials(), atol=8e-4, rtol=2e-6)

    def test_total_derivs(self):
        self.p.set_val("density_dv", self.rand.random(self.n_elem))
        self.p.run_model()

        om_assert.assert_check_totals(self.p.check_totals(["mass", "max_temp"], "density_dv"), atol=6e-2, rtol=1e-5)

if __name__=="__main__":
    unittest.main()
