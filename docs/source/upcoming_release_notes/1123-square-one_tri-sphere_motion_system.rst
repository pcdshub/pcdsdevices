1123 square-one tri-sphere motion system
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
- SQR1Axis: A class representing a single axis of the tri-sphere motion system. It inherits
  from PVPositionerIsClose and includes attributes for setpoint, readback, actuation, and
  stopping the motion.
- SQR1: A class representing the entire tri-sphere motion system. It is a Device that
  aggregates multiple SQR1Axis instances for each axis. It also includes methods for
  multi-axis movement and stopping the motion.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- baljamal
