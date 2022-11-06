import openmdao.api as om
import openmdao.utils.assert_utils as om_assert
import numpy as np
import unittest
from toasty import FEM


class SingleElem(unittest.TestCase):
    def setUp(self):
        self.nx = 2
        self.ny = 2

        self.T_set = np.full((self.nx, self.ny), np.inf)  # don't set any temperatures
        self.q = np.zeros((self.nx - 1, self.ny - 1))

        # Ordering in local and global matrices is different; this is the indices of the nodes in CCW order
        self.idx_glob = np.array([0, 2, 3, 1])

    def test_stiffness_mat(self):
        """
        Check that the global stiffness matrix equals
        the local one when the mesh is only one element.
        """
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)

        p.setup()
        p.run_model()

        K_loc = fem._local_stiffness(0, 0)

        np.testing.assert_allclose(K_loc, fem.K_glob.toarray()[np.ix_(self.idx_glob, self.idx_glob)])
        np.testing.assert_allclose(0.0, fem.F_glob)

    def test_single_elem_set_temp(self):
        """
        Set one of the nodal temperatures.
        """
        self.T_set[0, 0] = 10.0  # set the temperature of the lower left node

        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)

        p.setup()
        p.run_model()

        K_loc = fem._local_stiffness(0, 0)
        K_loc[0, :] = 0.0
        K_loc[0, 0] = 1.0

        F = np.zeros((self.nx * self.ny))
        F[0] = self.T_set[0, 0]

        np.testing.assert_allclose(K_loc, fem.K_glob.toarray()[np.ix_(self.idx_glob, self.idx_glob)])
        np.testing.assert_allclose(F, fem.F_glob.flatten())

        # No heat added or removed, so all temps should be the temp of the set one
        np.testing.assert_allclose(self.T_set[0, 0], p.get_val("temp"))


class FourElem(unittest.TestCase):
    """
    Some unique cases with the set temperature in the interior now that we have an interior node.
    """

    def setUp(self):
        self.nx = 3
        self.ny = 3

        self.T_set = np.full((self.nx, self.ny), np.inf)
        self.T_set[1, 1] = 1.0  # set the interior temperature
        self.q = np.zeros((self.nx - 1, self.ny - 1))
        self.q[0, 0] = 1e3  # need to set some heat addition to prevent totally uniform temp field

        self.p = om.Problem()
        self.fem = self.p.model.add_subsystem(
            "fem", FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q), promotes=["*"]
        )

        self.rand = np.random.default_rng(314)

    def test_set_temp_interior(self):
        """
        Regression test on stiffness matrix.
        """
        self.p.setup()
        self.p.run_model()

        K_glob = np.array(
            [
                [
                    6.66666667e02,
                    -1.66666667e02,
                    0.00000000e00,
                    -1.66666667e02,
                    -3.33333333e02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    -1.66666667e02,
                    1.33333333e03,
                    -1.66666667e02,
                    -3.33333333e02,
                    -3.33333333e02,
                    -3.33333333e02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    0.00000000e00,
                    -1.66666667e02,
                    6.66666667e02,
                    0.00000000e00,
                    -3.33333333e02,
                    -1.66666667e02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    -1.66666667e02,
                    -3.33333333e02,
                    0.00000000e00,
                    1.33333333e03,
                    -3.33333333e02,
                    0.00000000e00,
                    -1.66666667e02,
                    -3.33333333e02,
                    0.00000000e00,
                ],
                [
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    1.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    0.00000000e00,
                    -3.33333333e02,
                    -1.66666667e02,
                    0.00000000e00,
                    -3.33333333e02,
                    1.33333333e03,
                    0.00000000e00,
                    -3.33333333e02,
                    -1.66666667e02,
                ],
                [
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    -1.66666667e02,
                    -3.33333333e02,
                    0.00000000e00,
                    6.66666667e02,
                    -1.66666667e02,
                    0.00000000e00,
                ],
                [
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    -3.33333333e02,
                    -3.33333333e02,
                    -3.33333333e02,
                    -1.66666667e02,
                    1.33333333e03,
                    -1.66666667e02,
                ],
                [
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    -3.33333333e02,
                    -1.66666667e02,
                    0.00000000e00,
                    -1.66666667e02,
                    6.66666667e02,
                ],
            ]
        )

        np.testing.assert_allclose(K_glob, self.fem.K_glob.toarray())

    def test_check_partials(self):
        """
        Check that partial derivatives when an interior temperature is set.
        """
        self.p.setup()
        self.p.set_val("density", self.rand.random((self.nx - 1) * (self.ny - 1)))
        self.p.run_model()

        om_assert.assert_check_partials(self.p.check_partials(), atol=5e-6, rtol=5e-8)


