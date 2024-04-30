1228 fix_ims_set_current_position
#################################

API Breaks
----------
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
- Fix an issue with classes like `IMS` and `Newport` where calling
  ``set_current_position`` on a position outside of the user limits
  would fail, rather than change the limits to support the new
  offsets.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
