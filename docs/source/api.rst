API
###

pcdsdevices.analog_signals
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.analog_signals.Acromag
    pcdsdevices.analog_signals.FDQ
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
    pcdsdevices.areadetector.detectors.LasBaslerFF
    pcdsdevices.areadetector.detectors.LasBaslerNF
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
    pcdsdevices.atm.MFXATM
    pcdsdevices.atm.TM1K4
    pcdsdevices.atm.TM1K4Target
    pcdsdevices.atm.TM2K2
    pcdsdevices.atm.TM2K2Target
    pcdsdevices.atm.TM2K4
    pcdsdevices.atm.TM2K4Target

pcdsdevices.attenuator
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.attenuator.AT1K2
    pcdsdevices.attenuator.AT1K4
    pcdsdevices.attenuator.AT2K2
    pcdsdevices.attenuator.AT2L0
    pcdsdevices.attenuator.AT3K2
    pcdsdevices.attenuator.AttBase
    pcdsdevices.attenuator.AttBaseWith3rdHarmonic
    pcdsdevices.attenuator.AttBaseWith3rdHarmonicLP
    pcdsdevices.attenuator.Attenuator
    pcdsdevices.attenuator.AttenuatorCalculatorBase
    pcdsdevices.attenuator.AttenuatorCalculatorFilter
    pcdsdevices.attenuator.AttenuatorCalculatorSXR_Blade
    pcdsdevices.attenuator.AttenuatorCalculatorSXR_FourBlade
    pcdsdevices.attenuator.AttenuatorCalculatorSXR_TwoBlade
    pcdsdevices.attenuator.AttenuatorCalculator_AT2L0
    pcdsdevices.attenuator.AttenuatorSXR_Ladder
    pcdsdevices.attenuator.AttenuatorSXR_LadderTwoBladeLBD
    pcdsdevices.attenuator.FEESolidAttenuatorBlade
    pcdsdevices.attenuator.FEESolidAttenuatorStates
    pcdsdevices.attenuator.FeeAtt
    pcdsdevices.attenuator.FeeFilter
    pcdsdevices.attenuator.Filter
    pcdsdevices.attenuator.GasAttenuator
    pcdsdevices.attenuator.GattApertureX
    pcdsdevices.attenuator.GattApertureY
    pcdsdevices.attenuator.SXRGasAtt
    pcdsdevices.attenuator.SXRLadderAttenuatorBlade
    pcdsdevices.attenuator.SXRLadderAttenuatorStates
    pcdsdevices.attenuator.get_blade_enum
    pcdsdevices.attenuator.render_ascii_att

pcdsdevices.beam_stats
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.beam_stats.BeamEnergyRequest
    pcdsdevices.beam_stats.BeamEnergyRequestACRWait
    pcdsdevices.beam_stats.BeamEnergyRequestNoWait
    pcdsdevices.beam_stats.BeamStats
    pcdsdevices.beam_stats.FakeBeamEnergyRequest
    pcdsdevices.beam_stats.FakeBeamEnergyRequestACRWait
    pcdsdevices.beam_stats.FakeBeamEnergyRequestNoWait
    pcdsdevices.beam_stats.LCLS

pcdsdevices.ccm
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.ccm.CCM
    pcdsdevices.ccm.CCMAlio
    pcdsdevices.ccm.CCMConstantsMixin
    pcdsdevices.ccm.CCMEnergy
    pcdsdevices.ccm.CCMEnergyWithACRStatus
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

pcdsdevices.cvmi_bootstrap
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.cvmi_bootstrap.CVMI
    pcdsdevices.cvmi_bootstrap.KTOF

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

pcdsdevices.dccm
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.dccm.DCCM
    pcdsdevices.dccm.DCCMEnergy
    pcdsdevices.dccm.DCCMEnergyWithACRStatus
    pcdsdevices.dccm.DCCMEnergyWithVernier

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

pcdsdevices.digital_signals
---------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.digital_signals.J120K

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

pcdsdevices.dream_motion
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.dream_motion.DREAM_CoilMover
    pcdsdevices.dream_motion.DREAM_GasJet
    pcdsdevices.dream_motion.DREAM_GasNozzle
    pcdsdevices.dream_motion.DREAM_MC_Y
    pcdsdevices.dream_motion.DREAM_SL3K4

pcdsdevices.energy_monitor
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.energy_monitor.GEM
    pcdsdevices.energy_monitor.GMD
    pcdsdevices.energy_monitor.GMDPreAmp
    pcdsdevices.energy_monitor.XGMD

