import openmdao.api as om
import numpy as np
import scipy.sparse as sp
from collections.abc import Iterable
from time import time


def gen_mesh(nx, ny, xlim, ylim):
    x_linspace = np.linspace(*xlim, nx)
    y_linspace = np.linspace(*ylim, ny)
    return np.meshgrid(x_linspace, y_linspace, indexing="ij")


class Mass(om.ExplicitComponent):
    """
    Computes the "mass" of the mesh by summing the densities. This assumes all elements in the
    mesh are the same size and the mass of an element with a density of 1 is 1.

    Inputs
    ------
    density : float
        Densities of each element, which can remove/add elements to the problem
        by scaling their thermal conductivity. The shape corresponds to the flattened
        2D array of elements. By default 1 for every element.

    Outputs
    -------
    mass : float
        Sum of the densities, scalar.

    Options
    -------
    num_x : int
        Number of mesh coordinates in the x direction.
    num_y : int
        Number of mesh coordinates in the y direction.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")

    def setup(self):
        nx, ny = (self.options["num_x"], self.options["num_y"])
        self.add_input("density", shape=((nx - 1) * (ny - 1),))
        self.add_output("mass")

        self.declare_partials("mass", "density", val=1.0)

    def compute(self, inputs, outputs):
        outputs["mass"] = np.sum(inputs["density"])


class LinearDensityFilter(om.ExplicitComponent):
    """
    Filter the density using a linear density filter. The filtered densities
    for each element are a weighted sum of input densities of surrounding elements
    where the weights are inversely proportional to the distance between the two element
    centroids. For more information see equations 19 to 21 in "Topology optimization of
    non-linear elastic structures and compliant mechanisms" by Bruns and Tortorelli.

    Inputs
    ------
    density : float
        Densities of each element. The shape corresponds to the flattened
        2D array of elements.

    Outputs
    -------
    density_filtered : float
        Filtered densities of each element. The shape corresponds to
        the flattened 2D array of elements.

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
    r : float
        Filter radius. The dimensions correspond to the dimensions
        of the mesh (x and y limit options), by
        default 1e-2.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")
        self.options.declare("x_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on x range")
        self.options.declare("y_lim", default=(0.0, 1.0), types=Iterable, desc="Lower and upper bounds on y range")
        self.options.declare("r", default=1e-2, types=float, desc="Filter radius")

    def setup(self):
        t_start = time()
        print("Setting up LinearDensityFilter...")
        nx, ny = (self.options["num_x"], self.options["num_y"])
        n_elem = (nx - 1) * (ny - 1)
        r = self.options["r"]
        xlim, ylim = (self.options["x_lim"], self.options["y_lim"])
        x_spacing = (xlim[1] - xlim[0]) / (self.options["num_x"] - 1)
        y_spacing = (ylim[1] - ylim[0]) / (self.options["num_y"] - 1)

        # Compute the radius in indices in each direction we need to search for the filter
        r_idx_x = int(np.ceil(r / x_spacing))
        r_idx_y = int(np.ceil(r / y_spacing))

        self.add_input("density", shape=(n_elem,))
        self.add_output("density_filtered", shape=(n_elem,))

        rows = []
        cols = []
        vals = []

        # TODO: make this faster

        # Loop over the densities to be weighted
        slow_str = " sorry I'm slow :("
        for idx_x in range(nx - 1):
            for idx_y in range(ny - 1):
                # Row in the filtering matrix, which corresponds to the density of element (idx_x, idx_y), which we call i
                row_idx = idx_x * (ny - 1) + idx_y

                if row_idx % 10000 == 5000:
                    time_left = (n_elem - row_idx) / (row_idx + 1) * (time() - t_start)
                    print(
                        f"    I'll be done in {time_left:.0f} sec{slow_str if time_left > 10 else ''}                                 ",
                        end="\r",
                    )

                # Centroid coordinates of the element whose density is being weighted
                xi, yi = ((idx_x + 0.5) * x_spacing, (idx_y + 0.5) * y_spacing)

                # Box that contains all elements within the specified radius (+1 is because arange is exclusive)
                x_neighbor_list = np.arange(max(0, idx_x - r_idx_x), min(nx - 2, idx_x + r_idx_x) + 1, dtype=int)
                y_neighbor_list = np.arange(max(0, idx_y - r_idx_y), min(ny - 2, idx_y + r_idx_y) + 1, dtype=int)
                idx_x_neighbor, idx_y_neighbor = np.meshgrid(x_neighbor_list, y_neighbor_list, indexing="ij")
                idx_x_neighbor = idx_x_neighbor.flatten()
                idx_y_neighbor = idx_y_neighbor.flatten()

                # Columns in the filtering matrix that correspond to the effect of the density of
                # neighboring elements on the filtered density of element i
                col_idx = idx_x_neighbor * (ny - 1) + idx_y_neighbor

                # Centroid coordinates of element j
                xj, yj = ((idx_x_neighbor + 0.5) * x_spacing, (idx_y_neighbor + 0.5) * y_spacing)

                # Weight of element j on element i
                wj = 1 - ((xj - xi) ** 2 + (yj - yi) ** 2) / r**2
                idx_nonzero = wj > 0.0

                # Get rid of the nonzero elements
                wj = wj[idx_nonzero]
                rows_i = np.full(wj.shape, row_idx, dtype=int)
                cols_i = col_idx[idx_nonzero]

                # Normalize the weights
                wj /= np.sum(wj)

                # Add the vals, rows, cols to the lists
                rows.append(rows_i)
                cols.append(cols_i)
                vals.append(wj)

        self.weight_mtx = sp.csr_matrix((np.hstack(vals), (np.hstack(rows), np.hstack(cols))), shape=(n_elem, n_elem))
        self.declare_partials("density_filtered", "density", val=self.weight_mtx)
        print(f"    ...done in {time() - t_start} sec")

    def compute(self, inputs, outputs):
        outputs["density_filtered"] = self.weight_mtx @ inputs["density"]


