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
- Add the ``desc``, ``last_voltage_set``, and ``is_trip`` component signals to
  `MPODApalisChannel`. These have been helpful during operations at TMO.
  ``last_voltage_set`` will also get a ``voltage_setpoint`` alias, which is the
  original name as used in TMO's scripts.
- Add proper control limits to `MPODApalisChannel.voltage` and `MPODApalisChannel.current`.
  This will give useful errors when someone tries to put values outside of the
  channel's supported range.

New Devices
-----------
- N/A

Bugfixes
--------
- Fix an issue where arbitrarily large negative values were permitted to be
  passed during the `MPODApalisChannel.set_voltage` method, and where
  small values passed to a negative-polarity channel would jump to the
  most negative value. Now, this function will clamp all values between
  zero and the maximum channel voltage.

Maintenance
-----------
- Added unit tests to cover the `MPODApalisChannel` changes.

Contributors
------------
- zllentz
