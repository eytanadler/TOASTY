"""
A script containing the first attempt at a heat conduction FEM code
"""

import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize, Bounds, NonlinearConstraint
from math import sqrt
import matplotlib.pyplot as plt
import os


class FEM:
    def __init__(self, num_x=11, num_y=11, k=400.0):
        """
        Initialize the finite element method model.

        Parameters
        ----------
        num_x : int
            Number of x coordinates, by default 11
        num_y : int
            Number of y coordinates, by default 11
        k : float
            Material thermal conductivity, by default 1
        """
        # Create the mesh; ordering with index [0, 0] at the minimum x and y values
        self.x_linspace = np.linspace(0, 1.0, num_x)
        self.y_linspace = np.linspace(0, 1.0, num_y)
        self.mesh_x, self.mesh_y = np.meshgrid(self.x_linspace, self.y_linspace, indexing="ij")
        self.num_x = num_x
        self.num_y = num_y

        # Other input data
        self.k = k  # thermal conductivity

        # Density of each element
        self.density = np.ones((self.num_x - 1, self.num_y - 1))

        # Compute matrices that are element-independent
        # Derivative of shape functions w.r.t. standard coords at quadrature points
        self.quad_pts = [
            (-1 / sqrt(3), -1 / sqrt(3)),
            (-1 / sqrt(3), 1 / sqrt(3)),
            (1 / sqrt(3), -1 / sqrt(3)),
            (1 / sqrt(3), 1 / sqrt(3)),
        ]
        self.dN_dxi = []
        self.N = []
        for xi, eta in self.quad_pts:
            self.dN_dxi.append(FEM._dN_dxi(xi, eta))
            self.N.append(FEM._N(xi, eta))

        # Matrices for linear system
        n_tot = self.num_x * self.num_y
        self.K_glob = np.zeros((n_tot, n_tot), dtype=float)
        self._global_stiffness()
        self.F_glob = np.zeros((n_tot, 1), dtype=float)  # this depends on heats specified later
        self.T = None  # this is unknown until linear system is solved

        # Temporary matrix to store heat
        self.q = np.zeros((self.num_x - 1, self.num_y - 1))

    def solve(self):
        """
        Solve the linear system to compute temperatures.
        """
        # Bottom, left, and right side BCs have temp of 293 K
        T_set = 293.0
        K = self.K_glob.copy()
        bot = self._flattened_node_ij(np.arange(self.num_x), 0)
        left = self._flattened_node_ij(0, np.arange(self.num_y))
        right = self._flattened_node_ij(self.num_x - 1, np.arange(self.num_y))
        K[bot, :] = 0
        K[left, :] = 0
        K[right, :] = 0
        K[bot, bot] = 1.0
        K[left, left] = 1.0
        K[right, right] = 1.0
        # for i in range(K.shape[0]):
        #     for j in range(K.shape[1]):
        #         if K[i, j] == 0:
        #             print("-", end="")
        #         else:
        #             print("X", end="")
        #     print("")
        K = sp.csr_array(K)
        F = self.F_glob.copy()
        F[bot] = T_set
        F[left] = T_set
        F[right] = T_set

        self.T = sp.linalg.spsolve(K, F).reshape(self.mesh_x.shape)
        # self.T = np.linalg.solve(K, F).reshape(self.mesh_x.shape)

    def set_element_heat(self, q):
        """
        Set the heat produced within each element and recompute
        the "force" vector.

        Parameters
        ----------
        q : numpy array (num x-coord - 1 x num y-coord - 1)
            Heat generated by each element
        """
        self.q[:, :] = q[:, :]
        self.F_glob *= 0  # reset global stiffness matrix

        # Loop over each element and put its local stiffness matrix in the global one
        for i in range(self.num_x - 1):
            for j in range(self.num_y - 1):
                # 2D indices in the mesh of the nodes surrounding the current element
                idx = np.array(
                    [
                        [i, j],
                        [i + 1, j],
                        [i + 1, j + 1],
                        [i, j + 1],
                    ]
                )

                # Convert the 2D indices to flattened 1D to determine where in the
                # unknown vector (and global stiffness matrix) they'd be
                idx_glob = self._flattened_node_ij(idx[:, 0], idx[:, 1])

                self.F_glob[idx_glob] += self._local_force(i, j, self.q[i, j])

    def set_density(self, density):
        """
        Set the density of each element.

        Parameters
        ----------
        density : numpy array (num x-coord - 1 x num y-coord - 1)
            Density of each element (multiplier on conductivity)
        """
        self.density[:, :] = density[:, :]
        self._global_stiffness()

    def _global_stiffness(self):
        """
        Set up the global stiffness matrix and stores it in self.K_glob (overwrites).
        """
        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        self.K_glob *= 0  # reset global stiffness matrix

        # Loop over each element and put its local stiffness matrix in the global one
        for i in range(self.num_x - 1):
            for j in range(self.num_y - 1):
                # 2D indices in the mesh of the nodes surrounding the current element
                idx = np.array(
                    [
                        [i, j],
                        [i + 1, j],
                        [i + 1, j + 1],
                        [i, j + 1],
                    ]
                )

                # Convert the 2D indices to flattened 1D to determine where in the
                # unknown vector (and global stiffness matrix) they'd be
                idx_glob = self._flattened_node_ij(idx[:, 0], idx[:, 1])

                self.K_glob[np.ix_(idx_glob, idx_glob)] += self.density[i, j] * K_loc

    def _local_stiffness(self, i, j):
        """
        Compute the local stiffness matrix for a single quadrilateral element.

        Parameters
        ----------
        i : int
            Element x index (not coordinate index!)
        j : int
            Element y index (not coordinate index!)

        Returns
        -------
        numpy array (4 x 4)
            Stiffness matrix for the element
        """
        nodal_coord = np.array(
            [
                [self.mesh_x[i, j], self.mesh_y[i, j]],
                [self.mesh_x[i + 1, j], self.mesh_y[i + 1, j]],
                [self.mesh_x[i + 1, j + 1], self.mesh_y[i + 1, j + 1]],
                [self.mesh_x[i, j + 1], self.mesh_y[i, j + 1]],
            ]
        )

        stiff = np.zeros((4, 4), dtype=float)

        for dN in self.dN_dxi:
            # Compute the Jacobian matrix
            J = dN @ nodal_coord

            # Compute the B matrix
            B = np.linalg.solve(J, dN)

            stiff += self.k * (B.T @ B) * np.linalg.det(J)

        return stiff

    def _local_force(self, i, j, q):
        """
        Compute the local stiffness matrix for a single quadrilateral element.

        Parameters
        ----------
        i : int
            Element x index (not coordinate index!)
        j : int
            Element y index (not coordinate index!)
        q : float
            Heat produced in element

        Returns
        -------
        numpy array (4 x 1)
            Force vector for the element
        """
        nodal_coord = np.array(
            [
                [self.mesh_x[i, j], self.mesh_y[i, j]],
                [self.mesh_x[i + 1, j], self.mesh_y[i + 1, j]],
                [self.mesh_x[i + 1, j + 1], self.mesh_y[i + 1, j + 1]],
                [self.mesh_x[i, j + 1], self.mesh_y[i, j + 1]],
            ]
        )

        force = np.zeros((4, 1), dtype=float)

        for N, dN in zip(self.N, self.dN_dxi):
            # Compute the Jacobian matrix
            J = dN @ nodal_coord

            force += q * N.T * np.linalg.det(J)

        return force

    def _flattened_node_ij(self, i, j):
        """
        Given the i and j index of a node, compute the single index for it
        in the flattened vectors (for example, in the unknown temperature vector).
        """
        return i * self.num_y + j

    @staticmethod
    def _N(xi, eta):
        """
        Returns the following matrix, evaluated at the given xi and eta:

        [N1, N2, N3, N4]
        """
        return (
            1 / 4
            * np.array([[(xi - 1) * (eta - 1), -(xi + 1) * (eta - 1), (xi + 1) * (eta + 1), -(xi - 1) * (eta + 1)]])
        )

    @staticmethod
    def _dN_dxi(xi, eta):
        """
        Returns the following matrix, evaluated at the given xi and eta:

         -                                      -
        | dN1/dxi,  dN2/dxi,  dN3/dxi,  dN4/dxi  |
        | dN1/deta, dN2/deta, dN3/deta, dN4/deta |
         -                                      -
        """
        return (
            1 / 4
            * np.array(
                [
                    [eta - 1, -eta + 1, eta + 1, -eta - 1],
                    [xi - 1, -xi - 1, xi + 1, -xi + 1],
                ]
            )
        )


