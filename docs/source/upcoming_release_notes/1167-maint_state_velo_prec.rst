1167 maint_state_velo_prec
##########################

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
- TwinCAT state devices now properly report that their state_velo
  should be visualized with 3 decimal places instead of with 0.
  This caused no issues in hutch-python and was patched as a bug in
  typhos, and is done for completeness here.

Contributors
------------
- zllentz
