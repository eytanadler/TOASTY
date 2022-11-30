# TOASTY
*Topology Optimization of Airports for Selecting Taxiways Yessir*

Install with pip.

Try running `run_DTW.py` or `run_ORD.py`.
If you do not have [pyOptSparse](https://mdolab-pyoptsparse.readthedocs-hosted.com/en/latest/index.html) with IPOPT (with the HSL linear solvers) installed, you will have to change the driver to something else.
**_NOTE:_** If you are installing IPOPT with the HSL solvers and __not__ the MUMPS linear solver, you will need to change the default IPOPT `"linear_solver"` option in `pyoptsparse/pyIPOPT/pyIPOPT.py` to one of the HSL solvers, such as `"ma86"` for it to run with the default options (otherwise you will need to explicitly set `"linear_solver"` option in every run script).

For installing `pypardiso`, I've had trouble where I get an error code -3 when it calls Pardiso.
The solution that worked for me was switching to an older version of OpenMP that was compatible with the version of MKL installed.
See [here](https://stackoverflow.com/questions/70665142/pypardisoerror-the-pardiso-solver-failed-with-error-code-3-see-pardiso-docum).

Using `pypardiso` with multipoint cases on Windows may cause errors.
If it does, try uninstalling `pypardiso` from the current Python environment so it falls back to the `scipy` solvers.
