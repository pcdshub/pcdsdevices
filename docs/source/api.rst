API
###

pcdsdevices.analog_signals
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.analog_signals.Acromag
    pcdsdevices.analog_signals.Mesh
    pcdsdevices.analog_signals.acromag_ch_factory_func

pcdsdevices.areadetector.cam
----------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.areadetector.cam.FeeOpalCam

pcdsdevices.areadetector.detectors
----------------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.areadetector.detectors.Basler
    pcdsdevices.areadetector.detectors.BaslerBase
    pcdsdevices.areadetector.detectors.LasBasler
    pcdsdevices.areadetector.detectors.PCDSAreaDetector
    pcdsdevices.areadetector.detectors.PCDSAreaDetectorBase
    pcdsdevices.areadetector.detectors.PCDSAreaDetectorEmbedded
    pcdsdevices.areadetector.detectors.PCDSAreaDetectorTyphos
    pcdsdevices.areadetector.detectors.PCDSAreaDetectorTyphosBeamStats
    pcdsdevices.areadetector.detectors.PCDSAreaDetectorTyphosTrigger
    pcdsdevices.areadetector.detectors.PCDSHDF5BlueskyTriggerable

pcdsdevices.areadetector.plugins
--------------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.areadetector.plugins.ColorConvPlugin
    pcdsdevices.areadetector.plugins.FilePlugin
    pcdsdevices.areadetector.plugins.HDF5FileStore
    pcdsdevices.areadetector.plugins.HDF5Plugin
    pcdsdevices.areadetector.plugins.ImagePlugin
    pcdsdevices.areadetector.plugins.JPEGPlugin
    pcdsdevices.areadetector.plugins.MagickPlugin
    pcdsdevices.areadetector.plugins.NetCDFPlugin
    pcdsdevices.areadetector.plugins.NexusPlugin
    pcdsdevices.areadetector.plugins.Overlay
    pcdsdevices.areadetector.plugins.OverlayPlugin
    pcdsdevices.areadetector.plugins.PluginBase
    pcdsdevices.areadetector.plugins.ProcessPlugin
    pcdsdevices.areadetector.plugins.ROIPlugin
    pcdsdevices.areadetector.plugins.StatsPlugin
    pcdsdevices.areadetector.plugins.TIFFPlugin
    pcdsdevices.areadetector.plugins.TransformPlugin

pcdsdevices.atm
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.atm.ATMTarget
    pcdsdevices.atm.ArrivalTimeMonitor
    pcdsdevices.atm.TM1K4
    pcdsdevices.atm.TM1K4Target
    pcdsdevices.atm.TM2K2
    pcdsdevices.atm.TM2K2Target

pcdsdevices.attenuator
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.attenuator.AT1K4
    pcdsdevices.attenuator.AT2K2
    pcdsdevices.attenuator.AT2L0
    pcdsdevices.attenuator.AttBase
    pcdsdevices.attenuator.AttBaseWith3rdHarmonic
    pcdsdevices.attenuator.Attenuator
    pcdsdevices.attenuator.AttenuatorCalculatorBase
    pcdsdevices.attenuator.AttenuatorCalculatorFilter
    pcdsdevices.attenuator.AttenuatorCalculatorSXR_Blade
    pcdsdevices.attenuator.AttenuatorCalculatorSXR_FourBlade
    pcdsdevices.attenuator.AttenuatorCalculator_AT2L0
    pcdsdevices.attenuator.AttenuatorSXR_Ladder
    pcdsdevices.attenuator.FEESolidAttenuatorBlade
    pcdsdevices.attenuator.FEESolidAttenuatorStates
    pcdsdevices.attenuator.FeeAtt
    pcdsdevices.attenuator.FeeFilter
    pcdsdevices.attenuator.Filter
    pcdsdevices.attenuator.GasAttenuator
    pcdsdevices.attenuator.GattApertureX
    pcdsdevices.attenuator.GattApertureY
    pcdsdevices.attenuator.SXRLadderAttenuatorBlade
    pcdsdevices.attenuator.SXRLadderAttenuatorStates
    pcdsdevices.attenuator.get_blade_enum
    pcdsdevices.attenuator.render_ascii_att

