#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for EPICS-spefic base devices
"""
from pcdsdevices.epics import component, device, signal
from pcdsdevices.epics.areadetector import base, plugins, cam, detectors

def test_component():
    """
    Only change here is putting "ioc" as a default add_prefix for
    FormattedComponent.
    """
    class Test:
        pass
    comp = component.FormattedComponent(Test)
    assert("ioc" in comp.add_prefix)

def test_device():
    """
    No changes for now, just make sure we can import something named "Device"
    from this module.
    """
    device.Device

def test_signals():
    """
    No changes for now, just make sure we can import EpicsSignal, EpicsSignalRO 
    and EpicsSignalWithRBV from here.
    """
    signal.EpicsSignal
    signal.EpicsSignalRO
    base.EpicsSignalWithRBV

def test_areadetector_base():
    """
    No changes for now, just make sure we can import ADComponent and ADBase from
    here.
    """
    base.ADComponent
    base.ADBase

def test_areadetector_cam():
    """
    No changes for now, just make sure we can import all the standard cams in
    base from here.
    """
    cam.CamBase
    cam.AdscDetectorCam
    cam.Andor3DetectorCam
    cam.AndorDetectorCam
    cam.BrukerDetectorCam
    cam.FirewireLinDetectorCam
    cam.FirewireWinDetectorCam
    cam.LightFieldDetectorCam
    cam.Mar345DetectorCam
    cam.MarCCDDetectorCam
    cam.PSLDetectorCam
    cam.PcoDetectorCam
    cam.PcoDetectorIO
    cam.PcoDetectorSimIO
    cam.PerkinElmerDetectorCam
    cam.PilatusDetectorCam
    cam.PixiradDetectorCam
    cam.PointGreyDetectorCam
    cam.ProsilicaDetectorCam
    cam.PvcamDetectorCam
    cam.RoperDetectorCam
    cam.SimDetectorCam
    cam.URLDetectorCam
    
def test_areadetector_detectors():
    """
    No changes for now, just make sure we can import all the standard detectors
    in detectors from here.
    """
    detectors.DetectorBase
    detectors.AreaDetector
    detectors.FeeOpalDetector
    detectors.AdscDetector
    detectors.Andor3Detector
    detectors.AndorDetector
    detectors.BrukerDetector
    detectors.FirewireLinDetector
    detectors.FirewireWinDetector
    detectors.LightFieldDetector
    detectors.Mar345Detector
    detectors.MarCCDDetector
    detectors.PerkinElmerDetector
    detectors.PilatusDetector
    detectors.PixiradDetector
    detectors.PointGreyDetector
    detectors.ProsilicaDetector
    detectors.PSLDetector
    detectors.PvcamDetector
    detectors.RoperDetector
    detectors.SimDetector
    detectors.URLDetector

def test_area_detector_plugins():
    """
    No changes for now, just make sure we can import all the standard plugins 
    in plugins from here.
    """
    plugins.PluginBase
    plugins.ImagePlugin
    plugins.StatsPlugin
    plugins.ColorConvPlugin
    plugins.ProcessPlugin
    plugins.Overlay
    plugins.OverlayPlugin
    plugins.ROIPlugin
    plugins.TransformPlugin
    plugins.FilePlugin
    plugins.NetCDFPlugin
    plugins.TIFFPlugin
    plugins.JPEGPlugin
    plugins.NexusPlugin
    plugins.HDF5Plugin
    plugins.MagickPlugin
    
