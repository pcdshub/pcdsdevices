1183 fix_att_move_err
#####################

API Breaks
----------
- N/A

Features
--------
- Added `PVPositionerNoInterrupt`, a pv positioner base class whose moves
  cannot be interrupted (and will loudly complain about any such attempts).

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- LCLSI attenuator classes (generated from the `Attenuator` factory function)
  will now raise a much clearer error for when they cannot interrupt a
  previous move, without trying (and failing) to interrupt the previous move.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
