537 tab_component_names failing and inheritance issues
######################################################

API Changes
-----------
- :class:`BaseInterface` no longer inherits from :class:`ophyd.OphydObject`.
- The order of multiple inheritance for many devices using the LCLS-enhanced
  :class:`BaseInterface`, :class:`MvInterface`, and :class:`FltMvInterface` has
  been changed.

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
- Tab completion for many devices has been fixed. Regression tests have been
  added.

Maintenance
-----------
- N/A

Contributors
------------
- klauer
- zrylettc
