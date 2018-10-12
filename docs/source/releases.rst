Release History
###############

v1.0.0 (2018-10-12)
===================

Features
--------
- Display current position in ``umv`` progress bars
- Added ``ophyd`` ``Kind`` specification to every device in the library
- Added ``.DESC`` field to standard motor interface
- Added ``trigger`` to event sequencer and other changes to make it more
  useful in scans
- Added ``CCM`` class
- Added ``BeckhoffAxis`` class for the Beckhoff ADS-based motor record
- Added evr ``Trigger`` class for configuring evr triggers
- Added ``FeeAtt`` class for the wonky FEE attenuator
- Clean up ``Reflaser`` classes
- Added ``LensStack`` class python2 port for the xyz focusing assembly
  (not fully complete)
- Added ``DelayStage`` class for laser delay stages
- Added ``SyncAxes`` class for synchronizing axes e.g. tables, ccm
- Added ``keypress`` utilities python2 port
- Added ``wm_update`` python2 port to ``FltMvInterface``. This is essentially a
  ``camonitor``.
- Added ``mv_ginput`` python2 port to ``FltMvInterface``
- Added per-class icons to be picked up by ``lightpath`` and other
  applications

Bugfixes
--------
- Use ``IMAGE2`` instead of ``IMAGE1`` as the area detector default, because
  this is the low rate or binned image. Avoid sending huge images quickly
  through python processes.
- Prevent issue where presets from same-named device would interfere with
  eachother.
- Attenuator subclasses now have sane names
  (previously ``Attenuator1234567``, for example).
- Split the XPP and XCS lodcm foils (they are different).
- Warn the user about using certain classes directly when they need to be
  subclassed.
- Raise errors for any invalid state in a state positioner, not just the
  ``Unknown`` state.
- Add ``SUB_STATE`` subscription types for ``OffsetMirror`` and ``Attenuator``
- Valve interlock had inverted logic

Maintenance
-----------
- Standardize component imports as ``import Component as Cpt``
- Move some interlocks into ``check_value`` instead of ad-hoc locations
- Misc travis fixes and improvements
- State devices are more forgiving with certain inputs
- Clean up the `Slit` interface for ``lightpath``

API Breaks
----------
- Rework and improve various simulated hardware, removing old ``sim`` modules.
- Require some newer modules


v0.8.0 (2018-05-27)
===================

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
