"""
Ophyd device for the Hard X-ray Gas Energy Monitor
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Device
from ophyd import Component as Cpt
from ophyd import FormattedComponent as FCpt

from pcdsdevices.interface import BaseInterface

logger = logging.getLogger(__name__)

class acqiris_channel(Device):
    """
    Class to define a single acqiris channel and its data.

    Parameters
    ----------
    prefix : ``str``
        The PV base of the digitizer.
    channel : ``str``
        The channel number, e.g. '1',..,'4'
    board : ``str``
        3-digit ID of the board the channel belongs to, e.g. '241'
    """
    waveform = Cpt(EpicsSignalRO, ':Data',kind='hinted')

    def __init__(self, prefix, board, channel, name='acqiris_channel', **kwargs):
        self.prefix = prefix
        self.channel = channel
        super().__init__(prefix, name=name, **kwargs)


class acqiris_board(Device):
    """
    Class to define an acqiris digitizer board in the HXR gas detector.
    
    Parameters
    ----------
    prefix : ``str``
        The PV base of the digitizer.
    board : ``str``
        3-digit number representing the digitizer board, e.g. '240', '360'.

    """
    ch1 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}1', channel='1', board='{self.board}',kind='hinted')
    ch2 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}2', channel='2', board='{self.board}',kind='hinted')
    ch3 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}3', channel='3', board='{self.board}',kind='hinted')
    ch4 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}4', channel='4', board='{self.board}',kind='hinted')

    tab_component_names = True

    run_state = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MDAQStatus',kind='hinted')
    sample_interval = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MSampInterval',kind='hinted')
    delay_time = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MDelayTime',kind='hinted')
    num_samples = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MNbrSamples',kind='hinted')
    trig_source = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MTriggerSource',kind='hinted')
    trig_class = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MTrigClass',kind='hinted')
    samples_freq = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MSampFrequency',kind='hinted')
    rate =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MEventRate',kind='hinted')
    num_events =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MEventCount',kind='hinted')
    num_trig_timeouts = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTriggerTimeouts',kind='hinted')
    num_truncated = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTruncated',kind='hinted')

    # Extras
    acq_type = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MType',kind='hinted')
    acq_mode = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MMode',kind='hinted')
    acq_mode_flags = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MModeFlags',kind='hinted')
    clock_type = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MClockType',kind='hinted')
    crate_number =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MCrateNb',kind='hinted')
    nADC_bits =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MNbrADCBits',kind='hinted')
    crate_slot = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MPosInCrate',kind='hinted')
    temp = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTemperature_m',kind='hinted')
    input_freq = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MInputFrequency',kind='hinted')
    
    def __init__(self, prefix, platform=None, board=None, name='acqiris_board', *args, **kwargs):
        self.board = board
        self.prefix = prefix
        if len(self.board) != 3:
            raise ValueError("acqiris 'board' expects a 3-digit board identifier, e.g. '240'")
        self._board_pref = self.board[:2]
        super().__init__(prefix, name=name, **kwargs)
    
    def start(self):
        """
        Start the acqiris DAQ
        """
        self.run_state.put(1)

    def stop(self):
        """
        Stop the acqiris DAQ
        """
        self.run_state.put(0)

class gasdet(Device, BaseInterface):
    """
    Class to create complete gas detector with all acqiris boards.

    Parameters
    ----------
    prefix : ``str``
        The PV base of the digitizer.
    platform : ``str``
        This a legacy PV segment found in the GasDetDAQ IOC. The default '202' applies to
        the HXR gas detector system.
    acq1_board : ``str``
        3-digit number representing the first digitizer board, e.g. '240', '360'.
    acq2_board : ``str``
        3-digit number representing the second digitizer board, e.g. '240', '360'.

    """
    acq1 = FCpt(acqiris_board, '{self.prefix}:DIAG:202', platform='{self.platform}',board='{self.acq1_board}', kind='hinted')

    tab_component_names = True

    def __init__(self, prefix, platform='202', acq1_board=None, acq2_board=None, name='gasdet', *args, **kwargs):
        self.acq1_board = acq1_board
        super().__init__(prefix, name=name, **kwargs)




