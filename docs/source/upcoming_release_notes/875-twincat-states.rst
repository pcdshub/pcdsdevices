twincat-states 875
##################

API Changes
-----------
- TwinCATStateConfigAll has been removed. This was considered an
  internal API.

Features
--------
- Update TwinCATStatePositioner to have a configurable and variable number
  of state configuration PVs. These are the structures that allow you to
  check and change state setpoints, deltas, velocities, etc. This is
  implemented through the new TwinCATStateDynamic class.
- Increase the maximum number of connected state configuration records to
  match the current motion library limit (9)

Device Updates
--------------
- Using the new TwinCATStateDynamic mechanisms and the UpdateComponent,
  Update the following classes to contain exactly the correct number of
  twincat configuration states in their component state records:
  - ArrivalTimeMonitor (6)
  - AttenuatorSXR_Ladder (9)
  - AT2L0 (2)
  - FEESolidAttenuatorBlade (2)
  - LaserInCoupling (2)
  - PPM (4)
  - ReflaserL2SI (2)
  - WavefrontSensorTarget (6)
  - XPIM (4)

New Devices
-----------
- Add TM2K2, a variant of the ArrivalTimeMonitor class that has an extra
  state (7). The real TM2K2 has one extra target holder compared to the
  standard ArrivalTimeMonitor.

Bugfixes
--------
- Fix subtle bugs related to the UpdateComponent and using copy vs deepcopy.
  This was needed to make the dynamic state classes easy to customize.
- Add an extra error state in UpdateComponent for when you've made a typo
  in your component name. Previously this would give a confusing NameError.

Maintenance
-----------
- Add various missing docstrings and type annotations.

Contributors
------------
- zllentz
