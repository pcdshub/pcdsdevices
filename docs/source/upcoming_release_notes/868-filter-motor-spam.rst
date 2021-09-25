868 filter-motor-spam
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- ``EpicsMotorInterface`` subclasses will no longer spam logger errors and
  warnings about alarm issues encountered by other users. These log messages
  will only be shown if they were the result of moves in the current session.
  Note that this log filtering assumes that all epics motors will have unique
  ophyd names.

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
- zllentz
