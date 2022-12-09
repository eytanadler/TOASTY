from os import makedirs
from os.path import join, dirname
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Chicago import Chicago
from dataCollection.plotting.plotting import (
    plotAllInFolder,
    openPickle,
    plotMap,
    plotExitBoxes,
    plotFrequenciesColor,
    plotFrequenciesSize,
    extractTrail,
    createTrailGIF,
    plotMultipleTrails,
)

# departurePath = join(dirname(__file__), "../actualData/departures")
# airport = SanDiego()
# plotAllInFolder(departurePath, airport)

# f = "../actualData/departures/WN2777_SAN_to_LAS"
# file = openPickle(f)
# plotMap(file, airport, True)

# arrivalPath = join(dirname(__file__), "../actualData/arrivals")
# airport = SanDiego()
# plotAllInFolder(arrivalPath, airport)

# show = True
# airport = SanDiego()
# exitPercent = [0, 0, 0, 0, 0, 0.0769, 0.3462, 0.5769, 0, 0, 0, 0, 0, 0, 0]
# # plotFrequenciesColor(airport, exitPercent, "11-7", False, show)
# plotFrequenciesSize(airport, exitPercent, "11-7", False, show)

# exitPercent = [88.46, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 9.62, 0.00, 0.00, 0.00, 0.00, 0.00]
# # plotFrequenciesColor(airport, exitPercent, "11-7", True, show)
# plotFrequenciesSize(airport, exitPercent, "11-7", True, show)

# exitPercent = [0.00, 0.00, 4.55, 0.91, 0.91, 5.00, 62.73, 25.91, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
# # plotFrequenciesColor(airport, exitPercent, "11-8", False, show)
# plotFrequenciesSize(airport, exitPercent, "11-8", False, show)

# exitPercent = [0.6308, 0, 0.0036, 0.0108, 0.0072, 0.0, 0.0, 0.0, 0.2545, 0.086, 0.0036, 0, 0, 0, 0]
# # plotFrequenciesColor(airport, exitPercent, "11-8", True, show)
# plotFrequenciesSize(airport, exitPercent, "11-8", True, show)


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


# airport = Chicago()
airport = SanDiego()
outFolder = "allImagesSAN"

base = "../actualData/results"
fullBase = join(dirname(__file__), base)
# folders = [
#     "ORD_11_22",
#     "ORD_11_23",
#     "ORD_11_25",
#     "ORD_11_27",
#     "ORD_11_28",
#     "ORD_11_29",
#     "ORD_11_30",
#     "ORD_12_01",
#     "ORD_12_02",
#     "ORD_12_03",
#     "ORD_12_06",
# ]
folders = [
    "SAN_11_22",
    "SAN_11_23",
    "SAN_11_25",
    "SAN_11_27",
    "SAN_11_28",
    "SAN_11_29",
    "SAN_11_30",
    "SAN_12_01",
    "SAN_12_02",
    "SAN_12_03",
]

for i, folder in enumerate(folders):
    folders[i] = join(fullBase, folder)

plotMultipleTrails(airport, folders, outFolder, onlyLast=False, justCreateMovie=False)

# base = "../actualData/results"
# fullBase = join(dirname(__file__), base)
# folders = ["ORD_11_22", "ORD_11_23"]

# for i, folder in enumerate(folders):
#     folders[i] = join(fullBase, folder)t

# plotMultipleTrails(airport, folders, outFolder, departures=False, justCreateGIF=True)


# plotExitBoxes(airport, plotAll=True, show=False)
# path = join(dirname(__file__), "../actualData/11_21_new_new/")
# arrivalPath = join(path, "arrivals")
# plotAllInFolder(arrivalPath, airport, False, plotExit=True)
# # print(extractTrail(flightDetails))
# # plotMap(flightDetails, airport, True)

# # plotExitBoxes(airport, plotAll=True, exitList=None, show=False)

# file = "BR633_ORD_to_TPE"
# path = join(dirname(__file__), "../actualData/11_21_new_new_new/")
# arrivalPath = join(path, "departures")
# filePath = join(arrivalPath, file)
# flightDetails = openPickle(filePath)
# plotMap(flightDetails, airport, departure=False, plotExit=True, show=True)