pcdsdevices.beam_stats
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.beam_stats.BeamEnergyRequest
    pcdsdevices.beam_stats.BeamStats
    pcdsdevices.beam_stats.LCLS

pcdsdevices.ccm
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.ccm.CCM
    pcdsdevices.ccm.CCMAlio
    pcdsdevices.ccm.CCMConstantsMixin
    pcdsdevices.ccm.CCMEnergy
    pcdsdevices.ccm.CCMEnergyWithVernier
    pcdsdevices.ccm.CCMMotor
    pcdsdevices.ccm.CCMPico
    pcdsdevices.ccm.CCMX
    pcdsdevices.ccm.CCMY
    pcdsdevices.ccm.alio_to_theta
    pcdsdevices.ccm.energy_to_wavelength
    pcdsdevices.ccm.theta_to_alio
    pcdsdevices.ccm.theta_to_wavelength
    pcdsdevices.ccm.wavelength_to_energy
    pcdsdevices.ccm.wavelength_to_theta

pcdsdevices.crix_motion
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.crix_motion.QuadraticBeckhoffMotor
    pcdsdevices.crix_motion.QuadraticSimMotor
    pcdsdevices.crix_motion.VLSOptics
    pcdsdevices.crix_motion.VLSOpticsSim

pcdsdevices.cvmi_motion
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.cvmi_motion.CVMI
    pcdsdevices.cvmi_motion.KTOF

pcdsdevices.dc_devices
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.dc_devices.ICT
    pcdsdevices.dc_devices.ICTBus
    pcdsdevices.dc_devices.ICTChannel

pcdsdevices.delay_generator
---------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.delay_generator.DelayGenerator
    pcdsdevices.delay_generator.DelayGeneratorBase
    pcdsdevices.delay_generator.DgChannel

pcdsdevices.device
------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.device.GroupDevice
    pcdsdevices.device.InterfaceDevice
    pcdsdevices.device.to_interface

pcdsdevices.digitizers
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.digitizers.Qadc
    pcdsdevices.digitizers.Qadc134
    pcdsdevices.digitizers.Qadc134Sparsification
    pcdsdevices.digitizers.QadcBase
    pcdsdevices.digitizers.Wave8V2
    pcdsdevices.digitizers.Wave8V2ADCDelayLanes
    pcdsdevices.digitizers.Wave8V2ADCRegs
    pcdsdevices.digitizers.Wave8V2ADCSampleReadout
    pcdsdevices.digitizers.Wave8V2ADCSamples
    pcdsdevices.digitizers.Wave8V2AxiVersion
    pcdsdevices.digitizers.Wave8V2EventBuilder
    pcdsdevices.digitizers.Wave8V2EvrV2
    pcdsdevices.digitizers.Wave8V2Integrators
    pcdsdevices.digitizers.Wave8V2PgpMon
    pcdsdevices.digitizers.Wave8V2RawBuffers
    pcdsdevices.digitizers.Wave8V2Sfp
    pcdsdevices.digitizers.Wave8V2Simple
    pcdsdevices.digitizers.Wave8V2SystemRegs
    pcdsdevices.digitizers.Wave8V2Timing
    pcdsdevices.digitizers.Wave8V2TriggerEventManager
    pcdsdevices.digitizers.Wave8V2XpmMini
    pcdsdevices.digitizers.Wave8V2XpmMsg

pcdsdevices.energy_monitor
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.energy_monitor.GEM
    pcdsdevices.energy_monitor.GMD
    pcdsdevices.energy_monitor.XGMD

pcdsdevices.epics_motor
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.epics_motor.BeckhoffAxis
    pcdsdevices.epics_motor.BeckhoffAxisNoOffset
    pcdsdevices.epics_motor.BeckhoffAxisPLC
    pcdsdevices.epics_motor.BeckhoffAxisPLC_Pre140
    pcdsdevices.epics_motor.BeckhoffAxis_Pre140
    pcdsdevices.epics_motor.EpicsMotorInterface
    pcdsdevices.epics_motor.IMS
    pcdsdevices.epics_motor.MMC100
    pcdsdevices.epics_motor.Motor
    pcdsdevices.epics_motor.Newport
    pcdsdevices.epics_motor.OffsetIMSWithPreset
    pcdsdevices.epics_motor.OffsetMotor
    pcdsdevices.epics_motor.PCDSMotorBase
    pcdsdevices.epics_motor.PMC100
    pcdsdevices.epics_motor.SmarAct
    pcdsdevices.epics_motor.SmarActOpenLoop
    pcdsdevices.epics_motor.SmarActOpenLoopPositioner
    pcdsdevices.epics_motor.SmarActTipTilt

