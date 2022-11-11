import numpy as np
from dataCollection.airports.Airport import Airport


class Detroit(Airport):
    # basic info
    code = "DTW"
    atol = 1  # TODO fix this

    # runway info
    nRunways = 6

    nExits = 32958734698734698
    exitLocations = np.array((  # 4L/22R - A
                            (-83.383795, -83.382100, 42.201447, 42.202170),   # A1
                            (-83.382947, -83.381339, 42.202639, 42.203267),   # A2
                            (-83.380013, -83.379037, 42.205538, 42.207304),   # A3
                            (-83.377187, -83.376204, 42.209656, 42.211288),   # A4
                            (-83.372301, -83.370650, 42.216711, 42.218102),   # A7
                            (-83.369790, -83.368284, 42.220240, 42.221600),   # A8
                            (-83.367012, -83.365323, 42.224403, 42.224973),   # A9
                            (-83.366125, -83.364407, 42.225561, 42.226070),   # A10

                            # 21R/3L - M, P
                            (-83.352361, -83.351646, 42.208059, 42.208492),   # M1
                            # (, , , ),   # M2
                            (-83.349400, -83.348413, 42.212054, 42.212853),   # M3
                            # (, , , ),   # M5
                            (-83.337312, -83.336671, 42.228250, 42.228674),   # M6

                            (-83.350725, -83.349525, 42.207411, 42.207890),   # P1
                            (-83.347659, -83.346673, 42.211405, 42.211914),   # P3
                            # (, , , ),   # P5
                            (-83.335930, -83.335309, 42.227646, 42.228067),   # P6

                            # 21L/3R - S, W
                            (-83.341272, -83.340317, 42.208854, 42.209311),   # S1
                            (-83.337268, -83.336107, 42.214332, 42.214868),   # S6
                            (-83.353559, -83.352369, 42.195918, 42.196510),   # W1
                            (-83.346398, -83.345127, 42.205043, 42.206388),   # W2
                            (-83.344421, -83.343560, 42.206939, 42.209333),   # W3
                            (-83.342344, -83.341720, 42.209834, 42.211265),   # W4
                            (-83.340121, -83.339411, 42.212929, 42.214344),   # W5
                            (-83.339162, -83.338116, 42.214972, 42.21564),   # W6
                            (-83.336004, -83.334786, 42.219504, 42.220379),   # W7

                            # 27L/9R - T
                            # (, , , ),   # T1
                            # (, , , ),   # T2
                            # (, , , ),   # T3
                            # (, , , ),   # T4
                            # (, , , ),   # T5
                            # (, , , ),   # T6
                            # (, , , ),   # T7
                            # (, , , ),   # T8

                            # 27R/9L - V, S
                            # (, , , ),   # V1
                            # (, , , ),   # V2
                            # (, , , ),   # V4
                            (-83.331739, -83.330708, 42.216636, 42.217149),   # S7

                            # 4R/22L - Y, Z
                            (-83.370976, -83.369236, 42.201934, 42.202354),   # Y1
                            (-83.370113, -83.369167, 42.203222, 42.203704),   # Y2
                            (-83.363834, -83.362855, 42.211645, 42.212300),   # Y3
                            (-83.361940, -83.361171, 42.213426, 42.214871),   # Y4
                            (-83.356110, -83.355306, 42.221914, 42.222552),   # Y5
                            (-83.353332, -83.352745, 42.225618, 42.226196),   # Y7
                            (-83.350396, -83.349881, 42.229681, 42.230140),   # Y9
                            (-83.349808, -83.349124, 42.230581, 42.230974),   # Y10
                            (-83.357604, -83.357089, 42.222342, 42.222815),   # Z5
                            (-83.355013, -83.354298, 42.226266, 42.226889),   # Z7
                            (-83.351934, -83.350799, 42.231329, 42.231937)))  # Z10

    # plotting info
    centerLoc = [-83.358, 42.214]
    longRange = 0.035
    latRange = 0.023
