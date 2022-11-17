import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname
from dataCollection.plotting.makeItPretty import openPickle, extractTrail, plotMap


def countTotals(folderPath, airport, debug=False):
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

    for file in departureFiles:
        fullName = join(fullPath, file)
        flightDetails = openPickle(fullName)

        if flightDetails is not None:
            trail = extractTrail(flightDetails)

            exitCode = airport.findExitForTrail(trail)

            if debug:
                if exitCode is None:
                    plotMap(flightDetails, airport, show=True)
                    print("yikes", file)

            if exitCode is not None:
                exitCount[exitCode] += 1
            else:
                exitCount[-1] += 1

    return exitCount


def tabulateExits(category, airport, exitCount):
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
    totalMovements = np.sum(exitCount)
    table = []

    print(f"{category} totals for {airport.code}:")

    for i in range(airport.nExits):
        ex = exitCount[i]
        percentOfMove = ex / totalMovements * 100

        table.append([f"{i+1}", ex, percentOfMove])

    table.append(["Error", exitCount[-1], exitCount[-1] / totalMovements * 100])

    headers = ["Exit", "Flights using exit", "As % total"]
    print(tabulate(table, headers, floatfmt=(".0f", ".0f", ".2f")))
