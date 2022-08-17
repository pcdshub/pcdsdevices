1045 fix limits
###############

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
- Fix an issue where various types of motors could have inconsistent
  limits metadata when the IOC or gateway doesn't behave as expected.
- Fix an issue where the ``UpdateComponent`` was incompatible with
  subscription decorators.

Maintenance
-----------
- Make some of the test motor simulations slightly more accurate.

Contributors
------------
- zllentz
