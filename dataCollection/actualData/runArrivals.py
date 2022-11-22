import os
from dataCollection.actualData.catchFlights import catchArrivals
from dataCollection.airports.Chicago import Chicago

# from dataCollection.airports.SanDiego import SanDiego

outFolder = "11_21_real"
os.makedirs(os.path.join(os.path.dirname(__file__), outFolder), exist_ok=True)
os.makedirs(os.path.join(outFolder, "arrivals"), exist_ok=True)
os.makedirs(os.path.join(outFolder, "debug"), exist_ok=True)
airport = Chicago()
catchArrivals(airport, 60 * 60 * 26, outFolder)  # start nov 21 2:30 pm est
