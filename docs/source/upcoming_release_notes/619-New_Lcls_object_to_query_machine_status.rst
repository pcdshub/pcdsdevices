619 New Lcls object to query machine status
###########################################

API Changes
-----------
- The `SxrGmD` device has been removed from `beam_stats` module. SXR has been disassembled and the GMD was moved into the EBD. Its MJ PVs was not working anymore.

Features
--------
- N/A 

Device Updates
--------------
- N/A

New Devices
-----------
- A new Lcls class has been added to the `beam_stats` module.
- This new class contains PVs related to the Lcls Linac Status, as well as a few functions to support with checking the BYKIK status, turning that On and Off, and setting the period.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- cristinasewell
