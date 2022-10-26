import numpy as np
import scipy.sparse as sp
import openmdao.api as om


class FEM(om.ImplicitComponent):
    """
    Finite element method component.

    Options
    -------
    mesh_x : two-dimensional numpy array
        Structured mesh of x coordinates with a shape (num_x, num_y). Could
        be made, for example with (the indexing="ij" is important)
        ``mesh_x, mesh_y = np.meshgrid(x_linspace, y_linspace, indexing="ij")``
        By default from 0 to 1 with 21 nodes.
    mesh_y : two-dimensional numpy array
        Structured mesh of y coordinates with a shape (num_x, num_y). Could
        be made, for example with (the indexing="ij" is important)
        ``mesh_x, mesh_y = np.meshgrid(x_linspace, y_linspace, indexing="ij")``
        By default from 0 to 1 with 21 nodes.
    conductivity : float
        Material thermal conductivity, by default 1000
    
    Inputs
    ------
    density : float
        Densities of each element, which can remove/add elements to the problem
        by scaling their thermal conductivity. The shape corresponds to the flattened
        2D array of elements. By default 1 for every element.

    Outputs
    -------
    temp : float
        Nodal temperatures, flattened into a 1D array.
    """
    def initialize(self):
        x_linspace = np.linspace(0, 1.0, 21)
        y_linspace = np.linspace(0, 1.0, 21)
        mesh_x, mesh_y = np.meshgrid(x_linspace, y_linspace, indexing="ij")

        self.options.declare("mesh_x", default=mesh_x, types=np.ndarray, desc="2D mesh with x coordinates")
        self.options.declare("mesh_y", default=mesh_y, types=np.ndarray, desc="2D mesh with y coordinates")
        self.options.declare("conductivity", default=1e3, types=float, desc="Material thermal conductivity")

    def setup(self):
        self.nx = nx = self.options["mesh_x"].shape[0]
        self.ny = ny = self.options["mesh_x"].shape[1]

        self.add_input("density", val=1.0, shape=((nx - 1) * (ny - 1),), desc="Density of each element")
        self.add_output("temp", shape=(nx * ny,), desc="Nodal temperatures")

        # TODO: declare sparsity pattern
        self.declare_partials("temp", ["temp", "density"], rows=None, cols=None)

        # Compute matrices that are element-independent
        # Shape functions and their derivatives w.r.t. standard coords at quadrature points
        sq3 = np.sqrt(3)
        self.quad_pts = [
            (-1 / sq3, -1 / sq3),
            (-1 / sq3, 1 / sq3),
            (1 / sq3, -1 / sq3),
            (1 / sq3, 1 / sq3),
        ]
        self.dN_dxi = []
        self.N = []
        for xi, eta in self.quad_pts:
            self.dN_dxi.append(FEM._dN_dxi(xi, eta))
            self.N.append(FEM._N(xi, eta))

        # Stiffness matrix
        self.K_glob = np.zeros((nx * ny, nx * ny), dtype=float)
        self.density = np.ones((nx - 1) * (ny - 1))
        self._update_global_stiffness(self.density)

        # Set force vector to zero until user specifies nonzero heats
        self.F_glob = np.zeros((nx * ny, 1), dtype=float)
        self.q = np.zeros((nx - 1, ny - 1))  # temporary matrix to store heat
    
    def apply_nonlinear(self, inputs, outputs, residuals):
        self._update_global_stiffness(inputs["density"])
        residuals["temp"] = self.K_glob @ outputs["temp"] - self.F_glob.flatten()

    def linearize(self, inputs, outputs, jacobian):
        self._update_global_stiffness(inputs["density"])
        jacobian["temp", "temp"] = self.K_glob
        # TODO: derivative of temperature with respect to density
    
    def solve_nonlinear(self, inputs, outputs):
        self._update_global_stiffness(inputs["density"])
        outputs["temp"] = np.linalg.solve(self.K_glob, self.F_glob)

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
        for i in range(self.nx - 1):
            for j in range(self.ny - 1):
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

    def set_nodal_temps(self, T):
        """
        Specify nodal temperatures to hold constant.

        Parameters
        ----------
        T : numpy array (num x-coord x num y-coord)
            Array with specified nodal temperatures. The temperature of any node where the corresponding
            entry in T is finite (not infinite or NaN) is set to the value of that entry.
        """
        pass

    def get_mesh(self):
        """
        Get the mesh coordinates.

        Returns
        -------
        numpy array (num x-coord x num y-coord)
            Matrix of x coordinates
        numpy array (num x-coord x num y-coord)
            Matrix of y coordinates
        """
        return self.options["mesh_x"], self.options["mesh_y"]

    def _update_global_stiffness(self, density):
        """
        Set up the global stiffness matrix and stores it in self.K_glob (overwrites).

        Parameters
        ----------
        density : numpy array
            Densities of each element, which can remove/add elements to the problem
            by scaling their thermal conductivity. The shape corresponds to the flattened
            2D array of elements. By default 1 for every element.
        """
        dens_mat = np.reshape(density, (self.nx - 1, self.ny - 1))

        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        self.K_glob *= 0  # reset global stiffness matrix

        # Loop over each element and put its local stiffness matrix in the global one
        for i in range(self.nx - 1):
            for j in range(self.ny - 1):
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

                self.K_glob[np.ix_(idx_glob, idx_glob)] += dens_mat[i, j] * K_loc

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
        mesh_x = self.options["mesh_x"]
        mesh_y = self.options["mesh_y"]
        k = self.options["conductivity"]

        nodal_coord = np.array(
            [
                [mesh_x[i, j], mesh_y[i, j]],
                [mesh_x[i + 1, j], mesh_y[i + 1, j]],
                [mesh_x[i + 1, j + 1], mesh_y[i + 1, j + 1]],
                [mesh_x[i, j + 1], mesh_y[i, j + 1]],
            ]
        )

        stiff = np.zeros((4, 4), dtype=float)

        for dN in self.dN_dxi:
            # Compute the Jacobian matrix
            J = dN @ nodal_coord

            # Compute the B matrix
            B = np.linalg.solve(J, dN)

            stiff += k * (B.T @ B) * np.linalg.det(J)

        return stiff

    def _local_force(self, i, j, q):
        """
        Compute the local stiffness matrix for a single quadrilateral element.

        Parameters
        ----------
        i : int
            Element x index (not node index!)
        j : int
            Element y index (not node index!)
        q : float
            Heat produced in element

        Returns
        -------
        numpy array (4 x 1)
            Force vector for the element
        """
        mesh_x = self.options["mesh_x"]
        mesh_y = self.options["mesh_y"]

        nodal_coord = np.array(
            [
                [mesh_x[i, j], mesh_y[i, j]],
                [mesh_x[i + 1, j], mesh_y[i + 1, j]],
                [mesh_x[i + 1, j + 1], mesh_y[i + 1, j + 1]],
                [mesh_x[i, j + 1], mesh_y[i, j + 1]],
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
        return i * self.ny + j

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
