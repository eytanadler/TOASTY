import numpy as np
from dataCollection.airports.Airport import Airport


class Detroit(Airport):
    # basic info
    code = "DTW"
    atol = 1  # TODO fix this

    # runway info
    nRunways = 6

    # plotting info
    centerLoc = [-83.358, 42.214]
    longRange = 0.035
    latRange = 0.023
