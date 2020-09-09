535 lxt_ttc
###########

API Changes
-----------
- N/A

Features
--------
- :class:`~pcdsdevices.pseudopos.SyncAxes` has been adjusted to support
  scalar-valued pseudopositioners, allowing for more complex devices to be kept
  in lock-step motion.

Device Updates
--------------
- N/A

New Devices
-----------
- Adds :class:`~pcdsdevices.lxe.LaserTimingCompensation` (``lxt_ttc``) which
  synchronously moves :class:`LaserTiming` (``lxt``) with
  :class:`~pcdsdevices.lxe.TimeToolDelay` (``txt``) to compensate so that the
  true laser x-ray delay by using the ``lxt``-value and the result of time tool
  data analysis, avoiding double-counting.
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
