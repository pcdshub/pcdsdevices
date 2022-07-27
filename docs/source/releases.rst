Release History
###############

v6.3.0 (2022-07-27)
===================

Features
--------
- Add new module for controlling intensity of LEDs or Fiber-Lites, ``light_control.py``.
  CvmiLed from cvmi_motion.py has been moved to this new module and renamed to ``LightControl``.

Device Updates
--------------
- ``TM2K4`` now has its own class with 5 position states (4 targets and and OUT state)
- Upgrade ``BeamEnergyRequest`` from ``BaseInterface`` to ``FltMvInterface``
  to pick up all the move aliases.
- slits.py: add 'hg', 'ho', 'vg', 'vo' to tab_whitelist in ``SlitsBase``, upon request from the XPP scientists
- New ``set_zero`` method to ``DelayBase``

New Devices
-----------
- ``UsDigitalUsbEncoder`` in ``pcdsdevices.usb_encoder``.
  This is the EPICS interface for configuring the scale/offset of these encoders that are used in the DAQ.

Maintenance
-----------
- Delay the import of ``pint`` so that sessions with no unit conversions can
  start up 2 seconds faster.

Contributors
------------
- mbosum
- vespos
- wwright-slac
- zllentz


v6.2.0 (2022-06-20)
===================

Device Updates
--------------
- Add IMS.setup_pmgr as a public API for applications that want to initialize
  pmgr support before the first device uses it. This was previously private
  API at IMS._setup_pmgr.
- Added LED control PVs to CVMI motion class.

New Devices
-----------
- Added ItechRfof class: Instrumentation Technologies RF over Fiber unit

Bugfixes
--------
- Create the pmgr resources when they are first used rather than on IMS
  init, saving 3 seconds of startup time for users that don't need
  pmgr resources.

Maintenance
-----------
- Vendor happi.device.Device as LegacyItem instead of importing it, pending
  deprecation of the happi.device module.

Contributors
------------
- Mbosum
- mcb64
- slactjohnson
- wwright-slac
- zllentz


v6.1.0 (2022-06-03)
===================

Device Updates
--------------
- Updated the Laser Beam Transport Protection system configuration to
  reflect the latest PLC/IOC changes: the image sum from near and
  far-field cameras is now used instead of centroid positioning.
  The relevant screens have been updated as well.
- Added an optional ``acr_status_suffix`` argument to ``BeamEnergyRequest`` that
  instantiates an alternate version of the class that waits on an ACR PV to
  know when the motion is done. This is a more suitable version of the class
  for step scans and a less suitable version of the class for fly scans.

New Devices
-----------
- Added ``KBOMirrorHEStates`` - a class for KBO mirrors with coating states
  and cooling.
- Added ``KBOMirrorStates`` - a class for KBO mirrors with coating states
  and no cooling.

Bugfixes
--------
- Fixed the ``Stopper`` ``happi`` container definition.
- Removed unusable ``bunch_charge_2`` signal from LCLS beam stats. This PV seems
  to contain a stale value that disagrees with ``bunch_charge`` and causes EPICS
  errors on certain hosts.

Maintenance
-----------
- Added a run constraint for pyqt to avoid latest while we work out testing
  failures.

Contributors
------------
- klauer
- nrwslac
- tangkong
- zllentz


v6.0.0 (2022-05-03)
===================

API Changes
-----------
- ``MultiDerivedSignal`` and ``MultiDerivedSignalRO`` calculation functions
  (``calculate_on_get`` and ``calculate_on_put``) now take new signatures.
  Calculation functions may be either methods on an ``ophyd.Device`` (with
  ``self``) or standalone functions with the following signature:
  .. code::
    calculate_on_get(mds: MultiDerivedSignal, items: SignalToValue) -> OphydDataType
    calculate_on_put(mds: MultiDerivedSignal, value: OphydDataType) -> SignalToValue

Features
--------
- adds ``.screen()`` method to BaseInterface, which opens a typhos screen
- adds AreaDetector specific ``.screen()`` method, which calls camViewer
- Add utilities for rearranging the order of components as seen by typhos.
  This can be helpful for classes that inherit components from other classes
  if they want to slot their new components in at specific places in the
  automatic typhos tree.

Device Updates
--------------
- Added "ref" signal to "BeamEnergyRequest" to track the energy
  reference PV.
- ``TwinCATStatePositioner`` has been updated due to underlying
  ``MultiDerivedSignal`` API changes.
- TM1K4 now has its own class with 8 position states (7 targets and and OUT state)
- Updated AT2L0 to utilize newly implemented MultiderivedSignal for error checking and clearing in GUI and at the command line
- Updated AT2L0 Typhos GUI, includes error clearing button and display of error on individual blades
- clear_errors() method for AT2L0 to clear errors; e.g. at2l0.clear_errors()
- print_errors() method for AT2l0 to print error summary; e.g. at2l0.print_errors()

New Devices
-----------
- New ``JJSlits`` class and typhos screen for controlling JJSlits model AT-C8-HV with Beckhoff controls.
- XOffsetMirrorRTDs, offset mirrors with RTDs for measuring temperatures.
- FFMirrorZ, an extension to FFMirror to add a Z axis.
- The X apertures for AT1K0 now have their own device with 1 state, "centered"
- The Y apertures for AT1K0 now have their own device with 4 states, ["5.5mm","8mm","10mm","13mm"]
- OpticsPitchNotepad - a class for storing pitch positions based on state in a notepad IOC
  for mr1l0, mr2l0, mr1l4, mr1l3, and mr2l3.

Bugfixes
--------
- Fix calls to ipm_screen.
- Fix an issue where Beckhoff motion error reset signals could not be set twice in the same session.
- Fix an issue where the TMO Spectrometer and the HXRSSS would spam errors
  when loaded in lightpath.

Maintenance
-----------
- Ran pre-commit on all files in the repository, except the ones where it
  causes issues. Update the CI to require these checks to pass. (passive
  update, this is the new pcds-ci-helpers master). Notable changes were
  related to import sorting and removal of trailing whitespace.

Contributors
------------
- klauer
- mbosum
- mkestra
- nrwslac
- rsmm97
- tangkong
- zllentz


v5.2.0 (2022-03-31)
===================

Features
--------
- Added a post_elog_status method to the ``BaseInterface`` class, which posts to the registered primary elog if it exists.
- Added a function for posting ophyd object status (and lists of objects) to the ELog as html.
- Added new ``AggregateSignal`` variant ``MultiDerivedSignal``.  With a list of
  signal names and a calculation function, it is now possible to create a new
  signal derived from the values of the provided signals. For example, if a
  hutch has many temperature sensors - each with their own corresponding
  ``EpicsSignal`` instance - a signal that shows the maximum value from all of
  those temperatures would be easy to implement.
- Added the scale keyword argument to tweak() method, allowing the user to pick the initial step size.

Device Updates
--------------
- Added the Y axis to the ``KBOMirror`` status printout
- TwinCAT state devices now have a top-level "state_velo" summary signal.
  This can be used to view the highest speed of all the configured state
  speeds, and it can also be used to do a bulk edit. These are stored per
  state destination in the IOC.
- Added a biological parent attribute to ``GroupDevice``, for tracking parents without alerting stage() methods
- Added the current monitoring PV to ``pcdsdevices.pump.PTMPLC``.
- Allow for user offsets to TMO Spectrometer motors.
- Commented out the GasNeedleTheta motor for 3/22 LAMPMBES configuration.

New Devices
-----------
- Added ``PCDSHDF5BlueskyTriggerable``, a variant of area detector
  specialized for doing ``bluesky`` scans.
