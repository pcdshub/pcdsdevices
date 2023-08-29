1157 api_motion_pv_cull
#######################

API Changes
-----------
- Remove rarely-used TwinCAT state config PVs from `TwinCATStateConfigOne`
  that are also being removed from the IOCs.
  These are still available on the PLC itself.

  - ``delta``
  - ``accl``
  - ``dccl``
  - ``locked``
  - ``valid``

Features
--------
- N/A

Device Updates
--------------
- Add the following signals to `BeckhoffAxis`:

  - ``enc_count``: the raw encoder count.
  - ``pos_diff``: the distance between the readback and trajectory setpoint.
  - ``hardware_enable``: an indicator for hardware enable signals, such as STO buttons.

New Devices
-----------
- Add `BeckhoffAxisEPS`, which has the new-style EPS PVs on its directional and power enables.
  These correspond to structured EPS logic on the PLC that can be inspected from higher level applications.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
