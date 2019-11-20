"""
Standard classes for LCLS Gate Valves
"""
import logging
from enum import Enum

from ophyd import EpicsSignal, EpicsSignalRO, Component as Cpt

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

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls `Stopper`
    installations as well as un-interlocked `GateValves`

    Parameters
    ----------
    prefix : ``str``
        Full PPS Stopper PV

    name : ``str``
        Alias for the stopper

    Attributes
    ----------
    commands : ``Enum``
        An enum with integer values for ``open_valve``, ``close_valve`` values
    """
    # Limit-based states
    open_limit = Cpt(EpicsSignalRO, ':OPEN', kind='normal')
    closed_limit = Cpt(EpicsSignalRO, ':CLOSE', kind='normal')

    # Information on device control
    command = Cpt(EpicsSignal, ':CMD', kind='omitted')
    commands = Commands

    _state_logic = {'open_limit': {0: 'defer',
                                   1: 'OUT'},
                    'closed_limit': {0: 'defer',
                                     1: 'IN'}}
    # QIcon for UX
    _icon = 'fa.times-circle'

    tab_whitelist = ['open', 'close']

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

    This inherits directly from :class:`.Stopper` but adds additional logic to
    check the state of the interlock before requesting motion. This is not a
    safety feature, just a notice to the operator.
    """
    # Limit based states
    open_limit = Cpt(EpicsSignalRO, ':OPN_DI', kind='normal')
    closed_limit = Cpt(EpicsSignalRO, ':CLS_DI', kind='normal')

    # Commands and Interlock information
    command = Cpt(EpicsSignal,   ':OPN_SW', kind='omitted')
    interlock = Cpt(EpicsSignalRO, ':OPN_OK', kind='normal')

    # QIcon for UX
    _icon = 'fa.hourglass'

    tab_whitelist = ['interlocked']

    def check_value(self, value):
        """Check when removing GateValve interlock is off"""
        value = super().check_value(value)
        if value == self.states_enum.OUT and self.interlocked:
            raise InterlockError('Valve is currently forced closed')
        return value

    @property
    def interlocked(self):
        """
        Whether the interlock on the valve is active, preventing the valve from
        opening
        """
        return not bool(self.interlock.get())


class PPSStopper(InOutPositioner):
    """
    PPS Stopper

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position.

    Because naming conventions for the states are non-uniform this class allows
    you to enter the values at initialization.

    Parameters
    ----------
    prefix : ``str``
        Full PPS Stopper PV

    name : ``str``
        Alias for the stopper

    in_state : ``str``, optional
        String associatted with in enum value

    out_state : ``str``, optional
        String associatted with out enum value
    """
    state = Cpt(EpicsSignalRO, '', string=True, kind='hinted')
    # QIcon for UX
    _icon = 'fa.times-circle'

    def __init__(self, prefix, *, in_state='IN', out_state='OUT', **kwargs):
        # Store state information
        self.in_states = [in_state]
        self.out_states = [out_state]
        self.states_list = self.in_states + self.out_states
        # Load InOutPositioner
        super().__init__(prefix, **kwargs)

    def check_value(self, state):
        """
        PPSStopper can not be commanded via EPICS
        """
        raise PermissionError("PPSStopper can not be commanded via EPICS")
