from dataCollection.actualData.catchFlights import catchDepartures
from dataCollection.airports.SanDiego import SanDiego

airport = SanDiego()
catchDepartures(airport, 60 * 60 * 24)
