from os.path import join, dirname
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Detroit import Detroit
from dataCollection.plotting.makeItPretty import plotAllInFolder, openPickle, plotMap, plotExitBoxes

# departurePath = join(dirname(__file__), "../actualData/departures")
# airport = SanDiego()
# plotAllInFolder(departurePath, airport)

# f = "../actualData/departures/WN2777_SAN_to_LAS"
# file = openPickle(f)
# plotMap(file, airport, True)

# arrivalPath = join(dirname(__file__), "../actualData/arrivals")
# airport = SanDiego()
# plotAllInFolder(arrivalPath, airport)

airport = Detroit()
exitList = [0, 1, 2, 3, 4, 5, 6, 7]
plotExitBoxes(exitList, airport, True)
