1219 bug_lp_thread_overschedule
###############################

API Breaks
----------
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
- Prevent some devices from creating threads at high frequency when
  trying to get the lightpath state.  These devices classes include
  `XOffsetMirrorXYState`, `AttenuatorSXR_Ladder`,
  `AttenuatorSXR_LadderTwoBladeLBD`, `AT2L0`, `XCSLODCM`, and `XPPLODCM`

Maintenance
-----------
- N/A

Contributors
------------
- tangkong
