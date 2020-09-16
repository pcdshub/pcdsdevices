535 lxt_ttc
###########

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
- Adds :class:`~pcdsdevices.lxe.TimeToolDelay`, an alias for
  :class:`~pcdsdevices.pseudopos.DelayNewport` with additional contextual
  information and room for future development.


Bugfixes
--------
- The direction of :class:`LaserTiming` (``lxt``) was inverted and is now
  fixed.


Maintenance
-----------
- Added a copy-pastable example to
  :class:`~pcdsdevices.component.UnrelatedComponent` to ease creation of new
  devices.

Contributors
------------
- klauer
