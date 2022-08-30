1034 Kill ccm PID on move
#################

API Changes
-----------
Overwrite default move method for the CCMEnergy class to kill the PID loop at the end of each move (default)
This should prevent the piezo motor from heating up and breaking vacuum or frying itself.

Features
--------
- N/A

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
espov
