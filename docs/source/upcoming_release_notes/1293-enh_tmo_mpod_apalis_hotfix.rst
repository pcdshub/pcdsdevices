1293 enh_tmo_mpod_apalis_hotfix
###############################

API Breaks
----------
- N/A

Library Features
----------------
- N/A

Device Features
---------------
- Add the ``desc``, ``voltage_setpoint``, and ``is_trip`` component signals to
  `MPODApalisChannel`. These have been helpful during operations at TMO.

New Devices
-----------
- N/A

Bugfixes
--------
- Fix an issue where arbitrarily large negative values were permitted to be
  passed during the `MPODApalisChannel.set_voltage` method, and where
  small values passed to a negative-polarity channel would jump to the
  most negative value.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
