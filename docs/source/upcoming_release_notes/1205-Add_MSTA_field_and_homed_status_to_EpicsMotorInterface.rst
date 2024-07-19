1205 Add MSTA field and homed status to EpicsMotorInterface
#################

API Breaks
----------
- N/A

Features
--------
- MstaEnum: Enum describing the motor record MSTA bits

Device Updates
--------------
- EpicsMotorInterface: Add a "raw" MSTA value, as well as the interpreted
                       values as a dictionary. Adds a "homed" property based
                       based on this.

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
- slactjohnson
