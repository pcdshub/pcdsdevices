import math

from .state import StatePositioner, StateRecordPositioner, PVStatePositioner


class InOutPositioner(StatePositioner):
    """
    Basic InOut StatePositioner. It can be inserted and removed and queried for
    insertion and removal. It can also define transmission values for the
    various states.

    Attributes
    ----------
    in_states: list of strings
        State values that should be considered 'in'.

    out_states: list of strings
        State values that should be considered 'out'.

    _tranmsission: dict{str: number}
        Mapping from each state to the transition coefficient. This should be a
        number from 0 to 1. Default values will be 1 (full transmission) for
        out_states, 0 (full block) for in_states, and nan (no idea!) for
        unaccounted states.
    """
    states_list = ['IN', 'OUT']
    in_states = ['IN']
    out_states = ['OUT']
    _transmission = {}

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self._trans_enum = {}
        self._extend_trans_enum(self.in_states, 0)
        self._extend_trans_enum(self.out_states, 1)

    @property
    def inserted(self):
        return self._pos_in_list(self.in_states)

    @property
    def removed(self):
        return self._pos_in_list(self.out_states)

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """
        Macro to move this device to the first state on the in_states list.
        """
        return self.move(self.in_states[0], moved_cb=moved_cb,
                         timeout=timeout, wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """
        Macro to move this device to the first state on the out_states list.
        """
        return self.move(self.out_states[0], moved_cb=moved_cb,
                         timeout=timeout, wait=wait)

    @property
    def transmission(self):
        state = self.get_state(self.position)
        return self._trans_enum.get(state, math.nan)

    def _extend_trans_enum(self, state_list, default):
        for state in state_list:
            enumst = self.get_state(state)
            self._trans_enum[enumst] = self._transmission.get(state, default)

    def _pos_in_list(self, state_list):
        current_state = self.get_state(self.position)
        for state in state_list:
            if current_state == self.get_state(state):
                return True
        return False


class InOutRecordPositioner(StateRecordPositioner, InOutPositioner):
    """
    Positioner for a motor that moves to states IN and OUT using a standard
    states record. This can be subclassed for other states records that involve
    inserting and removing something into the beam.
    """
    pass


class TTReflaser(InOutRecordPositioner):
    """
    Motor stack that includes both a timetool and a reflaser.
    """
    states_list = ['TT', 'REFL', 'OUT']
    in_states = ['TT', 'REFL']


class InOutPVStatePositioner(PVStatePositioner, InOutPositioner):
    """
    Positioner for a set of PVs that result in aggregate IN and OUT states for
    a single device. This must be subclassed and provided a _state_logic
    attribute to be used. Consult the PVStatePositioner documentation for more
    information.
    """
    pass
