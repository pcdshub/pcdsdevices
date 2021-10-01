879 Various changes from XPP
#################

API Changes
-----------
- `isum` components have been renamed to `sum` in IPM detector classes.
- The motor components for PIM classes have been shortened by removing `_motor` from their names (e.g. `zoom_motor` is now `zoom`).

Features
--------
- N/A

Device Updates
--------------
- The default theta0 values for CCM objects has been changed from 14.9792 to 15.1027.
- An acceleration component was added to the IMS class.
- IPM objects now have short aliases for their motors (`ty`, `dx`, `dy`).

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Tab whitelists have been cut down to make things simpler for non-expert users.

Contributors
------------
- ZryletTC
