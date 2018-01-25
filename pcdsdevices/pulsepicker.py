import logging

from ophyd.device import Component as Cmp, FormattedComponent as FCmp
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.status import SubscriptionStatus, wait as status_wait

from .inout import InOutRecordPositioner, InOutPVStatePositioner

logger = logging.getLogger(__name__)


class PulsePicker(InOutPVStatePositioner):
    blade = Cmp(EpicsSignalRO, ':READ_DF')
    mode = Cmp(EpicsSignalRO, ':SD_SIMPLE')

    cmd_reset = Cmp(EpicsSignal, ':RESET_PG')
    cmd_open = Cmp(EpicsSignal, ':S_OPEN')
    cmd_close = Cmp(EpicsSignal, ':S_CLOSE')
    cmd_flipflop = Cmp(EpicsSignal, ':RUN_FLIPFLOP')
    cmd_burst = Cmp(EpicsSignal, ':RUN_BURSTMODE')
    cmd_follower = Cmp(EpicsSignal, ':RUN_FOLLOWERMODE')

    in_states = ['CLOSED']
    out_states = ['OPEN']
    _states_alias = {'CLOSED': ['CLOSED', 'IN']}
    _state_logic = {'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}

    _default_config_attrs = ['mode']

    def _do_move(self, state):
        if state.name == 'OPEN':
            self.open()
        if state.name == 'CLOSED':
            self.close()

    def reset(self, wait=True):
        self.cmd_reset.put(1)
        if wait:
            def cb(value, *args, **kwargs):
                return value in (0, 'IDLE')
            status = SubscriptionStatus(self.mode, cb)
            status_wait(status)

    def open(self):
        self.reset()
        self.cmd_open.put(1)

    def close(self):
        self.reset()
        self.cmd_close.put(1)

    def flipflop(self):
        self.reset()
        self.cmd_flipflop.put(1)

    def burst(self):
        self.reset()
        self.cmd_burst.put(1)

    def follower(self):
        self.reset()
        self.cmd_follower.put(1)


class PulsePickerInOut(PulsePicker):
    inout = FCmp(InOutRecordPositioner, '{self._inout}')

    out_states = ['OUT', 'OPEN']
    _state_logic = {'inout.state': {1: 'OUT',
                                    2: 'defer',
                                    3: 'defer'},
                    'blade': {0: 'OPEN',
                              1: 'CLOSED',
                              2: 'CLOSED'}}

    def __init__(self, prefix, *, name, **kwargs):
        # inout follows naming convention
        parts = prefix.split(':')
        self._inout = ':'.join(parts[:1] + ['PP', 'Y'])
        super().__init__(prefix, name=name, **kwargs)

    def _do_move(self, state):
        if state.name == 'OUT':
            self.in_out.remove()
        else:
            self.in_out.insert()
        super()._do_move(state)


class CCMRecordPositioner(InOutRecordPositioner):
    states_list = ['OUT', 'CCM', 'PINK']
    in_states = ['PINK', 'CCM']


class PulsePickerCCM(PulsePickerInOut):
    inout = FCmp(CCMRecordPositioner, '{self._inout}')
