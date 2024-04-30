1205 Add MSTA field and homed status to EpicsMotorInterface
#################

API Breaks
----------
- N/A

Features
--------
- MstaEnum: Enum describing the motor record MSTA bits
- NewportMstaEnum: Enum describing the special Newport motor record MSTA bits
- IMSMstaEnum: Enum describing the special IMS motor record MSTA bits

Device Updates
--------------
- EpicsMotorInterface: Add a "raw" MSTA value, as well as the interpreted
                       values as a dictionary. Adds a "homed" property based
                       on this. Uses a "generic" MstaEnum class.
- Newport: Add a "raw" MSTA value, as well as the interpreted values as a
           dictionary. Adds a "homed" property based on this. Uses the
           "NewportMstaEnum" class.
- IMS: Add a "raw" MSTA value, as well as the interpreted values as a
       dictionary. Adds a "homed" property based on this. Uses the
       "IMSMstaEnum" class.
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
