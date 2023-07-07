import matplotlib.pyplot as plt
import numpy as np
from os import listdir, makedirs
from os.path import isfile, join, dirname
import tilemapbase as tmb
import subprocess

from dataCollection.plotting.plotUtils import extractTrail, openPickle, flightIDString


tmb.init(create=True)
t = tmb.tiles.build_OSM_Humanitarian()

mdo_light_blue = "#0caaef"


def plotMap(
    flightDetails, airport, departure, outFolder=None, figTitle=None, plotExit=False, showPlot=False, fileName=None
):
    """
    Plot the trail of a flight on an airport map

    Parameters
    ----------
    flightDetails : flightDetails object
        comes from pickle file or directly from FlightRadar24API
    airport : airport class
        airport used here
    departure : bool
        whether this is an arrival or departure
    outFolder: string, optional
        Folder to save a the image in, by default None
    figTitle : string, optional
        Figure title to override auto generated, by default None
    plotExit : bool, optional
        Whether to plot exit/entrance aircraft takes, by default False
    showPlot : bool, optional
        Whether to show plot or save figure, by default False
    fileName : string, optional
        File name to override auto generated, by default None
    """

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

    ax.fill_between([0, 1], [0, 0], [1, 1], transform=ax.transAxes, color="white", alpha=0.3)

    xlist = []
    ylist = []

    for point in latlong:
        x, y = tmb.project(*point)
        xlist.append(x)
        ylist.append(y)

    ax.plot(xlist, ylist, color=mdo_light_blue, linewidth=6)

    if plotExit:
        ex = airport.findBetterExit(flightDetails, departure)
        coords = airport.exitLocations[ex][:]
        x1, y1 = tmb.project(*(coords[0], coords[3]))
        x2, y2 = tmb.project(*(coords[1], coords[3]))
        x3, y3 = tmb.project(*(coords[1], coords[2]))
        x4, y4 = tmb.project(*(coords[0], coords[2]))

        x = [x1, x2, x3, x4, x1]
        y = [y1, y2, y3, y4, y1]

        ax.plot(x, y, color="black", linewidth=5)

    if figTitle == "default":
        plt.title(flightID, fontsize=30)
    elif figTitle is None:
        pass
    else:
        plt.title(figTitle, fontsize=30)

    callsign = flightDetails["identification"]["callsign"]

    if showPlot:
        plt.show()
    else:
        path = join(dirname(__file__), outFolder)

        if fileName is None:
            plt.savefig(f"{path}/{callsign}.png", bbox_inches="tight", dpi=200)
        else:
            plt.savefig(f"{path}/{fileName}.png", bbox_inches="tight", dpi=200)


