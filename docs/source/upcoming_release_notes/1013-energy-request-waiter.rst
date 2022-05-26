1013 energy-request-waiter
##########################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Add an optional "acr_status_suffix" argument to ``BeamEnergyRequest`` that
  instantiates an alternate version of the class that waits on an ACR PV to
  know when the motion is done. This is a more suitable version of the class
  for step scans and a less suitable version of the class for fly scans.

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
