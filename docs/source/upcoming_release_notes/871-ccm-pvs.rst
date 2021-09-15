871 ccm-pvs
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- Switch the CCM energy devices to use user PVs as the canonical source
  of calculation constants. This allows the constants to be consistent
  between sessions and keeps different sessions in sync with each other.
- Add ``CCM.energy.set_current_position`` utility for adjusting the CCM
  theta0 offset in order to synchronize the calculation with a known
  photon energy values.

New Devices
-----------
- N/A

Bugfixes
--------
- Fix an issue where epics motors could time out on the getting of
  the ``egu`` property, which was causing issues with the displaying
  of device status.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
