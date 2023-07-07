TOASTY data collection
======================

Data structures
---------------

### Airport
Data for an airport is saved to a class that inherits from the common `Airport` baseclass.
This data includes:
- IATA airport code
- Number of runways
- Longitude and latitude of each runway exit - this can be debugged using `plotExitBoxes()` and `plotExitLabels()` in `plotting.py`
- Center location of airport
- Tolerance for determining whether flights are close enough to airport - larger for larger airports
- Plotting bounds


### Flight
Flight data comes from the FlightRadarAPI.
Relevant fields are:
- ID - FlightRadar code for flight
- Origin - IATA code for origin airport
- Destination - IATA code for destination airport
- Longitude
- Latitude
- Trail (position history)
- On_ground - flag for whether plane has taken off


Obtaining flight data
---------------------
Flight data is obtained from the [API](https://github.com/JeanExtreme002/FlightRadarAPI/tree/main) for [FlightRadar24](https://www.flightradar24.com/). 
This API was [modified](https://github.com/hajdik/FlightRadarAPI/tree/get-flight-request) slightly to work for this project.

> FlightRadarAPI relies on the ground data FlightRadar24 can obtain at airports. 
> At some airports, there is not good ADS-B coverage so one flight can switch between radar and ADS-B. 
> This causes the flight data up until this point to be lost, making this process infeasible. 
> DEN and DTW were observed to not have sufficient data for TOASTY.

This flight data is captured live as access into the historical data is limited.
All of the FlightRadar24 data on a flight is saved to pickle files once a flight uses a runway entry/exit. 
For an arriving flight, this is saved after the flight exits a runway and for a department lifhg this is saved after the flight enters a runway.

This capturing is handled in `catchFlights.py`.
For arrival aircraft, the flight does not save until the flight is on the ground and has exited the runway. 
Whether a flight has exited is determined by `findBetterExit()`, a function of the `Airport` baseclass.
For departing aircraft, the flight is saved once the flight is no longer on the ground.
Departures and arrivals for a given airport should be saved into separate folders for processing.
 

Processing flight data into exits
---------------------------------
A pickle file for a saved flight is opened and read by `countTotals()` in `countTotals.py`.
The totals for a folder of results is assembled by this function to 
find the arrivals or departures total for an airport
Where the flight entered or exited the runway is determined by `findBetterExit()`, a function in the `Airport` baseclass.
These results can be printed out in a table format and plotted using the functions in `Plotting`


Plotting exit data
------------------
Frequencies of exits can be plotted using `plotFrequenciesSize()`, which plots a circle on each exit whose size corresponds to the relative usage of that exit.
Another method, `plotFrequenciesColor`, plots a circle on each exit whose color corresponds to a heat map of relative usage.
