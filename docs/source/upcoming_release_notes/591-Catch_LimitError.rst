591 Catch LimitError
####################

API Changes
-----------
- User-facing move functions will not be able to catch the
  :class:`~ophyd.utils.LimitError` exception.  These interactive methods are
  not meant to be used in scans, as that is the role of bluesky.

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
- Catch :class:`~ophyd.utils.LimitError` in all
  :class:`pcdsdevices.interface.MvInterface` moves, reporting a simple error by
  way of the interface module-level logger.

Contributors
------------
- klauer
