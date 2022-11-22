import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname
from dataCollection.plotting.makeItPretty import (
    openPickle,
    extractTrail,
    plotMap,
    plotFrequenciesColor,
    plotFrequenciesSize,
)


def countTotals(
    folderPath,
    airport,
    departures=True,
    plotColor=False,
    plotSize=False,
    showPlot=False,
    plotString=None,
    printTable=False,
    debug=False,
):
    """
    _summary_

    Parameters
    ----------
    folderPath : _type_
        _description_
    airport : _type_
        _description_
    debug : bool, optional
        _description_, by default False

    Returns
    -------
    _type_
        _description_
    """
    fullPath = join(dirname(__file__), folderPath)
    departureFiles = [f for f in listdir(fullPath) if isfile(join(fullPath, f))]
    exitCount = np.zeros(airport.nExits + 1)
    exitPercent = np.zeros(airport.nExits + 1)

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
        plotFrequenciesColor(
            airport, exitPercent[0 : airport.nExits], exitCount[0 : airport.nExits], plotString, departures, showPlot
        )

    if plotSize:
        plotFrequenciesSize(
            airport, exitPercent[0 : airport.nExits], exitCount[0 : airport.nExits], plotString, departures, showPlot
        )

    if printTable:
        tabulateExits(departures, airport, exitCount, exitPercent)

    return exitCount, exitPercent


def tabulateExits(departures, airport, exitCount, exitPercent):
    """
    _summary_

    Parameters
    ----------
    category : _type_
        _description_
    airport : _type_
        _description_
    exitCount : _type_
        _description_
    """
    table = []

    if departures:
        category = "Departures"
    else:
        category = "Arrivals"

    print(f"{category} totals for {airport.code}:")

    for i in range(airport.nExits):
        table.append([f"{i+1}", exitCount[i], exitPercent[i]])

    table.append(["Error", exitCount[-1], exitPercent[-1]])

    headers = ["Exit", "Flights using exit", "As % total"]
    print(tabulate(table, headers, floatfmt=(".0f", ".0f", ".2f")))
