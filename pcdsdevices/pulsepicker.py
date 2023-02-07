"""
Module for the LCLS1 `PulsePicker`
"""
import logging

from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus
from ophyd.status import wait as status_wait

from pcdsdevices.interface import LightpathInOutMixin

from .device import GroupDevice
from .doc_stubs import basic_positioner_init
from .inout import InOutPVStatePositioner, InOutRecordPositioner

logger = logging.getLogger(__name__)


class PulsePicker(InOutPVStatePositioner, LightpathInOutMixin):
    """
    Device that picks which pulses to let through.

    This device opens/closes in response to event codes to let certain pulses
    through and block others.
    """

    __doc__ += basic_positioner_init

    blade = Cpt(EpicsSignalRO, ':READ_DF', kind='normal')
    mode = Cpt(EpicsSignalRO, ':SD_SIMPLE', kind='config')

    cmd_reset = Cpt(EpicsSignal, ':RESET_PG', kind='omitted')
    cmd_open = Cpt(EpicsSignal, ':S_OPEN', kind='omitted')
    cmd_close = Cpt(EpicsSignal, ':S_CLOSE', kind='omitted')
    cmd_flipflop = Cpt(EpicsSignal, ':RUN_FLIPFLOP', kind='omitted')
    cmd_burst = Cpt(EpicsSignal, ':RUN_BURSTMODE', kind='omitted')
    cmd_follower = Cpt(EpicsSignal, ':RUN_FOLLOWERMODE', kind='omitted')

    states_list = ['OPEN', 'CLOSED']
    in_states = ['CLOSED']
    out_states = ['OPEN']
    _states_alias = {'CLOSED': ['CLOSED', 'IN']}
    _state_logic = {'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}
    _state_logic_set_ref = 'cmd_open'
    # QIcon for UX
    _icon = 'fa.compass'

    tab_whitelist = ['reset', 'open', 'close', 'flipflop', 'burst', 'follower']

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

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """

        self._log_request('RESET')
        if self.mode.get() not in (0, 'IDLE'):
            self.cmd_reset.put(1)
            if wait:
                self._wait(self.mode, 0, 'IDLE')

    def open(self, wait=False):
        """
        Cancel the current mode and leave the PulsePicker OPEN.

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """

        self.reset(wait=True)
        self._log_request('OPEN')
        self.cmd_open.put(1)
        if wait:
            self._wait(self.blade, 0, 'OPEN')

    def close(self, wait=False):
        """
        Cancel the current mode and leave the PulsePicker CLOSED.

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """
        self.reset(wait=True)
        self._log_request('CLOSED')
        self.cmd_close.put(1)
        if wait:
            self._wait(self.blade, 1, 2, 'CLOSED -', 'CLOSED +')

    def flipflop(self, wait=False):
        """
        Change the current mode to FLIP-FLOP.

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """
        self.reset(wait=True)
        self._log_request('FLIP-FLOP')
        self.cmd_flipflop.put(1)
        if wait:
            self._wait(self.mode, 2, 'FLIP-FLOP')

    def burst(self, wait=False):
        """
        Change the current mode to BURST.

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """

        self.reset(wait=True)
        self._log_request('BURST')
        self.cmd_burst.put(1)
        if wait:
            self._wait(self.mode, 3, 'BURST')

    def follower(self, wait=False):
        """
        Change the current mode to FOLLOWER.

        Parameters
        ----------
        wait : bool, optional
            If `True`, block until procedure is done.
        """

        self.reset(wait=True)
        self._log_request('FOLLOWER')
        self.cmd_follower.put(1)
        if wait:
            self._wait(self.mode, 6, 'FOLLOWER')


class PulsePickerInOut(PulsePicker, GroupDevice):
    """
    `PulsePicker` paired with a states record to control the Y position.

    This allows us to insert and remove the entire device from the beam.

    The inout states record lives in a separate IOC from the main pulsepicker
    due to versioning issues. The parent IOC is called 'device_states'. We're
    expecting the resulting states record to have states 'Unknown', 'OUT',
    and 'IN', in that order. The naming convention for the states is to take
    the first two segments of the pulsepicker prefix and add 'PP:Y' to the end.
    So therefore, if the picker is 'TST:DG1:MMS:03', the inout states should be
    'TST:DG1:PP:Y'.
    """

    __doc__ += basic_positioner_init

    inout = FCpt(InOutRecordPositioner, '{self._inout}', kind='normal')

    states_list = ['OUT', 'OPEN', 'CLOSED']
    out_states = ['OUT', 'OPEN']
    _state_logic = {'inout.state': {1: 'defer',
                                    2: 'OUT',
                                    'IN': 'defer',
                                    'OUT': 'OUT'},
                    'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}
    _state_logic_mode = 'FIRST'

    # When we move PulsePickerInOut, it moves inout
    stage_group = [inout]

    def __init__(self, prefix, **kwargs):
        # inout follows naming convention
        parts = prefix.split(':')
        self._inout = ':'.join(parts[:2] + ['PP', 'Y'])
        super().__init__(prefix, **kwargs)

    def _do_move(self, state):
        """
        Handles movement to state 'OUT'.

        Handles moving the state motor OUT when commands like
        ``pulsepicker.move('OUT')`` are called, and inserting on other move
        commands.
        """

        if state.name == 'OUT':
            self.inout.remove()
        else:
            self.inout.insert()
        super()._do_move(state)
