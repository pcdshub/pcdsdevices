901 bk-user-enable
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Add the user_enable signal (bUserEnable) to the BeckhoffAxisPLC class.
  This is a signal that allows the user to unilaterally disable a
  running motor's power. When enabled, it is up to the controller
  whether or not to actually power the motor, but when disabled the
  power will be shut off.

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
