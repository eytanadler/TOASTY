# TOASTY
*Topology Optimization of Airports for Selecting Taxiways Yessir*

Install with pip.

For installing `pypardiso`, I've had trouble where I get an error code -3 when it calls Pardiso.
The solution that worked for me was switching to an older version of OpenMP that was compatible with the version of MKL installed.
See [here](https://stackoverflow.com/questions/70665142/pypardisoerror-the-pardiso-solver-failed-with-error-code-3-see-pardiso-docum).

## Notes after talking to Max
- Try only giving the optimizer access to redesign some portions of the taxiway system (maybe constrain the central terminal area and give it access to the runway area); runways 28L and 22L in particular could use some work
- Try general data where you put patches of heat where you'd expect airplanes to land, but not the data itself (first and last quarter of the runway generates heat or something)
- Arrivals and departures as separate multipoint cases
