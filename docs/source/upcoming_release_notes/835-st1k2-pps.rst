835 st1k2-pps
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Rename PPSStopperL2SI to PPSStopper2PV and generalize to all PPS stoppers
  whose states are determined by the combination of two PVs. The old name and
  old defaults are retained for backcompatibility and have not yet been
  deprecated. This was done to support the PVs for ST1K2 which do not follow
  any existing pattern.

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
- ZLLentz
