import matplotlib.pyplot as plt
import numpy as np
import pickle as pkl
import os
from os import listdir
from os.path import isfile, join
import tilemapbase as tmb
from dataCollection.SanDiego import SanDiego


t = tmb.tiles.build_OSM()


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
    callsign = flightDetails["identification"]["callsign"]
    origin = flightDetails["airport"]["origin"]["code"]["iata"]
    destination = flightDetails["airport"]["destination"]["code"]["iata"]

    return f"Flight {callsign} from {origin} to {destination}"


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

    for i, point in enumerate(trail):
        latlong[i, :] = [point["lng"], point["lat"]]

    return latlong


def plotMap(flightDetails, airport, show=False):
    """
    Plot the longitude and latitude for a flight on a map of a given airport

    Parameters
    ----------
    flightDetails : dict
        dictionary of all details on flight
    airport : Airport class
        airport being studied for this case
    show : bool, optional
        whether to show the plot, by default False, then it saves the figure
    """
    flightID = flightIDString(flightDetails)
    latlong = extractTrail(flightDetails)

    extent = tmb.Extent.from_lonlat(airport.centerLoc[0] - airport.longRange, airport.centerLoc[0] + airport.longRange, airport.centerLoc[1] - airport.latRange, airport.centerLoc[1] + airport.latRange)
    _, ax = plt.subplots()
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, t, width=600)
    plotter.plot(ax, t)

    for point in latlong:
        x, y = tmb.project(*point)
        ax.scatter(x, y, color="black", s=9)

    plt.title(flightID)

    if show:
        plt.show()
    else:
        plt.savefig(f"{flightID}.png")


def plotAllInFolder(path, airport):
    """
    plot all the flight files at a path to debug

    Parameters
    ----------
    path : string
        path to folder of files
    airport : Airport class
        airport being studied for this case
    """
    departureFiles = [f for f in listdir(path) if isfile(join(path, f))]

    for fileName in departureFiles:
        fullName = os.path.join(departurePath, fileName)

        flightDetails = openPickle(fullName)
        plotMap(flightDetails, airport, show=True)


departurePath = os.path.join(os.path.dirname(__file__), "../actualData/departures")
airport = SanDiego()
plotAllInFolder(departurePath, airport)

# f = "../actualData/departures/WN2777_SAN_to_LAS"
# file = openPickle(f)
# plotMap(file, airport, True)
