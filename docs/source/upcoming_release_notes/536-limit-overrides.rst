IssueNumber Title
#################

API Changes
-----------
- N/A

Features
--------
- Epics motors can now have local limits updated per-session, rather than
  only having the option of the EPICS limits. Setting limits attributes will
  update the python limits, putting to the limits PVs will update the limits
  PVs.

Device Updates
--------------
- N/A

New Devices
-----------
- N/A

Bugfixes
--------
- Fix issue where putting to the limits property would update live PVs,
  contrary to the behavior of all other limits attributes in ophyd.
- Fix issue where doing a getattr on the limits properties would fetch
  live PVs, which can cause slowdowns and instabilities.

Maintenance
-----------
- Use more of the built-in ophyd mechanisms for limits rather than
  relying on local overrides.

Contributors
------------
- zllentz
