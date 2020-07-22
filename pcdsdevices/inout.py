"""
Module to centralize code related to devices that can be 'IN' or 'OUT'.

The classes that are defined here can be used to create other devices that need
methods such as :meth:`~InOutPositioner.insert` or
:meth:`~InOutPositioner.remove` and the ability to mark discrete states as in
the beam or out of the beam.
"""
import math

from ophyd.device import required_for_connection
from ophyd.sim import NullStatus

from .doc_stubs import basic_positioner_init, insert_remove
from .state import (CombinedStateRecordPositioner, PVStatePositioner,
                    StatePositioner, StateRecordPositioner,
                    TwinCATStatePositioner)


class InOutPositioner(StatePositioner):
    """
    Base class for a device that can be inserted and removed from the beam.

    This must be subclassed and given a :attr:`state` signal to work properly.
    You should also update the :attr:`states_list`, :attr:`in_states`, and
    :attr:`out_states` lists appropriately.

    These devices can be inserted, removed and queried for insertion and
    removal state. They can also define transmission values for the
    various states.
%s
    Attributes
    ----------
    in_states : list of str
        State values that should be considered 'IN'.

    out_states : list of str
        State values that should be considered 'OUT'.

    _transmission : dict{str: float}
        Mapping from each state to the transmission ratio. This should be a
        number from 0 to 1. Default values will be 1 (full transmission) for
        :attr:`out_states`, 0 (full block) for :attr:`in_states`,
        and :const:`~math.nan` (no idea!) for unaccounted states.

    _in_if_not_out : bool
        If `True`, shorthand for saying "All states not unknown and
        not in out_states belong in the in_states list."
    """

    __doc__ = __doc__ % basic_positioner_init

    states_list = ['IN', 'OUT']
    in_states = ['IN']
    out_states = ['OUT']
    _transmission = {}
    _in_if_not_out = False

    tab_whitelist = ['inserted', 'removed', 'insert', 'remove', 'transmission']

    def __init__(self, prefix, *, name, **kwargs):
        if self.__class__ is InOutPositioner:
            raise TypeError(('InOutPositioner must be subclassed with at '
                             'least a state signal'))
        super().__init__(prefix, name=name, **kwargs)

    @required_for_connection
    def _state_init(self):
        super()._state_init()
        if self._in_if_not_out:
            self.in_states = [state for state in self.states_list
                              if state not in self.out_states
                              and state != self._unknown]
        self._trans_enum = {}
        self._extend_trans_enum(self.in_states, 0)
        self._extend_trans_enum(self.out_states, 1)

    @property
    def inserted(self):
        """`True` if the device is inserted."""
        return self.check_inserted()

    def check_inserted(self, state=None):
        """Query if a particular state counts as inserted."""
        return self._pos_in_list(self.in_states, check_state=state)

    @property
    def removed(self):
        """`True` if the device is removed."""
        return self.check_removed()

    def check_removed(self, state=None):
        """Query if a particular state counts as removed."""
        return self._pos_in_list(self.out_states, check_state=state)

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """
        Moves this device to the first state on the `in_states` list.
        If we're already at some other in state, do nothing instead.
        """
        if self.inserted:
            return NullStatus()
        return self.move(self.in_states[0], moved_cb=moved_cb,
                         timeout=timeout, wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """
        Macro to move this device to the first state on the `out_states` list.
        If we're already at some other out state, do nothing instead.
        """
        if self.removed:
            return NullStatus()
        return self.move(self.out_states[0], moved_cb=moved_cb,
                         timeout=timeout, wait=wait)

    insert.__doc__ += insert_remove
    remove.__doc__ += insert_remove

    @property
    def transmission(self):
        """
        The proportion of incoming beam that makes it through the device.

        This will be a float between 0 and 1, where 0 is no beam and 1 is full
        transmission.
        """
        return self.check_transmission()

    def check_transmission(self, state=None):
        """Query the transition at a particular state."""
        if state is None:
            state = self.position
        state_index = self.get_state(state).value
        return self._trans_enum.get(state_index, math.nan)

    def _extend_trans_enum(self, state_list, default):
        for state in state_list:
            self._update_trans_enum(state, default)

    def _update_trans_enum(self, state, default):
        index = self.states_list.index(state)
        self._trans_enum[index] = self._transmission.get(state, default)

    def _pos_in_list(self, state_list, check_state=None):
        if check_state is None:
            current_state = self.get_state(self.position)
        else:
            current_state = self.get_state(check_state)
        for state in state_list:
            if current_state == self.get_state(state):
                return True
        return False


class InOutRecordPositioner(StateRecordPositioner, InOutPositioner):
    """
    :class:`InOutPositioner` for a standard states record.

    Positioner for a motor that moves to states 'IN' and 'OUT' using a
    standard states record. This can be subclassed for other states records
    that involve inserting and removing something into the beam.
    """

    __doc__ += basic_positioner_init


class CombinedInOutRecordPositioner(CombinedStateRecordPositioner,
                                    InOutPositioner):
    """
    :class:`InOutPositioner` for a standard combined states record.

    Positioner for two motors that moves to states 'IN' and 'OUT' using a
    standard states record. This can be subclassed for other states records
    that involve two motors inserting and removing something into the beam.
    """

    __doc__ += basic_positioner_init


class Reflaser(InOutRecordPositioner):
    """Simple ReferenceLaser with In/Out States."""
    _icon = 'fa.empire'
    __doc__ += basic_positioner_init


class TTReflaser(Reflaser):
    """Motor stack that includes both a timetool and a reflaser."""
    states_list = ['TT', 'REFL', 'OUT']
    in_states = ['TT', 'REFL']
    __doc__ += basic_positioner_init


class InOutPVStatePositioner(PVStatePositioner, InOutPositioner):
    """
    :class:`InOutPositioner` on top of a :class:`~state.PVStatePositioner`.

    Positioner for a set of PVs that result in aggregate 'IN' and 'OUT' states
    for a single device. This must be subclassed and provided a
    :attr:`_state_logic` attribute to be used. Consult the
    :class:`PVStatePositioner` documentation for more information.
    """

    __doc__ += basic_positioner_init

    def __init__(self, *args, **kwargs):
        if self.__class__ is InOutPVStatePositioner:
            raise TypeError(('InOutPVStatePositioner must be subclassed, '
                             'adding signals and filling in the '
                             '_state_logic dict.'))
        super().__init__(*args, **kwargs)


class TwinCATInOutPositioner(TwinCATStatePositioner, InOutPositioner):
    """
    :class:`InOutPositioner` on top of a :class:`TwinCATStatePositioner`.

    This comes from the state record PVs included in the lcls-twincat-motion
    TwinCAT library. It can be used for any function block that follows the
    pattern set up by FB_EpicsInOut.

    Use :class:`TwinCATStatePositioner` instead if the device does not have
    clear inserted and removed states.

    Does not need to be subclassed to be used.
    :attr:`states_list` does not have to be provided in a subclass.

    Parameters
    ----------
    prefix : str
        The EPICS PV prefix for this motor.

    name : str
        An identifying name for this motor.

    settle_time : float, optional
        The amount of extra time to wait before interpreting a move as done.

    timeout : float, optional
        The amount of time to wait before automatically marking a long
        in-progress move as failed.
    """

    # Clear the default in/out state list
    states_list = []
    # In should be everything except state 0 (Unknown) and state 1 (Out)
    _in_if_not_out = True
