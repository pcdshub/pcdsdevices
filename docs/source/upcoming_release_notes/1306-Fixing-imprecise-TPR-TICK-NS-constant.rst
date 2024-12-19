1306 Fixing-imprecise-TPR-TICK-NS-constant
#################

API Breaks
----------
- N/A

Library Features
----------------
- N/A

Device Features
---------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- _get_delay, and by extension TprMotor.readback.get() and TprTrigger.ns_delay.get() will no longer calculate wrong delays
because TPR_TICK_NS is now set to the "exact" 70/13 instead of the approximate 5.384.

Maintenance
-----------
- N/A

Contributors
------------
- KaushikMalapati
