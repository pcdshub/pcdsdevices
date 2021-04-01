805 set-position-bug
####################

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
- Fix an issue where calling ``set_current_position`` on certain motors would
  cause the ipython session to freeze, leaving the motor in the ``set`` state
  instead of bringing it back to the ``use`` state.
- Hacky workaround for IMS motor part number strings being unable to be read
  through pyepics when they contain invalid utf-8 characters.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
