1297 avgsignal_trigger
######################

API Breaks
----------
- N/A

Library Features
----------------
- Add the capability for `AvgSignal` to reset itself on trigger,
  then wait a duration before marking the trigger as complete.
  This lets you use `AvgSignal` in a bluesky plan as a way to
  accumulate the time average of a fast-updating signal at each
  scan point. To enable this, provide a ``duration`` argument.

Device Features
---------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- N/A

Maintenance
-----------
- Add unit tests for the new `AvgSignal` features.

Contributors
------------
- mseaberg
- zllentz