pcdsdevices.epics_motor
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.epics_motor.BeckhoffAxis
    pcdsdevices.epics_motor.BeckhoffAxisEPS
    pcdsdevices.epics_motor.BeckhoffAxisEPSCustom
    pcdsdevices.epics_motor.BeckhoffAxisNoOffset
    pcdsdevices.epics_motor.BeckhoffAxisPLC
    pcdsdevices.epics_motor.BeckhoffAxisPLCEPS
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
    pcdsdevices.epics_motor.PI_M824
    pcdsdevices.epics_motor.PMC100
    pcdsdevices.epics_motor.SmarAct
    pcdsdevices.epics_motor.SmarActEncodedTipTilt
    pcdsdevices.epics_motor.SmarActOpenLoop
    pcdsdevices.epics_motor.SmarActOpenLoopPositioner
    pcdsdevices.epics_motor.SmarActPicoscale
    pcdsdevices.epics_motor.SmarActTipTilt

pcdsdevices.eps
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.eps.EPS

pcdsdevices.evr
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.evr.EvrMotor
    pcdsdevices.evr.Trigger

pcdsdevices.example
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.example.Example3D
    pcdsdevices.example.Example3DStates
    pcdsdevices.example.ExampleL2L
    pcdsdevices.example.ExampleL2LStates
    pcdsdevices.example.PLCExampleMotion
    pcdsdevices.example.PLCOnlyXPIM

pcdsdevices.fms
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.fms.AmbTemp
    pcdsdevices.fms.Floor
    pcdsdevices.fms.LCP1
    pcdsdevices.fms.LCP2
    pcdsdevices.fms.PCWFlow
    pcdsdevices.fms.PCWTemp
    pcdsdevices.fms.PDU_Humidity2
    pcdsdevices.fms.PDU_Humidity4
    pcdsdevices.fms.PDU_Humidity6
    pcdsdevices.fms.PDU_Humidity8
    pcdsdevices.fms.PDU_Load1
    pcdsdevices.fms.PDU_Load2
    pcdsdevices.fms.PDU_Load3
    pcdsdevices.fms.PDU_Load4
    pcdsdevices.fms.PDU_Temp2
    pcdsdevices.fms.PDU_Temp4
    pcdsdevices.fms.PDU_Temp6
    pcdsdevices.fms.PDU_Temp8
    pcdsdevices.fms.Rack
    pcdsdevices.fms.RaritanSensor
    pcdsdevices.fms.SRCController
    pcdsdevices.fms.Setra5000

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

pcdsdevices.gbs
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.gbs.GratingBeamSplitterStates
    pcdsdevices.gbs.GratingBeamSplitterTarget

pcdsdevices.gon
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.gon.BaseGon
    pcdsdevices.gon.GonWithDetArm
    pcdsdevices.gon.Goniometer
    pcdsdevices.gon.HxrDiffractometer
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
    pcdsdevices.inout.LightpathInOutRecordPositioner
    pcdsdevices.inout.Reflaser
    pcdsdevices.inout.TTReflaser
    pcdsdevices.inout.TwinCATInOutPositioner

pcdsdevices.interface
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.interface.BaseInterface
    pcdsdevices.interface.FltMvInterface
    pcdsdevices.interface.LegacyLightpathMixin
    pcdsdevices.interface.LightpathInOutCptMixin
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

    pcdsdevices.ipm.BeckhoffIntensityProfileTarget
    pcdsdevices.ipm.IPIMB
    pcdsdevices.ipm.IPIMBChannel
    pcdsdevices.ipm.IPM
    pcdsdevices.ipm.IPMDiode
    pcdsdevices.ipm.IPMMotion
    pcdsdevices.ipm.IPMTarget
    pcdsdevices.ipm.IPM_Det
    pcdsdevices.ipm.IPM_IPIMB
    pcdsdevices.ipm.IPM_Wave8
    pcdsdevices.ipm.IntensityProfileMonitorStates
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

pcdsdevices.keithley
--------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.keithley.IM3L0_K2700
    pcdsdevices.keithley.K2700
    pcdsdevices.keithley.K6514

pcdsdevices.lakeshore
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lakeshore.Heater
    pcdsdevices.lakeshore.Lakeshore336
    pcdsdevices.lakeshore.TemperatureSensor

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

    pcdsdevices.lasers.btps.BtpsSourceStatus
    pcdsdevices.lasers.btps.BtpsState
    pcdsdevices.lasers.btps.BtpsVGC
    pcdsdevices.lasers.btps.CentroidConfig
    pcdsdevices.lasers.btps.DestinationConfig
    pcdsdevices.lasers.btps.GlobalConfig
    pcdsdevices.lasers.btps.LssShutterStatus
    pcdsdevices.lasers.btps.RangeComparison
    pcdsdevices.lasers.btps.SourceToDestinationConfig

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
    pcdsdevices.lasers.ek9000.SimpleShutter

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
    pcdsdevices.lasers.rfof.ItechRfofAll
    pcdsdevices.lasers.rfof.ItechRfofErrors
    pcdsdevices.lasers.rfof.ItechRfofRx
    pcdsdevices.lasers.rfof.ItechRfofStatus
    pcdsdevices.lasers.rfof.ItechRfofTx

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

