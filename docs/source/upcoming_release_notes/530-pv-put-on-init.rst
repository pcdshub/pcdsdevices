IssueNumber Title
#################

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
- :class:`~pcdsdevices.pseudopos.LookupTablePositioner` will not by default
  attempt to change :class:`~pcdsdevices.epics_motor.EpicsMotor` limits.
  It is now a per-device init option that can be enabled on a case-by-case
  basis. (#530)

Maintenance
-----------
- N/A

Contributors
------------
- N/A
