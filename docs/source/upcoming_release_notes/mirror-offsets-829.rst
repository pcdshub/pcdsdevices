mirror-offsets 829
##################

API Changes
-----------
- N/A

Features
--------
- Add UpdateComponent, a component class to upgrade component args
  in subclasses.

Device Updates
--------------
- Set various beamline component motor offset signals to read-only, using the
  new BeckhoffAxisNoOffset class,  to prevent  accidental changes.
  These are static components that have no need for this level of
  customization, which tends to just cause confusion.

New Devices
-----------
- Add BeckhoffAxisNoOffset, a varition on BeckhoffAxis that uses
  UpdateComponent to remove write access on the user offset signals.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
- ZLLentz