- Added the ``KBOMirrorHE`` class to be used with KBO mirrors with cooling, like MR2K4.
- Added the laser beam transport protection system device classes and related
  screens.
- Added the Dg /DelayGenerator class to handle SRS645 delay generator
- Added the ``MMC100`` class, for motors controlled by Micronix MMC100 controllers
- Added a class for the HXR Single Shot Spectrometer.
- Add ``VRCDA``, a dual-acting valve class.

Bugfixes
--------
- Fixed an issue in sim.slow_motor classes where threading behavior could fail.
- State readbacks from preset positions are now correct.
- Fixed a race condition on initialization of new ``EpicsSignalEditMD`` and
  ``EpicsSignalROEditMD``. (#963, #978)
- Fix an issue where mirror devices had overfiltered tab completion results.

Maintenance
-----------
- Removed the instantiation of a status object at motor startup to help
  improve the performance of loading large sessions. This object was not
  strictly needed.
- Removed the deprecation warning from ``pcdsdevices.utils`` import.
- Updated the docstrings in the valve submodule with detailed descriptions.

Contributors
------------
- klauer
- mbosum
- nrwslac
- spenc333
- vespos
- tangkong
- zrylettc
- zllentz


v5.1.0 (2022-02-07)
===================

Features
--------
- Adds a new script, make_ophyd_device.py, that helps with autogeneration of
  an ophyd device class from an IOC db file. Includes a helper script.
- State names are no longer case-sensitive.

Device Updates
--------------
- Add pmgr methods to the IMS class's tab whitelist.

New Devices
-----------
- SliceDhvChannel: a device for controlling a single channel on a Vescent
  Photonics Slice-DHV controller.
- SliceDhvController: a device for controlling the controller of a Vescent
  Photonics Slice-DHV controller.
- SliceDhv: a top-level device for controlling a complete 2-channel Vescent
  Photonics Slice-DHV controller.
- QadcBase: Base class for qadc digitizers
- Qadc: Class for FMC126 (old) digitizers
- QadcSparsification: Class for holding FMC134 sparsification PVs.
- Qadc134: Class for FMC134 (new) digitizers
- Wave8V2Simple: A simple class for the LCLS-II Wave8. Provides waveforms
  and acquisition start/stop buttons.
- Wave8V2: A complete top-level class for the LCLS-II Wave8. Includes many
  configuration and diagnostic PVs, in addition to what is provided by
  Wave8V2Simple.
- DiconSwitch: new device class for the DiCon fiber switch.
- CycleRfofRx: class for Cycle RFoF receiver.
- CycleRfofTx: class for Cycle RFoF transmitter.
- Agilent53210A: Device for controlling frequency counters by the same name.
- Adds a new class to interface with the LAMP motion configuration for LV17.

Bugfixes
--------
- EpicsSignalEditMD will be more lenient for cases where we have unset
  metadata strings ("Invalid") from TwinCAT. This fixes recent issues
  involving terminal spam and failure to update enum strings for
  devices like the solid attenuators.
- EpicsSignalEditMD will not send metadata updates until all composite
  signals have connected and updated us with their values.
- Fix SL1K2 target count (2 states + out instead of default).
- Fixed mr1l0_homs and mr2l0_homs state counts in TwinCATMirrorStripe.
  This should be set to 2 for mr1l0 (B4C, B4C/Ni) and mr2l0 (B4C, Ni).

Maintenance
-----------
- ``detailed_tree.ui`` was vendored from typhos. The default attenuator screens
  AT2L0, AT1K4, and AT2K2 will now default to ``detailed_tree.ui``.
- HelpfulIntEnum has been vendored from pcdsutils. This will be
  switched to an import in a future release.

Contributors
------------
- mbosum
- klauer
- slactjohnson
- tangkong
- zllentz


v5.0.2 (2021-12-02)
===================

Bugfixes
--------
- Fix issue where EpicsSignalEditMD could log enum error messages
  for signals that did not edit their enum metadata.

Contributors
------------
- zllentz


v5.0.1 (2021-11-19)
===================

Bugfixes
--------
- CCM status representation fixed in certain situations. (#908)
- Exceptions will no longer be raised when generating device status
  representations. (#909)

Contributors
------------
- klauer


v5.0.0 (2021-11-15)
===================

API Changes
-----------
- ``TwinCATStateConfigAll`` has been removed. This was considered an
  internal API.
- ``isum`` components have been renamed to ``sum`` in IPM detector classes.
- The motor components for PIM classes have been shortened by removing
  ``_motor`` from their names (e.g. ``zoom_motor`` is now ``zoom``).
- Switch the target PVs for ``BeamEnergyRequest`` from e.g. "XPP:USR:MCC:EPHOT" to
  e.g. "XPP:USR:MCC:EPHOT:SET1", "RIX:USR:MCC:EPHOTK:SET1".

Features
--------
- ``EpicsSignalEditMD`` and ``EpicsSignalROEditMD`` now allow for overriding of
  enumeration strings (``enum_strs``) by way of a static list of strings
  (``enum_strs`` kwarg) or a list of signal attribute names (``enum_attrs``
  kwarg).
- Update ``TwinCATStatePositioner`` to have a configurable and variable number
  of state configuration PVs. These are the structures that allow you to
  check and change state setpoints, deltas, velocities, etc. This is
  implemented through the new ``TwinCATStateConfigDynamic`` class.
- Increase the maximum number of connected state configuration records to
  match the current motion library limit (9)

Device Updates
--------------
- Using the new ``TwinCATStateConfigDynamic`` mechanisms and the ``UpdateComponent``,
  update the following classes to contain exactly the correct number of
  twincat configuration states in their component state records.
  Note that the number of states here does not include the "Unknown"
  or "Moving" state associated with index 0. A device with n states will have
  typically have 1 out state and n-1 target states by this count, and the
  EPICS record will have n+1 possible enum values.
  - ``ArrivalTimeMonitor`` (6)
  - ``AttenuatorSXR_Ladder`` (9)
  - ``AT2L0`` (2)
  - ``FEESolidAttenuatorBlade`` (2)
  - ``LaserInCoupling`` (2)
  - ``PPM`` (4)
  - ``ReflaserL2SI`` (2)
  - ``WavefrontSensorTarget`` (6)
  - ``XPIM`` (4)
- The default ``theta0`` values for CCM objects has been changed from
  ``14.9792`` to ``15.1027``.
- ``IPM`` objects now have short aliases for their motors (`ty`, `dx`, `dy`).
- Reorganized the sample delivery ``Selector`` class to be composed of two
  ``Sensiron`` devices instead of a flat collection of PVs.
- In ``VGC_2S``, allow for the user to change the ``at_vac`` setpoint value
  for upstream and downstream gauges separately.
- Add the ``user_enable`` signal (``bUserEnable``) to the ``BeckhoffAxisPLC`` class.
  This is a signal that allows the user to unilaterally disable a
  running motor's power. When enabled, it is up to the controller
  whether or not to actually power the motor, but when disabled the
  power will be shut off.
- Add the ability for ``BeamEnergyRequest`` to write to PVs for either
  the K or the L line and for either bunch 1 or bunch 2 in two bunch mode.

New Devices
-----------
- Add ``TM2K2``, a variant of the ``ArrivalTimeMonitor`` class that has an extra
  state (7). The real ``TM2K2`` has one extra target holder compared to the
  standard ``ArrivalTimeMonitor``.
- ``BeckhoffAxis_Pre140`` has been added to support versions of ``lcls-twincat-motion``
  prior to ``v1.4.0``. This has been aliased to ``OldBeckhoffAxis`` for backcompat.
- Created ``Bronkhorst`` and ``Sensiron`` flow meter devices for sample delivery.
- Added the ``crix_motion.VLSOptics`` Device, which contains calculated
  axes for the VLS optical components. The rotation state of these
  crystals is approximated by a best-fit 2nd order polynomial.
- Add ``VRCClsLS``, a class for gate valves with control and closed limit switch readback.

Bugfixes
--------
- Fix subtle bugs related to the ``UpdateComponent`` and using copy vs deepcopy.
  This was needed to make the dynamic state classes easy to customize.
- Add an extra error state in ``UpdateComponent`` for when you've made a typo
  in your component name. Previously this would give a confusing ``NameError``.
- In the ``LODCM`` "inverse" calculations, return a NaN energy instead of
  raising an exception when there is a problem determining the crystal
  orientation. This prevents the calculated value from going stale when
  it has become invalid, and it prevents logger spam when this is
  called in the pseudopositioner update position callback.

Maintenance
-----------
- Add various missing docstrings and type annotations.
- Tab whitelists have been cut down to make things simpler for non-expert users.

Contributors
------------
- cymel123
- jyin999
- klauer
- mbosum
- zllentz
- zrylettc


v4.9.0 (2021-10-19)
===================

Device Updates
--------------
- Changed pv names for flow cell xyz-theta

New Devices
-----------
- LAMPFlowCell class for new 4 axis flow cell manipulator replacing cVMI on LAMP.

Bugfixes
--------
- All stop methods now use the ophyd-defined signature, including a
  keyword-only ``success`` boolean.
- Test suite utility ``find_all_classes`` will no longer report test suite
  classes.

Maintenance
-----------
- Removed prototype-grade documentation helpers in favor of those in ophyd.docs
- Added similar ``find_all_callables`` for the purposes of documentation and
  testing.
- Added documentation helper for auto-generating ``docs/source/api.rst``.  This
  should be run when devices are added, removed, or moved.
- Docstring fixup on CCM class.
- Imports changed to relative in test suite.
- Miscellaneous floating point comparison fixes for test suite.
- Fixed CCM test failure when run individually or quickly (failure when run
  less than 10 seconds after Python starts up)
- Linux-only ``test_presets`` now skips macOS as well.

Contributors
------------
- Mbosum
- klauer


v4.8.0 (2021-09-28)
===================

Features
--------
- Add ``GroupDevice``: A device that is a group of components that will act
  independently. This has some performance improvements and small optimizations
  for when we expect the different subdevices to act fully independently.
- Add a ``status`` method to ``BaseInterface`` to return the device's status
  string. This is useful for recording device status in the elog.
- Add ``typhos`` templates for ``BeckhoffSlits`` and ``PowerSlits`` using existing
  elements from their normal ``pydm`` screens.

Device Updates
--------------
- The following devices have become group devices:
  - Acromag
  - ArrivalTimeMonitor
  - BaseGon
  - BeckhoffJet
  - BeckhoffJetManipulator
  - BeckhoffJetSlits
  - CCM
  - CrystalTower1
  - CrystalTower2
  - CVMI
  - DiagnosticTower
  - ExitSlits
  - FFMirror
  - FlowIntegrator
  - GasManifold
  - ICT
  - Injector
  - IPIMB
  - IPMDiode
  - IPMMotion
  - Kappa
  - KBOMirror
  - KMono
  - KTOF
  - LAMP
  - LAMPMagneticBottle
  - LaserInCoupling
  - LCLS2ImagerBase
  - LODCM
  - LODCMEnergyC
  - LODCMEnergySi
  - Mono
  - MPODApalisModule
  - MRCO
  - OffsetMirror
  - PCM
  - PIM
  - PulsePickerInOut
  - ReflaserL2SI
  - RTDSBase
  - SamPhi
  - Selector
  - SlitsBase
  - StateRecordPositionerBase
  - VonHamosCrystal
  - VonHamosFE
  - Wave8
  - WaveFrontSensorTarget
  - XOffsetMirror
  - XYZStage
- Clean up pmgr loading on the IMS class.
- Edit stage/unstage on ``PIMY`` to be compatible with ``GroupDevice``.
- Edit stage/unstage and the class definition on ``SlitsBase`` to be
  compatible with ``GroupDevice``
- Change ``CCM`` from a ``InOutPositioner`` to a normal device with a
  ``LightpathMixin`` interface. Being a positioner that contained a bunch
  of other positioners, methods like ``move`` were extremely ambiguous
  and confusing. The ``insert`` and ``remove`` methods are re-implemented
  as they are useful enough to keep.
- Split ``CCMCalc`` into ``CCMEnergy`` and ``CCMEnergyWithVernier`` to
  make the code easier to follow
- Remove unused ``CCMCalc`` feature to move to wavelength or theta
  to make the code simpler to debug
- Add aliases to the ``CCM`` for each of the motors.
- Adjust the ``CCM`` status to be identical to that from the old python code.
- Add functions and PVs to kill and home the ``CCM`` alio
- Calculate intermediate quantities in the ``CCM`` energy calc and make them
  available in both the status and as read-only signals.
- ``EpicsMotorInterface`` subclasses will no longer spam logger errors and
  warnings about alarm issues encountered by other users. These log messages
  will only be shown if they were the result of moves in the current session.
  Note that this log filtering assumes that all epics motors will have unique
  ophyd names.
- Added ``GFS`` fault setpoint, ``GCC``, ``PIP`` auto-on and countdown timer
- Switch the ``CCM`` energy devices to use user PVs as the canonical source
  of calculation constants. This allows the constants to be consistent
  between sessions and keeps different sessions in sync with each other.
- Add ``CCM.energy.set_current_position`` utility for adjusting the ``CCM``
  theta0 offset in order to synchronize the calculation with a known
  photon energy values.

New Devices
-----------
- TMO Fresnel Photon Spectrometer Motion components class,
  ``TMOSpectrometer``

Bugfixes
--------
- Fix some race conditions in ``FuncPositioner``
- Fix a race condition in schedule_task that could cause a task to never be run
- Add a timeout parameter to ``IMS.reinitialize``, and set it as the default
  arg for use in the stage method, which is run during scans. This avoids
  a bug where the stage method could hang forever instead of erroring out,
  halting a scan in its tracks.
- Fix an issue where epics motors could time out on the getting of
  the ``egu`` property, which was causing issues with the displaying
  of device status.

Maintenance
-----------
- Move ``PVStateSignal`` from state.py to signal.py to avoid a circular import
- Make the tests importable and runnable on Windows
- Require Python 3.9 for type annotations
- Make pmgr optional, but if installed make sure it has a compatible version.
- Update to 3.9-only CI
- Fix the CI PIP test build
- Include the pcdsdevices test suite in the package distribution.
- Add missing docstrings in the ``ccm`` module where appropriate.
- Add doc kwarg to all components in the ``ccm`` module.
- Add type hints to all method signatures in the ``ccm`` module.
- Adjust the ``CCM`` unit tests appropriately.

Contributors
------------
- ghalym
- jyin999
- mbosum
- zllentz


v4.7.1 (2021-08-11)
===================

Maintenance
-----------
- Fix a packaging issue where the ui files were not included in the
  distribution.


v4.7.0 (2021-08-09)
===================

Features
--------
- Added a typhos.ui entry point, so we can version control our typhos
  templates in the same place as our device definitions. This also
  allows us to remove pcds-specific assumptions from typhos to make
  the library more community-friendly.
- Added the pcds typhos templates from typhos.

New Devices
-----------
- Add classes for controlling the new apalis mpods. The new apalis mpod
  PVs differ from previous model PVs and needed new classes to
  accommodate those changes. Features:

  - Turn on/off HV channels
  - Set current/voltage
  - Get max current/voltage
  - Clear module faults
  - Obtain module temperature
  - Power cycle mpod crate.

Maintenance
-----------
- Add missing jsonschema dependency.

Contributors
------------
- klauer
- spenc333
- zllentz


v4.6.0 (2021-07-09)
===================

Features
--------
- Add pmgr support to the `IMS` class! There are three new methods on IMS
  for interacting with pmgr: ``configure``, ``get_configuration``, and
  ``find_configuration``.

Device Updates
--------------
- User changes to offset/dir on python or UI level to MRCO motion have been disabled.
- Add the veto_device signal (:VETO_DEVICE_RBV) to the VFS class.
- `XYGridStage` now uses one file per sample instead of
  one giant file for all samples, and it writes to these files less often.
  This speeds up operations. Various additional improvements to the class.

New Devices
-----------
- Add special IM2K0 device for the new configuration of IM2K0, where we
  swapped its XTES style camera setup for a L2SI style camera setup.

Bugfixes
--------
- Fix an issue where DelayBase subclasses could spam the terminal at
  startup if we load too many devices at once.
- Fix a typo in the KBO DS Bender RMS PV.
- Fix issue where motor presets would not load until the first access of the
  presets object.
- Fix an issue where an epics motor could get stuck with a bad state of its
  set_use_switch after a call to set_current_position with a bad value.

Contributors
------------
- cristinasewell
- jsheppard95
- jyotiphy
- Mbosum
- mcb64
- zllentz


v4.5.0 (2021-06-03)
===================

Features
--------
- Add UpdateComponent, a component class to update component args
  in subclasses.

Device Updates
--------------
- Update kmono threshold for showing beam passing in lightpath
- Rename PPSStopperL2SI to PPSStopper2PV and generalize to all PPS stoppers
  whose states are determined by the combination of two PVs. The old name and
  old defaults are retained for backcompatibility and have not yet been
  deprecated. This was done to support the PVs for ST1K2 which do not follow
  any existing pattern.
- Set various beamline component motor offset signals to read-only, using the
  new BeckhoffAxisNoOffset class,  to prevent  accidental changes.
  These are static components that have no need for this level of
  customization, which tends to just cause confusion.

New Devices
-----------
- MRCO motion class for MRCO IP1 endstation in TMO.
- Added a class for the RIX ladder-style solid attenuator ``AT2K2``.
- Add BeckhoffAxisNoOffset, a varition on BeckhoffAxis that uses
  UpdateComponent to remove write access on the user offset signals.

Bugfixes
--------
- Fix issue where BeckhoffSlits devices could show metadata errors on startup
  by cleaning up the done moving handling. This would typically spam the
  terminal in cases where we were making large numbers of PV connections in
  the session at once, such as at the start of a hutch-python load.

Contributors
------------
- Mbosum
- ZLLentz
- jsheppard95
- klauer


v4.4.0 (2021-04-15)
===================

API Changes
-----------
- Move stoppers into stopper.py, but keep reverse imports for
  backwards compatibility. This will be deprecated and then removed
  at a later date.

Device Updates
--------------
- Add "confirm" variety metadata tag to ``EpicsMotorInterface`` and
  ``BeckhoffAxisPLC`` home commands, requiring user confirmation prior to
  performing the homing motion in auto-generated Typhos screens.
- Slits objects now have vo, vg, ho, and hg aliases.
- Motor objects now print out values with a precision of 3 places.
- Remove mpa3 and mpa4 from rtdsk0, they do not have filters and are always
  in invalid states that confuse the lightpath.
- Update the mono spectrometer class to provide status to lightpath.
- Make sim devices hinted by default so they show up in the
  best-effort callback in bluesky.

New Devices
-----------
- Add PPSStopperL2SI for having readbacks of the new PPS stoppers inside
  of lightpath.

Bugfixes
--------
- Fix issue where the mirror coating states were expecting the default
  'OUT' position, which does not exist on the real device.
- Fix an issue where ``ObjectComponent`` instances did not have proper class
  information.
- Increase the retry delay in lightpath state updater to avoid issue where
  long lightpaths would fail to update the first few devices in the path.
- Fix issue where LICMirror would appear blocking in the mirror states on
  lightpath.
- Fix issue where PowerSlits would appear blocking on lightpath for some
  positions reached by fulfilling normal PMPS requests.
- Fix issue where SxtTestAbsorber would report no status on lightpath.

Contributors
------------
- ZryletTC
- klauer
- zllentz


v4.3.2 (2021-04-05)
===================

Bugfixes
--------
- Fix an issue where pcdsdevices would break pyepics and ophyd in such a
  way to cause thousands of lines of teardown spam at exit.

Contributors
------------
- zllentz


v4.3.1 (2021-04-02)
===================

Features
--------
- New functions have been added to the LODCM object: `tweak_x`, `tweak_parallel`, `set_energy`, `wait_energy`.
- Custom status print has been added for the 3 towers as well as the energy classes.
- Added the `OffsetIMSWithPreset` subclass of `OffsetMotorBase` that has an additional `_SET` offset pv, and puts to this pv during `set_current_position`.

Maintenance
-----------
- Have cleaned up some docstring and changed the naming for the offset motors to the old style.

Contributors
------------
- cristinasewell


v4.3.0 (2021-04-02)
===================

API Changes
-----------
- Deprecate ``pcdsdevices.component`` in favor of ``pcdsdevices.device``
  to avoid circular imports and to more closely mirror the structure of
  ``ophyd``.

Features
--------
- Add FuncPositioner as a replacement for VirtualMotor.
  This is a "dirty" positioner intended for quick hacks
  in the beamline setup files, instantiated via handing
  various functions to the init.
- Add ``EpicsSignalEditMD`` and ``EpicsSignalROEditMD`` classes for
  situations where you need to override the control system's
  discovered metadata.
- Adding a normally open class (VRCNO) for VRC gate valves to valve module. VRCNO extends VVCNO and adds VRC functionality.
- Add ``SyncAxis`` to replace deprecated ``SyncAxesBase`` with expanded
  feature set, more sensible defaults, and more solid foundation.
- Add ``set_current_position`` to all ``PseudoPositioner`` classes.
- Add ``invert`` parameter to ``DelayBase`` for inverting any delay stage.
- Add ``set_position`` as an alias to ``set_current_position``
- New motor configuration for LAMP.  Hoping we only have two configurations to switch between
- Add ``InterfaceDevice`` and ``InterfaceComponent`` as a tool for
  including pre-build objects in a device at init time.
- Add ``to_interface`` helper function for converting normal ``Device``
  classes into ``InterfaceDevice`` classes.
- Add ``ObjectComponent`` as a tool for including pre-build objects in
  a device at class definition time.

Device Updates
--------------
- Add custom status prints for DelayBase and SyncAxis
- QminiSpectrometer: A few variety metadata updates for Typhos screens.
- Set EpicsMotor soft limit kinds to "config" for use in typhos.

New Devices
-----------
- QminiWithEvr: A new class with added PVs for controlling an EVR from a
  Typhos screen.
- LAMPMagneticBottle
- XOffsetMirrorState for mirror coatings

Bugfixes
--------
- Include hacky fix from XPP/XCS that allows LaserTiming to complete moves
  in all situations. The real cause and ideas for a clean fix are not
  currently known/explored.
- Fix issue where Newport motors would not show units in their status prints.
- Fix issue where SyncAxis was not compatible with PseudoPositioners as
  its synchronized "real" motors.
- Fix an issue where calling ``set_current_position`` on certain motors would
  cause the ipython session to freeze, leaving the motor in the ``set`` state
  instead of bringing it back to the ``use`` state.
- Hacky workaround for IMS motor part number strings being unable to be read
  through pyepics when they contain invalid utf-8 characters.
- Fix issue where ``Newport`` user_readback had incorrect metadata.
- :class:`~pcdsdevices.signal.UnitConversionDerivedSignal` will now pass
  through the ``units`` keyword argument in its metadata (``SUB_META`` or
  ``'meta'``) callbacks.  It will be included even if the original signal
  did not include ``units`` in metadata callbacks. (#767)
- Fix an issue where various special Signal classes had their kinds
  improperly reported as "hinted".

Maintenance
-----------
- Make unit handling in status_info more consistent to improve reliability of
  status printouts.

Contributors
------------
- Mbosum
- ghalym
- klauer
- tjohnson
- zllentz


v4.2.0 (2021-03-03)
===================

Features
--------
- Happi IOC Data: added new EntryInfo to happi.containers.LCLSItem  for ioc
  configuration data including engineer, location, hutch, release, arch, name,
  and ioc type.
- New containers: added new Happi containers with device specific metadata for
  building MODS IOCs.
- Custom status print for `LODCM` object.
- Added the `MPOD` class that determines the appropriate MPOD Channel classes. This is to help support the happi entry creation from the questionnaire.
- Add custom status for LaserTiming and for PseudoSingleInterface
- Add verbose_name attribute to PseudoSingleInterface and caclulated dial position
- Add verbose_name property to LaserTiming

Device Updates
--------------
- `LODCM` object has been updated to contain the Energy motors as well as the other motors and offsets.
- Update various signal kinds on PTMPLC from omitted to normal or config as
  appropriate.
- ThorlabsWfs40: Added wavefront PV and viewer, added some docs

New Devices
-----------
- `OffsetMotor` - PseudoPositioner with an offset
- Add GHCPLC (Hot Cathode) class as a counterpart to the GCCPLC (Cold Cathode)
  class.

Bugfixes
--------
- Fix issue where the Kappa had an incorrect e_phi calculation
  in certain situations.
- Fix issue where the Kappa used the calculated motors for the
  safety check instead of the real motors.
- Fix issue where legacy attenuator classes would break bluesky scans.
- Fix Kappa behavior for kappa angles above 180 degrees.

Contributors
------------
- cristinasewell
- klauer
- slacAdpai
- slactjohnson
- zllentz


v4.1.0 (2021-02-10)
===================

API Changes
-----------
- Update twincat motors to use the correct homing PV.
  This is an alternative PV to the normal motor record PVs for IOC/PLC
  management reasons.
  It is possible that this will break devices that have not updated to the
  latest motion PLC library.
- Added ``format`` and ``scale`` arguments to
  :func:`~pcdsdevices.utils.get_status_float`, which affect floating point
  formatting of values available in the ``status_info`` dictionary.
- CVMI Motion System Prefix: 'TMO:CVMI'
- KTOF Motion System Prefix: 'TMO:KTOF'

Features
--------
- Added :func:`~pcdsdevices.utils.format_status_table` for ease of generating
  status tables from ``status_info`` dictionaries.
- Added :func:`~pcdsdevices.utils.combine_status_info` to simplify joining
  status information of child components.

Device Updates
--------------
- VCN upper limit can be changed from epics.
- Added the ``active`` component to
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorFilter`, indicating
  whether or not the filter should be used in calculations.
- Multiple devices have been modified to include explicit argument and keyword
  argument names in ``__init__`` for clarity and introspectability.

New Devices
-----------
- XYGridStage - maps targets from grids to x,y positions, and supports multiple samples on a stage.
- Added :class:`~pcdsdevices.attenuator.AT1K4` and supporting SXR solid
  attenuator classes, including
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorSXR_Blade`,
  :class:`~pcdsdevices.attenuator.AttenuatorCalculatorSXR_FourBlade`, and
  :class:`~pcdsdevices.attenuator.AttenuatorSXR_Ladder`.
- pcdsdevices.cvmi_motion.CVMI
- pcdsdevices.cvmi_motion.KTOF

Bugfixes
--------
- The transmission status value for the 3rd harmonic has been fixed, it was previously using the wrong value.

Maintenance
-----------
- The test suite will now find all devices in pcdsdevices submodules at
  arbitrary import depth.
- Minor cleanup of the pcds-tag conda recipe
- Relocate happi name length restriction for lcls devices to this package
  as a requirement on LCLSItem
- Updated AT2L0 to use newer status formatting utilities.
- Added prettytable as an explicit dependency.  It was previously assumed to
  be installed with a sub-dependency.
- Added test suite to try to instantiate all device classes with
  ``make_fake_device`` and perform status print formatting checks on them.
- Added ``include_plus_sign`` option for ``get_status_float``.
- Perform continuous integration tests with pip-based installs, with
  dependencies installed from PyPI.

Contributors
------------
- cristinasewell
- ghalym
- jsheppard95
- klauer
- zllentz


v4.0.0 (2020-12-22)
===================

API Changes
-----------
- On our EPICS motor classes, remove the ability to use setattr for
  `low_limit` and `high_limit`.
- SmarActOpenLoop: Combined scan_move_cmd and scan_pos into single EpicsSignal,
  scan_move, with separate read and write PVs.

Features
--------
- Added pseudo motors and related calculations to the `Kappa` object.
- Added two methods to `EpicsMotorInterface`: `set_high_limit()` and `set_low_limit()`, as well as `get_low_limit()` and `get_high_limit()`.
- Added a little method to clear limits: `clear_limits` - by EPICS convention, this sets both limits to 0.
- Added 3rd harmonic frequncy transmission info to the status print for the Attenuator.
- Added custom status print for `XOffsetMirror`, `OffsetMirror`, `KBOMirror`, and `FFMirror`.
- Add custom status print for `gon` classes: `BaseGon`, and `XYZStage` class.
- Add notepad signals to `LaserTiming` and `DelayBase` classes

Device Updates
--------------
- Instead of creating separated devices for Fundamental Frequency and 3rd Harmonic Frequency, we are now creating Attenuators that have both frequencies.
- EpicsMotorInterface: Add metadata to various upstream Ophyd methods to clean
  up screens generated via Typhos.
- Allow negative positions in `LaserTiming` and `LaserTimingCompensation`
  devices
- Add LED power to the Mono device.
- led metadata scalar range

New Devices
-----------
- Added `ExitSlits` device.

Bugfixes
--------
- sequencer.EventSequencer.EventSequence: Add an explicit put to SEQ.PROC to
  force the event sequencer to update with the new sequence.
- Fix position handling in `ReversedTimeToolDelay`
- AvgSignal will no longer spam exceptions text to the terminal when the signal
  it is averaging is disconnected. This will primarily be noticed in the
  BeamStats class, loaded in every hutch-python session.

Contributors
------------
- ZryletTC
- cristinasewell
- ghalym
- tjohnson
- zllentz


v3.3.0 (2020-11-17)
===================

API Changes
-----------
- The belens classes use ``pcdscalc`` to handle their calculations,
  changing the lens file specifications as follows:

  - Changed the ``read_lens`` to open a normal file instead of a ``.yaml``
    file, and to be able to read one lens set at the time from a file
    with multiple lens sets.
  - Changed the ``create_lens`` methods to use a normal file instead of
    ``.yaml`` file, and also to be able to create a set with multiple sets of lens.

- This is not expected to be breaking, as this feature
  is underused in the deployed environments.

Features
--------
- Added a ``LensStack.set_lens_set`` method to allow the user
  to choose what set from the file to use for calculations.
- Added a factory function ``acromag_ch_factory_func`` to
  support the creation of happi entries from the questionnaire
  for a single acromag channel.

  - Added an alias for this function ``AcromagChannel``.

- Added a custom status print for motors by overriding the status info handler.
- Added a new component for ``EpicsMotorInterface.dial_position``
- Added a new method ``EpicsMotorInterface.check_limit_switches`` to return a
  string visualization of the limit switch state.
- Added a custom status print for slits by overriding the status info handler.
- Added a helper function in ``utils.get_status_value`` to support getting
  a value from a dictionary.
- Added a custom status print for PIM by overriding the status info handler.
- Added a custom status print for IPM by overriding the status info handler.

Device Updates
--------------
- ``SmarActOpenLoop``: open loop steps signal changed to RO.
  Added some docs.
- ``PCDSAreaDetectorTyphosBeamStats`` Now sub-classes
  ``PCDSAreaDetectorTyphosTrigger``
- ``TuttiFrutti``: Change camera class to ``LasBasler``

New Devices
-----------
- ``BaslerBase``: Base class for inheriting some Basler-specific PVs.
- ``Basler``: Class for "typical" Basler deployed in a hutch.
- ``LasBasler``: Class for more laser-specific Basler cameras.
- ``MPODChannelHV``, and ``MPODChannelLV`` for MPOD high voltage and
  low voltage channels, respectively.
- Added the ``AcromagChannel`` that supports the creation of an Acromag Channel signal
- Added ``mirror.XOffsetMirrorBend`` class for offset mirrors with benders.
- Added ``mirror.XOffsetMirrorSwitch``.
  This is nearly identical to mirror.XOffsetMirror but with no Bender and
  vertical axes YLEFT/YRIGHT instead of YUP/YDWN.
- Added ``spectrometer.Mono``,
  this includes all motion axes and Pytmc signals for SP1K1-MONO system

Bugfixes
--------
- ``lasers/elliptec.py``: Fix conflict with BlueSky interface and 'stop'
  signal.
- For event scheduling, ensure that we only try to put into the queue
  if event_thread is not None. This resolves some of the startup terminal spam
  in lucid.
- PTMPLC ilk pv was incorrect, changed from ILK_STATUS_RBV to ILK_OK_RBV
- Create a default status info message for devices that have
  errors in constructing their status.

Maintenance
-----------
- Added more documentation to methods and ``LensStack`` class.
- Refactored be lens classes to use ``pcdscalc.be_lens_calcs``
- Add laser imports to :mod:`pcdsdevices.device_types`.  Test fixtures now
  verify imported laser devices' tab completion settings.

Contributors
------------
- cristinasewell
- ghalym
- hhslepicka
- jsheppard95
- klauer
- sfsyunus
- tjohnson
- zllentz


v3.2.0 (2020-10-23)
===================

Device Updates
--------------
- PCDSAreaDetectorTyphos: Added a camera viewer button to the class to open a
  python camera viewer for the camera. Removed the old 'cam_image' viewer in
  favor of this new viewer.
- El3174AiCh: Added ESLO, EOFF fields, removed EGUH, EGUL

New Devices
-----------
- SmarActTipTilt: Class for bundling two SmarActOpenLoop axis classes together
  into a single device for Typhos screen generation and interactive use.
- Added VGC_2S, a new valve class that extends the VGC
  with the addition of a second setpoint and hysteresis.

Contributors
------------
- ghalym
- tjohnson


v3.1.0 (2020-10-21)
===================

API Changes
-----------
- The `SxrGmD` device has been removed from `beam_stats` module. SXR has been
  disassembled and the GMD was moved into the EBD. Its MJ PVs was not working
  anymore.

Device Updates
--------------
- Added RTD PVs to KBOMirror class for bender actuators
- Added PTYPE PV to SmarAct class
- Added metadata to SmarAct jog pvs for better screens
- Added additional PVs to lasers/elliptec.py classes
- TuttiFruttiCls: Added an option to specify the controller channel for
  Thorlabs Elliptec sliders.
- Added the Thorlabs WFS class to the TuttiFrutti class.

New Devices
-----------
- Add XYTargetGrid, an interactive utility class for managing a target grid
  oriented normal to the beam, with regular X-Y spacing between targets.
- PCDSAreaDetectorTyphosBeamStats, a variant of PCSDAreaDetectorTyphos that
  includes centroid information and the crosshair PVs.
- KBOMirror Class: Kirkpatrick-Baez Mirror class, X, Y, Pitch, Bender axes
- FFMirror Class: Kirkpatrick-Baez Mirror without Bender axes. (Fixed focus)
- LAMP motion Class for the LAMP endstation TMO. This includes the following motion axes:

  - Gas Jet X/Y/Z Axes
  - Gas Needle X/Y/Z Axes
  - Sample Paddle X/Y/Z Axes

- A new LCLS class has been added to the `beam_stats` module that contains PVs
  related to the Lcls Linac Status, as well as a few functions to support with
  checking the BYKIK status, turning it On and Off, and setting the period.
- SmarActOpenLoopPositioner: Class intended for performing Bluesky scans using
  open-loop SmarAct motors.

Bugfixes
--------
- Corrected X/Y error in KBOMirror and FFMirror classes
- Fix issues with L2SI Reflaser Picos being unable to successfully move.
  This was because they were using the wrong motor class, which had extra
  PVs that would never connect.
- Fixed a bug preventing instantiation of the Elliptec sliders in the
  TuttiFrutti device.

Maintenance
-----------
- Add prefix and lightpath tests for KBOMirror.

Contributors
------------
- cristinasewell
- jsheppard95
- sfsyunus
- tjohnson
- zllentz


v3.0.0 (2020-10-07)
===================

API Changes
-----------
- The calculations for `alio_to_theta` and `theta_to_alio` in `ccm.py`
  have been reverted to the old calculations.
- User-facing move functions will not be able to catch the
  :class:`~ophyd.utils.LimitError` exception.  These interactive methods are
  not meant to be used in scans, as that is the role of bluesky.

Features
--------
- :class:`pcdsdevices.attenuator.AT2L0` now has a textual representation of
  filter status, and supports the move interface by way of transmission values.
- :class:`~pcdsdevices.pseudopos.SyncAxes` has been adjusted to support
  scalar-valued pseudopositioners, allowing for more complex devices to be kept
  in lock-step motion.
- :class:`~pcdsdevices.pseudopos.PseudoPositioner` position tuples, when of
  length 1, now support casting to floating point, meaning they can be used
  in many functions which only support floating point values.
- Added signal annotations for auto-generated notepad IOC support.

Device Updates
--------------
- Add event/trigger information to PPM, XPIM.
- Reclassify twincat motor and states error resets as "normal" for
  accessibility.
- Add PMPS maintenance/config PVs class for TwinCAT states devices,
  propagating this to all consumers.

New Devices
-----------
- Adds :class:`~pcdsdevices.lxe.LaserTimingCompensation` (``lxt_ttc``) which
  synchronously moves :class:`LaserTiming` (``lxt``) with
  :class:`~pcdsdevices.lxe.TimeToolDelay` (``txt``) to compensate so that the
  true laser x-ray delay by using the ``lxt``-value and the result of time tool
  data analysis, avoiding double-counting.
- Adds :class:`~pcdsdevices.lxe.TimeToolDelay`, an alias for
  :class:`~pcdsdevices.pseudopos.DelayNewport` with additional contextual
  information and room for future development.
- Add LaserInCoupling device for TMO.
- Add ArrivalTimeMonitor device for TMO.
- Add ReflaserL2SI device for TMO.

Bugfixes
--------
- Fixed a typo in a ``ValueError`` exception in
  :meth:`pcdsdevices.state.StatePositioner.check_value`.
- A read-only PV was erroneously marked as read-write in
  :class:`pcdsdevices.gauge.GaugeSerialGPI`, component ``autozero``.
  All other devices were audited, finding no other RBV-related read-only items.
- The direction of :class:`LaserTiming` (``lxt``) was inverted and is now
  fixed.
- Allow setting of :class:`~ophyd.EpicsMotor` limits when unset in the motor
  record (i.e., ``(0, 0)``) when using
  :class:`~pcdsdevices.epics_motor.EpicsMotorInterface`.

Maintenance
-----------
- Added a copy-pastable example to
  :class:`~pcdsdevices.component.UnrelatedComponent` to ease creation of new
  devices.
- Catch :class:`~ophyd.utils.LimitError` in all
  :class:`pcdsdevices.interface.MvInterface` moves, reporting a simple error by
  way of the interface module-level logger.

Contributors
------------
- cristinasewell
- klauer
- zlentz


v2.11.0 (2020-09-21)
====================

API Changes
-----------
- :class:`BaseInterface` no longer inherits from :class:`ophyd.OphydObject`.
- The order of multiple inheritance for many devices using the LCLS-enhanced
  :class:`BaseInterface`, :class:`MvInterface`, and :class:`FltMvInterface` has
  been changed.
- Added :class:`pcdsdevices.interface.TabCompletionHelperClass` to help hold
  tab completion information state and also allow for tab-completion
  customization on a per-instance level.
- :class:`~pcdsdevices.interface.Presets` ``add_hutch`` (and all similar
  ``add_*``) methods no longer require a position.  When unspecified, the
  current position is used.

Features
--------
- For :class:`pcdsdevices.pseudopos.DelayBase`, added
  :meth:`~pcdsdevices.pseudopos.DelayBase.set_current_position` and its related
  component `user_offset`, allowing for custom offsets.
- Epics motors can now have local limits updated per-session, rather than
  only having the option of the EPICS limits. Setting limits attributes will
  update the python limits, putting to the limits PVs will update the limits
  PVs.
- Add PVPositionerDone, a setpoint-only PVPositioner class that is done moving
  immediately. This is not much more useful than just using a PV, but it is
  compatibile with pseudopositioners and has a built-in filter for ignoring
  small moves.
- Moves using mv and umv will log their moves at info level for interactive
  use to keep track of the sessions.
- Add ``user_offset`` to :class:`~pcdsdevices.signal.UnitConversionDerivedSignal`,
  allowing for an arbitrary user offset in user-facing units.
- Add ``user_offset`` signal to the :class:`pcdsdevices.lxe.LaserTiming`, by
  way of :class:`~pcdsdevices.signal.UnitConversionDerivedSignal`, offset
  support.

Device Updates
--------------
- CCM energy limited to the range of 4 to 25 keV
- CCM theta2fine done moving tolerance raised to 0.01
- Beam request default move start tolerance dropped to 5eV

New Devices
-----------
- Add WaveFrontSensorTarget for the wavefront sensor targets (PF1K0, PF1L0).
- Add TwinCATTempSensor for the updated twincat FB with corrected PV pragmas.

Bugfixes
--------
- Adds hints to the :class:`pcdsdevices.lxe.LaserTiming` class for
  ``LiveTable`` support.
- umv will now properly display position and completion status after a move.
- Tab completion for many devices has been fixed. Regression tests have been
  added.
- Fix bug in PulsePickerInOut where it would grab only the first section of
  of the PV instead of the first two
- Tweak will feel less "janky" now and give useful feedback.
- Tweak now accepts + and - as valid inputs for changing the step size.
- Tweak properly clears lines between prints.
- Fix issue where putting to the limits property would update live PVs,
  contrary to the behavior of all other limits attributes in ophyd.
- Fix issue where doing a getattr on the limits properties would fetch
  live PVs, which can cause slowdowns and instabilities.
- Preset methods are now visible when not in engineering mode. (#576)
- Rework BeamEnergyPositioner to be setpoint-only to work properly
  with the behavior of the energy PVs.
- FltMvPositioner.wm will now return numeric values if the position
  value is a tuple. This value is the first element of the tuple, which
  for pseudo positioners is a value that can be passed into move and have
  it do the right thing. This resolves consistency issues and fixes bugs
  where mvr and umvr would fail.
- Fixed a race condition in the EventSequencer device's status objects. Waiting
  on these statuses will now be more reliable.
- Fix issue where converting units could incur time penalties of up to
  7 seconds. This should take around 10ms now.
- Fix bug on beam request where you could not override the tolerance
  via init kwarg, despite docstring's indication.

Maintenance
-----------
- Establish DOC conventions for accumulating release notes from every
  pull request.
- Tweak refactored for maintainability.
- Use more of the built-in ophyd mechanisms for limits rather than
  relying on local overrides.

Contributors
------------
- klauer
- zllentz
- zrylettc


v2.10.0 (2020-08-21)
====================

Features
--------
- Add LookupTablePositioner PseudoPositioner base class for moves
  based on a calibration table.
- Add UnitConversionDerivedSignal as a Signal class for converting
  EPICS units to more desirable units for the user.
- Add units to the IPython prettyprint repr.

Device Updates
--------------
- Add Vernier integration into the CCM class using BeamEnergyRequest.

New Devices
-----------
- Add support for Thorlabs WFS40 USB Wavefront Sensor Camera.
- Add LaserEnergyPositioner PseudoPositioner (lxe) using
  LookupTablePositioner.
- Add LaserTiming PVPositioner (lxt) using UnitConversionDerivedSignal.
- Add BeamEnergyRequest PVPositioner for requesting beam energies in eV from
  ACR.


v2.9.0 (2020-08-18)
===================

Features
--------
- Devices will now show detailed status information when returned
  in the ipython terminal.

Device Updates
--------------
- Update docs on FSV fast shutter valve
- Update AT2L0 with state positioners and calculator
- Update Elliptec classes for cleaner implementation
- Add missing CCM motors and fix the energy motion (no vernier yet)
- Add HDF5 plugin to PCDSAreaDetectorEmbedded

New Devices
-----------
- Add support for SmarAct motors
- Add attenuator calculator device for Ken's new calculator
- Add support for TuttiFruitti diagnostic stack

Bugfixes
--------
- Fix typo in PV name of BeckhoffJet slits


v2.8.0 (2020-07-24)
===================

Features
--------
- Expand variety schema support and add dotted dictionary access.

Device Updates
--------------
- Update various vacuum char waveforms with ``string=True`` for proper
  handling in ``typhos``.
- Add various missing vacuum PVs to various vacuum devices.
- Switch twincat state device error reset to ``kind=config`` so it shows up
  by default in ``typhos``.
- Update LCLS-II imagers to use the new ``AreaDetectorTyphos``.
- The following devices now have ``lightpath`` support:
  - ``FeeAtt``
  - ``FEESolidAttenuator``
  - ``XOffsetMirror``
  - ``PPM``
  - ``XPIM``
  - ``PowerSlits``
  - ``Kmono``
  - ``VRC`` and all subclasses, such as ``VGC``
  - ``VFS``
- Update ``XOffsetMirror`` ``y_up``, ``x_up``, and ``pitch`` to
  ``kind=hinted`` (previously ``normal``). These axes are usually the
  most important.
- Rename ``PPM.y_states`` and ``XPIM.y_states`` to ``target`` for reduced
  redundancy in screens. The only name is aliased via a property.
- ``PowerSlits`` now have a feature set on par with the old slits.
- Update ``VFS`` ``valve_position`` and ``vfs_state`` to ``kind=hinted``
  (previously ``normal``) for more focused statuses.

New Devices
-----------
- Add support for Qmini Spectrometer.
- Add ``AreaDetectorTyphos`` class for optimized screen view of most used
  area detector signals.
- Add ``RTDSL0`` and ``RTDSK0`` to support the rapid turnaround diagnostic
  station configurations.

Bugfixes
--------
- Fix issue with failing callback in ``IMS`` from upstream ``ophyd`` change.

Maintenance
-----------
- Switch from using ``cf-units`` to ``pint`` for portability.
- Add the following helpers:
  - ``interface.LightpathMixin`` to help establish ``lightpath`` support.
  - ``signal.NotImplementedSignal`` to help devices that will expand later.
  - ``signal.InternalSignal`` to help implement read-only signals that can
    be updated by the parent class.
  - ``utils.schedule_task`` to help interface with the ``ophyd`` callback
    queues.
- The ``slits`` module has been refactored to accomodate both old and new
  slits.


v2.7.0 (2020-07-01)
===================

Features
--------
- Add component variety metadata and schema validation.

Device Updates
--------------
- Add many components to ``PIPPLC`` class, adjust component
  ``kinds`` to be more appropriate, and fix errant PV names.
- Update component names on ``VVC`` for clarity, and pvnames for accuracy.
- Update ``XPIM`` class to reflect additional IOC features.
- Update docs and metadata on all LCLS 2 imager classes.
- Update spammy TwinCAT state config parameters to omitted.
- Add interlock device information to ``VGC``.
- Add ``SPMG`` field to ``BeckhoffAxis``.

New Devices
-----------
- Add ``SxrTestAbsorber`` class.
- Add ``ZoomTelescope`` to support MODS zoom telescope.
- Add ``El3174AiCh`` to support EK9000 module.
- Add ``EnvironmentalMonitor`` to support MODS environmental monitors.
- Add support for ThorLabs Elliptec motors for MODS.
- Add ``Ebara_EV_A03_1`` class for specific roughing pump support.
- Migrate SDS jet tracking classes into this repo.
- Add ``VFS`` class to support fast shutters.

Maintenance
-----------
- Remove monkeypatch of ``EventSequence`` in tests, as it was no longer needed.
- Update dependency from ``cf_units`` to its renamed ``cf-units``.
- xfail test that fails with ``bluesky=1.6.2``


v2.6.0 (2020-05-21)
===================

Features
--------
- ``happi`` entry points have been moved to this library for proper
  modularization.
- Area detectors embedded inside of larger devices have been made
  considerably smaller to improve performance in other applications,
  for example in ``typhos``.

Bugfixes
--------
- Provide ``FakePytmcSignal`` for testing in external libraries. This
  fixes issues with fake devices not working if they contain ``PytmcSignal``
  instances outside of the ``pcdsdevices`` testing suite.
- Fix various issues related to moving to ``ophyd`` ``v1.5.0``.
- This library is now importable on win32.

Docs
----
- Docstrings now conform to the new pcds standards.


v2.5.0 (2020-04-15)
===================

Features
--------
- Add classes for Goniometers, Von Hamos spectrometers, Beckhoff liquid jets, TimeTools, and PFLSs
- Add ``UnrelatedComponent`` as a helper for writing devices with many prefixes

Bugfixes
--------
- Fix TwinCAT states enum states
- Add missing packages to requirements file
- Compatibility with newest ``ophyd``

Misc
----
- Add pre-commit hooks to help with development flow
- Add license file to manifest
- Eliminate ``m2r`` docs dependency


v2.4.0 (2020-03-12)
===================

Features
--------
- Add ``PytmcSignal``
- Add ``PPM``, ``XPIM``, ``XOffsetMirror``, and ``Kmono`` classes
- Update ``IPM`` and ``PIM`` modules to better match physical devices
- Add various helper classes for TwinCAT devices
- Stubs created for attenuators, ``RTD``, and ``PowerSlit``
- Make ``cmd_err_reset`` in ``BeckhoffAxisPLC`` accessible in Typhos

API Changes
-----------
- Changed ``set_point_relay`` to ``pump_on_status``, ``at_vac_sp`` to
  ``at_vac_setpoint`` and added ``pump_state`` to ``PIPPLC``

- Changed ``at_vac_sp`` to ``at_vac_setpoint``, ``at_vac_hysterisis``
  to ``setpoint_hysterisis``, and added mps_state to ``VGC``

Bugfixes
--------
- Make ``protection_setpoint`` writeable in ``GCCPLC``
- Make ``state`` writeable in ``VCN``

Misc
----
- Allow build docs failure to speed up overall CI
- Specify old working conda version as temporary solution for
  build failures


v2.3.0 (2020-02-05)
===================

Features
--------
- Make everything compatible with the upcoming ``ophyd`` ``v1.4.0``
- Add be lens calculations port from old python system


v2.2.0 (2020-01-22)
===================

Features
--------
- Add a bunch vacuum-related classes for L2SI

Misc
----
- Fix an issue with the doctr deploy key


v2.1.0 (2020-01-10)
===================

Features
--------
- Add ``screen`` method to ``PCDSMotorBase`` to open the motor expert screen
- Add tab completion filtering via whitelists as the first feature of the
  ``engineering_mode`` switch. This was implemented because the tab
  completion on ophyd devices is extremely overwhelming.
  Use ``set_engineering_mode(bool)`` to turn ``engineering_mode`` on or off.
  The default is "on", which means "everything is normal".
  Turning ``engineering_mode`` off enables the whitelist filtering,
  and in the future may also have other effects on the user interface.
- Add ``dc_devices`` module for components from the new DC power system.
  This currently contains the ``ICT`` and related classes.

Misc
----
- Fixed a race condition in the tests
- Clean up the Travis CI configuration
- Pin pyepics to >=3.4.1 due to a breaking change from python 3.7.6


v2.0.0 (2019-06-28)
===================

Features
--------
- Add ``gauge`` and ``pump`` modules
- Add ``Acromag`` and ``Mesh`` classes
- Add ``motor`` subdevice to state record devices
- Add ``status`` string to ``BeckhoffAxis``

API Breaks
----------
- State devices no longer have the ``readback`` signal, as it is redundant
  with the new ``motor`` subdevice
- ``PCDSDetector`` has been renamed to ``PCDSAreaDetector`` for clarity.
  ``PCDSDetectorBase`` is also renamed to ``PCDSAreaDetectorBase``.

Bugfixes
--------
- Fix PVs in ``BeckhoffAxis``

Misc
----
- Officially build for ``python=3.7``


v1.2.0 (2019-03-08)
===================

Features
--------
- Add all common plugins to ``PCDSDetector``
- ``EventSequencer`` now accepts human-readable sequences

Fixes
-----
- Fix debug PV names in ``BeckhoffAxis``

Misc
----
- Add a py37 build to the CI
- Remove outdated hotfix for ``FakeEpicsSignal`` in tests
- Fix misc testing errors


v1.1.0 (2018-10-26)
===================

Features
--------
- Support for reading and writing sequences to and from the ``EventSequencer``
- Add ``Motor`` factory function for choosing which motor class to use based
  on the text in the ``prefix``.

Bugfixes
--------
- ``IMS`` class will no longer get its ``.SPG`` field stuck on ``paused`` or
  ``stopped`` when a scan is interrupted. Scans will start even if these
  fields are blocked.
- Update out-of-date ``requirements.txt`` file for ``pip``
- Pin ``matplotlib`` to ``<3`` to avoid import incompatibility pitfalls, and
  confine the ``matplotlib`` imports to function scope instead of module scope
  to avoid having a backend be set on import.


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
