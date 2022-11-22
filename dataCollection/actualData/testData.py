from dataCollection.actualData.countExits import countTotals, tabulateExits
from dataCollection.actualData.catchFlights import catchArrivals, catchDepartures
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Detroit import Detroit
from dataCollection.airports.Chicago import Chicago


color = False
size = True
show = False
debug = False
table = True


def testCatch():
    airport = SanDiego()
    catchDepartures(airport, 3600)
    catchArrivals(airport, 1000)


def testExitsSAN():
    airport = SanDiego()

    exitCountA, exitPercentA = countTotals(
        folderPath="results/11_7_SAN/arrivals",
        airport=airport,
        departures=False,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        plotString="11-7",
        printTable=table,
        debug=debug,
    )
    print()
    exitCountD, exitPercentD = countTotals(
        folderPath="results/11_7_SAN/departures",
        airport=airport,
        departures=True,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        plotString="11-7",
        printTable=table,
        debug=debug,
    )


def testExitsORD():
    airport = Chicago()

    exitCountA, exitPercentA = countTotals(
        folderPath="11_21_real/arrivals",
        airport=airport,
        departures=False,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        plotString="11-21,2",
        printTable=table,
        debug=debug,
    )
    print()
    exitCountD, exitPercentD = countTotals(
        folderPath="11_21_real/departures",
        airport=airport,
        departures=True,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        plotString="11-21,2",
        printTable=table,
        debug=debug,
    )


# testExitsSAN()
# testExitsDTW()
testExitsORD()
