import numpy as np


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
        """
        This method is bad! It doesn't account for the aircraft taxiing through multiple exits

        Parameters
        ----------
        trail : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """

        for i in range(self.nExits):
            exitLat1 = self.exitLocations[i][0]
            exitLat2 = self.exitLocations[i][1]
            exitLong1 = self.exitLocations[i][2]
            exitLong2 = self.exitLocations[i][3]

            for point in trail:
                thisLat = point[0]
                thisLong = point[1]

                if exitLat1 < thisLat and thisLat < exitLat2:
                    if exitLong1 < thisLong and thisLong < exitLong2:
                        return i


    def findBetterExit(self, trail, isDeparture):
        """
        Determine which runway exit a trail passes through, hopefully better this time
        For arrivals, grabs the first exit a trail passes through chronologically
        For departures, this is the last exit, so we have to reverse the trail

        Parameters
        ----------
        trail : array
            Points representing the path the flight took
        isDeparture : bool
            True if the trail is for a departing flight, False if arriving.
            Tells us whether to reverse the search

        Returns
        -------
        int
            code for runway exit
        """

        # reverse the trail if this is departures so we grab the last exit the plane passes through
        if isDeparture:
            trail = np.flip(trail)

        # go through each point in the trail in chronological (arrivals) or reverse (departures) order
        for [thisLat, thisLong] in trail:
            # TODO if point close enough to airport (save time)

            # check every exit to see if this point goes through one
            for i in range(self.nExits):
                exitLat1 = self.exitLocations[i][0]
                exitLat2 = self.exitLocations[i][1]
                exitLong1 = self.exitLocations[i][2]
                exitLong2 = self.exitLocations[i][3]

                if exitLat1 < thisLat and thisLat < exitLat2:
                    if exitLong1 < thisLong and thisLong < exitLong2:
                        return i
