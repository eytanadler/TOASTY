from PIL import Image
import os
import glob
import numpy as np


def load_airport(airport_name, resolution, min_density=1e-3):
    """
    Reads in airport data from TOASTY's database of airports (which is
    very limited because we have to make them all manually).

    Parameters
    ----------
    airport_name : str
        Airport code or source image directory name (e.g., "SAN" or "ORD_28L22L")
    resolution : str
        Name of folder that stores the images for the desired resolution (e.g., "1500w")
    min_density : float
        Minimum density allowed, which sets the lower bound of density_lower, by default 1e-3

    Returns
    -------
    dict
        Data about the airport geometry and temperatures/heats. The keys/values are
            num_x: number of x nodes in the mesh
            num_y: number of y nodes in the mesh
            x_lim: lower and upper limit of the x values for the mesh
            y_lim: lower and upper limit of the y values for the mesh
            density_lower: lower bound on density for optimization problem. This prevents the optimizer from
                reducing the conductivitiy of heat-generating elements and also sets the density of areas
                the optimizer can't touch (a.k.a. keep out zones). Otherwise it is min_density.
            density_upper: upper bound on density for optimization problem. This prevents the optimizer from
                building taxiways through buildings and also sets the density of areas the optimizer can't
                touch (a.k.a. keep out zones). Otherwise it is 1.
            buildings: matrix that is zero where there are no buildings and one where there are
            taxiways: matrix that is zero where there are no taxiways and one where there are
            runways: matrix that is zero where there are no runways and one where there are,
                this will become the lower bound on the density design variables (will want
                to increase the zeros to something small though, such as 1e-3)
            q_elem: dict of heat-generating elements for each approach pattern (one in elements
                that generate heat and zero otherwise)
            T_set_node: dict of nodes where temperatures are set for each approach pattern (one at
                nodes where the temperature is set and zero otherwise)
            keep_out: matrix that is zero where the optimizer is allowed to modify and one otherwise
    """
    # Check that the desired airport and resolution exists
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    apt_data_dir = os.path.join(cur_dir, "airports")

    if not os.path.isdir(os.path.join(apt_data_dir, airport_name)):
        raise FileNotFoundError(
            f"{airport_name} is not an available airport, please select from {subdirectories(apt_data_dir)}"
        )

    apt_dir = os.path.join(apt_data_dir, airport_name)
    if not os.path.isdir(os.path.join(apt_dir, resolution)):
        raise FileNotFoundError(
            f"{resolution} is not an available resolution for {airport_name}, please select from {subdirectories(apt_dir)}"
        )

    data_dir = os.path.join(apt_dir, resolution)

    # Read in the images. They'll be stored as 3D numpy arrays where the rows and columns use the same
    # ordering as the meshes in TOASTY. The 3rd dimension is a 3-element array with R, G, and B values.
    im = {}
    try:
        for name in ["buildings", "runways", "taxiways", "keep_out"]:
            # If there are multiple extensions, just use the first one
            try:
                f = glob.glob(os.path.join(data_dir, f"{name}.*"))[0]
                im[name] = np.flipud(np.array(Image.open(f).convert("RGB"))).astype(int)
            except IndexError:  # no files found
                if name == "keep_out":  # that's ok, keep out zones are not required
                    im[name] = np.full_like(im["buildings"], 255)  # fill it with white (no keep out zones)
                else:  # all the others are required
                    raise FileNotFoundError(f"No {name} image found for airport configuration \"{airport_name}\"")

        # Do the different approach patterns
        im["thermals"] = {}
        f = glob.glob(os.path.join(data_dir, "thermals_*.*"))
        if len(f) == 0:
            raise IndexError
        for app in f:
            app_name = app.split("thermals_")[-1].split(".")[0]
            im["thermals"][app_name] = np.flipud(np.array(Image.open(app).convert("RGB"))).astype(int)
    except IndexError:  # glob would throw an index error because it'd return an empty list
        raise FileNotFoundError(
            f"The data folder for {airport_name} at a resolution of {resolution} must contain images "
            + 'named "buildings", "runways", "taxiways", and "thermals_*" where "*" is any '
            + f"number of approach pattern names, but it contains only {os.listdir(data_dir)}"
        )

    # Reshape them so they're ordered properly
    nx = im["runways"].shape[1] + 1
    ny = im["runways"].shape[0] + 1
    for key in im.keys():
        if key == "thermals":
            for app in im[key].keys():
                im[key][app] = np.transpose(im[key][app], axes=(1, 0, 2))
        else:
            im[key] = np.transpose(im[key], axes=(1, 0, 2))

    # Dictionary to return
    data = {
        "num_x": nx,
        "num_y": ny,
        "x_lim": (0, nx / max(nx, ny)),
        "y_lim": (0, ny / max(nx, ny)),
    }

    # Figure out where the runways, buildings, and taxiways are by finding all pixels where the sum of the RGB
    # values divided by the max sum of RGB values (255 + 255 + 255) is < 90% (not close to white)
    for obj in ["runways", "buildings", "taxiways"]:
        data[obj] = ((1 - np.sum(im[obj], axis=2) / (3 * 255)) > 0.1).astype(float)
        data[obj][data[obj] < 0] = 0
        data[obj][data[obj] > 1] = 1
        data[obj][[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images

    # Keep out areas are red (red channel is more than twice both the blue and green channel values)
    keep_out = (
        (im["keep_out"][:, :, 0] > (2 * im["keep_out"][:, :, 1]))
        & (im["keep_out"][:, :, 0] > (2 * im["keep_out"][:, :, 2]))
    )
    keep_out[[0, 1], -1] = False  # not sure why but these squares sometimes end up red in the images
    data["keep_out"] = keep_out.astype(float)

    # Get the heat-generating elements for each approach from the elements
    # whose red channel is more than twice the blue and green channels
    data["q_elem"] = {}
    for app in im["thermals"].keys():
        data["q_elem"][app] = (
            (im["thermals"][app][:, :, 0] > (2 * im["thermals"][app][:, :, 1]))
            & (im["thermals"][app][:, :, 0] > (2 * im["thermals"][app][:, :, 2]))
        ).astype(float)
        data["q_elem"][app][[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images

    # Get the set temperature nodes by taking the nodes around elements
    # whose blue channel is more than twice the red and green channels
    data["T_set_node"] = data["T_set_node"] = {}
    for app in im["thermals"].keys():
        data["T_set_node"][app] = np.zeros((nx, ny))
        T_set_elem = (
            (im["thermals"][app][:, :, 2] > (2 * im["thermals"][app][:, :, 0]))
            & (im["thermals"][app][:, :, 2] > (2 * im["thermals"][app][:, :, 1]))
        ).astype(float)
        idx_lower_left = np.argwhere(T_set_elem)
        data["T_set_node"][app][idx_lower_left[:, 0], idx_lower_left[:, 1] + 1] += 1
        data["T_set_node"][app][idx_lower_left[:, 0], idx_lower_left[:, 1]] += 1
        data["T_set_node"][app][idx_lower_left[:, 0] + 1, idx_lower_left[:, 1]] += 1
        data["T_set_node"][app][idx_lower_left[:, 0] + 1, idx_lower_left[:, 1] + 1] += 1
        data["T_set_node"][app][data["T_set_node"][app] != 0] /= data["T_set_node"][app][data["T_set_node"][app] != 0]

    # Figure out the upper and lower bounds for the optimization problem
    data["density_lower"] = np.zeros_like(data["runways"])
    data["density_upper"] = np.ones_like(data["runways"])

    # Taxiways must be maintained in keep out areas
    data["density_lower"][np.logical_and(data["taxiways"] > 0.99, keep_out)] = 1.0
    data["density_upper"][np.logical_and(data["taxiways"] < 0.01, keep_out)] = 0.0

    # Runways and buildings can't conduct heat (heat-generating elements must, which is fixed later)
    for k in ["density_upper", "density_lower"]:
        data[k][data["runways"] > 0.99] = 0.0
        data[k][data["buildings"] > 0.99] = 0.0

    # Heat-generating elements must be conductive
    for case in data["q_elem"].values():
        data["density_lower"][case > 0.99] = 1.0
        data["density_upper"][case > 0.99] = 1.0

    # Keep the density bounds within the desired range
    for k in ["density_upper", "density_lower"]:
        data[k][data[k] < min_density] = min_density
        data[k][data[k] > 1.0] = 1.0

    return data


def subdirectories(dir):
    """
    Returns a list of all the subdirectory names within the directory specified.
    """
    entries = os.listdir(dir)
    subdirs = []
    for entry in entries:
        if os.path.isdir(os.path.join(dir, entry)):
            subdirs.append(entry)
    return subdirs
