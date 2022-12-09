from dataCollection.actualData.countExits import countTotals
from dataCollection.actualData.catchFlights import catchArrivals, catchDepartures
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Chicago import Chicago
import os


color = False
size = True
show = False
debug = False
table = True


def testCatch():
    airport = Chicago()
    # catchArrivals(airport, 1000, os.path.join(os.path.dirname(__file__), "test"))
    catchDepartures(airport, 3600, os.path.join(os.path.dirname(__file__), "test"))


def testExitsSAN():
    airport = SanDiego()

    countTotals(
        folderList=["results/SAN_11_29/arrivals"],
        airport=airport,
        departures=False,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        printTable=table,
        debug=debug,
        date="11-29",
    )
    print()
    countTotals(
        folderList=["results/SAN_11_29/departures"],
        airport=airport,
        departures=True,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        printTable=table,
        debug=debug,
        date="11-29",
    )


def testExitsORD():
    airport = Chicago()

    countTotals(
        folderList=["results/ORD_11_29/arrivals"],
        airport=airport,
        departures=False,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        printTable=table,
        debug=debug,
        date="11-29",
    )
    print()
    countTotals(
        folderList=["results/ORD_11_29/departures"],
        airport=airport,
        departures=True,
        plotColor=color,
        plotSize=size,
        showPlot=show,
        printTable=table,
        debug=debug,
        date="11-29",
    )


# testExitsSAN()
# testExitsORD()
testCatch()