pcdsdevices.lic_2d_tmo
----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.lic_2d_tmo.LaserCouplingStates
    pcdsdevices.lic_2d_tmo.TMOLaserInCouplingTwoDimension

pcdsdevices.light_control
-------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.light_control.LightControl

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
    pcdsdevices.lodcm.LODCMEnergyC1
    pcdsdevices.lodcm.LODCMEnergySi
    pcdsdevices.lodcm.SimDiagnosticsTower
    pcdsdevices.lodcm.SimEnergyC
    pcdsdevices.lodcm.SimEnergySi
    pcdsdevices.lodcm.SimFirstTower
    pcdsdevices.lodcm.SimLODCM
    pcdsdevices.lodcm.SimSecondTower
    pcdsdevices.lodcm.XCSLODCM
    pcdsdevices.lodcm.XPPLODCM
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
    pcdsdevices.lxe.Lcls2LaserTiming
    pcdsdevices.lxe.LxtTtcExample
    pcdsdevices.lxe.TimeToolDelay
    pcdsdevices.lxe._ReversedTimeToolDelay
    pcdsdevices.lxe._ScaledUnitConversionDerivedSignal
    pcdsdevices.lxe.load_calibration_file

pcdsdevices.make_ophyd_device
-----------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.make_ophyd_device.flatten_list
    pcdsdevices.make_ophyd_device.get_components
    pcdsdevices.make_ophyd_device.make_class
    pcdsdevices.make_ophyd_device.make_class_line
    pcdsdevices.make_ophyd_device.make_class_name
    pcdsdevices.make_ophyd_device.make_cpt
    pcdsdevices.make_ophyd_device.make_signal
    pcdsdevices.make_ophyd_device.make_signal_wrbv
    pcdsdevices.make_ophyd_device.print_class
    pcdsdevices.make_ophyd_device.recurse_record
    pcdsdevices.make_ophyd_device.write_file

pcdsdevices.mirror
------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.mirror.FFMirror
    pcdsdevices.mirror.FFMirrorZ
    pcdsdevices.mirror.Gantry
    pcdsdevices.mirror.KBOMirror
    pcdsdevices.mirror.KBOMirrorChin
    pcdsdevices.mirror.KBOMirrorHE
    pcdsdevices.mirror.KBOMirrorHEStates
    pcdsdevices.mirror.KBOMirrorStates
    pcdsdevices.mirror.MirrorInsertState
    pcdsdevices.mirror.MirrorStripe2D2P
    pcdsdevices.mirror.MirrorStripe2D4P
    pcdsdevices.mirror.OMMotor
    pcdsdevices.mirror.OffsetMirror
    pcdsdevices.mirror.OpticsPitchNotepad
    pcdsdevices.mirror.Pitch
    pcdsdevices.mirror.PointingMirror
    pcdsdevices.mirror.TwinCATMirrorStripe
    pcdsdevices.mirror.XOffsetMirror
    pcdsdevices.mirror.XOffsetMirror2D4PState
    pcdsdevices.mirror.XOffsetMirrorBend
    pcdsdevices.mirror.XOffsetMirrorNoBend
    pcdsdevices.mirror.XOffsetMirrorRTDs
    pcdsdevices.mirror.XOffsetMirrorState
    pcdsdevices.mirror.XOffsetMirrorStateCool
    pcdsdevices.mirror.XOffsetMirrorStateCoolNoBend
    pcdsdevices.mirror.XOffsetMirrorSwitch
    pcdsdevices.mirror.XOffsetMirrorXYState

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

pcdsdevices.pc
--------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pc.PhotonCollimator
    pcdsdevices.pc.PhotonCollimatorFDQ

pcdsdevices.pdu
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pdu.PDU
    pcdsdevices.pdu.PDU16
    pcdsdevices.pdu.PDU24
    pcdsdevices.pdu.PDU8
    pcdsdevices.pdu.PDUChannel
    pcdsdevices.pdu.TripplitePDU
    pcdsdevices.pdu.TripplitePDU16
    pcdsdevices.pdu.TripplitePDU24
    pcdsdevices.pdu.TripplitePDU8
    pcdsdevices.pdu.TripplitePDUChannel

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
    pcdsdevices.pim.IM3L0
    pcdsdevices.pim.LCLS2ImagerBase
    pcdsdevices.pim.LCLS2Target
    pcdsdevices.pim.PIM
    pcdsdevices.pim.PIMWithBoth
    pcdsdevices.pim.PIMWithFocus
    pcdsdevices.pim.PIMWithLED
    pcdsdevices.pim.PIMY
    pcdsdevices.pim.PPM
    pcdsdevices.pim.PPMCOOL
    pcdsdevices.pim.PPMCoolSwitch
    pcdsdevices.pim.PPMPowerMeter
    pcdsdevices.pim.XPIM
    pcdsdevices.pim.XPIMFilterWheel
    pcdsdevices.pim.XPIMLED

