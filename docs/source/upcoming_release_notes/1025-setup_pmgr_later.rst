1025 setup_pmgr_later
#####################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Add IMS.setup_pmgr as a public API for applications that want to initialize
  pmgr support before the first device uses it. This was previously private
  API at IMS._setup_pmgr.

New Devices
-----------
- N/A

Bugfixes
--------
- Create the pmgr resources when they are first used rather than on IMS
  init, saving 3 seconds of startup time for users that don't need
  pmgr resources.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
