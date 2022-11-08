from dataCollection.actualData.catchFlights import catchArrivals
from dataCollection.airports.SanDiego import SanDiego
import os

outFolder = "11_7_night"
os.makedirs(os.path.join(os.path.dirname(__file__), outFolder), exist_ok=True)
os.makedirs(os.path.join(outFolder, "arrivals"), exist_ok=True)
os.makedirs(os.path.join(outFolder, "debug"), exist_ok=True)
airport = SanDiego()
catchArrivals(airport, 60 * 60 * 12, outFolder)    # start nov 7 9:30 pm
