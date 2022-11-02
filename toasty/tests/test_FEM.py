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

    def test_sparsity(self):
        """
        One element global stiffness is DENSE.
        """
        p = om.Problem()
        fem = p.model = FEM(num_x=self.nx, num_y=self.ny, T_set=self.T_set, q=self.q)
        p.setup()

        idx_i = np.repeat(np.arange(self.nx * self.ny), 4)
        idx_j = np.repeat(np.arange(self.nx * self.ny).reshape(4, 1), 4, axis=1).T.flatten()

        np.testing.assert_allclose(idx_i, fem.sp_rows)
        np.testing.assert_allclose(idx_j, fem.sp_cols)

    # TODO: test that when temps are set the sparsity accounts for the changes


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


if __name__ == "__main__":
    unittest.main()
