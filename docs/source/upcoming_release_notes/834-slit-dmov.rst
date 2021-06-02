834 slit-dmov
#############

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
- Fix issue where BeckhoffSlits devices could show metadata errors on startup
  by cleaning up the done moving handling. This would typically spam the
  terminal in cases where we were making large numbers of PV connections in
  the session at once, such as at the start of a hutch-python load.

Maintenance
-----------
- N/A

Contributors
------------
- ZLLentz
