import logging

from ophyd.device import Component as Cmp, FormattedComponent as FCmp
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus, wait as status_wait

from .inout import InOutRecordPositioner, InOutPVStatePositioner

logger = logging.getLogger(__name__)


class PulsePicker(InOutPVStatePositioner):
    """
    Device that can open/close in response to event codes to let certain pulses
    through and block others.
    """
    blade = Cmp(EpicsSignalRO, ':READ_DF')
    mode = Cmp(EpicsSignalRO, ':SD_SIMPLE')

    cmd_reset = Cmp(EpicsSignal, ':RESET_PG')
    cmd_open = Cmp(EpicsSignal, ':S_OPEN')
    cmd_close = Cmp(EpicsSignal, ':S_CLOSE')
    cmd_flipflop = Cmp(EpicsSignal, ':RUN_FLIPFLOP')
    cmd_burst = Cmp(EpicsSignal, ':RUN_BURSTMODE')
    cmd_follower = Cmp(EpicsSignal, ':RUN_FOLLOWERMODE')

    states_list = ['OPEN', 'CLOSED']
    in_states = ['CLOSED']
    out_states = ['OPEN']
    _states_alias = {'CLOSED': ['CLOSED', 'IN']}
    _state_logic = {'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}

    _default_config_attrs = ['mode']

    def _do_move(self, state):
        """
        Handle move requests for basic open/close commands. This allows us to
        make calls like pulsepicker.move('OPEN')
        """
        if state.name == 'OPEN':
            self.open(wait=False)
        if state.name == 'CLOSED':
            self.close(wait=False)

    def _wait(self, sig, *goals):
        """
        Helper function to wait for a signal to reach a value. This is used
        here because most commands are only valid when mode is IDLE.
        """
        def cb(value, *args, **kwargs):
            logger.debug((value, goals))
            return value in goals
        status = SubscriptionStatus(sig, cb)
        status_wait(status)

    def _log_request(self, mode):
        logger.debug('Request %s %s', self.name, mode)

    def reset(self, wait=False):
        """
        Cancel the current mode.
        """
        self._log_request('RESET')
        if self.mode not in (0, 'IDLE'):
            self.cmd_reset.put(1)
            if wait:
                self._wait(self.mode, 0, 'IDLE')

    def open(self, wait=False):
        """
        Cancel the current mode and leave the PulsePicker OPEN.
        """
        self.reset(wait=True)
        self._log_request('OPEN')
        self.cmd_open.put(1)
        if wait:
            self._wait(self.blade, 0, 'OPEN')

    def close(self, wait=False):
        """
        Cancel the current mode and leave the PulsePicker CLOSED.
        """
        self.reset(wait=True)
        self._log_request('CLOSED')
        self.cmd_close.put(1)
        if wait:
            self._wait(self.blade, 1, 2, 'CLOSED -', 'CLOSED +')

    def flipflop(self, wait=False):
        """
        Change the current mode to FLIP-FLOP.
        """
        self.reset(wait=True)
        self._log_request('FLIP-FLOP')
        self.cmd_flipflop.put(1)
        if wait:
            self._wait(self.mode, 2, 'FLIP-FLOP')

    def burst(self, wait=False):
        """
        Change the current mode to BURST.
        """
        self.reset(wait=True)
        self._log_request('BURST')
        self.cmd_burst.put(1)
        if wait:
            self._wait(self.mode, 3, 'BURST')

    def follower(self, wait=False):
        """
        Change the current mode to FOLLOWER.
        """
        self.reset(wait=True)
        self._log_request('FOLLOWER')
        self.cmd_follower.put(1)
        if wait:
            self._wait(self.mode, 6, 'FOLLOWER')


class PulsePickerInOut(PulsePicker):
    """
    PulsePicker paired with a states record to control the Y position. This
    allows us to insert and remove the entire device from the beam.

    The inout states record lives in a separate IOC from the main pulsepicker
    due to versioning issues. The parent IOC is called 'device_states'. We're
    expecting the resulting states record to have states 'Unknown', 'OUT',
    and 'IN', in that order. The naming convention for the states is to take
    the first two segments of the pulsepicker prefix and add 'PP:Y' to the end.
    So therefore, if the picker is 'TST:DG1:MMS:03', the inout states should be
    'TST:DG1:PP:Y'.
    """
    inout = FCmp(InOutRecordPositioner, '{self._inout}')

    states_list = ['OUT', 'OPEN', 'CLOSED']
    out_states = ['OUT', 'OPEN']
    _state_logic = {'inout.state': {1: 'OUT',
                                    2: 'defer',
                                    'OUT': 'OUT',
                                    'IN': 'defer'},
                    'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}
    _state_logic_mode = 'FIRST'

    def __init__(self, prefix, **kwargs):
        # inout follows naming convention
        parts = prefix.split(':')
        self._inout = ':'.join(parts[:1] + ['PP', 'Y'])
        super().__init__(prefix, **kwargs)

    def _do_move(self, state):
        """
        Handle moving the state motor OUT when commands like
        pulsepicker.move('OUT') are called, and inserting on other move
        commands.
        """
        if state.name == 'OUT':
            self.inout.remove()
        else:
            self.inout.insert()
        super()._do_move(state)
