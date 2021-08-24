859 group_device
#################

API Changes
-----------
- N/A

Features
--------
- Add GroupDevice: A device that is a group of components that will act independently.

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

- Clean up pmgr loading a bit on IMS (my previous edit to Mike's setup was a bit rough)
- Edit stage/unstage on PIMY to be compatible with GroupDevice
- Edit stage/unstage and the class definition on SlitsBase to be compatible with GroupDevice

New Devices
-----------
- N/A

Bugfixes
--------
- Fix some race conditions in FuncPositioner
- Fix a race condition in schedule_task that could cause a task to never be run

Maintenance
-----------
- Move PVStateSignal from state.py to signal.py to avoid a circular import
- Make the tests importable and runnable on Windows
- Require Python 3.9 for type annotations
- Make pmgr optional, but if installed make sure it has a compatible version.
- Update to 3.9-only CI
- Fix the CI PIP test build

Contributors
------------
- ZLLentz
