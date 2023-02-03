1105 fix_cxi_pim
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
- Certain PIMs, such as cxi_dg1_pim, did not work properly because pcdsdevices
  assumed that these devices had a "DIODE" state, which is not necessarily
  true. This has been fixed by making all PIMs autodiscover their states from
  EPICS.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
