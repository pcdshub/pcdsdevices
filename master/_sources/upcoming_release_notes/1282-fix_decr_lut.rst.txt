1282 fix_decr_lut
#################

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
- Fix an issue where the LookupTablePositioner would fail silently if the
  lookup table was not strictly increasing in both axes.
  Lookup tables that are strictly decreasing in either axis
  will now be supported.
  Lookup tables that have inconsistent ordering in either axis will
  log a warning when the conversion is done.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
