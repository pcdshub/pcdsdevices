767 fix_ucds_unit_md_callback
#############################

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
- :class:`~pcdsdevices.signal.UnitConversionDerivedSignal` will now pass
  through the ``units`` keyword argument in its metadata (``SUB_META`` or
  ``'meta'``) callbacks.  It will be included even if the original signal
  did not include ``units`` in metadata callbacks. (#767)

Maintenance
-----------
- N/A

Contributors
------------
- klauer
