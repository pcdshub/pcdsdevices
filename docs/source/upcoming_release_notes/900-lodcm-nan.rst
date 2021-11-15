900 lodcm-nan
#############

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
- In the LODCM "inverse" calculations, return a NaN energy instead of
  raising an exception when there is a problem determining the crystal
  orientation. This prevents the calculated value from going stale when
  it has become invalid, and it prevents logger spam when this is
  called in the pseudopositioner update position callback.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
