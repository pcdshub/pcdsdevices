766 LODCM Additional Functions
#################

API Changes
-----------
- N/A

Features
--------
- New functions have been added to the LODCM object: `tweak_x`, `tweak_parallel`, `set_energy`, `wait_energy`.
- Custom status print has been added for the 3 towers as well as the energy classes.
- Added the `OffsetIMSWithPreset` subclass of `OffsetMotorBase` that has an additional `_SET` offset pv, and puts to this pv during `set_current_position`.

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
- Have cleaned up some docstring and changed the naming for the offset motors to the old style.

Contributors
------------
- cristinasewell
