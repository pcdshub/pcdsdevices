1106 optics_cooling
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- `XOffsetMirrorBend` gets cooling PVs: `FWM:*_RBV` and `PRSM:*_RBV`
  `KBOMirrorHE` set PVs to `FWM` and `PRSM` to match ccc.
  `Mono` set PVs to `FWM` and `PRSM` to match ccc.

New Devices
-----------
- `XOffsetMirrorStateCool` created for offset mirrors with state and cooling.

Bugfixes
--------
- N/A

Maintenance
-----------
- removed `CoatingState` class, used `@reorder_components` instead.

Contributors
------------
- N/A
