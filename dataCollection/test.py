from FlightRadar24.api import FlightRadar24API
import numpy as np
import matplotlib.pyplot as plt
import niceplots as nice

# def plot_path(ac_id):
#     trail = 

fr_api = FlightRadar24API()

sd_icao = "KSAN"
sd_info = fr_api.get_airport(sd_icao)
#print(sd_info)
#thy_flights = fr_api.get_flights(iata = airport_code)


#32.7314872,-117.1882776
#32.7380255,-117.1783667
#sd_bounds = "32.5,32.8,-117.0,-117.3"
#sw_flight = fr_api.get_flights(bounds=sd_bounds)

# grab flights from airline because it's hard to get from bounds
sw_flight = fr_api.get_flights(airline="SWA")

sd_flights = []
for f in sw_flight:
    if f.origin_airport_iata == "SAN" and f.on_ground == 1:
        sd_flights.append(f)

"""
32.7343
32.7337
-117.1972
-117.199
"""

"""
32.739481
32.728491
-117.1755774
-117.2100507
"""


# grab flights from bounds - these need narrowed
#bound_flights = fr_api.get_flights(bounds="32.7, 32.8, -117.5, -117.2")

flights = fr_api.get_flights(airport="SAN")
bound_flights = fr_api.get_flights(bounds="32.728491, 32.739481, -117.2100507, -117.1755774")
san_bound_flights = []
for flight in bound_flights:
    if flight.on_ground == 1 or flight.ground_speed < 100:
        san_bound_flights.append(flight)

new_flights = []
for f in sw_flight:
    if f.origin_airport_iata == "SAN":
        new_flights.append(f)


flight = sd_flights[0]
ac_id = flight.id
details = fr_api.get_flight_details(ac_id)
trail = details["trail"]

latlong = np.zeros((len(trail), 2))
for i, point in enumerate(trail):
    latlong[i, :] = [point["lat"], point["lng"]]

nice.setRCParams()
fig, ax = plt.subplots()
ax.scatter(latlong[:, 1], latlong[:, 0], color=nice.get_niceColors()["Blue"])
plt.title(f"{flight.airline_icao} flight {flight.number} from {flight.origin_airport_iata} to {flight.destination_airport_iata}")
ax.ticklabel_format(useOffset=False)
fig.tight_layout()
# plt.savefig("test_path.png")
plt.show()



# taxi in


# taxi out

print(sd_flights)
