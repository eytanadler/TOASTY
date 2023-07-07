
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Chicago import Chicago
from dataCollection.actualData.countExits import countTotals 
from dataCollection.plotting.plotUtils import openPickle
from dataCollection.plotting.plotting import (
    plotMap,
    plotMultipleTrails,
    plotExitBoxes,
)
import os

SAN = SanDiego()
ORD = Chicago()

allSAN = os.path.join(os.path.dirname(__file__), "sampleData/SAN")
departuresSAN = f"{allSAN}/departures"
arrivalsSAN = f"{allSAN}/arrivals"
departuresORD = os.path.join(os.path.dirname(__file__), "sampleData/ORD/departures")
arrivalsORD = os.path.join(os.path.dirname(__file__), "sampleData/ORD/arrivals")

# get information for one saved file
file = f"{arrivalsSAN}/AA1939_DFW_to_SAN"
flight = openPickle(file)

# print everything to see what the data looks like
# except the trail - it takes up so much space
for key, val in flight.items():
    if key == "trail":
        pass
    else:
        if isinstance(val, dict):
            for subkey, subval in val.items():
                if subkey == "trail":
                    print("trail 1")
                    pass
                else:
                    if isinstance(subval, dict):
                        for subsubkey, subsubval in subval.items():
                            if subsubkey == "trail":
                                print("trail 2")
                                pass
                            else:
                                print(f"{subsubkey}: {subsubval}")
                    else:
                        print(f"{subkey}: {subval}")
        else:
            print(f"{key}: {val}\n")

# test out plotting functions
plotMap(flight, SAN, departure=False, showPlot=True, figTitle="SAN Arrival")
plotExitBoxes(SAN, plotAll=True, show=True)

# this calls the data processing and can plot the frequency map if showPlot=True
countTotals([departuresSAN], SAN, departures=True, plotSize=True, showPlot=True, printTable=True, title="SAN Departures")
countTotals([arrivalsSAN], SAN, departures=False, plotSize=True, showPlot=True, printTable=True, title="SAN Arrivals")
countTotals([departuresORD], ORD, departures=True, plotSize=True, showPlot=True, printTable=True, title="ORD Departures")
countTotals([arrivalsORD], ORD, departures=False, plotSize=True, showPlot=True, printTable=True, title="ORD Arrivals")

# plot all the approach paths on top of each other - this can make a gif of all of them or just show one image to test it
plotMultipleTrails(SAN, [allSAN], os.path.join(os.path.dirname(__file__), "gif"), onlyLast=True, alpha=0.2, show=True)
