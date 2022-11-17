import numpy as np
from dataCollection.airports.Airport import Airport


class SanDiego(Airport):
    # basic info
    code = "SAN"
    atol = 0.1

    # runway info
    nRunways = 1
    exitLocations = np.array(
        (
            # real exits
            (-117.177617, -117.175235, 32.729318, 32.729787),  # B1
            (-117.181531, -117.180608, 32.730730, 32.730974),  # B?
            (-117.185061, -117.184417, 32.731588, 32.731904),  # B4
            (-117.188870, -117.188205, 32.732554, 32.732843),  # B5
            (-117.191916, -117.191241, 32.733303, 32.733574),  # B6
            (-117.195594, -117.194394, 32.734134, 32.734332),  # B7
            (-117.199045, -117.197898, 32.734973, 32.735162),  # B8
            (-117.202463, -117.201218, 32.735797, 32.736023),  # B9
            (-117.204457, -117.203686, 32.736104, 32.736853),  # B10
            # cargo/GA area
            (-117.175991, -117.175154, 32.730561, 32.731398),  # C1
            (-117.177143, -117.176413, 32.730885, 32.731147),  # C2
            (-117.182337, -117.181650, 32.732194, 32.732505),  # C3
            (-117.184657, -117.184088, 32.732736, 32.733124),  # C4
            (-117.188519, -117.187875, 32.733684, 32.734009),  # C5
            (-117.191190, -117.190332, 32.734370, 32.734650),  # C6
        )
    )
    nExits = len(exitLocations)

    # plotting info
    centerLoc = [-117.1916, 32.734]
    longRange = 0.018
    latRange = 0.007
