"""
Module for digitizers such as the Wave8.
"""

import logging

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.variety import set_metadata

logger = logging.getLogger(__name__)


class Wave8V2Channel(Device):
    """
    Class for a single LCLS-II Wave8 channel.
    """

    waveform = Cpt(EpicsSignalRO, ':ArrayData', kind='normal')
    

class Wave8V2SystemRegs(Device):
    """
    Class for Wave8 system registers.
    """

    trigger_enable = Cpt(EpicsSignal, ':TrigEn_RBV', write_pv=':TrigEn',
                         kind='configure')
    trigger_source = Cpt(EpicsSignal, ':TrigSrcSel_RBV',
                         write_pv=':TrigSrcSel', kind='configure')
    trigger_delay = Cpt(EpicsSignal, ':TrigDelay_RBV', write_pv=':TrigDelay',
                        kind='configure')
    timing_mini_tpg = Cpt(EpicsSignal, ':timingUseMiniTpg_RBV',
                          write_pv=':timingUseMiniTpg', kind='configure')


class Wave8V2RawBuffers(Device):
    """
    Class for LCLS-II Wave8 raw buffer registers.
    """

    buffer0_enable = Cpt(EpicsSignal, ':BuffEn0_RBV', write_pv=':BuffEn0',
                         kind='configure')
    buffer1_enable = Cpt(EpicsSignal, ':BuffEn1_RBV', write_pv=':BuffEn1',
                         kind='configure')
    buffer2_enable = Cpt(EpicsSignal, ':BuffEn2_RBV', write_pv=':BuffEn2',
                         kind='configure')
    buffer3_enable = Cpt(EpicsSignal, ':BuffEn3_RBV', write_pv=':BuffEn3',
                         kind='configure')
    buffer4_enable = Cpt(EpicsSignal, ':BuffEn4_RBV', write_pv=':BuffEn4',
                         kind='configure')
    buffer5_enable = Cpt(EpicsSignal, ':BuffEn5_RBV', write_pv=':BuffEn5',
                         kind='configure')
    buffer6_enable = Cpt(EpicsSignal, ':BuffEn6_RBV', write_pv=':BuffEn6',
                         kind='configure')
    buffer7_enable = Cpt(EpicsSignal, ':BuffEn7_RBV', write_pv=':BuffEn7',
                         kind='configure')

    buffer_length = Cpt(EpicsSignal, ':BuffLen_RBV', write_pv=':BuffLen',
                        kind='configure')

    trigger_prescale = Cpt(EpicsSignal, ':TriggerPrescale_RBV',
                           write_pv=':TriggerPrescale', kind='configure')

    counter_reset = Cpt(EpicsSignal, ':CntRst_RBV', write_pv=':CntRst',
                        kind='configure')

    fifo_pause_threshold = Cpt(EpicsSignal, ':FifoPauseThreshold_RBV',
                              write_pv=':FifoPauseThreshold', kind='configure')

    trigger_count = Cpt(EpicsSignalRO, 'TrigCnt', kind='config')


class Wave8V2Sfp(Device):
    """
    Class for LCLS-II Wave8 SFP connection (PGP, EVR).
    """

    sfp_type = Cpt(EpicsSignalRO, ':Type_RBV', kind='config')
    sfp_connector = Cpt(EpicsSignalRO, ':Connector_RBV', kind='config')
    rx_watts = Cpt(EpicsSignalRO, ':RxWatts_RBV', kind='config')
    rx_power = Cpt(EpicsSignalRO, ':RxPower_RBV', kind='config')
    tx_power = Cpt(EpicsSignalRO, ':TxPower_RBV', kind='config')


class Wave8V2TrigEventBuffer(Device):
    """
    Class for LCLS-II Wave8 trigger event buffer.
    """

    

class Wave8V2(Device):
    """
    Top-level class for the LCLS-II Wave8.
    """

    run_start = Cpt(EpicsSignal, ':SeqStartRun.PROC', kind='normal')
    set_metadata(run_start, dict(variety='command-proc', value=1))

    run_stop = Cpt(EpicsSignal, ':SeqStopRun.PROC', kind='normal')
    set_metadata(run_stop, dict(variety='command-proc', value=1))
    
    ch0 = Cpt(Wave8V2Channel, ':CH0')
    ch1 = Cpt(Wave8V2Channel, ':CH1')
    ch2 = Cpt(Wave8V2Channel, ':CH2')
    ch3 = Cpt(Wave8V2Channel, ':CH3')
    ch4 = Cpt(Wave8V2Channel, ':CH4')
    ch5 = Cpt(Wave8V2Channel, ':CH5')
    ch6 = Cpt(Wave8V2Channel, ':CH6')
    ch7 = Cpt(Wave8V2Channel, ':CH7')

    sys_regs = Cpt(Wave8V2SystemRegs, ':Top:SystemRegs')

    raw_buffers = Cpt(Wave8V2RawBuffers, ':Top:RawBuffers')

    sfp0 = Cpt(Wave8V2Sfp, ':Sfp0') # Typ. DAQ fiber
    sfp1 = Cpt(Wave8V2Sfp, ':Sfp1') # Typ. Controls fiber
    sfp2 = Cpt(Wave8V2Sfp, ':Sfp2') # Typ. LCLS-II timing
    sfp3 = Cpt(Wave8V2Sfp, ':Sfp3') # Typ. LCLS-I timing
