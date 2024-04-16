1214 SmarAct Updates
#################

API Breaks
----------
- If release < R1.0.20 then the EPICS signals will timeout on the new PVs.
  Please make sure to update your children IOCs.

Features
--------
- Adds the following temperature monitoring PVs:
  - channel_temp
  - module_temp
- Adds the following hidden config PVs to encoded devices:
  - log_scale_offset
  - log_scale_inv
  - def_range_min
  - def_range_max
- Adds SmarActEncodedTipTilt device to epics_motor.py

Device Updates
--------------
- SmarActOpenLoop gets temp monitoring PVs
- SmarAct gets temp monitoring PVs

New Devices
-----------
- SmarActEncodedTipTilt

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- aberges
