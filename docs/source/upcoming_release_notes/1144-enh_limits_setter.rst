1144 enh_limits_setter
######################

API Changes
-----------
- N/A

Features
--------
- EPICS motors now support setattr on their ``limits`` attribute.
  That is, you can do e.g. ``motor.limits = (0, 100)`` to set
  the low limit to 0 and the high limit to 100.

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
- zllentz
