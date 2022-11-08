from dataCollection.actualData.catchFlights import catchDepartures
from dataCollection.airports.SanDiego import SanDiego
import os

outFolder = "11_7_night"
os.makedirs(os.path.join(os.path.dirname(__file__), outFolder), exist_ok=True)
os.makedirs(os.path.join(outFolder, "departures"), exist_ok=True)
os.makedirs(os.path.join(outFolder, "debug"), exist_ok=True)
airport = SanDiego()
catchDepartures(airport, 60 * 60 * 24, outFolder)   # start nov 7 9:30 pm
