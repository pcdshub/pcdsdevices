866 ims_timeout
#################

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
- Add a timeout parameter to IMS.reinitialize, and set it as the default arg
  for use in the stage method, which is run during scans. This avoids
  a bug where the stage method could hang forever instead of erroring out,
  halting a scan in its tracks.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
