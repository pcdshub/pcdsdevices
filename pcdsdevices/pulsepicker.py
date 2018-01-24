import logging

from ophyd.device import Component as Cmp, FormattedComponent as FCmp
from ophyd.signal import EpicsSignal, EpicsSignalRO

from .inout import InOutPositioner, InOutStatePositioner
from .signal import AggregateSignal

logger = logging.getLogger(__name__)


class PickerState(AggregateSignal):
    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._inout = self.parent.inout
        self._blade = self.parent.blade
        self._sub_signals = [self._inout.state, self._blade]

    def _calc_readback(self):
        inout = self._cache[self._inout.state]
        inout = self._inout.get_state(inout).name
        if inout == 'OUT':
            return 'OUT'
        else:
            blade = self._cache[self._blade]
            if blade in (0, 'Open'):
                return 'OPEN'
            elif blade in (1, 2, '+ Closed', '- Closed'):
                return 'Closed'
            else:
                return self.parent._unknown

    def put(self, value, **kwargs):
        self.parent.move(value, **kwargs)


class PulsePicker(InOutPositioner):
    state = Cmp(PickerState)
    blade = Cmp(EpicsSignalRO, ':READ_DF')
    mode = Cmp(EpicsSignal, ':SD_SIMPLE', ':SE')
    inout = FCmp(InOutStatePositioner, '{self._inout}')

    states_list = ['OUT', 'OPEN', 'CLOSED']
    in_states = ['CLOSED']
    out_states = ['OUT', 'OPEN']
    _states_alias = {'CLOSED': ['CLOSED', 'IN']}

    _default_config_attrs = ['mode']

    def __init__(self, prefix, inout, *, name, **kwargs):
        self._inout = inout
        super().__init__(prefix, name=name, **kwargs)

    def _do_move(self, state):
        if state.name == 'OUT':
            self.in_out.remove()
        elif state.name == 'OPEN':
            self.in_out.insert()
            self.mode.put(4)
        elif state.name == 'CLOSED':
            self.in_out.insert()
            self.mode.put(5)
