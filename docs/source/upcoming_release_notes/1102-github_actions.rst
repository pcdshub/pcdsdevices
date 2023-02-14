1102 github_actions
#################

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
- N/A

Maintenance
-----------
- pcdsdevices no longer uses Travis CI and has migrated to GitHub Actions for
  continuous integration, testing, and documentation deployment.
- pcdsdevices has been migrated to use setuptools-scm, replacing versioneer, as
  its version-string management tool of choice.
- pcdsdevices has been migrated to use the modern ``pyproject.toml``, replacing
  ``setup.py`` and related files.
- Older language features and syntax found in the repository have been updated
  to Python 3.9+ standards by way of ``pyupgrade``.
- Sphinx 6.0 is now supported for documentation building.
- ``docs-versions-menu`` replaces ``doctr-versions-menu`` and ``doctr`` usage
  for documentation deployment on GitHub Actions.  The deployment key is now
  no longer required.

Contributors
------------
- klauer