class PenalizeDensity(om.ExplicitComponent):
    """
    Apply a penalty to density as density^p where p is an option.

    Inputs
    ------
    density : float
        Densities of each element. The shape corresponds to the flattened
        2D array of elements.

    Outputs
    ------
    density_penalized : float
        The penalized densities of each element. The shape corresponds to
        the flattened 2D array of elements.

    Options
    -------
    num_x : int
        Number of mesh coordinates in the x direction.
    num_y : int
        Number of mesh coordinates in the y direction.
    p : float
        Penalty factor.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")
        self.options.declare("p", default=3.0, types=float, desc="Penalty factor")

    def setup(self):
        nx, ny = (self.options["num_x"], self.options["num_y"])
        n_elem = (nx - 1) * (ny - 1)

        self.add_input("density", shape=(n_elem,))
        self.add_output("density_penalized", shape=(n_elem,))

        arng = np.arange(n_elem)
        self.declare_partials("density_penalized", "density", rows=arng, cols=arng)

    def compute(self, inputs, outputs):
        outputs["density_penalized"] = inputs["density"] ** self.options["p"]

    def compute_partials(self, inputs, jacobian):
        jacobian["density_penalized", "density"] = self.options["p"] * inputs["density"] ** (self.options["p"] - 1)


class SmoothStep(om.ExplicitComponent):
    """
    Smooth step function to guide values closer to 0 or 1.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")
        self.options.declare("n", types=int, default=3, desc="Polynomial order of the smoothstep")
        self.options.declare("x_min", types=float, default=0.25, desc="Step start x value")
        self.options.declare("x_max", types=float, default=0.75, desc="Step end x value")
        self.options.declare("y_min", types=float, default=1e-3, desc="Step minimum value")
        self.options.declare("y_max", types=float, default=1.0, desc="Step maximum value")

    def setup(self):
        nx, ny = (self.options["num_x"], self.options["num_y"])
        self.size = (nx - 1) * (ny - 1)
        self.add_input("in", shape=(self.size,))
        self.add_output("out", shape=(self.size,))

        self.inds = np.arange(self.size).tolist()
        self.declare_partials("out", "in", rows=self.inds, cols=self.inds)

    def compute(self, inputs, outputs):
        # Normalize the x values to the range [0, 1] and compute rational polynomial value
        x_scaled = (inputs["in"] - self.options["x_min"]) / (self.options["x_max"] - self.options["x_min"])
        y_scaled = x_scaled ** self.options["n"] / (x_scaled ** self.options["n"] + (1 - x_scaled) ** self.options["n"])

        # Clip the values outside the step range
        y_scaled = np.where(x_scaled < 0.0, 0.0, y_scaled)
        y_scaled = np.where(x_scaled > 1.0, 1.0, y_scaled)

        # Convert back to the desired range
        outputs["out"] = self.options["y_min"] + (self.options["y_max"] - self.options["y_min"]) * y_scaled

    def compute_partials(self, inputs, partials):
        # Normalize the x values to the range [0, 1] and compute rational polynomial derivative
        x_scaled = (inputs["in"] - self.options["x_min"]) / (self.options["x_max"] - self.options["x_min"])
        dYdX_scaled = (
            self.options["n"]
            * x_scaled ** (self.options["n"] - 1)
            * (1.0 - x_scaled) ** (self.options["n"] - 1)
            / (x_scaled ** self.options["n"] + (1.0 - x_scaled) ** self.options["n"]) ** 2
        )

        # Clip the values outside the step range
        dYdX_scaled = np.where(x_scaled < 0.0, 0.0, dYdX_scaled)
        dYdX_scaled = np.where(x_scaled > 1.0, 0.0, dYdX_scaled)

        # Scale the derivatives back to the user's scale
        dYdX = (
            dYdX_scaled
            * (self.options["y_max"] - self.options["y_min"])
            / (self.options["x_max"] - self.options["x_min"])
        )

        partials["out", "in"] = dYdX.flatten()


