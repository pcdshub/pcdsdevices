820 fix-docs-api
#################

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
- Test suite utility ``find_all_classes`` will no longer report test suite
  classes.

Maintenance
-----------
- Removed prototype-grade documentation helpers in favor of those in ophyd.docs
- Added similar ``find_all_callables`` for the purposes of documentation and
  testing.
- Added documentation helper for auto-generating ``docs/source/api.rst``.  This
  should be run when devices are added, removed, or moved.

Contributors
------------
- klauer
