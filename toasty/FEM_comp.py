import numpy as np
import scipy.sparse as sp
import openmdao.api as om
from .utils import gen_mesh
from collections.abc import Iterable
from time import time
import matplotlib.pyplot as plt
import matplotlib
import os

try:
    from pypardiso import spsolve
except ImportError:
    print("Install pypardiso for faster linear solves, falling back to scipy")
    from scipy.sparse.linalg import spsolve


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
    plot : list
        List with the output folder and frequency at which to plot, for example ["~/Documents/plot", 10],
        by default will not plot. Make sure the directory is absolute, not relative!
    airport_data : dict
        If plot is set to something, pass in the dictionary returned by load_airport
        to plot airport buildings and the runways.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")
        self.options.declare("x_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on x range")
        self.options.declare("y_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on y range")
        self.options.declare("T_set", types=np.ndarray, desc="Nodal temperatures to hold constant")
        self.options.declare("q", types=np.ndarray, desc="Heat generated by each element")
        self.options.declare("conductivity", default=1e3, types=float, desc="Material thermal conductivity")
        self.options.declare("plot", default=None, desc="List with the output folder and frequency at which to plot")
        self.options.declare("airport_data", default=None, desc="Airport data to make the plot cool")

    def setup(self):
        from time import time

        t_start = time()
        print("Setting up FEM...", end="")
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
        self.density = np.zeros((nx - 1) * (ny - 1))
        self._preprocess_global_stiffness()
        self._update_global_stiffness(np.ones((nx - 1) * (ny - 1)))

        # Also set up the necessary info to efficiently get partial(R)/partial(x)
        self._preprocess_pRpx()

        # Set force vector to zero until user specifies nonzero heats
        self.F_glob = np.zeros((nx * ny,), dtype=float)
        self._update_global_force()

        print(f"done in {time() - t_start} sec")

        self.plot_counter = -1
        self.plot_result = False
        if self.options["plot"] is not None:
            self.plot_result = True
            self.plot_dir = self.options["plot"][0]
            self.plot_freq = self.options["plot"][1]
            self.cmap_white = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#ffffffff", "#ffffff00"])
            self.cmap_runway = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#00000000", "#00000055"])
            self.cmap_building = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#00000000", "#000000ff"])

    def apply_nonlinear(self, inputs, outputs, residuals):
        print("apply_nonlinear...", end="")
        t_start = time()
        self._update_global_stiffness(inputs["density"])
        residuals["temp"] = self.K_glob @ outputs["temp"] - self.F_glob.flatten()
        print(f"done in {time() - t_start} sec")

    def solve_nonlinear(self, inputs, outputs):
        print("solve_nonlinear...", end="")
        t_start = time()
        self._update_global_stiffness(inputs["density"])
        outputs["temp"] = spsolve(self.K_glob, self.F_glob)
        print(f"done in {time() - t_start} sec")

        if self.plot_result:
            self.plot_counter += 1

            if self.plot_counter % self.plot_freq != 0:
                return

            T = outputs["temp"].reshape(self.nx, self.ny)
            density = inputs["density"].reshape(self.nx - 1, self.ny - 1)

            if self.options["airport_data"] is None:
                fig, axs = plt.subplots(2, 1, figsize=(8.5, 8))
                c = axs[0].contourf(self.mesh_x, self.mesh_y, T, 100, cmap="coolwarm")
                axs[0].pcolorfast(
                    self.mesh_x, self.mesh_y, density, cmap=self.cmap_white, vmin=0.0, vmax=1.0, zorder=10
                )
                cbar = fig.colorbar(c, ax=axs[0])
                cbar.set_label("Temperature (K?)")
                axs[0].set_aspect("equal")

                c = axs[1].pcolorfast(self.mesh_x, self.mesh_y, density, cmap="Blues", vmin=0.0, vmax=1.0)
                cbar = fig.colorbar(c, ax=axs[1])
                cbar.set_label("Density")
                axs[1].set_aspect("equal")
            else:
                xlim, ylim = (self.options["x_lim"], self.options["y_lim"])
                apt_data = self.options["airport_data"]
                fig, ax = plt.subplots(figsize=((xlim[1] - xlim[0]) * 10, (ylim[1] - ylim[0]) * 10))
                c = ax.contourf(self.mesh_x, self.mesh_y, T, 100, cmap="coolwarm", zorder=0)
                ax.pcolorfast(self.mesh_x, self.mesh_y, density, cmap=self.cmap_white, vmin=0.0, vmax=1.0, zorder=1)
                ax.pcolorfast(
                    self.mesh_x, self.mesh_y, apt_data["runways"], cmap=self.cmap_run, vmin=0.0, vmax=1.0, zorder=2
                )
                ax.pcolorfast(
                    self.mesh_x, self.mesh_y, apt_data["buildings"], cmap=self.cmap_build, vmin=0.0, vmax=1.0, zorder=2
                )
                cbar = fig.colorbar(c, ax=ax, fraction=0.02, pad=0.05)
                cbar.set_label("Temperature (K?)")
                ax.set_aspect("equal")
                ax.set_axis_off()

            fig.savefig(os.path.join(self.plot_dir, f"opt_{self.plot_counter:05d}.png"), dpi=300)
            plt.close(fig)

    def linearize(self, inputs, outputs, _):
        print("linearize...", end="")
        t_start = time()

        # Matrix for partial(residual)/partial(temperature)
        self._update_global_stiffness(inputs["density"])
        self.pRpu = self.K_glob

        # Matrix for partial(residual)/partial(density)
        pRpx_temp_mat = sp.csr_matrix((outputs["temp"][self.pRpx_temp_idx], (self.pRpx_temp_rows, self.pRpx_temp_cols)))
        self.pRpx = self.pRpx_coeff_mat.dot(pRpx_temp_mat)

        print(f"done in {time() - t_start} sec")

    def apply_linear(self, inputs, outputs, d_inputs, d_outputs, d_residuals, mode):
        if "temp" not in d_residuals:
            return

        if mode == "fwd":
            print("apply_linear fwd...", end="")
            t_start = time()
            if "temp" in d_outputs:
                d_residuals["temp"] += self.pRpu @ d_outputs["temp"]
            if "density" in d_inputs:
                d_residuals["temp"] += self.pRpx @ d_inputs["density"]
        elif mode == "rev":
            print("apply_linear rev...", end="")
            t_start = time()
            if "temp" in d_outputs:
                d_outputs["temp"] += self.pRpu.T @ d_residuals["temp"]
            if "density" in d_inputs:
                d_inputs["density"] += self.pRpx.T @ d_residuals["temp"]

        print(f"done in {time() - t_start} sec")

    def solve_linear(self, d_outputs, d_residuals, mode):
        if mode == "fwd":
            print("solve_linear fwd...", end="")
            t_start = time()
            d_outputs["temp"] = spsolve(self.pRpu, d_residuals["temp"])
        elif mode == "rev":
            print("solve_linear rev...", end="")
            t_start = time()
            d_residuals["temp"] = spsolve(self.pRpu, d_outputs["temp"])

        print(f"done in {time() - t_start} sec")

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

    def _update_global_stiffness(self, density):
        """
        Set up the global stiffness matrix and store it in self.K_glob (overwrites).

        Parameters
        ----------
        density : numpy array
            Densities of each element, which can remove/add elements to the problem
            by scaling their thermal conductivity. The shape corresponds to the flattened
            2D array of elements. By default 1 for every element.
        """
        # If density hasn't changed, no need to update it
        if not np.any(self.density != density):
            return
        self.density[:] = density[:]

        vals = self.K_vals.copy()
        vals[self.idx_val_map] *= density[self.idx_density_map]

        self.K_glob = sp.coo_matrix((vals, (self.K_rows, self.K_cols))).tocsr()

    def _update_global_force(self):
        """
        Set up the global force vector and store it in self.F_glob (overwrites).
        """
        self.F_glob *= 0  # reset global stiffness matrix

        # Loop over each element and put its local stiffness matrix in the global one
        nonzero_q_idx = np.argwhere(self.options["q"] != 0)
        for i, j in nonzero_q_idx:
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
        finite_T_set_idx = np.argwhere(np.isfinite(self.options["T_set"]))
        for i, j in finite_T_set_idx:
            self.F_glob[self._flattened_node_ij(i, j)] = self.options["T_set"][i, j]

    def _preprocess_global_stiffness(self):
        """
        By splitting up the global stiffness matrix into four components where there is no
        overlap of elements at any spot in the matrix, we can avoid doing the global stiffness
        matrix assembly every time the densities change. Instead, we simple have to multiply the
        correct spots in the four components by the associated densities and use the resulting
        values to initialize a sparse matrix.

        This method creates those four components of the stiffness matrix, along with the associated
        rows and columns of the values. It also creates the index map that defines which densities
        to multiply each element the four components by. Because it depends only on the mesh and
        temperature boundary conditions (which are defined once at the beginning), this method
        must run only once at the start of the evaluation/optimization.

        Creating the stifness matrix will look something like this:
            vals = self.K_vals.copy()
            vals[self.idx_val_map] *= density[self.idx_density_map]
            self.K_glob = sp.coo_matrix((vals, (self.K_rows, self.K_cols))).tocsr()

        The member variables this function adds are:
            K_rows
            K_cols
            K_vals
            idx_density_map
            idx_val_map
        """
        nx, ny = (self.nx, self.ny)
        n_elem = (nx - 1) * (ny - 1)
        nodes_per_elem = 4

        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        # Global indices of the corner nodes of each element
        i, j = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
        i = i.flatten()
        j = j.flatten()
        node_glob_idx = np.array(
            [
                i * ny + j,  # lower left
                (i + 1) * ny + j,  # lower right
                (i + 1) * ny + j + 1,  # upper right
                i * ny + j + 1,  # upper left
            ]
        )

        self.K_rows = []
        self.K_cols = []
        self.K_vals = []
        self.idx_density_map = []
        self.idx_val_map = []
        for i_corner, corner_idx in enumerate(node_glob_idx):
            self.K_rows.append(np.repeat(corner_idx, nodes_per_elem))
            self.K_cols.append(node_glob_idx.T.flatten())
            self.K_vals.append(np.tile(K_loc[i_corner, :], n_elem))
            self.idx_density_map.append(np.repeat(np.arange(n_elem), nodes_per_elem))
            self.idx_val_map.append(np.arange(n_elem * nodes_per_elem) + n_elem * nodes_per_elem * i_corner)

        # Account for the specified nodal temperatures.
        # Start by setting the stiffness matrix values to have a one
        # along the diagonal where the temperatures are specified.
        T_is_set = np.isfinite(self.options["T_set"]).flatten()
        diag_mask = np.zeros(n_elem * 4)
        for i_corner in range(nodes_per_elem):
            diag_mask *= 0
            diag_mask[i_corner::nodes_per_elem] = 1
            T_set_mask = np.repeat(T_is_set[node_glob_idx[i_corner]], nodes_per_elem)
            self.K_vals[i_corner][T_set_mask] = 0.0

            # Mask of the diagonals that must be set to ones
            T_set_diag = np.logical_and(T_set_mask, diag_mask)

            # The COO sparse matrix format will end up summing duplicate row and column values.
            # To account for this, we must set any values that come up twice (middle edge nodes) to
            # 0.5, any values that come up four times (interior nodes) to 0.25, and any values that
            # come up once (corner nodes) to 1.0.
            diag_glob_idx = node_glob_idx[i_corner][T_is_set[node_glob_idx[i_corner]]]  # glob idx of set nodes
            diag_j = diag_glob_idx % ny  # i idx of set nodes
            diag_i = (diag_glob_idx - diag_j) // ny  # j idx of set nodes
            is_corner = ((diag_i == 0) | (diag_i == nx - 1)) & ((diag_j == 0) | (diag_j == ny - 1))
            is_edge = ((diag_i == 0) | (diag_i == nx - 1) | (diag_j == 0) | (diag_j == ny - 1)) & np.logical_not(
                is_corner
            )
            is_interior = np.logical_not(is_corner) & np.logical_not(is_edge)

            # The indexing isn't pretty, but it's what must be done to avoid assigning values to a copy of K_vals
            self.K_vals[i_corner][np.ix_(T_set_diag)[0][np.ix_(is_corner)]] = 1.0
            self.K_vals[i_corner][np.ix_(T_set_diag)[0][np.ix_(is_edge)]] = 0.5
            self.K_vals[i_corner][np.ix_(T_set_diag)[0][np.ix_(is_interior)]] = 0.25

            # Remove any indices from the val and density maps that correspond to the ones along the diagonal since
            # those are not multiplied by density. The indices we've zeroed out will be removed in a sec, hold your horses.
            self.idx_density_map[i_corner] = np.delete(self.idx_density_map[i_corner], np.ix_(T_set_diag)[0])
            self.idx_val_map[i_corner] = np.delete(self.idx_val_map[i_corner], np.ix_(T_set_diag)[0])

        # Flatten the values
        self.K_rows = np.array(self.K_rows).flatten()
        self.K_cols = np.array(self.K_cols).flatten()
        self.K_vals = np.array(self.K_vals).flatten()
        self.idx_val_map = np.hstack(self.idx_val_map)
        self.idx_density_map = np.hstack(self.idx_density_map)

    def _preprocess_pRpx(self):
        """
        Compute the sparse matrices and other data necessary to efficiently compute the partial
        derivative of the residuals with respect to the densities. These matrices are dependent
        only on the mesh and which temperatures are set, so this must be called only once at the
        beginning.

        The approach used here will compute the pRpx matrix by multiplying two sparse matrices.
        The first sparse matrix contains copies of the local stiffness matrix. It does not depend
        on density or temperature, so it is fully definied when this function is called. The second
        sparse matrix is the temperatures arranged so that when multiplied by the first it returns
        pRpx. The temperatures will change at runtime, so here we define the rows and columns
        that define the second matrix's sparsity. We also define the indices from the temperature
        that return the values for the sparse matrix.

        Computing pRpx after calling this function will look something like:

            pRpx_temp_mat = sp.csr_matrix((outputs["temp"][self.pRpx_temp_idx], (self.pRpx_temp_rows, self.pRpx_temp_cols)))
            pRpx = self.pRpx_coeff_mat.dot(pRpx_temp_mat)

        The member variables this functions adds are:
            pRpx_coeff_mat
            pRpx_temp_idx
            pRpx_temp_rows
            pRpx_temp_cols
        """
        nx, ny = (self.nx, self.ny)
        n_elem = (nx - 1) * (ny - 1)
        nodes_per_elem = 4

        # Because we use meshgrid, all elements are the same size and shape,
        # and we use the same thermal conductivity throughout. Thus, the local
        # stiffness matrix is identical for each element.
        K_loc = self._local_stiffness(0, 0)

        # Rearrange K_loc so instead of being ordered by the nodes of an element CCW,
        # they're ordered lower left, upper left, lower right, and upper right because
        # this is the ordering used in the global indexing
        idx_reorder_K = [0, 3, 1, 2]
        K_loc = K_loc[np.ix_(idx_reorder_K, idx_reorder_K)]

        # Global indices of the corners of the elements. This ordering is not CCW as it is in some other places!
        i, j = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
        i = i.flatten()
        j = j.flatten()
        #                          lower left  upper left      lower right       upper right
        nodal_glob_idx = np.array([i * ny + j, i * ny + j + 1, (i + 1) * ny + j, (i + 1) * ny + j + 1])

        # The rows and columns are ordered such that they iterate over each element's K matrix (after being reordered)
        # starting at the top left, going through each row left to right, then to the next row and repeat
        coeff_mat_rows = np.repeat(nodal_glob_idx.T, nodes_per_elem)
        coeff_mat_cols = np.tile(np.arange(nodes_per_elem), n_elem * nodes_per_elem) + np.repeat(
            np.arange(n_elem) * nodes_per_elem, nodes_per_elem**2
        )
        coeff_mat_vals = np.tile(K_loc.flatten(), n_elem)

        # Remove any rows where the temperature is set
        T_is_set = np.isfinite(self.options["T_set"]).flatten()
        idx_where_T_is_set = np.argwhere(T_is_set).flatten()
        idx_to_remove = np.in1d(coeff_mat_rows, idx_where_T_is_set)
        coeff_mat_rows = np.delete(coeff_mat_rows, idx_to_remove)
        coeff_mat_cols = np.delete(coeff_mat_cols, idx_to_remove)
        coeff_mat_vals = np.delete(coeff_mat_vals, idx_to_remove)

        # Finally, we have the pRpx coefficient matrix!
        self.pRpx_coeff_mat = sp.csr_matrix(
            (coeff_mat_vals, (coeff_mat_rows, coeff_mat_cols)), shape=(nx * ny, n_elem * nodes_per_elem)
        )

        # Set up the stuff for the pRpx temperature matrix
        self.pRpx_temp_rows = np.arange(n_elem * nodes_per_elem, dtype=int)
        self.pRpx_temp_cols = np.repeat(np.arange(n_elem, dtype=int), nodes_per_elem)
        self.pRpx_temp_idx = nodal_glob_idx.T.flatten()

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

        force = np.zeros((4,), dtype=float)

        for N, dN in zip(self.N, self.dN_dxi):
            # Compute the Jacobian matrix
            J = dN @ nodal_coord

            force += q * N * np.linalg.det(J)

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
            1 / 4 * np.array([(xi - 1) * (eta - 1), -(xi + 1) * (eta - 1), (xi + 1) * (eta + 1), -(xi - 1) * (eta + 1)])
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
