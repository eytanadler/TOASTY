import numpy as np
from dataCollection.airports.Airport import Airport


class Detroit(Airport):
    # basic info
    code = "DTW"
    atol = 1  # TODO fix this

    # runway info
    nRunways = 6

    nExits = 32958734698734698
    exitLocations = np.array(((-83.383795, -83.382100, 42.201447, 42.202170),   # A1
                              (-83.382947, -83.381339, 42.202639, 42.203267),   # A2
                              (-83.380913, -83.378037, 42.205138, 42.207904),   # A3
                              (-83.378187, -83.375204, 42.209056, 42.211488),   # A4
                              (-83.373401, -83.369998, 42.215811, 42.218442),   # A7
                              (-83.370276, -83.367383, 42.219968, 42.222209),   # A8
                              (-83.367012, -83.365323, 42.224403, 42.224973),   # A9
                              (-83.366125, -83.364407, 42.225561, 42.226070),   # A10
                              ))

    # plotting info
    centerLoc = [-83.358, 42.214]
    longRange = 0.035
    latRange = 0.023
