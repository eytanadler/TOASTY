import numpy as np
from dataCollection.airports.Airport import Airport

class Detroit(Airport):
    # basic info
    code = "DTW"

    # runway info
    nRunways = 6

    # plotting info
    centerLoc = [-83.3624792, 42.2119291]
    longRange = 0.02
    latRange = 0.02
