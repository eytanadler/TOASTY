"""
A script containing the first attempt at a heat conduction FEM code
"""

import numpy as np
from math import sqrt

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
        self.x_linspace = np.linspace(0, 1, num_x)
        self.y_linspace = np.linspace(0, 1, num_y)
        self.mesh_x, self.mesh_y = np.meshgrid(self.x_linspace, self.y_linspace)
        self.num_x = num_x
        self.num_y = num_y

        # Other input data
        self.k = k  # thermal conductivity

        # Compute matrices that are element-independent
        # Derivative of shape functions w.r.t. standard coords at quadrature points
        self.quad_pts = [
            (-1/sqrt(3), -1/sqrt(3)),
            (-1/sqrt(3), 1/sqrt(3)),
            (1/sqrt(3), -1/sqrt(3)),
            (1/sqrt(3), 1/sqrt(3)),
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
        # Set the temperature of the first node to 100
        T_set = 0.0
        K = self.K_glob.copy()
        K[:, 0] = 0
        K[0, :] = 0
        K[0, 0] = 1.0
        F = self.F_glob.copy()
        F[0] = T_set
        self.T = np.linalg.solve(K, F).reshape(self.mesh_x.shape)

    def set_element_heat(self, q):
        """
        Set the heat produced within each element and recompute
        the "force" vector.

        Parameters
        ----------
        q : numpy array (num x-coord - 1 x num y-coord - 1)
        """
        self.q[:, :] = q[:, :]
        self.F_glob *= 0  # reset global stiffness matrix

        # Loop over each element and put its local stiffness matrix in the global one
        for i in range(self.num_y - 1):
            for j in range(self.num_x - 1):
                # 2D indices in the mesh of the nodes surrounding the current element
                idx = np.array([
                    [i, j],
                    [i + 1, j],
                    [i + 1, j + 1],
                    [i, j + 1],
                ])

                # Convert the 2D indices to flattened 1D to determine where in the
                # unknown vector (and global stiffness matrix) they'd be
                idx_glob = self._flattened_node_ij(idx[:, 0], idx[:, 1])

                self.F_glob[idx_glob] += self._local_force(i, j, q[i, j])

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
        for i in range(self.num_y - 1):
            for j in range(self.num_x - 1):
                # 2D indices in the mesh of the nodes surrounding the current element
                idx = np.array([
                    [i, j],
                    [i + 1, j],
                    [i + 1, j + 1],
                    [i, j + 1],
                ])

                # Convert the 2D indices to flattened 1D to determine where in the
                # unknown vector (and global stiffness matrix) they'd be
                idx_glob = self._flattened_node_ij(idx[:, 0], idx[:, 1])

                self.K_glob[np.ix_(idx_glob, idx_glob)] += K_loc

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
        nodal_idx = np.array([
            [self.mesh_x[i, j], self.mesh_y[i, j]],
            [self.mesh_x[i + 1, j], self.mesh_y[i + 1, j]],
            [self.mesh_x[i + 1, j + 1], self.mesh_y[i + 1, j + 1]],
            [self.mesh_x[i, j + 1], self.mesh_y[i, j + 1]],
        ])

        stiff = np.zeros((4, 4), dtype=float)

        for dN in self.dN_dxi:
            # Compute the Jacobian matrix
            J = dN @ nodal_idx

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
        nodal_idx = np.array([
            [self.mesh_x[i, j], self.mesh_y[i, j]],
            [self.mesh_x[i + 1, j], self.mesh_y[i + 1, j]],
            [self.mesh_x[i + 1, j + 1], self.mesh_y[i + 1, j + 1]],
            [self.mesh_x[i, j + 1], self.mesh_y[i, j + 1]],
        ])

        force = np.zeros((4, 1), dtype=float)

        for N, dN in zip(self.N, self.dN_dxi):
            # Compute the Jacobian matrix
            J = dN @ nodal_idx

            force += q * N.T * np.linalg.det(J)

        return force

    def _flattened_node_ij(self, i, j):
        """
        Given the i and j index of a node, compute the single index for it
        in the flattened vectors (for example, in the unknown temperature vector).
        """
        return i * self.num_x + j

    @staticmethod
    def _N(xi, eta):
        """
        Returns the following matrix, evaluated at the given xi and eta:

        [N1, N2, N3, N4]
        """
        return 1 / 4 * np.array([[
            (xi - 1) * (eta - 1), (xi + 1) * (eta - 1), (xi + 1) * (eta + 1), (xi - 1) * (eta + 1)
        ]])

    @staticmethod
    def _dN_dxi(xi, eta):
        """
        Returns the following matrix, evaluated at the given xi and eta:

         -                                      -
        | dN1/dxi,  dN2/dxi,  dN3/dxi,  dN4/dxi  |
        | dN1/deta, dN2/deta, dN3/deta, dN4/deta |
         -                                      -
        """
        return 1 / 4 * np.array([
            [eta - 1, -eta + 1, eta + 1, -eta - 1],
            [xi - 1,  -xi - 1,  xi + 1,  -xi + 1],
        ])

if __name__=="__main__":
    import matplotlib.pyplot as plt

    nx = 11
    ny = 11
    x = FEM(num_x=nx, num_y=ny)

    for i in range(3, 10, 1):
        q = np.zeros((nx - 1, ny - 1), dtype=float)
        q[nx // 2, ny // 2] = 10**i
        # q[-1, :] = -10**i
        x.set_element_heat(q)
        x.solve()
        print(x.T)

        fig, ax = plt.subplots()
        c = ax.contourf(x.mesh_x, x.mesh_y, x.T, 100)
        fig.colorbar(c)
        ax.set_aspect("equal")
        plt.show()
        plt.close(fig)
