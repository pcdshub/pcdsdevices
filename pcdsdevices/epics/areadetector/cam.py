#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCDS cams and overrides for ophyd Cams.
"""
import logging

import ophyd
from ophyd import cam
from ophyd.utils import enum

from .plugins import (ImagePlugin, StatsPlugin)
from .base import (ADBase, ADComponent, EpicsSignalWithRBV)
from ..signal import (EpicsSignal, EpicsSignalRO, FakeSignal)
from ...device import DynamicDeviceComponent
from ...component import Component

logger = logging.getLogger(__name__)

__all__ = ['CamBase',
           'PulnixCam',
           'FEEOpalCam',
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


class CamBase(cam.CamBase, ADBase):
    array_size = DynamicDeviceComponent(ophyd.base.ad_group(EpicsSignalRO,
                              (('array_size_x', 'ArraySizeX_RBV'),
                               ('array_size_y', 'ArraySizeY_RBV'),
                               ('array_size_z', 'ArraySizeZ_RBV'))),
                     doc='Size of the array in the XYZ dimensions')
    max_size = DynamicDeviceComponent(ophyd.base.ad_group(EpicsSignalRO,
                            (('max_size_x', 'MaxSizeX_RBV'),
                             ('max_size_y', 'MaxSizeY_RBV'))),
                   doc='Maximum sensor size in the XY directions')
    reverse = DynamicDeviceComponent(ophyd.base.ad_group(EpicsSignalWithRBV,
                           (('reverse_x', 'ReverseX'),
                            ('reverse_y', 'ReverseY'))))
    size = DynamicDeviceComponent(ophyd.base.ad_group(EpicsSignalWithRBV,
                        (('size_x', 'SizeX'),
                         ('size_y', 'SizeY'))))
    pass

class AreaDetectorCam(cam.AreaDetectorCam, CamBase):
    pass


class PulnixCam(CamBase):
    image2 = Component(ImagePlugin, "IMAGE2:")
    stats1 = Component(StatsPlugin, "Stats1:")
    stats2 = Component(StatsPlugin, "Stats2:")


class FEEOpalCam(CamBase):
    # enums?
    # trigger_modes = enum("Internal", "External", start=0)
    # exposure_modes = enum("Full Frame", "HW ROI", start=0)
    # acquire_enum = enum("Done", "Acquire", start=0)
    # test_patterns = enum("Off", "On", start=0)
    # trigger_line_enum = enum("CC1", "CC2", "CC3", "CC4", start=0)
    # polarity_enum = enum("Normal", "Inverted", start=0)
    # prescale_enum = enum("119 : 1 us", "1 : 1/119 us", start=0)
    # pack_enum = enum("24", "16", start=0)
    # video_out_enum = enum("Top Down", "Top & Bottom", start=0)
    # baud_rates = enum("9600", "19200", "38400", "57600", "115200", start=0)

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

    # Overridden Components
    # array_rate = Component(Signal)
    array_rate = Component(EpicsSignalRO, 'FrameRate')

    # Attrs that arent in the fee opal
    array_counter = Component(FakeSignal) # C(SignalWithRBV, 'ArrayCounter')
    nd_attributes_file = Component(FakeSignal) # C(EpicsSignal, 'NDAttributesFile', string=True)
    pool_alloc_buffers = Component(FakeSignal) # C(EpicsSignalRO, 'PoolAllocBuffers')
    pool_free_buffers = Component(FakeSignal) # C(EpicsSignalRO, 'PoolFreeBuffers')
    pool_max_buffers = Component(FakeSignal) # C(EpicsSignalRO, 'PoolMaxBuffers')
    pool_max_mem = Component(FakeSignal) # C(EpicsSignalRO, 'PoolMaxMem')
    pool_used_buffers = Component(FakeSignal) # C(EpicsSignalRO, 'PoolUsedBuffers')
    pool_used_mem = Component(FakeSignal) # C(EpicsSignalRO, 'PoolUsedMem')
    port_name = Component(FakeSignal) # C(EpicsSignalRO, 'PortName_RBV', string=True)
    array_callbacks = Component(FakeSignal) # C(SignalWithRBV, 'ArrayCallbacks')
    array_size = Component(FakeSignal) # DDC(ad_group(EpicsSignalRO,
                 #              (('array_size_x', 'ArraySizeX_RBV'),
                 #               ('array_size_y', 'ArraySizeY_RBV'),
                 #               ('array_size_z', 'ArraySizeZ_RBV'))),
                 #     doc='Size of the array in the XYZ dimensions')
    color_mode = Component(FakeSignal) # C(SignalWithRBV, 'ColorMode')
    data_type = Component(FakeSignal) # C(SignalWithRBV, 'DataType')
    array_size_bytes = Component(FakeSignal) # C(EpicsSignalRO, 'ArraySize_RBV')
    


class SimDetectorCam(cam.SimDetectorCam, CamBase):
    pass


class AdscDetectorCam(cam.AdscDetectorCam, CamBase):
    pass


class AndorDetectorCam(cam.AndorDetectorCam, CamBase):
    pass


class Andor3DetectorCam(cam.Andor3DetectorCam, CamBase):
    pass


class BrukerDetectorCam(cam.BrukerDetectorCam, CamBase):
    pass


class FirewireLinDetectorCam(cam.FirewireLinDetectorCam, CamBase):
    pass


class FirewireWinDetectorCam(cam.FirewireWinDetectorCam, CamBase):
    pass


class LightFieldDetectorCam(cam.LightFieldDetectorCam, CamBase):
    pass


class Mar345DetectorCam(cam.Mar345DetectorCam, CamBase):
    pass


class MarCCDDetectorCam(cam.MarCCDDetectorCam, CamBase):
    pass


class PcoDetectorCam(cam.PcoDetectorCam, CamBase):
    pass


class PcoDetectorIO(cam.PcoDetectorIO, ADBase):
    pass


class PcoDetectorSimIO(cam.PcoDetectorSimIO, ADBase):
    pass


class PerkinElmerDetectorCam(cam.PerkinElmerDetectorCam, CamBase):
    pass


class PSLDetectorCam(cam.PSLDetectorCam, CamBase):
    pass


class PilatusDetectorCam(cam.PilatusDetectorCam, CamBase):
    pass


class PixiradDetectorCam(cam.PixiradDetectorCam, CamBase):
    pass


class PointGreyDetectorCam(cam.PointGreyDetectorCam, CamBase):
    pass


class ProsilicaDetectorCam(cam.ProsilicaDetectorCam, CamBase):
    pass


class PvcamDetectorCam(cam.PvcamDetectorCam, CamBase):
    pass


class RoperDetectorCam(cam.RoperDetectorCam, CamBase):
    pass


class URLDetectorCam(cam.URLDetectorCam, CamBase):
    pass