pcdsdevices.pmps
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pmps.TwinCATStatePMPS

pcdsdevices.pneumatic
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.pneumatic.BeckhoffPneumatic
    pcdsdevices.pneumatic.BeckhoffPneumaticFDQ

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
    pcdsdevices.pseudopos.is_strictly_increasing

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

    pcdsdevices.pv_positioner.OnePVMotor
    pcdsdevices.pv_positioner.PVPositionerComparator
    pcdsdevices.pv_positioner.PVPositionerDone
    pcdsdevices.pv_positioner.PVPositionerIsClose
    pcdsdevices.pv_positioner.PVPositionerNoInterrupt

pcdsdevices.qadc
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.qadc.Qadc
    pcdsdevices.qadc.Qadc134
    pcdsdevices.qadc.Qadc134Common
    pcdsdevices.qadc.Qadc134Lcls2
    pcdsdevices.qadc.QadcCommon
    pcdsdevices.qadc.QadcLcls1Timing
    pcdsdevices.qadc.QadcLcls2Timing

pcdsdevices.radiation
---------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.radiation.HPI6030

pcdsdevices.ref
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.ref.ReflaserL2SI
    pcdsdevices.ref.ReflaserL2SIMirror

pcdsdevices.rs_powersupply
--------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.rs_powersupply.RSChannel
    pcdsdevices.rs_powersupply.RohdeSchwarzPowerSupply

pcdsdevices.rtds_ebd
--------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.rtds_ebd.PneumaticActuator
    pcdsdevices.rtds_ebd.RTDSBase
    pcdsdevices.rtds_ebd.RTDSK0
    pcdsdevices.rtds_ebd.RTDSL0
    pcdsdevices.rtds_ebd.RTDSX0ThreeStage

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
    pcdsdevices.signal.SummarySignal
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
    pcdsdevices.slits.SL2K4Slits
    pcdsdevices.slits.SimLusiSlits
    pcdsdevices.slits.SlitPositioner
    pcdsdevices.slits.Slits
    pcdsdevices.slits.SlitsBase

pcdsdevices.smarpod
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.smarpod.SmarPod
    pcdsdevices.smarpod.SmarPodAxis
    pcdsdevices.smarpod.SmarPodPose
    pcdsdevices.smarpod.SmarPodStatus

pcdsdevices.spectrometer
------------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.spectrometer.DCCMono
    pcdsdevices.spectrometer.FZPStates
    pcdsdevices.spectrometer.Gen1VonHamos4Crystal
    pcdsdevices.spectrometer.Gen1VonHamosCrystal
    pcdsdevices.spectrometer.HXRSpectrometer
    pcdsdevices.spectrometer.Kmono
    pcdsdevices.spectrometer.Mono
    pcdsdevices.spectrometer.MonoGratingStates
    pcdsdevices.spectrometer.TMOSpectrometer
    pcdsdevices.spectrometer.TMOSpectrometerSOLIDATTStates
    pcdsdevices.spectrometer.VonHamos4Crystal
    pcdsdevices.spectrometer.VonHamos6Crystal
    pcdsdevices.spectrometer.VonHamosCrystal
    pcdsdevices.spectrometer.VonHamosCrystal_2
    pcdsdevices.spectrometer.VonHamosFE
    pcdsdevices.spectrometer.VonHamosFER

pcdsdevices.sqr1
----------------

.. autosummary::
    :toctree: generated

    pcdsdevices.sqr1.SQR1
    pcdsdevices.sqr1.SQR1Axis

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
    pcdsdevices.state.state_config_dotted_attribute
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
    pcdsdevices.sxr_test_absorber.SxrTestAbsorberStates

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

pcdsdevices.tmo_ip1
-------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.tmo_ip1.CalibrationAxis
    pcdsdevices.tmo_ip1.SCaFoil

pcdsdevices.tpr
---------------

.. autosummary::
    :toctree: generated

    pcdsdevices.tpr.TprMotor
    pcdsdevices.tpr.TprTrigger

pcdsdevices.usb_encoder
-----------------------

.. autosummary::
    :toctree: generated

    pcdsdevices.usb_encoder.UsDigitalUsbEncoder

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
    pcdsdevices.utils.re_arg
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
    pcdsdevices.valve.VCN_OpenLoop
    pcdsdevices.valve.VCN_VAT590
    pcdsdevices.valve.VCN_VAT590_Status
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
    pcdsdevices.wfs.WaveFrontSensorTargetCool
    pcdsdevices.wfs.WaveFrontSensorTargetFDQ
