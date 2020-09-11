IssueNumber Title
#################

API Changes
-----------
- N/A

Features
--------
- Add PVPositionerDone, a setpoint-only PVPositioner class that is done moving
  immediately. This is not much more useful than just using a PV, but it is
  compatibile with pseudopositioners and has a built-in filter for ignoring
  small moves.

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- Rework BeamEnergyPositioner to be setpoint-only to work properly
  with the behavior of the energy PVs.

Maintenance
-----------
- N/A

Contributors
------------
- N/A
