864 test_cleanup
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
- N/A

Maintenance
-----------
- Imports changed to relative in test suite.
- Miscellaneous floating point comparison fixes for test suite.
- Fixed CCM test failure when run individually or quickly (failure when run
  less than 10 seconds after Python starts up)
- Linux-only ``test_presets`` now skips macOS as well.

Contributors
------------
- klauer
