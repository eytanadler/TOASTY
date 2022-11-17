from dataCollection.actualData.countExits import countTotals, tabulateExits
from dataCollection.actualData.catchFlights import catchArrivals, catchDepartures
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Detroit import Detroit


def testCatch():
    airport = SanDiego()
    catchDepartures(airport, 3600)
    catchArrivals(airport, 1000)


def testExitsDTW():
    airport = Detroit()

    exitCountA = countTotals("11_10_night_DTW/arrivals", airport)
    exitCountD = countTotals("11_10_night_DTW/departures", airport, debug=True)

    tabulateExits("Arrivals", airport, exitCountA)
    print()
    tabulateExits("Departures", airport, exitCountD)


def testExitsSAN():
    airport = SanDiego()

    exitCountA = countTotals("11_7_SAN/arrivals", airport)
    exitCountD = countTotals("11_7_SAN/departures", airport, debug=True)

    tabulateExits("Arrivals", airport, exitCountA)
    print()
    tabulateExits("Departures", airport, exitCountD)


testExitsSAN()
# testExitsDTW()
