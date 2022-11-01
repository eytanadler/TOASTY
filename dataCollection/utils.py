from FlightRadar24.api import FlightRadar24API
import numpy as np
import niceplots as nice
import matplotlib as plt
import time


fr_api = FlightRadar24API()
SAN = "SAN"

def extractLatLong(trail):
    latlong = np.zeros((len(trail), 2))

    for i, point in enumerate(trail):
        latlong[i, :] = [point["lat"], point["lng"]]

    return latlong

def flightIDString(flight):
    return f"{flight.number}_{flight.origin_airport_iata}_to_{flight.destination_airport_iata}"

def saveTrail(flight):
    trail = fr_api.get_flight_details(flight.id)["trail"]
    latlong = extractLatLong(trail)

    fname = flightIDString(flight)

    np.savetxt(fname, latlong)

def catchArrivals(openTime, refreshRate=60):
    startTime = time.time()
    endTime = startTime + openTime

    flightNumbers = []

    while time.time() < endTime():
        time.sleep(refreshRate)

        try:
            boundFlights = fr_api.get_flights(airport=SAN)

            for flight in boundFlights:
                if flight.destination_airport_iata == SAN and flight.number not in flightNumbers:
                    flightNumbers.append(flight.number)
                    saveTrail(flight)

        except Exception:
            continue


def plotTrail(flight, fileName=None):
    details = fr_api.get_flight_details(flight.id)
    trail = details["trail"]

    latlong = extractLatLong(trail)

    nice.setRCParams()
    fig, ax = plt.subplots()
    ax.scatter(latlong[:, 0], latlong[:, 1], color=nice.get_niceColors()["Blue"])
    plt.title(f"{flight.airline_icao} flight {flight.number} from {flight.origin_airport_iata} to {flight.destination_airport_iata}")
    ax.ticklabel_format(useOffset=False)
    fig.tight_layout()

    if fileName is None:
        fileName = flightIDString(flight)

    plt.savefig(fileName)
