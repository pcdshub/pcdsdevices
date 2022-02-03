935 fix_edit_md
#################

API Changes
-----------
- N/A

Features
--------
- State names are no longer case-sensitive.

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- EpicsSignalEditMD will be more lenient for cases where we have unset
  metadata strings ("Invalid") from TwinCAT. This fixes recent issues
  involving terminal spam and failure to update enum strings for
  devices like the solid attenuators.
- EpicsSignalEditMD will not send metadata updates until all composite
  signals have connected and updated us with their values.

Maintenance
-----------
- HelpfulIntEnum has been vendored from pcdsutils. This will be
  switched to an import in a future release.

Contributors
------------
- klauer
- zllentz
- tangkong
