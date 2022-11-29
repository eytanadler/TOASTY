import numpy as np
import pickle as pkl


def extractTrail(flightDetails):
    """
    Get the longitude and latitude from the flightDetails dict in the right order for plotting

    Parameters
    ----------
    flightDetails : dict
        dictionary of all details on flight

    Returns
    -------
    numpy array (n, 2)
        longitude & latitude trail info for a flight for plotting
    """
    trail = flightDetails["trail"]
    latlong = np.zeros((len(trail), 2))
    alt = np.zeros(len(trail))
    speed = np.zeros(len(trail))

    for i, point in enumerate(trail):
        latlong[i, :] = [point["lng"], point["lat"]]
        alt[i] = point["alt"]
        speed[i] = point["spd"]

    return latlong, alt, speed


def openPickle(fileName):
    """
    Opens pickle file containg details of flight

    Parameters
    ----------
    fileName : string
        file name to be opened

    Returns
    -------
    flightDetails dictionary
        dictionary of all details on flight
    """
    flightFile = open(fileName, "rb")
    flightDetails = pkl.load(flightFile)
    flightFile.close()

    # check for garbage data being zipped on accident
    if not isinstance(flightDetails, dict) or len(flightDetails) < 2:
        flightDetails = None

    return flightDetails


def flightIDString(flightDetails):
    """
    Create a nice string for a flight plot title

    Parameters
    ----------
    flightDetails : dict
        dictionary of all details on flight

    Returns
    -------
    string
        nice string for a title or something
    """
    if flightDetails["identification"]["callsign"] is not None:
        callsign = flightDetails["identification"]["callsign"]
    else:
        callsign = "Unknown"

    if flightDetails["airport"]["origin"] is not None:
        origin = flightDetails["airport"]["origin"]["code"]["iata"]
    else:
        origin = "Unknown"

    if flightDetails["airport"]["destination"] is not None:
        destination = flightDetails["airport"]["destination"]["code"]["iata"]
    else:
        destination = "Unknown"

    return f"Flight {callsign} from {origin} to {destination}"
