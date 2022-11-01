import openmdao.api as om
import numpy as np

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

class PenalizeDensity(om.ExplicitComponent):
    """
    Apply a penalty to density as density^p where p is an option.

    Inputs
    ------
    density_dv : float
        Densities of each element. The shape corresponds to the flattened
        2D array of elements.
    
    Outputs
    ------
    density : float
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

        self.add_input("density_dv", shape=(n_elem,))
        self.add_output("density", shape=(n_elem,))

        arng = np.arange(n_elem)
        self.declare_partials("density", "density_dv", rows=arng, cols=arng)
    
    def compute(self, inputs, outputs):
        outputs["density"] = inputs["density_dv"] ** self.options["p"]

    def compute_partials(self, inputs, jacobian):
        jacobian["density", "density_dv"] = self.options["p"] * inputs["density_dv"] ** (self.options["p"] - 1)