def plotMultipleTrails(airport, flightFolderList, outDirPath, onlyLast=False, justCreateMovie=False, alpha=0.002, show=False):
    """
    Plot multiple trails on one airport map

    Parameters
    ----------
    airport : airport class
        airport to pull from
    flightFolderList : list of strings
        Folders containing arrival and departure data
    outFolder : string
        folder to save output files in
    onlyLast : bool, optional
        whether to only create the last image, by default False
    justCreateMovie : bool, optional
        whether to just create the movie from the images, by default False
    alpha : double, optional
        transparancy for trails - use larger values when plotting fewer for visibility and smaller values when plotting more for contrast
    show : bool, optional
        show the figure instead of saving it. this is only when onlyLast is True because otherwise there could be many figures.
    """

    # just make the movie from the existing images and exit
    if justCreateMovie:
        subprocess.run(
            [
                "ffmpeg",
                "-framerate",
                "30",
                "-pattern_type",
                "glob",
                "-i",
                join(outDirPath, "*.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # handle divisble by 2 errors
                join(outDirPath, "path_movie.mp4"),
            ]
        )
        exit()

    makedirs(outDirPath, exist_ok=True)

    plotCount = 0

    # set up the figure and only plot stuff on that one figure - do not create multiple figures to save time
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

    ax.fill_between([0, 1], [0, 0], [1, 1], transform=ax.transAxes, color="white", alpha=0.5)

    # count how many files we have, we need this if we want to only save the last image
    nFiles = 0
    for folder in flightFolderList:
        cases = ["arrivals", "departures"]
        for case in cases:
            casePath = join(folder, case)
            files = [f for f in listdir(casePath) if isfile(join(casePath, f))]
            nFiles += len(files)

    # go through multiple folders, assume folder structure of
    # --some name
    # ----arrivals
    # ----departures
    for folder in flightFolderList:
        cases = ["arrivals", "departures"]

        for case in cases:
            casePath = join(folder, case)
            files = [f for f in listdir(casePath) if isfile(join(casePath, f))]

            # open every flight file and get the data out
            for file in files:
                fullName = join(casePath, file)
                flightDetails = openPickle(fullName)

                # if flightDetails is None then openPickle ran into an issue, skip this file
                if flightDetails is not None:
                    latlong, _, _ = extractTrail(flightDetails)
                    xlist = []
                    ylist = []

                    for point in latlong:
                        x, y = tmb.project(*point)
                        xlist.append(x)
                        ylist.append(y)

                    # plot the trail on top of the existing stuff
                    ax.plot(xlist, ylist, color=mdo_light_blue, alpha=alpha, linewidth=6)

                    # path = join(dirname(__file__), outFolder)

                    # save it as a new file
                    if not onlyLast:
                        if plotCount % 67 == 0:
                            plt.savefig(f"{outDirPath}/{plotCount:06d}.png", bbox_inches="tight", dpi=200)

                    # we might only want the last file to save time
                    if onlyLast:
                        if plotCount == nFiles - 1:
                            if show:
                                plt.show()
                            else:
                                plt.savefig(f"{outDirPath}/{plotCount:06d}.png", bbox_inches="tight", dpi=200)

                plotCount += 1


def createTrailGIF(airport, flightFolderList, imageFolder, departures, justCreateGIF=False, plotTitle=None):

    outDirPath = join(dirname(__file__), imageFolder)
    makedirs(outDirPath, exist_ok=True)

    if departures:
        depPath = join(outDirPath, "dep")
        makedirs(depPath, exist_ok=True)
    else:
        arrPath = join(outDirPath, "arr")
        makedirs(arrPath, exist_ok=True)

    if departures:
        caseName = "dep"
    else:
        caseName = "arr"

    if justCreateGIF:
        subprocess.run(
            [
                "ffmpeg",
                "-framerate",
                "60",
                "-pattern_type",
                "glob",
                "-i",
                join(outDirPath, caseName, "*.png"),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                "crop=trunc(iw/2)*2:trunc(ih/2)*2",  # handle divisble by 2 errors
                join(outDirPath, caseName, "path_movie.mp4"),
            ]
        )

    else:
        for folder in flightFolderList:
            if departures:
                fullPath = join(folder, "departures")
            else:
                fullPath = join(folder, "arrivals")

            # fullPath = join(dirname(__file__), folder)
            files = [f for f in listdir(fullPath) if isfile(join(fullPath, f))]

            for file in files:
                fullName = join(fullPath, file)
                flightDetails = openPickle(fullName)

                if flightDetails is not None:
                    plotMap(flightDetails, airport, departures, imageFolder, figTitle=plotTitle)


def plotExitBoxes(airport, plotAll=False, exitList=None, show=False):
    """
    Plot the exits or a subset on top of an airport map. Useful for debugging lat/log

    Parameters
    ----------
    airport : airport class
        airport to grab exits for
    plotAll : bool, optional
        whether to plot all the exits, by default False
    exitList : list of ints, optional
        Subset of exits if you don't want all of them to be plotted, by default None
    show : bool, optional
        whether to show the plot or save the figure, by default False
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
        plt.savefig(f"figures/bounds_{airport.code}.pdf", dpi=600, bbox_inches="tight")


def plotExitLabels(airport, show=False):
    """
    Plot the labels for runway exits on top of the map

    Parameters
    ----------
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
    _, ax = plt.subplots(figsize=(16, 9))
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    plotter = tmb.Plotter(extent, t, width=1200)
    plotter.plot(ax, t)

    for i, ex in enumerate(airport.exitLocations):
        long = np.average((ex[0], ex[1]))
        lat = np.average((ex[2], ex[3]))

        x, y = tmb.project(*(long, lat))

        ax.plot(x, y, color="black", linewidth=0.75)
        plt.text(x, y, str(i), fontsize=5, ha="center", va="center")

    plt.title(f"Taxiway exit/entrance labels for {airport.code}")

    if show:
        plt.show()
    else:
        plt.savefig(f"figures/labels_{airport.code}.pdf", dpi=600, bbox_inches="tight")


def plotFrequenciesColor(airport, exitPercent, departures=True, show=False, date=None, title=None, filename=None):
    """
    Plot a heat map (really just some dots representing frequency) on an airport map
    Normalize the frequency at which the aircraft use the exits so the full range of the colormap is used
    This seemed easier than adjusting the colorbar bounds

    Parameters
    ----------
    airport : Airport class
        airport being studied for this case
    exitPercent : list of doubles
        Percentages of aircraft using each exit/entrance
    departures : bool, optional
        whether this case is departures or arrivals, by default True
    show : bool, optional
        whether to show the plot or save to a file, by default False
    date : string, optional
        date this data is from, by default None
    title : string, optional
        override the auto generated figure title, by default None
    filename : string, optional
        override the auto generated filename, by default None
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

    ax.fill_between([0, 1], [0, 0], [1, 1], transform=ax.transAxes, color="white", alpha=0.3)

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

    if title is not None:
        plt.title(title)
    elif date is not None:
        plt.title(f"{key2} frequencies for {airport.code} {key1} on {date}")
    else:
        plt.title(f"{key2} frequencies for {airport.code} {key1}")

    plt.scatter(x=allX, y=allY, c=normalizedPercent, cmap="plasma", s=55)
    plt.colorbar(label=f"{key2} use frequency", orientation="vertical", shrink=0.6)

    if show:
        plt.show()
    else:
        if filename is not None:
            plt.savefig(f"figures/{filename}.png", dpi=200, bbox_inches="tight")
        elif date is not None:
            plt.savefig(f"figures/color_{key2}_freq_{airport.code}_{key1}_{date}.png", dpi=600, bbox_inches="tight")
        else:
            plt.savefig(f"figures/color_{key2}_freq_{airport.code}_{key1}.png", dpi=600, bbox_inches="tight")


def plotFrequenciesSize(airport, exitPercent, departures=True, show=False, date=None, title=None, filename=None):
    """
    Plot a heat map (really just some dots representing frequency) on an airport map

    Parameters
    ----------
    airport : Airport class
        airport being studied for this case
    exitPercent : list of doubles
        Percentages of aircraft using each exit/entrance
    departures : bool, optional
        whether this case is departures or arrivals, by default True
    show : bool, optional
        whether to show the plot or save to a file, by default False
    date : string, optional
        date this data is from, by default None
    title : string, optional
        override the auto generated figure title, by default None
    filename : string, optional
        override the auto generated filename, by default None
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

    ax.fill_between([0, 1], [0, 0], [1, 1], transform=ax.transAxes, color="white", alpha=0.3)

    for i, ex in enumerate(airport.exitLocations):
        long = np.average((ex[0], ex[1]))
        lat = np.average((ex[2], ex[3]))

        x, y = tmb.project(*(long, lat))

        if exitPercent[i] == 0:
            size = 0
        else:
            size = 40 * np.log(exitPercent[i]) / np.log(100)

        ax.plot(x, y, marker="o", markersize=size, color=mdo_light_blue, alpha=0.7)
        # plt.text(x, y, str(i), fontsize=4, ha="center", va="center")
        plt.text(x, y, f"{exitPercent[i]:.1f}", fontsize=4, ha="center", va="center")

    if departures:
        key1 = "departures"
        key2 = "Entrance"
    else:
        key1 = "arrivals"
        key2 = "Exit"

    if title is not None:
        plt.title(title)
    elif date is not None:
        plt.title(f"{key2} frequencies for {airport.code} {key1} on {date}")
    else:
        plt.title(f"{key2} frequencies for {airport.code} {key1}")

    if show:
        plt.show()
    else:
        if filename is not None:
            plt.savefig(f"figures/{filename}.png", dpi=200, bbox_inches="tight")
        elif date is not None:
            plt.savefig(f"figures/{key2}_freq_{airport.code}_{key1}_{date}.png", dpi=200, bbox_inches="tight")
        else:
            plt.savefig(f"figures/{key2}_freq_{airport.code}_{key1}.png", dpi=200, bbox_inches="tight")


def plotAllInFolder(path, airport, departures, plotExit=False):
    """
    Plot all the flight trails in a folder to debug

    Parameters
    ----------
    path : string
        path to folder
    airport : airport class
        airport used for those files
    departures : bool
        whether this is a departures case
    plotExit : bool, optional
        whether to plot the exit that has been detected, by default False
    """
    departureFiles = [f for f in listdir(path) if isfile(join(path, f))]

    for fileName in departureFiles:
        fullName = join(path, fileName)

        flightDetails = openPickle(fullName)
        plotMap(flightDetails, airport, departures, plotExit=plotExit, show=True)