pcdsdevices.evr
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.evr.Trigger

pcdsdevices.gauge
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.gauge.BaseGauge
    pcdsdevices.gauge.GCC500PLC
    pcdsdevices.gauge.GCCPLC
    pcdsdevices.gauge.GCT
    pcdsdevices.gauge.GFSPLC
    pcdsdevices.gauge.GHCPLC
    pcdsdevices.gauge.GaugeColdCathode
    pcdsdevices.gauge.GaugePLC
    pcdsdevices.gauge.GaugePirani
    pcdsdevices.gauge.GaugeSerial
    pcdsdevices.gauge.GaugeSerialGCC
    pcdsdevices.gauge.GaugeSerialGPI
    pcdsdevices.gauge.GaugeSet
    pcdsdevices.gauge.GaugeSetBase
    pcdsdevices.gauge.GaugeSetMks
    pcdsdevices.gauge.GaugeSetPirani
    pcdsdevices.gauge.GaugeSetPiraniMks
    pcdsdevices.gauge.MKS937AController
    pcdsdevices.gauge.MKS937BController
    pcdsdevices.gauge.MKS937a

pcdsdevices.gon
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.gon.BaseGon
    pcdsdevices.gon.GonWithDetArm
    pcdsdevices.gon.Goniometer
    pcdsdevices.gon.Kappa
    pcdsdevices.gon.KappaXYZStage
    pcdsdevices.gon.SamPhi
    pcdsdevices.gon.SimKappa
    pcdsdevices.gon.SimSampleStage
    pcdsdevices.gon.XYZStage

pcdsdevices.inout
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.inout.CombinedInOutRecordPositioner
    pcdsdevices.inout.InOutPVStatePositioner
    pcdsdevices.inout.InOutPositioner
    pcdsdevices.inout.InOutRecordPositioner
    pcdsdevices.inout.Reflaser
    pcdsdevices.inout.TTReflaser
    pcdsdevices.inout.TwinCATInOutPositioner

pcdsdevices.interface
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.interface.BaseInterface
    pcdsdevices.interface.FltMvInterface
    pcdsdevices.interface.LightpathInOutMixin
    pcdsdevices.interface.LightpathMixin
    pcdsdevices.interface.MvInterface
    pcdsdevices.interface.TabCompletionHelperClass
    pcdsdevices.interface.TabCompletionHelperInstance
    pcdsdevices.interface._TabCompletionHelper
    pcdsdevices.interface.device_info
    pcdsdevices.interface.get_engineering_mode
    pcdsdevices.interface.get_kind
    pcdsdevices.interface.get_name
    pcdsdevices.interface.get_units
    pcdsdevices.interface.get_value
    pcdsdevices.interface.ophydobj_info
    pcdsdevices.interface.positionerbase_info
    pcdsdevices.interface.set_engineering_mode
    pcdsdevices.interface.setup_preset_paths
    pcdsdevices.interface.signal_info
    pcdsdevices.interface.tweak_base

pcdsdevices.ipm
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.ipm.IPIMB
    pcdsdevices.ipm.IPIMBChannel
    pcdsdevices.ipm.IPM
    pcdsdevices.ipm.IPMDiode
    pcdsdevices.ipm.IPMMotion
    pcdsdevices.ipm.IPMTarget
    pcdsdevices.ipm.IPM_Det
    pcdsdevices.ipm.IPM_IPIMB
    pcdsdevices.ipm.IPM_Wave8
    pcdsdevices.ipm.Wave8
    pcdsdevices.ipm.Wave8Channel

pcdsdevices.jet
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.jet.BeckhoffJet
    pcdsdevices.jet.BeckhoffJetManipulator
    pcdsdevices.jet.BeckhoffJetSlits
    pcdsdevices.jet.Injector
    pcdsdevices.jet.InjectorWithFine

