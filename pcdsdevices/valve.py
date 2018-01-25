"""
Standard classes for LCLS Gate Valves
"""
import logging
from enum import Enum
from functools import partial

from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)

from .inout import InOutPositioner, InOutPVStatePositioner

logger = logging.getLogger(__name__)


class Commands(Enum):
    """
    Command aliases for opening and closing valves
    """
    close_valve = 0
    open_valve = 1


class InterlockError(PermissionError):
    """
    Error when request is blocked by interlock logic
    """
    pass


class Stopper(InOutPVStatePositioner):
    """
    Controls Stopper

    Similar to the :class:`.GateValve`, the Stopper class provides basic
    support for Controls stoppers i.e stoppers that can be commanded from
    outside the PPS system

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper
    """
    # Default attributes
    _default_read_attrs = ['open_limit', 'closed_limit']

    # Limit-based states
    open_limit = C(EpicsSignalRO, ':OPEN')
    closed_limit = C(EpicsSignalRO, ':CLOSE')

    # Information on device control
    command = C(EpicsSignal, ':CMD')
    commands = Commands

    _state_logic = {'open_limit': {0: 'defer',
                                   1: 'OUT'},
                    'closed_limit': {0: 'defer',
                                     1: 'IN'}}

    def _do_move(self, state):
        if state.name == 'IN':
            self.command.put(self.commands.close_valve.value)
        elif state.name == 'OUT':
            self.command.put(self.commands.open_valve.value)

    def open(self, **kwargs):
        """
        Open the stopper
        """
        return self.remove(**kwargs)

    def close(self, **kwargs):
        """
        Close the stopper
        """
        return self.insert(**kwargs)


class GateValve(Stopper):
    """
    Basic Vacuum Valve

    Attributes
    ----------
    commands : Enum
        Command aliases for valve
    """
    # Limit based states
    open_limit = C(EpicsSignalRO, ':OPN_DI')
    closed_limit = C(EpicsSignalRO, ':CLS_DI')

    # Commands and Interlock information
    command = C(EpicsSignal,   ':OPN_SW')
    interlock = C(EpicsSignalRO, ':OPN_OK')

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return bool(self.interlock.get())

    def open(self, **kwargs):
        """
        Open the valve
        """
        if self.interlocked:
            raise InterlockError('Valve is currently forced closed')

        return super().open(**kwargs)


class PPSStopper(InOutPositioner):
    """
    PPS Stopper

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV

    name : str, optional
        Alias for the stopper

    in_state : str, optional
        String associatted with in enum value

    out_state :str, optional
        String associatted with out enum value
    """
    state = C(EpicsSignalRO, '', string=True)
    # Default attributes
    _default_read_attrs = ['summary']

    def __init__(self, prefix, *, in_state='IN', out_state='OUT', **kwargs):
        # Store state information
        self.in_states = [in_state]
        self.out_states = [out_state]
        self.state_list = self.in_states + self.out_states
        # Load InOutPositioner
        super().__init__(prefix, **kwargs)

    def _do_move(self, state):
        """
        PPSStopper can not be commanded via EPICS
        """
        raise NotImplementedError("PPSStopper can not be commanded via EPICS")
