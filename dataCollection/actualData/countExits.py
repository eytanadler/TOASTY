import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname
from dataCollection.plotting.makeItPretty import openPickle, extractTrail, plotMap


def countTotals(folderPath, airport, debug=False):
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
                # elif exitCode != 8:
                #     print(f"{file} registered as {exitCode+1}")
                #     plotMap(flightDetails, airport, show=True)

            if exitCode is not None:
                exitCount[exitCode] += 1
            else:
                exitCount[-1] += 1

    return exitCount


def tabulateExits(category, airport, exitCount):
    print(f"{category} totals for {airport.code}:")
    table = []
    for i in range(airport.nExits):
        table.append([f"{i+1}", exitCount[i]])
    table.append(["Error", exitCount[-1]])
    print(tabulate(table))
