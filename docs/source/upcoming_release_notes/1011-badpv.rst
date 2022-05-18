1011 badpv
##########

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
- Remove unusable bunch_charge_2 signal from LCLS beam stats. This PV seems
  to contain a stale value that disagrees with bunch_charge and causes EPICS
  errors on certain hosts.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
