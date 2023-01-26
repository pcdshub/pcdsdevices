1097 enh_readback_desync
########################

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
- Fix an issue where ``PseudoPositioner`` devices defined in this module
  but running from separate terminals would fight over control of the
  ``ophyd_readback`` helper signal, a PV that can be used to monitor
  progress of the calculated readback.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
