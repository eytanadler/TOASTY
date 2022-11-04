import openmdao.api as om
import openmdao.utils.assert_utils as om_assert
import numpy as np
import unittest
from toasty import Mass, AvgTemp, PenalizeDensity


class TestMass(unittest.TestCase):
    def setUp(self):
        self.rand = np.random.default_rng(219)

    def test_simple(self):
        nx = ny = 4

        p = om.Problem()
        p.model = Mass(num_x=nx, num_y=ny)
        p.setup()

        p.set_val("density", np.ones(((nx - 1) * (ny - 1))))
        p.run_model()

        self.assertAlmostEqual((nx - 1) * (ny - 1), p.get_val("mass").item())

    def test_simple(self):
        nx = ny = 4

        rho = self.rand.random(((nx - 1) * (ny - 1)))

        p = om.Problem()
        p.model = Mass(num_x=nx, num_y=ny)
        p.setup()

        p.set_val("density", rho)
        p.run_model()

        self.assertAlmostEqual(np.sum(rho), p.get_val("mass").item())

    def test_partials(self):
        nx = ny = 4

        rho = self.rand.random(((nx - 1) * (ny - 1)))

        p = om.Problem()
        p.model.add_subsystem("mass", Mass(num_x=nx, num_y=ny), promotes=["*"])
        p.setup()

        p.set_val("density", rho)

        om_assert.assert_check_partials(p.check_partials())


class TestPenalizeDensity(unittest.TestCase):
    def setUp(self):
        self.rand = np.random.default_rng(58)

    def test_simple(self):
        nx = ny = 4

        p = om.Problem()
        p.model = PenalizeDensity(num_x=nx, num_y=ny)
        p.setup()

        p.set_val("density", np.ones(((nx - 1) * (ny - 1))))
        p.run_model()

        np.testing.assert_allclose(np.ones(((nx - 1) * (ny - 1))), p.get_val("density_penalized"))

    def test_simple(self):
        nx = ny = 4

        rho = self.rand.random(((nx - 1) * (ny - 1)))

        p = om.Problem()
        p.model = PenalizeDensity(num_x=nx, num_y=ny)
        p.setup()

        p.set_val("density", rho)
        p.run_model()

        np.testing.assert_allclose(rho**3, p.get_val("density_penalized"))

    def test_partials(self):
        nx = ny = 4

        rho = self.rand.random(((nx - 1) * (ny - 1)))

        p = om.Problem()
        p.model.add_subsystem("penalize_rho", PenalizeDensity(num_x=nx, num_y=ny), promotes=["*"])
        p.setup()

        p.set_val("density", rho)

        om_assert.assert_check_partials(p.check_partials(), atol=5e-6, rtol=5e-6)


if __name__ == "__main__":
    unittest.main()
