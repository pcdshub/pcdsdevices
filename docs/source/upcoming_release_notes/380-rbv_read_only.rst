380 Read-only RBV
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
- A read-only PV was erroneously marked as read-write in
  :class:`pcdsdevices.gauge.GaugeSerialGPI`, component ``autozero``.
  All other devices were audited, finding no other RBV-related read-only items.

Maintenance
-----------
- N/A

Contributors
------------
- klauer
