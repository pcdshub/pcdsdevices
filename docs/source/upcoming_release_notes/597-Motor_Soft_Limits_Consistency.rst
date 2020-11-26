597 Motor Soft Limits Consistency
#################

API Changes
-----------
-  Remove the ability to use setattr for `low_limit` and `high_limit`.

Features
--------
- Added two methods to `EpicsMotorInterface`: `set_high_limit()` and `set_low_limit()`, as well as `get_low_limit()` and `get_high_limit()`.
- Added a little method to clear limits: `clear_limits` - by EPICS convention, this sets both limits to 0.

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
- N/A

Contributors
------------
- cristinasewell
