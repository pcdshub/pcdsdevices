"""
Ophyd devices for the Hard X-ray Gas Energy Monitor
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
    waveform = Cpt(EpicsSignalRO, ':Data', kind='hinted')
    

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

    ch1 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}1',kind='hinted')
    ch2 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}2',kind='hinted')
    ch3 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}3',kind='hinted')
    ch4 = FCpt(acqiris_channel, '{self.prefix}:{self._board_pref}4',kind='hinted')


    tab_component_names = True

    run_state = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MDAQStatus',kind='config', string=True)
    sample_interval = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MSampInterval',kind='config')
    delay_time = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MDelayTime',kind='config')
    num_samples = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MNbrSamples',kind='config')
    trig_source = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MTriggerSource',kind='config', string=True)
    trig_class = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MTrigClass',kind='config', string=True)
    samples_freq = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MSampFrequency',kind='config')
    rate =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MEventRate',kind='config')
    num_events =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MEventCount',kind='config')
    num_trig_timeouts = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTriggerTimeouts',kind='config')
    num_truncated = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTruncated',kind='config')

    # "Extras"
    acq_type = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MType',kind='config', string=True)
    acq_mode = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MMode',kind='config', string=True)
    acq_mode_flags = FCpt(EpicsSignal, '{self.prefix}:{self.board}:MModeFlags',kind='config', string=True)
    clock_type = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MClockType',kind='config', string=True)
    crate_number =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MCrateNb',kind='config')
    nADC_bits =  FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MNbrADCBits',kind='config')
    crate_slot = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MPosInCrate',kind='config')
    temp = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MTemperature_m',kind='config')
    input_freq = FCpt(EpicsSignalRO, '{self.prefix}:{self.board}:MInputFrequency',kind='config')
    
    def __init__(self, prefix, *, platform, board, name='acqiris_board', **kwargs):
        self.board = board
        self.prefix = prefix
        self.platform = platform
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

# class gasdet(Device, BaseInterface):
#     """
#     Class to create complete gas detector with all acqiris boards.

#     Parameters
#     ----------
#     prefix : ``str``
#         The PV base of the digitizer.
#     platform : ``str``
#         This a legacy PV segment found in the GasDetDAQ IOC. The default '202' applies to
#         the HXR gas detector system.
#     board1 : ``str``
#         3-digit number representing the first digitizer board, e.g. '240', '360'.
#     board2 : ``str``
#         3-digit number representing the second digitizer board, e.g. '240', '360'.

#     """
#     ###
#     # At the moment I cannot get the self.board and self.platfrom arguments to be interpreted by component 
#     # (they just pass the literal string "{self.board}" etc.
#     ##
#     acq1 = FCpt(acqiris_board, '{self.prefix}:DIAG:{self.platform}', platform='{self.platform}',board='{self.board1}', kind='hinted')
#     acq2 = FCpt(acqiris_board, '{self.prefix}:DIAG:{self.platform}', platform='{self.platform}',board='{self.board2}.', kind='hinted')

#     tab_component_names = True
#     tab_whitelist = ['acq1', 'acq2']

#     def __init__(self, prefix, *, platform, board1, board2, name='gasdet', **kwargs):
#         self.platform = platform
#         self.board1 = board1
#         self.board2 = board2
#         super().__init__(prefix, name=name, **kwargs)