pcdsdevices.lamp_motion
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lamp_motion.LAMP
    pcdsdevices.lamp_motion.LAMPFlowCell
    pcdsdevices.lamp_motion.LAMPMagneticBottle
    pcdsdevices.lamp_motion.LAMP_LV_17

pcdsdevices.lasers.btps
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.btps.BtpsState
    pcdsdevices.lasers.btps.CentroidConfig
    pcdsdevices.lasers.btps.DestinationConfig
    pcdsdevices.lasers.btps.GlobalConfig
    pcdsdevices.lasers.btps.RangeComparison
    pcdsdevices.lasers.btps.ShutterSafety
    pcdsdevices.lasers.btps.SourceConfig

pcdsdevices.lasers.counters
---------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.counters.Agilent53210A

pcdsdevices.lasers.dicon
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.dicon.DiconSwitch

pcdsdevices.lasers.ek9000
-------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.ek9000.El3174AiCh
    pcdsdevices.lasers.ek9000.EnvironmentalMonitor

pcdsdevices.lasers.elliptec
---------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.elliptec.Ell6
    pcdsdevices.lasers.elliptec.Ell9
    pcdsdevices.lasers.elliptec.EllBase
    pcdsdevices.lasers.elliptec.EllLinear
    pcdsdevices.lasers.elliptec.EllRotation

pcdsdevices.lasers.qmini
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.qmini.QminiSpectrometer
    pcdsdevices.lasers.qmini.QminiWithEvr

pcdsdevices.lasers.rfof
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.rfof.CycleRfofRx
    pcdsdevices.lasers.rfof.CycleRfofTx

pcdsdevices.lasers.thorlabsWFS
------------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.thorlabsWFS.ThorlabsWfs40

pcdsdevices.lasers.tuttifrutti
------------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.tuttifrutti.TuttiFrutti
    pcdsdevices.lasers.tuttifrutti.TuttiFruttiCls

pcdsdevices.lasers.zoomtelescope
--------------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lasers.zoomtelescope.ZoomTelescope

pcdsdevices.lens
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lens.LensStack
    pcdsdevices.lens.LensStackBase
    pcdsdevices.lens.Prefocus
    pcdsdevices.lens.SimLensStack
    pcdsdevices.lens.SimLensStackBase
    pcdsdevices.lens.XFLS

pcdsdevices.lic
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lic.LICMirror
    pcdsdevices.lic.LaserInCoupling

pcdsdevices.lodcm
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lodcm.CHI1
    pcdsdevices.lodcm.CHI2
    pcdsdevices.lodcm.CrystalTower1
    pcdsdevices.lodcm.CrystalTower2
    pcdsdevices.lodcm.Dectris
    pcdsdevices.lodcm.DiagnosticsTower
    pcdsdevices.lodcm.Diode
    pcdsdevices.lodcm.Foil
    pcdsdevices.lodcm.H1N
    pcdsdevices.lodcm.H2N
    pcdsdevices.lodcm.LODCM
    pcdsdevices.lodcm.LODCMEnergyC
    pcdsdevices.lodcm.LODCMEnergySi
    pcdsdevices.lodcm.SimDiagnosticsTower
    pcdsdevices.lodcm.SimEnergyC
    pcdsdevices.lodcm.SimEnergySi
    pcdsdevices.lodcm.SimFirstTower
    pcdsdevices.lodcm.SimLODCM
    pcdsdevices.lodcm.SimSecondTower
    pcdsdevices.lodcm.Y1
    pcdsdevices.lodcm.Y2
    pcdsdevices.lodcm.YagLom

pcdsdevices.lxe
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lxe.FakeLxtTtc
    pcdsdevices.lxe.LaserEnergyPositioner
    pcdsdevices.lxe.LaserTiming
    pcdsdevices.lxe.LaserTimingCompensation
    pcdsdevices.lxe.LxtTtcExample
    pcdsdevices.lxe.TimeToolDelay
    pcdsdevices.lxe._ReversedTimeToolDelay
    pcdsdevices.lxe._ScaledUnitConversionDerivedSignal
    pcdsdevices.lxe.load_calibration_file

