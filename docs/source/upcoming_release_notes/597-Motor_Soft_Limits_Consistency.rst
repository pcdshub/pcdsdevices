597 Motor Soft Limits Consistency
#################

API Changes
-----------
- N/A

Features
--------
- Added two methods to the `epics_motors`: `set_high_limit()` and `set_low_limit()`, as well as `get_low_limit()` and `get_high_limit()`.
- Added a little method to clear limits: `clear_limits` - this sets both limits to 0.
- Removed the other limit setters and getters `low_limit`, `high_limit` `limits`
- Overrode the `limits` property

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
