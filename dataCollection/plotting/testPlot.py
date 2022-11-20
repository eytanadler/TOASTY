from os.path import join, dirname
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Detroit import Detroit
from dataCollection.plotting.makeItPretty import plotAllInFolder, openPickle, plotMap, plotExitBoxes, plotHeatMap

# departurePath = join(dirname(__file__), "../actualData/departures")
# airport = SanDiego()
# plotAllInFolder(departurePath, airport)

# f = "../actualData/departures/WN2777_SAN_to_LAS"
# file = openPickle(f)
# plotMap(file, airport, True)

# arrivalPath = join(dirname(__file__), "../actualData/arrivals")
# airport = SanDiego()
# plotAllInFolder(arrivalPath, airport)

show = False
airport = SanDiego()
exitPercent = [0, 0, 0, 0, 0, 0.0769, 0.3462, 0.5769, 0, 0, 0, 0, 0, 0, 0]
plotHeatMap(airport, exitPercent, "11-7", False, show)

exitPercent = [88.46, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 9.62, 0.00, 0.00, 0.00, 0.00, 0.00]
plotHeatMap(airport, exitPercent, "11-7", True, show)

exitPercent = [0.00, 0.00, 4.55, 0.91, 0.91, 5.00, 62.73, 25.91, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
plotHeatMap(airport, exitPercent, "11-8", False, show)

exitPercent = [0.6308, 0, 0.0036, 0.0108, 0.0072, 0.0, 0.0, 0.0, 0.2545, 0.086, 0.0036, 0, 0, 0, 0]
plotHeatMap(airport, exitPercent, "11-8", True, show)


# exitList = [0, 1, 2, 3, 4, 5, 6, 7]
# plotExitBoxes(airport, plotAll=True, show=True)
# airport = SanDiego()
# exitList = [0, 1, 2, 3, 4, 5, 6, 7, 8]
# plotExitBoxes(exitList, airport, True)

# airport = Detroit()

# file = "AA2377_DTW_to_DFW"
# path = join(dirname(__file__), "../actualData/11_8_night_2/")
# departurePath = join(path, "departures")
# arrivalPath = join(path, "arrivals")

# filePath = join(departurePath, file)
# flightDetails = openPickle(filePath)

# # plotMap(flightDetails, airport, True)

# plotAllInFolder(departurePath, airport)
