"""
Module for piezo drivers.
"""

import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.variety import set_metadata

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class SliceDhvChannel(BaseInterface, Device):
    """
    Class for controlling a single channel from a Vescent Photonics Slice-DHV
    piezo driver channel PVs.
    """

    voltage_limit = Cpt(EpicsSignal, ':VLIM_GET', write_pv=':VLIM_SET',
                        kind='config')

    control_settings = Cpt(EpicsSignal, ':CTL_SETTINGS_GET',
                           write_pv=':CTL_SETTINGS_SET', kind='config')

    bias_voltage = Cpt(EpicsSignal, ':VMEAS_GET', write_pv=':VBIAS_SET',
                       kind='normal')

    sweep_voltage = Cpt(EpicsSignal, ':VSWEEP_GET', write_pv=':VSWEEP_SET',
                        kind='config')

    sweep_freq = Cpt(EpicsSignal, ':FSWEEP_GET', write_pv=':FSWEEP_SET',
                     kind='config')

    sweep_mode = Cpt(EpicsSignal, ':SWEEP_MODE_GET',
                     write_pv=':SWEEP_MODE_SET', kind='config')

    error_status = Cpt(EpicsSignalRO, ':ERROR', kind='config')

    trigger_in = Cpt(EpicsSignal, ':TRIGIN_STATUS_GET',
                     write_pv=':TRIGIN_STATUS_SET', kind='config')

    trigger_out = Cpt(EpicsSignal, ':TRIGOUT_STATUS_GET',
                      write_pv=':TRIGOUT_STATUS_SET', kind='config')

    modulation = Cpt(EpicsSignal, ':MODULATION_GET',
                     write_pv=':MODULATION_SET', kind='config')

    output_mode = Cpt(EpicsSignal, ':OUTPUT_MODE_GET',
                      write_pv=':OUTPUT_MODE_SET', kind='config')


class SliceDhvController(BaseInterface, Device):
    """
    Class for the Vescent Photonics Slice-DHV piezo driver controller PVs.
    """

    _command = Cpt(EpicsSignal, ':CMD', kind='omitted')

    _reply = Cpt(EpicsSignalRO, ':REPLY', kind='omitted')

    version = Cpt(EpicsSignalRO, ':VERSION', kind='omitted')

    reset_ch1 = Cpt(EpicsSignal, ':FACTORY_RESET_CH1', kind='omitted')
    set_metadata(reset_ch1, dict(variety='command-proc', value=1))

    reset_ch2 = Cpt(EpicsSignal, ':FACTORY_RESET_CH2', kind='omitted')
    set_metadata(reset_ch2, dict(variety='command-proc', value=1))

    save_config = Cpt(EpicsSignal, ':SAVE_CONFIG', kind='config')
    set_metadata(save_config, dict(variety='command-proc', value=1))

    save_status = Cpt(EpicsSignalRO, ':SAVE_STATUS', kind='config')

    manufacturer = Cpt(EpicsSignalRO, ':MANUFACTURER', kind='omitted')

    model = Cpt(EpicsSignalRO, ':MODEL', kind='omitted')

    serial = Cpt(EpicsSignalRO, ':SERIAL', kind='omitted')

    ctl_fw = Cpt(EpicsSignalRO, ':CTL_FW', kind='omitted')

    dhv_fw = Cpt(EpicsSignalRO, ':DHV_FW', kind='omitted')


class SliceDhv(BaseInterface, Device):
    """
    Class for a complete two channel  Vescent Photonics Slice-DHV piezo
    driver.
    """

    channel_1 = Cpt(SliceDhvChannel, ':CH1')
    channel_2 = Cpt(SliceDhvChannel, ':CH2')

    controller = Cpt(SliceDhvController, '')
