740 status_print_checks
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Multiple devices have been modified to include explicit argument and keyword
  argument names in ``__init__`` for clarity and introspectability.

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Added test suite to try to instantiate all device classes with
  ``make_fake_device`` and perform status print formatting checks on them.
- Added ``include_plus_sign`` option for ``get_status_float``.

Contributors
------------
- klauer