class AvgTemp(om.ExplicitComponent):
    """
    Compute the average temperature in each element weighted by the element's density.

    Inputs
    ------
    density : float
        Densities of each element, which can remove/add elements to the problem
        by scaling their thermal conductivity. The shape corresponds to the flattened
        2D array of elements. By default 1 for every element.
    temp : float
        Nodal temperatures, flattened into a 1D array.

    Outputs
    -------
    avg_temp : float
        Average element temperature weighted by densities, same shape as density input.

    Options
    -------
    num_x : int
        Number of mesh coordinates in the x direction.
    num_y : int
        Number of mesh coordinates in the y direction.
    """

    def initialize(self):
        self.options.declare("num_x", types=int, desc="Number of mesh coordinates in the x direction")
        self.options.declare("num_y", types=int, desc="Number of mesh coordinates in the y direction")

    def setup(self):
        nx, ny = (self.options["num_x"], self.options["num_y"])
        n_elem = (nx - 1) * (ny - 1)

        # Indices
        i, j = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
        i = i.flatten()
        j = j.flatten()
        self.node_idx = np.array([i * ny + j, i * ny + j + 1, (i + 1) * ny + j, (i + 1) * ny + j + 1])

        self.add_input("density", shape=(n_elem,))
        self.add_input("temp", shape=(nx * ny,))

        self.add_output("avg_temp", shape=(n_elem,))

        arng = np.arange(n_elem)
        self.declare_partials("avg_temp", "density", rows=arng, cols=arng)

        self.declare_partials("avg_temp", "temp", rows=np.repeat(np.arange(n_elem), 4), cols=self.node_idx.T.flatten())

    def compute(self, inputs, outputs):
        outputs["avg_temp"] *= 0.0

        for idx in self.node_idx:
            outputs["avg_temp"] += inputs["temp"][idx]

        outputs["avg_temp"] *= inputs["density"] / 4

    def compute_partials(self, inputs, jacobian):
        jacobian["avg_temp", "density"] *= 0
        for idx in self.node_idx:
            jacobian["avg_temp", "density"] += inputs["temp"][idx] / 4

        jacobian["avg_temp", "temp"] *= 0
        jacobian["avg_temp", "temp"] += np.repeat(inputs["density"], 4) / 4
