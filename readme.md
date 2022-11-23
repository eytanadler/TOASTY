# TOASTY
*Topology Optimization of Airports for Selecting Taxiways Yessir*

Install with pip.

Try running `run_DTW.py` or `run_ORD.py`.
If you do not have [pyOptSparse](https://mdolab-pyoptsparse.readthedocs-hosted.com/en/latest/index.html) with IPOPT (with the HSL linear solvers) installed, you will have to change the driver to something else.

For installing `pypardiso`, I've had trouble where I get an error code -3 when it calls Pardiso.
The solution that worked for me was switching to an older version of OpenMP that was compatible with the version of MKL installed.
See [here](https://stackoverflow.com/questions/70665142/pypardisoerror-the-pardiso-solver-failed-with-error-code-3-see-pardiso-docum).
