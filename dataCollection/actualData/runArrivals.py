import os
from dataCollection.actualData.catchFlights import catchArrivals
from dataCollection.airports.Detroit import Detroit

# from dataCollection.airports.SanDiego import SanDiego

outFolder = "11_8_night"
os.makedirs(os.path.join(os.path.dirname(__file__), outFolder), exist_ok=True)
os.makedirs(os.path.join(outFolder, "arrivals"), exist_ok=True)
os.makedirs(os.path.join(outFolder, "debug"), exist_ok=True)
airport = Detroit()
catchArrivals(airport, 60 * 60 * 12, outFolder)  # start nov 8 6 pm
