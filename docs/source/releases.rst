Release History
###############

v0.8.0 (2018-05-27)
============

Features
--------
- Added `AvgSignal` class. This can be used when you want to
  run a callback on a rolling average of a ``Signal``. (#227)
- Added an average of the gas detector energy to the `BeamStats` class (#227)
- Implemented motor `.SPG` field from LCLS motor record into PCDSMotorBase (#236)

Bugfixes
--------
- Fix a bug where the `LODCM` class had a ``readback`` signal with an invalid PV. (#232)
- Fix a bug where the tests would never pass, ever (#238)

v0.7.0 (2018-05-08)
===================

Features
--------
- Revamp states handling for devices like IPM and XFLS (#205)
- Add a `BeamStats` class (#200)
- Add an `EventSequencer` class (#196)
- Add ``DISP`` field to `PCDSMotorBase` (#192)

Bugfixes
--------
- Fix a bug where preset saving could break the session if passed bad arguments (#218)
- Fix a bug where malformed states could fail silently or cryptically (#216)
- Fix a bug where the mirror states were reversed (#215)
- Fix a bug where IMS velocity limits were ignored (#209)

v0.6.0 (2018-04-05)
===================

Features
--------
- Improved documentation (#170)
- Recreated the presets feature from existing hutch_python deployments.
  This allows operators to record the positions of anything that implements
  the `FltMvInterface` to a ``YAML`` file. This helps keep track of various
  important experimental motor positions that are too dynamic to place in EPICS. (#187)

Bugfixes
--------
- Fixed a rare race condition in the testing suite (#189)

CI
--
- Testing suite now uses the conda-forge build of ophyd instead of NSLS-II lightsource2-tag (#191)

v0.5.0 (2018-03-08)
===================

API Changes
-----------
- The `pcdsdevices.EpicsMotor` has been replaced by
  `pcdsdevices.PCDSMotorBase` and three child classes
  `IMS`, `Newport` and `PMC100`. This is an attempt to have a reasonable MRO
  for the discrepenacies between all our different implementations
  of the EPICS Motor Record (#167)
- Due to the growing complication of the Daq class and related utilities,
  all related functions were moved to `<https://pcdshub.github.io/pcdsdaq>`_ (#168)
