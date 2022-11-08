from FlightRadar24.api import FlightRadar24API
import time
import pickle as pkl
import os
import numpy as np
import logging
from dataCollection.plotting.makeItPretty import extractTrail


# initialize FlightRadar24 API
fr_api = FlightRadar24API()


def flightIDString(flight, airport, outFolder):
    """
    Create a nice string for a flight filename

    Parameters
    ----------
    flight : object
        from FlightRadar24 API representing a single flight
    airport : Airport class
        airport being studied for this case

    Returns
    -------
    string
        filename, including folder (arrivals or departures)
    """
    origin = flight.origin_airport_iata
    destination = flight.destination_airport_iata
    airline = flight.airline_iata

    # set whether we're looking at an arrival or a departure for our given airport
    if origin == airport.code:
        subFolder = "departures"
    elif destination == airport.code:
        subFolder = "arrivals"

    # in some cases we lose the origin, destination, or airline info - manually save these to avoid killing the data collection
    if origin == "N/A" or destination == "N/A" or airline == "N/A":
        fileName = os.path.join(os.path.dirname(__file__), f"{outFolder}/debug/{flight.id}")
        debugFile = open(fileName, "wb")
        pkl.dump(fr_api.get_flight_details(flight.id), debugFile)
        debugFile.close()

        return "debug"

    return f"{outFolder}/{subFolder}/{flight.number}_{origin}_to_{destination}"


def saveFlightInfo(flight, airport, outFolder):
    """
    Saves the flight details into a pickle file

    Parameters
    ----------
    flight : object
        from FlightRadar24 API representing a single flight
    airport : Airport class
        airport being studied for this case
    """
    flightDetails = fr_api.get_flight_details(flight.id)

    fname = flightIDString(flight, airport, outFolder)

    if fname != "debug":
        print(f"saving {fname}")
        fname = os.path.join(os.path.dirname(__file__), f"{fname}")

        flightFile = open(f"{fname}", "wb")
        pkl.dump(flightDetails, flightFile)
        flightFile.close()


def flightAtAirport(airport, flight, atol=0.1):
    """
    Check to see if a flight is at a given airport using longitude and latitude values and a specified tolerance

    Parameters
    ----------
    flight : object
        from FlightRadar24 API representing a single flight
    airport : Airport class
        airport being studied for this case
    atol : float, optional
        absolute tolerance for numpy.allclose() comparison, by default 0.1

    Returns
    -------
    boolean
        True if at airport, False if not
    """
    airportCoord = airport.centerLoc
    flightCoord = [flight.longitude, flight.latitude]

    atAirport = np.allclose(airportCoord, flightCoord, atol=atol)
    return atAirport


def catchDepartures(airport, openTime, outFolder, refreshRate=120):
    """
    Catch departures that left or are leaving <airport> over <openTime>
    Checks again every <refreshRate>
    Contains logic to ensure information is only saved if flights have left the ground

    Parameters
    ----------
    airport : Airport class
         airport being studied for this case
    openTime : int
        time to leave this running for
    refreshRate : int, optional
        rate at which to check for new flights, by default 120 (seconds)
    """
    startTime = time.time()
    endTime = startTime + openTime

    flightNumbers = []

    first = True

    # set up logging for exceptions
    logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), "departure_log"),
                        level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger = logging.getLogger(__name__)

    # leave this running until we hit endTime
    while time.time() < endTime:
        print("checking")
        # don't sleep the first time through
        if not first:
            print("sleep")
            time.sleep(refreshRate)
        first = False

        try:
            allFlights = fr_api.get_flights(airport=airport.code)

            for flight in allFlights:

                # just look for new flights with our designated airport as the origin
                if flight.number not in flightNumbers and flight.origin_airport_iata == airport.code:

                    # check to see if the flight is in the air
                    if flight.on_ground == 0:
                        print(f"found flight {flight.number}")
                        flightNumbers.append(flight.number)
                        saveFlightInfo(flight, airport, outFolder)

                    # if the flight is on the ground make sure it's left the origin airport
                    elif flight.on_ground == 1:
                        if not flightAtAirport(airport, flight):
                            print(f"found flight {flight.number}")
                            flightNumbers.append(flight.number)
                            saveFlightInfo(flight, airport, outFolder)

                        else:
                            print(f"hi {flight.number}")

        # log exceptions but move on
        except Exception as ex:
            print(ex)
            logger.error(ex)
            continue


def catchArrivals(airport, openTime, outFolder, refreshRate=60):
    """
    Catch flights that have arrived at <airport> over <openTime>
    Checks again every <refreshRate>
    Flights have to be on the ground at destination airport for arrival taxiing info to be present
    Flights have to be caught before they switch to being classified as a departing flight, so refresh is lower than catchDepartures()
    Flights also can't be caught before they've exited the runway

    Parameters
    ----------
    airport : Airport class
         airport being studied for this case
    openTime : int
        time to leave this running for
    refreshRate : int, optional
        rate at which to check for new flights, by default 60 (seconds)
    """
    startTime = time.time()
    endTime = startTime + openTime

    flightNumbers = []

    first = True

    # set up logging for exceptions
    logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), "arrival_log"),
                        level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    logger = logging.getLogger(__name__)

    # leave this running until we hit endTime
    while time.time() < endTime:
        print("checking")
        # don't sleep the first time through
        if not first:
            print("sleep")
            time.sleep(refreshRate)
        first = False

        try:
            allFlights = fr_api.get_flights(airport=airport.code)

            for flight in allFlights:

                # just look for new flights with our designated airport as the destination
                if flight.number not in flightNumbers and flight.destination_airport_iata == airport.code:

                    # flight has to be on the ground
                    if flight.on_ground == 1:

                        # flight has to be at detination airport
                        if flightAtAirport(airport, flight):
                            # check if aircraft has gone through an exit yet - this returns None if it hasn't
                            trail = extractTrail(fr_api.get_flight_details(flight.id))
                            exitCode = airport.findExitForTrail(trail)
                            print(f"flight {flight.number} exited at {exitCode}")

                            # flight has to be off the runway or we'll wait to get it next time
                            if exitCode is not None:
                                print(f"found flight {flight.number}")
                                flightNumbers.append(flight.number)
                                saveFlightInfo(flight, airport, outFolder)
                            else:
                                print(f"skip flight {flight.number}")

        # log exceptions but move on
        except Exception as ex:
            print(ex)
            logger.error(ex)
            continue
