#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Cam.
"""
import logging
import ophyd.cam

from .base import (ADBase, EpicsSignalWithRBV)
from ..signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)

__all__ = ['CamBase',
           'OpalCam',
           'AdscDetectorCam',
           'Andor3DetectorCam',
           'AndorDetectorCam',
           'BrukerDetectorCam',
           'FirewireLinDetectorCam',
           'FirewireWinDetectorCam',
           'LightFieldDetectorCam',
           'Mar345DetectorCam',
           'MarCCDDetectorCam',
           'PSLDetectorCam',
           'PcoDetectorCam',
           'PcoDetectorIO',
           'PcoDetectorSimIO',
           'PerkinElmerDetectorCam',
           'PilatusDetectorCam',
           'PixiradDetectorCam',
           'PointGreyDetectorCam',
           'ProsilicaDetectorCam',
           'PvcamDetectorCam',
           'RoperDetectorCam',
           'SimDetectorCam',
           'URLDetectorCam',
]


class CamBase(ophyd.cam.CamBase, ADBase):
    pass


class OpalCam(ophyd.cam.CamBase, ADBass):
    
    # Enums?
    trigger_modes = Enum("Internal", "External", start=0)
    exposure_modes = Enum("Full Frame", "HW ROI", start=0)
    acquire_enum = Enum("Done", "Acquire", start=0)
    test_patterns = Enum("Off", "On", start=0)
    trigger_line_enum = Enum("CC1", "CC2", "CC3", "CC4", start=0)
    polarity_enum = Enum("Normal", "Inverted", start=0)
    prescale_enum = Enum("119 : 1 us", "1 : 1/119 us", start=0)
    pack_enum = Enum("24", "16", start=0)
    video_out_enum = Enum("Top Down", "Top & Bottom", start=0)
    baud_rates = Enum("9600", "19200", "38400", "57600", "115200", start=0)

    # Signals with RBV
    min_callback_time = ADComponent(EpicsSignalWithRBV, 'MinCallbackTime')
    blocking_callbacks = ADComponent(EpicsSignalWithRBV, 'BlockingCallbacks')
    enable_callbacks = ADComponent(EpicsSignalWithRBV, 'EnableCallbacks')
    dropped_arrays = ADComponent(EpicsSignalWithRBV, 'DroppedArrays')
    nd_array_address = ADComponent(EpicsSignalWithRBV, 'NDArrayAddress')
    queue_size = ADComponent(EpicsSignalWithRBV, 'QueueSize')
    nd_array_port = ADComponent(EpicsSignalWithRBV, 'NDArrayPort', string=True)

    # Signals
    pixel_size = ADComponent(EpicsSignal, 'PixelSize')
    exposure_mode = ADComponent(EpicsSignal, 'ExposureMode')
    test_pattern = ADComponent(EpicsSignal, 'TestPattern')
    trg_polarity = ADComponent(EpicsSignal, 'TrgPolarity')
    queue_use = ADComponent(EpicsSignal, 'QueueUse')
    queue_free_low = ADComponent(EpicsSignal, 'QueueFreeLow')
    queue_use_high = ADComponent(EpicsSignal, 'QueueUseHIGH')
    queue_use_hihi = ADComponent(EpicsSignal, 'QueueUseHIHI')
    num_col = ADComponent(EpicsSignal, 'NumCol')
    num_cycles = ADComponent(EpicsSignal, 'NumCycles')
    num_row = ADComponent(EpicsSignal, 'NumRow')
    num_trains = ADComponent(EpicsSignal, 'NumTrains')
    queue_free = ADComponent(EpicsSignal, 'QueueFree')
    status_word = ADComponent(EpicsSignal, 'StatusWord')
    trg2_frame = ADComponent(EpicsSignal, 'Trg2Frame')
    bl_set = ADComponent(EpicsSignal, 'BL_SET')
    fp_set = ADComponent(EpicsSignal, 'FP_SET')
    full_col = ADComponent(EpicsSignal, 'FullCol')
    full_row = ADComponent(EpicsSignal, 'FullRow')
    ga_set = ADComponent(EpicsSignal, 'GA_SET')
    it_set = ADComponent(EpicsSignal, 'IT_SET')
    ssus = ADComponent(EpicsSignal, 'SSUS')
    skip_col = ADComponent(EpicsSignal, 'SkipCol')
    skip_row = ADComponent(EpicsSignal, 'SkipRow')
    trg_code = ADComponent(EpicsSignal, 'TrgCode')
    trg_delay = ADComponent(EpicsSignal, 'TrgDelay')
    trg_width = ADComponent(EpicsSignal, 'TrgWidth')
    baud = ADComponent(EpicsSignal, 'Baud')
    evr_prescale = ADComponent(EpicsSignal, 'EvrPrescale')
    v_out = ADComponent(EpicsSignal, 'VOut')
    resp = ADComponent(EpicsSignal, 'Resp', string=True)
    cmd = ADComponent(EpicsSignal, 'CMD', string=True)
    cmd_evr = ADComponent(EpicsSignal, 'CmdEVR', string=True)
    cmd_free = ADComponent(EpicsSignal, 'CmdFree', string=True)
    cmd_full = ADComponent(EpicsSignal, 'CmdFull', string=True)
    cmd_init = ADComponent(EpicsSignal, 'CmdInit', string=True)
    cmd_roi = ADComponent(EpicsSignal, 'CmdROI', string=True)
    cmd_t_ptn = ADComponent(EpicsSignal, 'CmdTPtn', string=True)

    # Read Only Signals
    array_data = ADComponent(EpicsSignalRO, 'ArrayData')
    execution_time = ADComponent(EpicsSignalRO, 'ExecutionTime_RBV')
    temp_f = ADComponent(EpicsSignalRO, 'TempF_RBV')
    bl = ADComponent(EpicsSignalRO, 'BL_RBV')
    bits_per_pixel = ADComponent(EpicsSignalRO, 'BitsPerPixel_RBV')
    fp = ADComponent(EpicsSignalRO, 'FP_RBV')
    ga = ADComponent(EpicsSignalRO, 'GA_RBV')
    err = ADComponent(EpicsSignalRO, 'ERR_RBV')
    mid = ADComponent(EpicsSignalRO, 'MID_RBV')
    plugin_type = ADComponent(EpicsSignalRO, 'PluginType_RBV', string=True)
    sdk_version = ADComponent(EpicsSignalRO, 'SDKVersion_RBV', string=True)
    ufdt = ADComponent(EpicsSignalRO, 'UFDT_RBV', string=True)


class AreaDetectorCam(ophyd.cam.AreaDetectorCam, Cambase):
    pass


class SimDetectorCam(ophyd.cam.SimDetectorCam, Cambase):
    pass


class AdscDetectorCam(ophyd.cam.AdscDetectorCam, Cambase):
    pass


class AndorDetectorCam(ophyd.cam.AndorDetectorCam, Cambase):
    pass


class Andor3DetectorCam(ophyd.cam.Andor3DetectorCam, Cambase):
    pass


class BrukerDetectorCam(ophyd.cam.BrukerDetectorCam, Cambase):
    pass


class FirewireLinDetectorCam(ophyd.cam.FirewireLinDetectorCam, Cambase):
    pass


class FirewireWinDetectorCam(ophyd.cam.FirewireWinDetectorCam, Cambase):
    pass


class LightFieldDetectorCam(ophyd.cam.LightFieldDetectorCam, Cambase):
    pass


class Mar345DetectorCam(ophyd.cam.Mar345DetectorCam, Cambase):
    pass


class MarCCDDetectorCam(ophyd.cam.MarCCDDetectorCam, Cambase):
    pass


class PcoDetectorCam(ophyd.cam.PcoDetectorCam, Cambase):
    pass


class PcoDetectorIO(ophyd.cam.PcoDetectorIO, ADBase):
    pass


class PcoDetectorSimIO(ophyd.cam.PcoDetectorSimIO, ADBase):
    pass


class PerkinElmerDetectorCam(ophyd.cam.PerkinElmerDetectorCam, Cambase):
    pass


class PSLDetectorCam(ophyd.cam.PSLDetectorCam, Cambase):
    pass


class PilatusDetectorCam(ophyd.cam.PilatusDetectorCam, Cambase):
    pass


class PixiradDetectorCam(ophyd.cam.PixiradDetectorCam, Cambase):
    pass


class PointGreyDetectorCam(ophyd.cam.PointGreyDetectorCam, Cambase):
    pass


class ProsilicaDetectorCam(ophyd.cam.ProsilicaDetectorCam, Cambase):
    pass


class PvcamDetectorCam(ophyd.cam.PvcamDetectorCam, Cambase):
    pass


class RoperDetectorCam(ophyd.cam.RoperDetectorCam, Cambase):
    pass


class URLDetectorCam(ophyd.cam.URLDetectorCam, Cambase):
    pass


