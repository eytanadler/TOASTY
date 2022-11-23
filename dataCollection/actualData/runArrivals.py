import os
from dataCollection.actualData.catchFlights import catchArrivals
from dataCollection.airports.Chicago import Chicago
from dataCollection.airports.SanDiego import SanDiego


def catchSAN():
    outFolder = "SAN_11_22"
    outDirPath = os.path.join(os.path.dirname(__file__), outFolder)
    os.makedirs(outDirPath, exist_ok=True)
    os.makedirs(os.path.join(outDirPath, "arrivals"), exist_ok=True)
    os.makedirs(os.path.join(outDirPath, "debug"), exist_ok=True)
    airport = SanDiego()
    catchArrivals(airport, 60 * 60 * 30, outFolder)  # start nov 22 4 pm est


def catchORD():
    outFolder = "ORD_11_22"
    outDirPath = os.path.join(os.path.dirname(__file__), outFolder)
    os.makedirs(outDirPath, exist_ok=True)
    os.makedirs(os.path.join(outDirPath, "arrivals"), exist_ok=True)
    os.makedirs(os.path.join(outDirPath, "debug"), exist_ok=True)
    airport = Chicago()
    catchArrivals(airport, 60 * 60 * 30, outFolder)  # start nov 22 7 pm est


# catchSAN()
catchORD()
