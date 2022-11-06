class Airport():
    # runway information
    exitLocations = []
    # a: [lat1, lat2, long1, long2]

    # centroid
    # lon range
    # lat range

    # nExits
    # exitLocations

    def findExitForTrail(self, trail):

        for exitName, exitLoc in self.exitLocations:
            exitLat1 = exitLoc[0]
            exitLat2 = exitLoc[1]
            exitLong1 = exitLoc[2]
            exitLong2 = exitLoc[3]

            for point in trail:
                thisLat = point[0]
                thisLong = point[1]

                if exitLat1 < thisLat and thisLat < exitLat2:
                    if exitLong2 < thisLong and thisLong < exitLong1:   # longitude is reversed
                        return exitName
