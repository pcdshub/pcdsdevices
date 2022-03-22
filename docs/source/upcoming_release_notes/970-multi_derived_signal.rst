970 multi_derived_signal
#################

API Changes
-----------
- N/A

Features
--------
- Added new ``AggregateSignal`` variant ``MultiDerivedSignal``.  With a list of
  signal names and a calculation function, it is now possible to create a new
  signal derived from the values of the provided signals. For example, if a
  hutch has many temperature sensors - each with their own corresponding
  ``EpicsSignal`` instance - a signal that shows the maximum value from all of
  those temperatures would be easy to implement.

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
- Removed deprecation warning from ``pcdsdevices.utils`` import.

Contributors
------------
- klauer