class NineElem(unittest.TestCase):
    """
    The 9-element case covers all possible element arrangements (I believe) because it
    has full interior elements, edge elements, and corner elements.
    """

    def setUp(self):
        self.rand = np.random.default_rng(37)  # random generator

        self.nx = 4
        self.ny = 4

        self.T_set = np.full((self.nx, self.ny), np.inf)  # don't set any temperatures
        self.q = np.zeros((self.nx - 1, self.ny - 1))

        self.K_glob = np.array(
            [
                [
                    666.66666667,
                    -166.66666667,
                    0.0,
                    0.0,
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    -166.66666667,
                    1333.33333333,
                    -166.66666667,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    -166.66666667,
                    1333.33333333,
                    -166.66666667,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    -166.66666667,
                    666.66666667,
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                    1333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    2666.66666667,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    2666.66666667,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                    0.0,
                    0.0,
                    -333.33333333,
                    1333.33333333,
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                    1333.33333333,
                    -333.33333333,
                    0.0,
                    0.0,
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    2666.66666667,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    2666.66666667,
                    -333.33333333,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                    0.0,
                    0.0,
                    -333.33333333,
                    1333.33333333,
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -166.66666667,
                    -333.33333333,
                    0.0,
                    0.0,
                    666.66666667,
                    -166.66666667,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -166.66666667,
                    1333.33333333,
                    -166.66666667,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -333.33333333,
                    -333.33333333,
                    0.0,
                    -166.66666667,
                    1333.33333333,
                    -166.66666667,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -333.33333333,
                    -166.66666667,
                    0.0,
                    0.0,
                    -166.66666667,
                    666.66666667,
                ],
            ]
        )

    def test_stiffness(self):
        """
        Regression test for 9-element stiffness matrix.
        """
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)
        p.setup()

        np.testing.assert_allclose(self.K_glob, fem.K_glob.toarray())
        np.testing.assert_allclose(0.0, fem.F_glob)

    def test_stiffness_set_node(self):
        """
        Regression test for 9-element stiffness matrix.
        """
        self.T_set[1, 1] = 10.0
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)
        p.setup()

        K = self.K_glob
        K[self.ny + 1, :] = 0.0
        K[self.ny + 1, self.ny + 1] = 1.0

        F = np.zeros(self.nx * self.ny)
        F[self.ny + 1] = self.T_set[1, 1]

        np.testing.assert_allclose(self.K_glob, fem.K_glob.toarray())
        np.testing.assert_allclose(F, fem.F_glob.flatten())

    def test_partials(self):
        """
        Test partial derivatives at a reasonable design point.
        """
        self.T_set[0, 3] = 1.0
        self.q[2, 1] = 1e3

        p = om.Problem()
        p.model.add_subsystem("fem", FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q), promotes=["*"])
        p.setup()
        p.run_model()

        om_assert.assert_check_partials(p.check_partials(), atol=1e-5, rtol=1e-7)

    def test_partials_random_densities(self):
        """
        Test partial derivatives at a reasonable design point.
        """
        self.T_set[0, 3] = 1.0
        self.q[2, 1] = 1e3

        p = om.Problem()
        p.model.add_subsystem("fem", FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q), promotes=["*"])
        p.setup()

        p.set_val("density", self.rand.random((self.nx - 1, self.ny - 1)).flatten())
        p.run_model()

        om_assert.assert_check_partials(p.check_partials(), atol=1e-5, rtol=1e-8)