def opt():
    def mass(dv):
        print(f"Mass = {np.sum(dv)}")
        return np.sum(dv)

    def max_T(dv, rho=20.0):
        nx = 21
        ny = 21

        x = FEM(num_x=nx, num_y=ny, k=0.13)

        q = np.zeros((nx - 1, ny - 1), dtype=float)
        q[nx // 2, ny - 2] = 20.0 * nx * ny
        # q[-2, nx // 3 : 2 * nx // 3] = -2e5
        x.set_element_heat(q)

        x.set_density(dv.reshape((nx - 1, ny - 1)))

        x.solve()
        print(f"Max T = {np.max(x.T)}")
        return np.max(x.T)

    def plot_callback(dv):
        nx = 21
        ny = 21

        x = FEM(num_x=nx, num_y=ny, k=0.13)

        q = np.zeros((nx - 1, ny - 1), dtype=float)
        q[nx // 2, ny - 2] = 20.0 * nx * ny
        # q[-2, nx // 3 : 2 * nx // 3] = -10.0 * nx * ny
        x.set_element_heat(q)

        x.set_density(dv.reshape((nx - 1, ny - 1)))

        x.solve()

        fig, axs = plt.subplots(2, 1, figsize=(5, 8))
        c = axs[0].contourf(x.mesh_x, x.mesh_y, x.T, 100, cmap="coolwarm")
        fig.colorbar(c, ax=axs[0])
        axs[0].set_aspect("equal")

        c = axs[1].pcolorfast(x.mesh_x, x.mesh_y, x.density, cmap="Blues", vmin=0.0, vmax=1.0)
        fig.colorbar(c, ax=axs[1])
        axs[1].set_aspect("equal")

        cur_dir = os.path.dirname(__file__)
        fig.savefig(os.path.join(cur_dir, "test.pdf"))

    nx = 21
    ny = 21
    minimize(
        mass,
        0.9 * np.ones((nx - 1) * (ny - 1)),
        method="SLSQP",
        jac="2-point",
        bounds=Bounds(1e-4, 1 - 1e-4),
        constraints=[NonlinearConstraint(max_T, -np.inf, 480)],
        callback=plot_callback,
        options={"disp": True},
    )


if __name__ == "__main__":
    optimize = True

    if optimize:
        opt()
    else:
        nx = 101
        ny = 101
        x = FEM(num_x=nx, num_y=ny, k=0.13)

        q = np.zeros((nx - 1, ny - 1), dtype=float)
        q[nx // 2, ny - 2] = 20.0 * nx * ny
        q[-2, nx // 3 : 2 * nx // 3] = -2e5
        x.set_element_heat(q)
        density = np.ones((nx - 1, ny - 1))
        density[np.ix_(np.arange(nx // 3, 2 * nx // 3), np.arange(ny // 6, 5 * ny // 6))] = 0.00001
        density[np.ix_(np.arange(0, nx // 3), np.arange(ny // 6, 5 * ny // 6))] = 0.2
        x.set_density(density)
        x.solve()

        fig, axs = plt.subplots(2, 1, figsize=(5, 8))
        c = axs[0].contourf(x.mesh_x, x.mesh_y, x.T, 100, cmap="coolwarm")
        fig.colorbar(c, ax=axs[0])
        axs[0].set_aspect("equal")

        c = axs[1].pcolorfast(x.mesh_x, x.mesh_y, x.density, cmap="Blues", vmin=0.0, vmax=1.0)
        fig.colorbar(c, ax=axs[1])
        axs[1].set_aspect("equal")

        cur_dir = os.path.dirname(__file__)
        fig.savefig(os.path.join(cur_dir, "test.pdf"))