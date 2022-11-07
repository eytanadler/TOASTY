from dataCollection.actualData.countExits import countTotals, tabulateExits
from dataCollection.actualData.catchFlights import catchArrivals, catchDepartures
from dataCollection.airports.SanDiego import SanDiego


def testCatch():
    airport = SanDiego()
    catchDepartures(airport, 3600)
    catchArrivals(airport, 1000)

def testExits():
    airport = SanDiego()
    exitCountA = countTotals("arrivals", airport)
    exitCountD = countTotals("departures", airport)
    tabulateExits(airport, exitCountA)
    tabulateExits(airport, exitCountD)


testExits()