class RectangularMesh(unittest.TestCase):
    """
    Test where there are a different number of nodes in the x and y directions.
    """

    def setUp(self):
        self.rand = np.random.default_rng(95)  # random generator

        self.nx = 3
        self.ny = 4

        self.T_set = np.full((self.nx, self.ny), np.inf)  # don't set any temperatures
        self.q = np.zeros((self.nx - 1, self.ny - 1))

        self.K_glob = np.array(
            [
                [722.22222222, -388.88888889, 0.0, 0.0, 27.77777778, -361.11111111, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [
                    -388.88888889,
                    1444.44444444,
                    -388.88888889,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [
                    0.0,
                    -388.88888889,
                    1444.44444444,
                    -388.88888889,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                ],
                [0.0, 0.0, -388.88888889, 722.22222222, 0.0, 0.0, -361.11111111, 27.77777778, 0.0, 0.0, 0.0, 0.0],
                [
                    27.77777778,
                    -361.11111111,
                    0.0,
                    0.0,
                    1444.44444444,
                    -777.77777778,
                    0.0,
                    0.0,
                    27.77777778,
                    -361.11111111,
                    0.0,
                    0.0,
                ],
                [
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    -777.77777778,
                    2888.88888889,
                    -777.77777778,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                ],
                [
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    -777.77777778,
                    2888.88888889,
                    -777.77777778,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                ],
                [
                    0.0,
                    0.0,
                    -361.11111111,
                    27.77777778,
                    0.0,
                    0.0,
                    -777.77777778,
                    1444.44444444,
                    0.0,
                    0.0,
                    -361.11111111,
                    27.77777778,
                ],
                [0.0, 0.0, 0.0, 0.0, 27.77777778, -361.11111111, 0.0, 0.0, 722.22222222, -388.88888889, 0.0, 0.0],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    -388.88888889,
                    1444.44444444,
                    -388.88888889,
                    0.0,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    -361.11111111,
                    55.55555556,
                    -361.11111111,
                    0.0,
                    -388.88888889,
                    1444.44444444,
                    -388.88888889,
                ],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -361.11111111, 27.77777778, 0.0, 0.0, -388.88888889, 722.22222222],
            ]
        )

    def test_stiffness(self):
        """
        Regression test for 9-element stiffness matrix.
        """
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)
        p.setup()

        np.testing.assert_allclose(self.K_glob, fem.K_glob.toarray())
        np.testing.assert_allclose(0.0, fem.F_glob)

    def test_stiffness_set_node(self):
        """
        Regression test for 9-element stiffness matrix.
        """
        self.T_set[1, 1] = 10.0
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)
        p.setup()

        K = self.K_glob
        K[self.ny + 1, :] = 0.0
        K[self.ny + 1, self.ny + 1] = 1.0

        F = np.zeros(self.nx * self.ny)
        F[self.ny + 1] = self.T_set[1, 1]

        np.testing.assert_allclose(self.K_glob, fem.K_glob.toarray())
        np.testing.assert_allclose(F, fem.F_glob.flatten())

    def test_partials(self):
        """
        Test partial derivatives at a reasonable design point.
        """
        self.T_set[0, 3] = 1.0
        self.q[1, 1] = 1e3

        p = om.Problem()
        p.model.add_subsystem("fem", FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q), promotes=["*"])
        p.setup()
        p.run_model()

        om_assert.assert_check_partials(p.check_partials(), atol=5e-6, rtol=1e-7)

    def test_partials_random_densities(self):
        """
        Test partial derivatives at a reasonable design point.
        """
        self.T_set[0, 3] = 1.0
        self.q[1, 1] = 1e3

        p = om.Problem()
        p.model.add_subsystem("fem", FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q), promotes=["*"])
        p.setup()

        p.set_val("density", self.rand.random((self.nx - 1, self.ny - 1)).flatten())
        p.run_model()

        om_assert.assert_check_partials(p.check_partials(), atol=5e-6, rtol=1e-8)


if __name__ == "__main__":
    unittest.main()
