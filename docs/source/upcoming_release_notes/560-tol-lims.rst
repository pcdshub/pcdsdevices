560 CCM Tols and Lims
#####################

API Changes
-----------
- N/A

Features
--------
- N/A

Device Updates
--------------
- CCM energy limited to the range of 4 to 25 keV
- CCM theta2fine done moving tolerance raised to 0.01
- Beam request default move start tolerance dropped to 5eV

New Devices
-----------
- N/A

Bugfixes
--------
- Fix bug on beam request where you could not override the tolerance
  via init kwarg, despite docstring's indication.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
