from dataCollection.actualData.catchFlights import catchArrivals
from dataCollection.airports.SanDiego import SanDiego

airport = SanDiego()
catchArrivals(airport, 60 * 60 * 24)