pcdsdevices.mirror
------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mirror.CoatingState
    pcdsdevices.mirror.FFMirror
    pcdsdevices.mirror.FFMirrorZ
    pcdsdevices.mirror.Gantry
    pcdsdevices.mirror.KBOMirror
    pcdsdevices.mirror.KBOMirrorHE
    pcdsdevices.mirror.OMMotor
    pcdsdevices.mirror.OffsetMirror
    pcdsdevices.mirror.OpticsPitchNotepad
    pcdsdevices.mirror.Pitch
    pcdsdevices.mirror.PointingMirror
    pcdsdevices.mirror.TwinCATMirrorStripe
    pcdsdevices.mirror.XOffsetMirror
    pcdsdevices.mirror.XOffsetMirrorBend
    pcdsdevices.mirror.XOffsetMirrorRTDs
    pcdsdevices.mirror.XOffsetMirrorState
    pcdsdevices.mirror.XOffsetMirrorSwitch

pcdsdevices.misc
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.misc.MyDevice2

pcdsdevices.movablestand
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.movablestand.MovableStand

pcdsdevices.mpod
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mpod.MPOD
    pcdsdevices.mpod.MPODChannel
    pcdsdevices.mpod.MPODChannelHV
    pcdsdevices.mpod.MPODChannelLV
    pcdsdevices.mpod.get_card_number

pcdsdevices.mpod_apalis
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mpod_apalis.MPODApalisChannel
    pcdsdevices.mpod_apalis.MPODApalisCrate
    pcdsdevices.mpod_apalis.MPODApalisModule
    pcdsdevices.mpod_apalis.MPODApalisModule16Channel
    pcdsdevices.mpod_apalis.MPODApalisModule24Channel
    pcdsdevices.mpod_apalis.MPODApalisModule4Channel
    pcdsdevices.mpod_apalis.MPODApalisModule8Channel

pcdsdevices.mps
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mps.MPS
    pcdsdevices.mps.MPSBase
    pcdsdevices.mps.MPSLimits
    pcdsdevices.mps.mps_factory
    pcdsdevices.mps.must_be_known
    pcdsdevices.mps.must_be_out

pcdsdevices.mrco_motion
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mrco_motion.MRCO

pcdsdevices.my_device
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.my_device.MyDevice

pcdsdevices.piezo
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.piezo.SliceDhv
    pcdsdevices.piezo.SliceDhvChannel
    pcdsdevices.piezo.SliceDhvController

pcdsdevices.pim
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pim.IM2K0
    pcdsdevices.pim.LCLS2ImagerBase
    pcdsdevices.pim.LCLS2Target
    pcdsdevices.pim.PIM
    pcdsdevices.pim.PIMWithBoth
    pcdsdevices.pim.PIMWithFocus
    pcdsdevices.pim.PIMWithLED
    pcdsdevices.pim.PIMY
    pcdsdevices.pim.PPM
    pcdsdevices.pim.PPMPowerMeter
    pcdsdevices.pim.XPIM
    pcdsdevices.pim.XPIMFilterWheel
    pcdsdevices.pim.XPIMLED

pcdsdevices.pmps
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pmps.TwinCATStatePMPS

pcdsdevices.positioner
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.positioner.FuncPositioner

pcdsdevices.pseudopos
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pseudopos.DelayBase
    pcdsdevices.pseudopos.DelayMotor
    pcdsdevices.pseudopos.LookupTablePositioner
    pcdsdevices.pseudopos.OffsetMotorBase
    pcdsdevices.pseudopos.PseudoPositioner
    pcdsdevices.pseudopos.PseudoSingleInterface
    pcdsdevices.pseudopos.SimDelayStage
    pcdsdevices.pseudopos.SyncAxesBase
    pcdsdevices.pseudopos.SyncAxis
    pcdsdevices.pseudopos.delay_class_factory
    pcdsdevices.pseudopos.delay_instance_factory

pcdsdevices.pulsepicker
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pulsepicker.PulsePicker
    pcdsdevices.pulsepicker.PulsePickerInOut

