import matplotlib.pyplot as plt
import tilemapbase as tmb
from FlightRadar24.api import FlightRadar24API
import numpy as np


# tmb.start_logging()
# tmb.init(create=True)

t = tmb.tiles.build_OSM()
SAN = (-117.1916, 32.734)
lon_range = 0.018
lat_range = 0.007

# lon_range = 0.5
# lat_range = 0.5
extent = tmb.Extent.from_lonlat(SAN[0] - lon_range, SAN[0] + lon_range, SAN[1] - lat_range, SAN[1] + lat_range)
# extent = extent.to_aspect(1.0)
fig, ax = plt.subplots()
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)

plotter = tmb.Plotter(extent, t, width=600)
plotter.plot(ax, t)

# latlong = np.array(([-116.675575,   32.713989],
# [-116.66819,    32.724968],
# [-116.662025,   32.734184],
# [-116.654961,   32.744797],
# [-116.64772,    32.755692],
# [-116.640671,   32.766491],
# [-116.633049,   32.778267],
# [-116.625481,   32.789951],
# [-116.616844,   32.803452],
# [-116.609619,   32.814671],
# [-116.60125,    32.827606],
# [-116.592789,   32.840744]))
# # latlong = np.array(((-117.1916, 32.734), (-117.18188, 32.73254), (-117.1967, 32.7353)))
# # x, y = tmb.project(*SAN)

# for i, point in enumerate(latlong):
#     x, y = tmb.project(*point)
#     ax.scatter(x, y, color="black")

fr_api = FlightRadar24API()
allFlights = fr_api.get_flights(airport="SAN")

someFlights = []
for f in allFlights:
    if f.destination_airport_iata == "SAN" and f.on_ground == 1:
        someFlights.append(f)

trail = fr_api.get_flight_details(someFlights[0].id)["trail"]
latlong = np.zeros((len(trail), 2))
for i, point in enumerate(trail):
    latlong[i, 0:] = [point["lng"], point["lat"]]

for i, point in enumerate(latlong):
    print(point)
    x, y = tmb.project(*point)
    ax.scatter(x, y, color="black")
    # if i > 10:
    #     break

plt.savefig("path_on_san.png")
# plt.show()
