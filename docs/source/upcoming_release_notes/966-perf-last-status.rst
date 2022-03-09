966 perf-last-status
####################

API Changes
-----------
- N/A

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
- Remove the instantiation of a status object at motor startup to help
  improve the performance of loading large sessions. This object was not
  strictly needed.

Contributors
------------
- klauer
- zllentz
