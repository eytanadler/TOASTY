import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname
from dataCollection.SanDiego import SanDiego
from dataCollection.plotting.makeItPretty import openPickle, extractTrail, plotMap

def countTotals(folderPath, airport):
    departureFiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]
    exitCount = np.zeros(airport.nExits)

    for file in departureFiles:
        fullName = join(folderPath, file)
        flightDetails = openPickle(fullName)
        trail = extractTrail(flightDetails)

        exitCode = airport.findExitForTrail(trail)
        # if exitCode is None:
        #     plotMap(flightDetails, airport, show=True)
        #     print("yikes", file)
        # elif exitCode != 8:
        #     print(f"{file} registered as {exitCode+1}")
        #     plotMap(flightDetails, airport, show=True)
        if exitCode is not None:
            exitCount[exitCode] += 1

    return exitCount


def tabulateExits(airport, exitCount):
    print(f"Totals for {airport.code}:")
    table = []
    for i in range(airport.nExits):
        table.append([f"{i+1}", exitCount[i]])
    print(tabulate(table))


airport = SanDiego()
exitCount = countTotals("arrivals", airport)
# exitCount = countTotals("departures", airport)
tabulateExits(airport, exitCount)
