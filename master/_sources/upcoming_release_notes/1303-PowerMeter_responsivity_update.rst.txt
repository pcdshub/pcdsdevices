1303 PowerMeter_responsivity_update
#################

API Breaks
----------
- N/A

Library Features
----------------
- Added the ability to add custom units for convert_unit with a unit test

Device Features
---------------
- Added calibrated_uj and manual_in_progress
- Renamed manual-collections components to have manual in their name to distinguish them from auto-background collection

New Devices
-----------
- N/A

Bugfixes
--------
- Made responsivity component input only like the pytmc pragma so the connection does not fail when looking for the non-RBV pv

Maintenance
-----------
- N/A

Contributors
------------
- KaushikMalapati
