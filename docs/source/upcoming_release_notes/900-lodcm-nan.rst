900 lodcm-nan
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
- In the LODCM calculation callback updates, return a NaN energy instead of
  raising an exception in background thread when there is a problem
  determining the crystal orientation. This prevents the calculated value
  from going stale when it has become invalid, and it prevents logger spam.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
