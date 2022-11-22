import matplotlib.pyplot as plt
import numpy as np
from os import listdir
from os.path import isfile, join
import tilemapbase as tmb
import niceplots as nice

from dataCollection.plotting.plotUtils import extractTrail, openPickle, flightIDString


tmb.init(create=True)

t = tmb.tiles.build_OSM_Humanitarian()


def plotMap(flightDetails, airport, departure, plotExit=False, show=False):
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
    nice.setRCParams()
    flightID = flightIDString(flightDetails)
    latlong, _, _ = extractTrail(flightDetails)

    extent = tmb.Extent.from_lonlat(
        airport.centerLoc[0] - airport.longRange,
        airport.centerLoc[0] + airport.longRange,
        airport.centerLoc[1] - airport.latRange,
        airport.centerLoc[1] + airport.latRange,
    )
    _, ax = plt.subplots(figsize=(32, 18))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, t, width=1200)
    plotter.plot(ax, t)

    for point in latlong:
        x, y = tmb.project(*point)
        ax.scatter(x, y, color="black", s=40)

    if plotExit:
        ex = airport.findBetterExit(flightDetails, departure)
        coords = airport.exitLocations[ex][:]
        x1, y1 = tmb.project(*(coords[0], coords[3]))
        x2, y2 = tmb.project(*(coords[1], coords[3]))
        x3, y3 = tmb.project(*(coords[1], coords[2]))
        x4, y4 = tmb.project(*(coords[0], coords[2]))

        x = [x1, x2, x3, x4, x1]
        y = [y1, y2, y3, y4, y1]

        ax.plot(x, y, color="black")

    plt.title(flightID, fontsize=30)

    if show:
        plt.show()
    else:
        plt.savefig(f"{flightID}.png")


def plotExitBoxes(airport, plotAll=False, exitList=None, show=False):
    """
    Plot the bounding box enclosing a runway exit on top of the map

    Parameters
    ----------
    exitList : array
        list of which exit boxes to plot
    airport : Airport class
        airport being studied for this case
    show : bool, optional
        whether to show the plot, by default False, then it saves the figure
    """
    extent = tmb.Extent.from_lonlat(
        airport.centerLoc[0] - airport.longRange,
        airport.centerLoc[0] + airport.longRange,
        airport.centerLoc[1] - airport.latRange,
        airport.centerLoc[1] + airport.latRange,
    )
    _, ax = plt.subplots()
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, t, width=1200)
    plotter.plot(ax, t)

    if exitList is not None:
        for i in exitList:
            coords = airport.exitLocations[i][:]
            x1, y1 = tmb.project(*(coords[0], coords[3]))
            x2, y2 = tmb.project(*(coords[1], coords[3]))
            x3, y3 = tmb.project(*(coords[1], coords[2]))
            x4, y4 = tmb.project(*(coords[0], coords[2]))

            x = [x1, x2, x3, x4, x1]
            y = [y1, y2, y3, y4, y1]

            ax.plot(x, y, color="black")

    if plotAll is True:  # duplicated code is the root of all eveil but I am TIRED TODO
        for i in range(len(airport.exitLocations)):
            coords = airport.exitLocations[i][:]
            x1, y1 = tmb.project(*(coords[0], coords[3]))
            x2, y2 = tmb.project(*(coords[1], coords[3]))
            x3, y3 = tmb.project(*(coords[1], coords[2]))
            x4, y4 = tmb.project(*(coords[0], coords[2]))

            x = [x1, x2, x3, x4, x1]
            y = [y1, y2, y3, y4, y1]

            ax.plot(x, y, color="black", linewidth=0.75)

    plt.title(f"Taxiway exit/entrance bounds for {airport.code}")

    if show:
        plt.show()
    else:
        plt.savefig(f"figures/bounds_{airport.code}.png", dpi=600, bbox_inches="tight")


