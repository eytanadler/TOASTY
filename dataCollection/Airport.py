class Airport():
    # runway information
    # exitLocations = []
    # a: [lat1, lat2, long1, long2]

    # centroid
    # lon range
    # lat range

    # nExits
    # exitLocations

    def findExitForTrail(self, trail):

        for i in range(self.nExits):
            exitLat1 = self.exitLocations[i][0]
            exitLat2 = self.exitLocations[i][1]
            exitLong1 = self.exitLocations[i][2]
            exitLong2 = self.exitLocations[i][3]

            for point in trail:
                thisLat = point[0]
                thisLong = point[1]

                if exitLat1 < thisLat and thisLat < exitLat2:
                    if exitLong1 < thisLong and thisLong < exitLong2:   # longitude is reversed
                        return i
