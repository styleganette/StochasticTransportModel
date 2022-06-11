# StochasticTransportModel

Installing mpi-sppy (the package for solving SPs with pyomo) must be done before running.


If single instance is run on own computer, run script_MainAnalysis_TwoStage.py with "instance_run" set to the chosen instance.

If multiple instances are run remote on Solstorm, run master.bash with the chosen scenarios, and change "instance_run" variable in script_MainAnalysis_TwoStage to sys.argv[1].

To run Progressive Hedging Algorithm with upper and lower bounding procedures, run run_model.py.

The model formulation implementation is given in TranspModelClass.py, with sets and parameters given in Create_Sets_Class.py.
All data used is in the Data folder.

