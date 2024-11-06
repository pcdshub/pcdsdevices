1304 chin-rtds
#################

API Breaks
----------
- `FFMirrorZ` components `chin_left_rtd`, `chin_right_rtd`, and `chin_tail_rtd` are renamed: `mirror_temp_[l,r,tail]`.

Library Features
----------------
- N/A

Device Features
---------------
- `KBOMirrorHE` gets 2 new RTD readouts for RTDs installed on the mirror inside vaccum.

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- reorder `cool_flow1` and `cool_flow2` components in `KBOMirrorHE` to the end of the list.
- reorder `mirror_temp_[l,r,tail]` components in `FFMirrorZ` to align with other temperature sensors.

Contributors
------------
- nrwslac
