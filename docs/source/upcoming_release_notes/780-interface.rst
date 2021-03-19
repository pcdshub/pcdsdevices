780 interface
#############

API Changes
-----------
- Deprecate ``pcdsdevices.component`` in favor of ``pcdsdevices.device``
  to avoid circular imports and to more closely mirror the structure of
  ``ophyd``.

Features
--------
- Add ``InterfaceDevice`` and ``InterfaceComponent`` as a tool for
  including pre-build objects in a device at init time.
- Add ``to_interface`` helper function for converting normal ``Device``
  classes into ``InterfaceDevice`` classes.
- Add ``ObjectComponent`` as a tool for including pre-build objects in
  a device at class definition time.

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
