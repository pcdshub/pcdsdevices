1312 fix_mmc100_sig
###################

API Breaks
----------
- N/A

Library Features
----------------
- N/A

Device Features
---------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- Replace the ``velocity_base`` (``.VBAS``) signal in the `MMC100` class
  with a base `Signal` to avoid a PV disconnected error
  that was preventing moves.
  The `MMC100` record does not have this field.
  With this fix, `MMC100` devices can move again.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
