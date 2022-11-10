import os
from dataCollection.actualData.catchFlights import catchDepartures
from dataCollection.airports.Detroit import Detroit

# from dataCollection.airports.SanDiego import SanDiego

outFolder = "11_8_night_2"
os.makedirs(os.path.join(os.path.dirname(__file__), outFolder), exist_ok=True)
os.makedirs(os.path.join(outFolder, "departures"), exist_ok=True)
os.makedirs(os.path.join(outFolder, "debug"), exist_ok=True)
airport = Detroit()
catchDepartures(airport, 60 * 60 * 24, outFolder)  # start nov 8 6 pm
