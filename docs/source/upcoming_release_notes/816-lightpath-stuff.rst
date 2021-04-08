816 lightpath-stuff
###################

API Changes
-----------
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
- Increase the retry delay in lightpath state updater to avoid issue where
  long lightpaths would fail to update the first few devices in the path.
- Fix issue where LICMirror would appear blocking in the mirror states on
  lightpath.
- Fix issue where PowerSlits would appear blocking on lightpath for some
  positions reached by fulfilling normal PMPS requests.
- Fix issue where SxtTestAbsorber would report no status on lightpath.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
