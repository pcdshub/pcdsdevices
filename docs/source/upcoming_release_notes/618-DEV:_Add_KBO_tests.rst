618 DEV: Add KBO tests
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- pcdsdevices/mirror.py
  added RTD PVs to KBOMirror class for bender actuators

New Devices
-----------
- N/A

Bugfixes
--------
- pcdsdevices/mirror.py
  corrected X/Y error in KBOMirror and FFMirror classes

Maintenance
-----------
- tests/test_mirror.py
  add prefix and lightpath tests for KBOMirror. FFMirror is an identical
  but reduced class so did not write an additional test for that.

Contributors
------------
- sfsyunus
