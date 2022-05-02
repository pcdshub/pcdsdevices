996 ADD AT2L0 err support
#################

API Changes
-----------
-N/A

Features
--------
-N/A

Device Updates
--------------
- Updated AT2L0 to utilize newly implemented MultiderivedSignal for error checking and clearing in GUI and at the command line
- Updated AT2L0 Typhos GUI, includes error clearing button and display of error on individual blades
- clear_errors() method for AT2L0 to clear errors; e.g. at2l0.clear_errors()
- print_errors() method for AT2l0 to print error summary; e.g. at2l0.print_errors()

New Devices
-----------
- N/A

Bugfixes
--------
- adjusted epics_motor/cmd_err_reset to better accomodate dynamic error updating after the gui has been opened
- adjusted state/reset_cmd to better acoomodate dynamic error updating after the gui has been opened

Maintenance
-----------
- N/A

Contributors
------------
-mkestra
