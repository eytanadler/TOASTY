from PIL import Image
import os
import glob
import numpy as np


def load_airport(airport_name, resolution):
    """
    Reads in airport data from TOASTY's database of airports (which is
    very limited because we have to make them all manually).

    Parameters
    ----------
    airport_name : str
        Airport code (e.g., "SAN")
    resolution : str
        Name of folder that stores the images for the desired resolution (e.g., "1500w")

    Returns
    -------
    dict
        Data about the airport geometry and temperatures/heats. The keys/values are
            num_x: number of x nodes in the mesh
            num_y: number of y nodes in the mesh
            x_lim: lower and upper limit of the x values for the mesh
            y_lim: lower and upper limit of the y values for the mesh
            buildings: matrix that is zero where there are no buildings and one where there are
            taxiways: matrix that is zero where there are no taxiways and one where there are
            runways: matrix that is zero where there are no runways and one where there are,
                this will become the lower bound on the density design variables (will want
                to increase the zeros to something small though, such as 1e-3)
            q_elem: dict of heat-generating elements for each approach pattern (one in elements
                that generate heat and zero otherwise)
            T_set_node: dict of nodes where temperatures are set for each approach pattern (one at
                nodes where the temperature is set and zero otherwise)
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
        for name in ["buildings", "runways", "taxiways"]:
            # If there are multiple extensions, just use the first one
            f = glob.glob(os.path.join(data_dir, f"{name}.*"))[0]
            im[name] = np.flipud(np.array(Image.open(f).convert("RGB"))).astype(int)

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

    # Get a lower bound on density from the runway
    density_lower = 1 - np.sum(im["runways"], axis=2) / (3 * 255)
    density_lower[density_lower < 0] = 0
    density_lower[density_lower > 1] = 1
    density_lower[[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images

    # Identify buildings and taxiways
    buildings = ((1 - np.sum(im["buildings"], axis=2) / (3 * 255)) > 0.1).astype(float)
    taxiways = ((1 - np.sum(im["taxiways"], axis=2) / (3 * 255)) > 0.1).astype(float)
    buildings[[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images
    taxiways[[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images

    # Get the heat-generating elements for each approach from the elements
    # whose red channel is more than twice the blue and green channels
    q_elem_app = {}
    for app in im["thermals"].keys():
        q_elem_app[app] = (
            (im["thermals"][app][:, :, 0] > (2 * im["thermals"][app][:, :, 1]))
            & (im["thermals"][app][:, :, 0] > (2 * im["thermals"][app][:, :, 2]))
        ).astype(float)
        q_elem_app[app][[0, 1], -1] *= 0  # not sure why but these squares sometimes end up red in the images

    # Get the set temperature nodes by taking the nodes around elements
    # whose blue channel is more than twice the red and green channels
    T_set_app = {}
    for app in im["thermals"].keys():
        T_set_app[app] = np.zeros((nx, ny))
        T_set_elem = (
            (im["thermals"][app][:, :, 2] > (2 * im["thermals"][app][:, :, 0]))
            & (im["thermals"][app][:, :, 2] > (2 * im["thermals"][app][:, :, 1]))
        ).astype(float)
        idx_lower_left = np.argwhere(T_set_elem)
        T_set_app[app][idx_lower_left[:, 0], idx_lower_left[:, 1] + 1] += 1
        T_set_app[app][idx_lower_left[:, 0], idx_lower_left[:, 1]] += 1
        T_set_app[app][idx_lower_left[:, 0] + 1, idx_lower_left[:, 1]] += 1
        T_set_app[app][idx_lower_left[:, 0] + 1, idx_lower_left[:, 1] + 1] += 1
        T_set_app[app][T_set_app[app] != 0] /= T_set_app[app][T_set_app[app] != 0]

    return {
        "num_x": nx,
        "num_y": ny,
        "x_lim": (0, nx / max(nx, ny)),
        "y_lim": (0, ny / max(nx, ny)),
        "buildings": buildings,
        "taxiways": taxiways,
        "runways": density_lower,
        "q_elem": q_elem_app,
        "T_set_node": T_set_app,
    }


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
