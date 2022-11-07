from os.path import join, dirname
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.plotting.makeItPretty import plotAllInFolder, openPickle, plotMap

departurePath = join(dirname(__file__), "../actualData/departures")
airport = SanDiego()
plotAllInFolder(departurePath, airport)

f = "../actualData/departures/WN2777_SAN_to_LAS"
file = openPickle(f)
plotMap(file, airport, True)

arrivalPath = join(dirname(__file__), "../actualData/arrivals")
airport = SanDiego()
plotAllInFolder(arrivalPath, airport)
