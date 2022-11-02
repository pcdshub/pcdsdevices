1063 enh_nc_error_status
########################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Allow ``BeckhoffAxis`` devices to report the NC error from the
  beckhoff PLC as part of the move status.

New Devices
-----------
- N/A

Bugfixes
--------
- Fix an issue where ``BeckhoffAxis`` devices would show error status
  after nearly any move, even those that ended normally.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
