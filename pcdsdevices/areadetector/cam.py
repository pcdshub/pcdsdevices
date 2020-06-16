"""
PCDS cams and overrides for ophyd Cams.

All components (EPICS PVs) associated with a specific camera are added here.
"""
import logging

import ophyd
from ophyd import (Component, DynamicDeviceComponent, EpicsSignal,
                   EpicsSignalRO, FormattedComponent, cam)
from ophyd.areadetector.base import ADBase, ADComponent, EpicsSignalWithRBV
from ophyd.sim import SynSignal
from ophyd.utils import enum

logger = logging.getLogger(__name__)

__all__ = ['FeeOpalCam']


class FeeOpalCam(cam.CamBase):
    """Opal camera used in the FEE for the PIMs."""
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
    acquire = Component(EpicsSignal, 'Acquire')

    # Attrs that arent in the fee opal
    array_counter = Component(SynSignal) # C(SignalWithRBV, 'ArrayCounter')
    nd_attributes_file = Component(SynSignal) # C(EpicsSignal, 'NDAttributesFile', string=True)
    pool_alloc_buffers = Component(SynSignal) # C(EpicsSignalRO, 'PoolAllocBuffers')
    pool_free_buffers = Component(SynSignal) # C(EpicsSignalRO, 'PoolFreeBuffers')
    pool_max_buffers = Component(SynSignal) # C(EpicsSignalRO, 'PoolMaxBuffers')
    pool_max_mem = Component(SynSignal) # C(EpicsSignalRO, 'PoolMaxMem')
    pool_used_buffers = Component(SynSignal) # C(EpicsSignalRO, 'PoolUsedBuffers')
    pool_used_mem = Component(SynSignal) # C(EpicsSignalRO, 'PoolUsedMem')
    port_name = Component(SynSignal) # C(EpicsSignalRO, 'PortName_RBV', string=True)
    array_callbacks = Component(SynSignal) # C(SignalWithRBV, 'ArrayCallbacks')
    array_size = Component(SynSignal) # DDC(ad_group(EpicsSignalRO,
                 #              (('array_size_x', 'ArraySizeX_RBV'),
                 #               ('array_size_y', 'ArraySizeY_RBV'),
                 #               ('array_size_z', 'ArraySizeZ_RBV'))),
                 #     doc='Size of the array in the XYZ dimensions')
    color_mode = Component(SynSignal) # C(SignalWithRBV, 'ColorMode')
    data_type = Component(SynSignal) # C(SignalWithRBV, 'DataType')
    array_size_bytes = Component(SynSignal) # C(EpicsSignalRO, 'ArraySize_RBV')
