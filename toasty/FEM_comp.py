import numpy as np
import scipy.sparse as sp
import openmdao.api as om
from .utils import gen_mesh
from collections.abc import Iterable


class FEM(om.ImplicitComponent):
    """
    Finite element method component.

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

    Options
    -------
    num_x : int
        Number of mesh coordinates in the x direction.
    num_y : int
        Number of mesh coordinates in the y direction.
    x_lim : 2-element iterable
        Lower and upper limits of the x coordinates.
    y_lim : 2-element iterable
        Lower and upper limits of the y coordinates.
    T_set : numpy array (num x-coord x num y-coord)
        Array with specified nodal temperatures. The temperature of any node where the corresponding
        entry in T is finite (not infinite or NaN) is set to the value of that entry.
    q : numpy array (num x-coord - 1 x num y-coord - 1)
        Heat generated by each element.
    conductivity : float
        Material thermal conductivity, by default 1000
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")
        self.options.declare("x_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on x range")
        self.options.declare("y_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on y range")
        self.options.declare("T_set", types=np.ndarray, desc="Nodal temperatures to hold constant")
        self.options.declare("q", types=np.ndarray, desc="Heat generated by each element")
        self.options.declare("conductivity", default=1e3, types=float, desc="Material thermal conductivity")

    def setup(self):
        self.nx = nx = self.options["num_x"]
        self.ny = ny = self.options["num_y"]
        self.mesh_x, self.mesh_y = gen_mesh(nx, ny, self.options["x_lim"], self.options["y_lim"])

        self.add_input("density", val=1.0, shape=((nx - 1) * (ny - 1),), desc="Density of each element")
        self.add_output("temp", shape=(nx * ny,), desc="Nodal temperatures")

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
        self.sp_rows, self.sp_cols = self._get_sparsity_pattern()
        self.K_glob = None
        self.density = np.zeros((nx - 1) * (ny - 1))
        self._update_global_stiffness(np.ones((nx - 1) * (ny - 1)))

        # Set force vector to zero until user specifies nonzero heats
        self.F_glob = np.zeros((nx * ny, 1), dtype=float)
        self._update_global_force()

    def apply_nonlinear(self, inputs, outputs, residuals):
        print("apply_nonlinear")
        self._update_global_stiffness(inputs["density"])
        residuals["temp"] = self.K_glob @ outputs["temp"] - self.F_glob.flatten()

    def solve_nonlinear(self, inputs, outputs):
        print("solve_nonlinear")
        self._update_global_stiffness(inputs["density"])
        outputs["temp"] = sp.linalg.spsolve(self.K_glob, self.F_glob)

    def linearize(self, inputs, outputs, jacobian):
        print("linearize")
        self._update_global_stiffness(inputs["density"])
        self.pRpu = self.K_glob

        # Loop over each element and brute force the derivatives w.r.t. density
        self.pRpx = np.zeros((self.nx * self.ny, (self.nx - 1) * (self.ny - 1)))

        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        idx_elem = 0
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

                self.pRpx[idx_glob, idx_elem] += K_loc @ outputs["temp"][idx_glob]
                idx_elem += 1

        # Any temperatures that are specified get a one along the diagonal and zeros otherwise in K
        for i in range(self.nx):
            for j in range(self.ny):
                if np.isfinite(self.options["T_set"][i, j]):
                    idx_glob = self._flattened_node_ij(i, j)
                    self.pRpx[idx_glob, :] = 0.0

    def apply_linear(self, inputs, outputs, d_inputs, d_outputs, d_residuals, mode):
        if "temp" not in d_residuals:
            return

        if mode == "fwd":
            print("apply_linear fwd")
            if "temp" in d_outputs:
                d_residuals["temp"] = self.pRpu @ d_outputs["temp"]
            if "density" in d_inputs:
                d_residuals["temp"] = self.pRpx @ d_inputs["density"]
        elif mode == "rev":
            print("apply_linear rev")
            if "temp" in d_outputs:
                d_outputs["temp"] = self.pRpu.T @ d_residuals["temp"]
            if "density" in d_inputs:
                d_inputs["density"] = self.pRpx.T @ d_residuals["temp"]

    def solve_linear(self, d_outputs, d_residuals, mode):
        if mode == "fwd":
            print("solve_linear fwd")
            d_outputs["temp"] = sp.linalg.spsolve(self.pRpu, d_residuals["temp"])
        elif mode == "rev":
            print("solve_linear rev")
            d_residuals["temp"] = sp.linalg.spsolve(self.pRpu, d_outputs["temp"])

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
        return self.mesh_x, self.mesh_y

    def _update_global_stiffness(self, density, partial=False):
        """
        Set up the global stiffness matrix and store it in self.K_glob (overwrites).

        Parameters
        ----------
        density : numpy array
            Densities of each element, which can remove/add elements to the problem
            by scaling their thermal conductivity. The shape corresponds to the flattened
            2D array of elements. By default 1 for every element.
        partial : bool, optional
            If using this function to compute partial derivatives, setting this to True
            will zero out rows where temperatures are specified.
        """
        if not np.any(self.density != density):
            return

        self.density[:] = density[:]

        nx, ny = (self.nx, self.ny)
        dens_mat = np.reshape(density, (nx - 1, ny - 1))

        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        # Initialize sparse matrix
        # TODO: don't be lazy; create vals and then the matrix instead of indexing in
        #   (will have to uncomment num_nonzeros T_set line and if statement in for loop in _get_sparsity_pattern)
        rows = self.sp_rows
        cols = self.sp_cols
        vals = np.zeros_like(rows, dtype=float)
        self.K_glob = sp.csr_matrix((vals, (rows, cols)), shape=(nx * ny, nx * ny))

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

        # Any temperatures that are specified get a one along the diagonal and zeros otherwise in K
        for i in range(self.nx):
            for j in range(self.ny):
                if np.isfinite(self.options["T_set"][i, j]):
                    idx_glob = self._flattened_node_ij(i, j)
                    self.K_glob[idx_glob, cols[rows == idx_glob]] = 0.0
                    self.K_glob[idx_glob, idx_glob] = 1.0 * (not partial)

    def _update_global_force(self):
        """
        Set up the global force vector and store it in self.F_glob (overwrites).
        """
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

                self.F_glob[idx_glob] += self._local_force(i, j, self.options["q"][i, j])

        # Any temperatures that are specified get the specified temperature in the force vector
        for i in range(self.nx):
            for j in range(self.ny):
                if np.isfinite(self.options["T_set"][i, j]):
                    self.F_glob[self._flattened_node_ij(i, j)] = self.options["T_set"][i, j]

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
        mesh_x = self.mesh_x
        mesh_y = self.mesh_y
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
        mesh_x = self.mesh_x
        mesh_y = self.mesh_y

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

    def _get_sparsity_pattern(self):
        """
        Returns
        -------
        numpy array
            Row indices of sparsity pattern
        numpy array
            Column indices of sparsity pattern
        """
        T_is_set = np.isfinite(self.options["T_set"])
        nx = self.nx
        ny = self.ny

        # Figure out the number of nonzero elements in the sparse matrix
        num_corners = 4
        num_middle_edges = 2 * (nx - 2) + 2 * (ny - 2)
        num_interiors = (nx - 2) * (ny - 2)

        num_T_set_corners = 0
        num_T_set_middle_edges = 0
        num_T_set_interiors = 0
        for i in range(nx):
            for j in range(ny):
                if T_is_set[i, j]:
                    # Corners
                    if (i == 0 or i == nx - 1) and (j == 0 or j == ny - 1):
                        num_T_set_corners += 1

                    # Middle edges
                    elif i == 0 or i == nx - 1 or j == 0 or j == ny - 1:
                        num_T_set_middle_edges += 1

                    else:
                        num_T_set_interiors += 1

        num_nonzeros = (
            4 * num_corners + 6 * num_middle_edges + 9 * num_interiors
        )  # - 3 * num_T_set_corners - 5 * num_T_set_middle_edges - 8 * num_T_set_interiors

        # Initialize the arrays to store nonzero row and column indices
        rows = np.zeros(num_nonzeros, dtype=int)
        cols = np.zeros(num_nonzeros, dtype=int)

        idx_nonzero = 0
        for i in range(nx):
            for j in range(ny):
                idx_glob = self._flattened_node_ij(i, j)

                # # If T of the current node is set, it only depends on itself (nonzero along diagonal)
                # if T_is_set[i, j]:
                #     rows[idx_nonzero] = idx_glob
                #     cols[idx_nonzero] = idx_glob
                #     idx_nonzero += 1
                #     continue

                # Influence of nodes to the left
                if i > 0:
                    # Down left
                    if j > 0:
                        rows[idx_nonzero] = idx_glob
                        cols[idx_nonzero] = idx_glob - ny - 1
                        idx_nonzero += 1

                    # Directly left
                    rows[idx_nonzero] = idx_glob
                    cols[idx_nonzero] = idx_glob - ny
                    idx_nonzero += 1

                    # Up left
                    if j < ny - 1:
                        rows[idx_nonzero] = idx_glob
                        cols[idx_nonzero] = idx_glob - ny + 1
                        idx_nonzero += 1

                # Down
                if j > 0:
                    rows[idx_nonzero] = idx_glob
                    cols[idx_nonzero] = idx_glob - 1
                    idx_nonzero += 1

                # Itself
                rows[idx_nonzero] = idx_glob
                cols[idx_nonzero] = idx_glob
                idx_nonzero += 1

                # Up
                if j < ny - 1:
                    rows[idx_nonzero] = idx_glob
                    cols[idx_nonzero] = idx_glob + 1
                    idx_nonzero += 1

                # Influence of nodes to the right
                if i < nx - 1:
                    # Down right
                    if j > 0:
                        rows[idx_nonzero] = idx_glob
                        cols[idx_nonzero] = idx_glob + ny - 1
                        idx_nonzero += 1

                    # Directly right
                    rows[idx_nonzero] = idx_glob
                    cols[idx_nonzero] = idx_glob + ny
                    idx_nonzero += 1

                    # Up right
                    if j < ny - 1:
                        rows[idx_nonzero] = idx_glob
                        cols[idx_nonzero] = idx_glob + ny + 1
                        idx_nonzero += 1

        return rows, cols

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
            1
            / 4
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
            1
            / 4
            * np.array(
                [
                    [eta - 1, -eta + 1, eta + 1, -eta - 1],
                    [xi - 1, -xi - 1, xi + 1, -xi + 1],
                ]
            )
        )
