736 sxr_solid_attenuators
#########################

API Changes
-----------
- Added ``format`` and ``scale`` arguments to
  :func:`~pcdsdevices.utils.get_status_float`, which are affect floating point
  formatting of values available in the ``status_info`` dictionary.

Features
--------
- Added :func:`~pcdsdevices.utils.format_status_table` for ease of generating
  status tables from ``status_info`` dictionaries.
- Added :func:`~pcdsdevices.utils.combine_status_info` to simplify joining
  status information of child components.

Device Updates
--------------
- Added the ``active`` component to
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorFilter`, indicating
  whether or not the filter should be used in calculations.

New Devices
-----------
- Added :class:`~pcdsdevices.attenuator.AT1K4` and supporting SXR solid
  attenuator classes, including
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorSXR_Blade`,
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorSXR_FourBlade`, and
  :class:`~pcdsdevices.attenuator.AttenuatorSXR_Ladder`.

Bugfixes
--------
- N/A

Maintenance
-----------
- Updated AT2L0 to use newer status formatting utilities.
- Added prettytable as an explicit dependency.  It was previously assumed to
  be installed with a sub-dependency.

Contributors
------------
- klauer