pcdsdevices.pump
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pump.AgilentSerial
    pcdsdevices.pump.EbaraPump
    pcdsdevices.pump.Ebara_EV_A03_1
    pcdsdevices.pump.GammaController
    pcdsdevices.pump.GammaPCT
    pcdsdevices.pump.IonPump
    pcdsdevices.pump.IonPumpBase
    pcdsdevices.pump.IonPumpWithController
    pcdsdevices.pump.Navigator
    pcdsdevices.pump.PIPPLC
    pcdsdevices.pump.PIPSerial
    pcdsdevices.pump.PROPLC
    pcdsdevices.pump.PTMPLC
    pcdsdevices.pump.QPCPCT
    pcdsdevices.pump.TurboPump

pcdsdevices.pv_positioner
-------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pv_positioner.PVPositionerComparator
    pcdsdevices.pv_positioner.PVPositionerDone
    pcdsdevices.pv_positioner.PVPositionerIsClose

pcdsdevices.ref
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.ref.ReflaserL2SI
    pcdsdevices.ref.ReflaserL2SIMirror

pcdsdevices.rtds_ebd
--------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.rtds_ebd.PneumaticActuator
    pcdsdevices.rtds_ebd.RTDSBase
    pcdsdevices.rtds_ebd.RTDSK0
    pcdsdevices.rtds_ebd.RTDSL0

pcdsdevices.sample_delivery
---------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sample_delivery.Bronkhorst
    pcdsdevices.sample_delivery.CoolerShaker
    pcdsdevices.sample_delivery.FlowIntegrator
    pcdsdevices.sample_delivery.GasManifold
    pcdsdevices.sample_delivery.HPLC
    pcdsdevices.sample_delivery.IntegratedFlow
    pcdsdevices.sample_delivery.M3BasePLCDevice
    pcdsdevices.sample_delivery.ManifoldValve
    pcdsdevices.sample_delivery.PCM
    pcdsdevices.sample_delivery.PropAir
    pcdsdevices.sample_delivery.Selector
    pcdsdevices.sample_delivery.Sensirion
    pcdsdevices.sample_delivery.ViciValve

pcdsdevices.sensors
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sensors.RTD
    pcdsdevices.sensors.TwinCATTempSensor
    pcdsdevices.sensors.TwinCATThermocouple

pcdsdevices.sequencer
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sequencer.EventSequence
    pcdsdevices.sequencer.EventSequencer

pcdsdevices.signal
------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.signal.AggregateSignal
    pcdsdevices.signal.AvgSignal
    pcdsdevices.signal.EpicsSignalBaseEditMD
    pcdsdevices.signal.EpicsSignalEditMD
    pcdsdevices.signal.EpicsSignalROEditMD
    pcdsdevices.signal.FakeEpicsSignalEditMD
    pcdsdevices.signal.FakeEpicsSignalROEditMD
    pcdsdevices.signal.FakeNotepadLinkedSignal
    pcdsdevices.signal.FakePytmcSignal
    pcdsdevices.signal.FakePytmcSignalRO
    pcdsdevices.signal.FakePytmcSignalRW
    pcdsdevices.signal.InternalSignal
    pcdsdevices.signal.MultiDerivedSignal
    pcdsdevices.signal.MultiDerivedSignalRO
    pcdsdevices.signal.NotImplementedSignal
    pcdsdevices.signal.NotepadLinkedSignal
    pcdsdevices.signal.PVStateSignal
    pcdsdevices.signal.PytmcSignal
    pcdsdevices.signal.PytmcSignalRO
    pcdsdevices.signal.PytmcSignalRW
    pcdsdevices.signal.SignalEditMD
    pcdsdevices.signal.UnitConversionDerivedSignal
    pcdsdevices.signal._OptionalEpicsSignal
    pcdsdevices.signal.pytmc_writable
    pcdsdevices.signal.select_pytmc_class

pcdsdevices.sim
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sim.FastMotor
    pcdsdevices.sim.SimTwoAxis
    pcdsdevices.sim.SlowMotor
    pcdsdevices.sim.SynMotor

pcdsdevices.slits
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.slits.BadSlitPositionerBase
    pcdsdevices.slits.BeckhoffSlitPositioner
    pcdsdevices.slits.BeckhoffSlits
    pcdsdevices.slits.ExitSlitTarget
    pcdsdevices.slits.ExitSlits
    pcdsdevices.slits.JJSlits
    pcdsdevices.slits.LusiSlitPositioner
    pcdsdevices.slits.LusiSlits
    pcdsdevices.slits.PowerSlits
    pcdsdevices.slits.SimLusiSlits
    pcdsdevices.slits.SlitPositioner
    pcdsdevices.slits.Slits
    pcdsdevices.slits.SlitsBase

