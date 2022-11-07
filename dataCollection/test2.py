import numpy as np
from tabulate import tabulate
from os import listdir
from os.path import isfile, join, dirname

from SanDiego import SanDiego
from plotting.makeItPretty import openPickle, extractTrail, plotMap

airport = SanDiego()

path = join(dirname(__file__), "actualData/departures")
departureFiles = [f for f in listdir(path) if isfile(join(path, f))]

exitCount = np.zeros(airport.nExits)

for file in departureFiles:
    fullName = join(path, file)
    flightDetails = openPickle(fullName)
    trail = extractTrail(flightDetails)

    exitCode = airport.findExitForTrail(trail)
    if exitCode is None:
        plotMap(flightDetails, airport, show=True)
        print("yikes", file)
    elif exitCode != 8:
        print(f"{file} registered as {exitCode+1}")
        plotMap(flightDetails, airport, show=True)
    if exitCode is not None:
        exitCount[exitCode] += 1

    # print(f"{file} used {exitCode}")

print(f"Totals for {airport.code}:")
table = []
for i in range(airport.nExits):
    table.append([f"{i+1}", exitCount[i]])
print(tabulate(table))