def plotFrequenciesColor(airport, exitPercent, date, departures=True, show=False):
    """
    Plot a heat map (really just some dots representing frequency) on an airport map
    Normalize the frequency at which the aircraft use the exits so the full range of the colormap is used
    This seemed easier than adjusting the colorbar bounds

    Parameters
    ----------
    airport : Airport class
        airport being studied for this case
    exitPercent : list
        Percentages of aircraft using each exit
    dateString : string
        date this data is from
    departures : bool, optional
        whether this data is from departing aircraft, used for titles, by default True
    show : bool, optional
        whether to show the plot, by default False, then it saves the figure
    """
    extent = tmb.Extent.from_lonlat(
        airport.centerLoc[0] - airport.longRange,
        airport.centerLoc[0] + airport.longRange,
        airport.centerLoc[1] - airport.latRange,
        airport.centerLoc[1] + airport.latRange,
    )
    _, ax = plt.subplots(figsize=(16, 9))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, t, width=1200)
    plotter.plot(ax, t)

    normalizedPercent = (exitPercent - np.min(exitPercent)) / (np.max(exitPercent) - np.min(exitPercent))

    allX = []
    allY = []
    for ex in airport.exitLocations:
        long = np.average((ex[0], ex[1]))
        lat = np.average((ex[2], ex[3]))

        x, y = tmb.project(*(long, lat))
        allX.append(x)
        allY.append(y)

    if departures:
        key1 = "departures"
        key2 = "Exit"
    else:
        key1 = "arrivals"
        key2 = "Entrance"

    plt.title(f"{key2} frequencies for {airport.code} {key1} on {date}")
    plt.scatter(x=allX, y=allY, c=normalizedPercent, cmap="plasma", s=55)
    plt.colorbar(label=f"{key2} use frequency", orientation="vertical", shrink=0.6)

    if show:
        plt.show()
    else:
        plt.savefig(f"figures/{key2}_freq_{airport.code}_{key1}_{date}.png", dpi=600, bbox_inches="tight")


def plotFrequenciesSize(airport, exitPercent, exitCount, date, departures=True, show=False):
    """
    Plot a heat map (really just some dots representing frequency) on an airport map
    Normalize the frequency at which the aircraft use the exits so the full range of the colormap is used
    This seemed easier than adjusting the colorbar bounds

    Parameters
    ----------
    airport : Airport class
        airport being studied for this case
    exitPercent : list
        Percentages of aircraft using each exit
    dateString : string
        date this data is from
    departures : bool, optional
        whether this data is from departing aircraft, used for titles, by default True
    show : bool, optional
        whether to show the plot, by default False, then it saves the figure
    """
    extent = tmb.Extent.from_lonlat(
        airport.centerLoc[0] - airport.longRange,
        airport.centerLoc[0] + airport.longRange,
        airport.centerLoc[1] - airport.latRange,
        airport.centerLoc[1] + airport.latRange,
    )
    _, ax = plt.subplots(figsize=(16, 9))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, tile_provider=t, width=1200)
    plotter.plot(ax, t)

    # normalizedPercent = (exitPercent - np.min(exitPercent)) / (np.max(exitPercent) - np.min(exitPercent))

    for i, ex in enumerate(airport.exitLocations):
        long = np.average((ex[0], ex[1]))
        lat = np.average((ex[2], ex[3]))

        x, y = tmb.project(*(long, lat))
        # ax.plot(x, y, marker="o", markersize=1, color="black")

        if exitPercent[i] == 0:
            size = 0
        else:
            size = 40 * np.log(exitPercent[i]) / np.log(100)

        ax.plot(x, y, marker="o", markersize=size, color="lightcoral", alpha=0.7)
        plt.text(x, y, str(i), fontsize=4, ha="center", va="center")
        # print(f"i {i} size {10 * int(normalizedPercent[i])}")
        # ax.plot(x, y, marker="o", markersize=30, color="lightcoral", alpha=0.7)

    if departures:
        key1 = "departures"
        key2 = "Entrance"
    else:
        key1 = "arrivals"
        key2 = "Exit"

    plt.title(f"{key2} frequencies for {airport.code} {key1} on {date}")

    if show:
        plt.show()
    else:
        # plt.savefig("test.png", dpi=600, bbox_inches="tight")
        plt.savefig(f"figures/{key2}_freq_{airport.code}_{key1}_{date}.png", dpi=600, bbox_inches="tight")


def plotAllInFolder(path, airport, departures, plotExit=False):
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
        fullName = join(path, fileName)

        flightDetails = openPickle(fullName)
        plotMap(flightDetails, airport, departures, plotExit=plotExit, show=True)