pcdsdevices.spectrometer
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.spectrometer.HXRSpectrometer
    pcdsdevices.spectrometer.Kmono
    pcdsdevices.spectrometer.Mono
    pcdsdevices.spectrometer.TMOSpectrometer
    pcdsdevices.spectrometer.VonHamos4Crystal
    pcdsdevices.spectrometer.VonHamosCrystal
    pcdsdevices.spectrometer.VonHamosFE
    pcdsdevices.spectrometer.VonHamosFER

pcdsdevices.state
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.state.CombinedStateRecordPositioner
    pcdsdevices.state.FakeTwinCATStateConfigDynamic
    pcdsdevices.state.PVStatePositioner
    pcdsdevices.state.StatePositioner
    pcdsdevices.state.StateRecordPositioner
    pcdsdevices.state.StateRecordPositionerBase
    pcdsdevices.state.TwinCATStateConfigDynamic
    pcdsdevices.state.TwinCATStateConfigOne
    pcdsdevices.state.TwinCATStatePositioner
    pcdsdevices.state.get_dynamic_state_attr
    pcdsdevices.state.state_config_dotted_names
    pcdsdevices.state.state_config_dotted_velos

pcdsdevices.stopper
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.stopper.PPSStopper
    pcdsdevices.stopper.PPSStopper2PV
    pcdsdevices.stopper.Stopper

pcdsdevices.sxr_test_absorber
-----------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sxr_test_absorber.SxrTestAbsorber

pcdsdevices.tags
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.tags.explain_tag
    pcdsdevices.tags.get_valid_tags

pcdsdevices.targets
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.targets.StageStack
    pcdsdevices.targets.convert_to_physical
    pcdsdevices.targets.get_unit_meshgrid
    pcdsdevices.targets.mesh_interpolation
    pcdsdevices.targets.snake_grid_list

pcdsdevices.timetool
--------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.timetool.Timetool
    pcdsdevices.timetool.TimetoolWithNav

pcdsdevices.utils
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.utils.check_kind_flag
    pcdsdevices.utils.combine_status_info
    pcdsdevices.utils.convert_unit
    pcdsdevices.utils.doc_format_decorator
    pcdsdevices.utils.format_ophyds_to_html
    pcdsdevices.utils.format_status_table
    pcdsdevices.utils.get_component
    pcdsdevices.utils.get_input
    pcdsdevices.utils.get_status_float
    pcdsdevices.utils.get_status_value
    pcdsdevices.utils.ipm_screen
    pcdsdevices.utils.is_input
    pcdsdevices.utils.maybe_make_method
    pcdsdevices.utils.move_subdevices_to_start
    pcdsdevices.utils.post_ophyds_to_elog
    pcdsdevices.utils.reorder_components
    pcdsdevices.utils.schedule_task
    pcdsdevices.utils.set_many
    pcdsdevices.utils.set_standard_ordering
    pcdsdevices.utils.sort_components_by_kind
    pcdsdevices.utils.sort_components_by_name

pcdsdevices.valve
-----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.valve.GateValve
    pcdsdevices.valve.VCN
    pcdsdevices.valve.VFS
    pcdsdevices.valve.VGC
    pcdsdevices.valve.VGCLegacy
    pcdsdevices.valve.VGC_2S
    pcdsdevices.valve.VRC
    pcdsdevices.valve.VRCClsLS
    pcdsdevices.valve.VRCDA
    pcdsdevices.valve.VRCNO
    pcdsdevices.valve.VVC
    pcdsdevices.valve.VVCNO
    pcdsdevices.valve.ValveBase

pcdsdevices.variety
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.variety.expand_dotted_dict
    pcdsdevices.variety.get_metadata
    pcdsdevices.variety.set_metadata
    pcdsdevices.variety.validate_metadata

pcdsdevices.wfs
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.wfs.WaveFrontSensorStates
    pcdsdevices.wfs.WaveFrontSensorTarget
