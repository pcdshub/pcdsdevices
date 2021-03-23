790 delaysync-pp
################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Add custom status prints for DelayBase and SyncAxis

New Devices
-----------
- N/A

Bugfixes
--------
- Fix issue where Newport motors would not show units in their status prints.
- Fix issue where SyncAxis was not compatible with PseudoPositioners as
  its synchronized "real" motors.

Maintenance
-----------
- Make unit handling in status_info more consistent to improve reliability of
  status printouts.

Contributors
------------
- zllentz
