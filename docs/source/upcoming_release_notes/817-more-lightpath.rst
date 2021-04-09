817 more-lightpath
##################

API Changes
-----------
- Move stoppers into stopper.py, but keep reverse imports for
  backwards compatibility. This will be deprecated and then removed
  at a later date.

Features
--------
- N/A

Device Updates
--------------
- Update the mono spectrometer class to provide status to lightpath.

New Devices
-----------
- Add PPSStopperL2SI for having readbacks of the new PPS stoppers inside
  of lightpath.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
