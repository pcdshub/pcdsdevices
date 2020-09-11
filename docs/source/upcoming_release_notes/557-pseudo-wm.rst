557 Pseudo Wm
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
- FltMvPositioner.wm will now return numeric values if the position
  value is a tuple. This value is the first element of the tuple, which
  for pseudo positioners is a value that can be passed into move and have
  it do the right thing. This resolves consistency issues and fixes bugs
  where mvr and umvr would fail.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
