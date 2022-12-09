import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname
from dataCollection.plotting.plotting import openPickle, plotMap, plotFrequenciesColor, plotFrequenciesSize


def countTotals(
    folderList,
    airport,
    departures=True,
    plotColor=False,
    plotSize=False,
    showPlot=False,
    printTable=False,
    debug=False,
    date=None,
    title=None,
    filename=None,
):
    """
    Count the number of aircraft using a given runway exit/entrance for files in a folder/set of folders

    Parameters
    ----------
    folderList : list of strings
        Set of folders to look in for aircraft data files
    airport : airport class
        Airport used here
    departures : bool, optional
        Whether this case is departures or arrivals, by default True
    plotColor : bool, optional
        Whether to plot a heat map by color, by default False
    plotSize : bool, optional
        Whether to plot a heat map by size, by default False
    showPlot : bool, optional
        Whether to show the map or save it, by default False
    printTable : bool, optional
        Whether to print the final data or not, by default False
    debug : bool, optional
        Send the counting into debug mode, by default False
    date : string, optional
        Date string to use as a figure title, by default None
    title : string, optional
        Custom title to override, by default None
    filename : string, optional
        Custome filename to override, by default None

    Returns
    -------
    list, list
        lists of exis used by counts and by percentage
    """
    exitCount = np.zeros(airport.nExits + 1)
    exitPercent = np.zeros(airport.nExits + 1)

    for folder in folderList:
        fullPath = join(dirname(__file__), folder)
        departureFiles = [f for f in listdir(fullPath) if isfile(join(fullPath, f))]

        for file in departureFiles:
            fullName = join(fullPath, file)
            flightDetails = openPickle(fullName)

            if flightDetails is not None:
                exitCode = airport.findBetterExit(flightDetails, isDeparture=departures)

                if debug:
                    if exitCode is None:
                        plotMap(flightDetails, airport, show=True)
                        print("yikes", file)

                if exitCode is not None:
                    exitCount[exitCode] += 1
                else:
                    exitCount[-1] += 1

    totalMovements = np.sum(exitCount)
    for i in range(airport.nExits + 1):
        exitPercent[i] = exitCount[i] / totalMovements * 100

    if plotColor:
        plotFrequenciesColor(airport, exitPercent[0 : airport.nExits], departures, showPlot, date, title, filename)

    if plotSize:
        plotFrequenciesSize(airport, exitPercent[0 : airport.nExits], departures, showPlot, date, title, filename)

    if printTable:
        tabulateExits(departures, airport, exitCount, exitPercent, totalMovements)

    return exitCount, exitPercent


def tabulateExits(departures, airport, exitCount, exitPercent, totalMovements):
    """
    Print a nice table of the exits/entrances used given some data

    Parameters
    ----------
    departures : bool
        Whether this is departures or arrivals
    airport : airport class
        Which airport is used
    exitCount : list
        Raw number of exits/entrances used
    exitPercent : list
        Exits/entrances used as percent total
    totalMovements : int
        Total aircraft seen for this case so we don't have to recalculate here
    """
    table = []

    if departures:
        category = "Departures"
    else:
        category = "Arrivals"

    print(f"{category} totals for {airport.code}:")

    for i in range(airport.nExits):
        table.append([f"{i}", exitCount[i], exitPercent[i]])

    table.append(["Error", exitCount[-1], exitPercent[-1]])

    headers = ["Exit", "Flights using exit", "As % total"]
    print(tabulate(table, headers, floatfmt=(".0f", ".0f", ".2f")))
    print(f"{int(totalMovements)} flights in total")
