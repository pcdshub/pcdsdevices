1049 enh_btms
#############

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Updated ``pcdsdevices.laser.btps`` device classes following a PV rename.
- Updated ``pcdsdevices.laser.btps`` device classes to support the Laser Beam
  Transport Motion System (BTMS).  In addition, this includes a module
  ``pcdsdevices.laser.btms_config`` which has utilities to represent the state
  of the BTS in a control system independent way and allows for motion
  verification and other sanity checks.

New Devices
-----------
- ``pcdsdevices.laser.btps.BtpsVGC`` a variant of the VGC class that includes
  ``valve_position``.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- klauer
