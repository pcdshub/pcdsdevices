from enum import IntEnum

from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .inout import InOutPositioner, InOutPVStatePositioner
from .interface import BaseInterface, LightpathInOutMixin, LightpathMixin


class Commands(IntEnum):
    """Command aliases for opening and closing stoppers."""
    close_valve = 0
    open_valve = 1


class Stopper(InOutPVStatePositioner, LightpathInOutMixin):
    """
    Controls Stopper.

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls Stopper
    installations as well as un-interlocked `GateValve` s.

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV.

    name : str
        Alias for the stopper.

    Attributes
    ----------
    commands : ~enum.IntEnum
        An enum with integer values for `~Commands.open_valve` and
        `~Commands.close_valve` values.
    """

    # Limit-based states
    open_limit = Cpt(EpicsSignalRO, ':OPEN', kind='normal',
                     doc='Reads 1 if the stopper is out, at the open limit.')
    closed_limit = Cpt(EpicsSignalRO, ':CLOSE', kind='normal',
                       doc=('Reads 1 if the stopper is in, '
                            'at the closed limit.'))

    # Information on device control
    command = Cpt(EpicsSignal, ':CMD', kind='omitted',
                  doc='Put here to command a stopper move.')
    commands = Commands

    _state_logic = {'open_limit': {0: 'defer',
                                   1: 'OUT'},
                    'closed_limit': {0: 'defer',
                                     1: 'IN'}}
    _state_logic_set_ref = 'command'

    # QIcon for UX
    _icon = 'fa.times-circle'

    tab_whitelist = ['open', 'close']

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)

    def _do_move(self, state):
        if state.name == 'IN':
            self.command.put(self.commands.close_valve.value)
        elif state.name == 'OUT':
            self.command.put(self.commands.open_valve.value)

    def open(self, **kwargs):
        """Open the stopper."""
        return self.remove(**kwargs)

    def close(self, **kwargs):
        """Close the stopper."""
        return self.insert(**kwargs)


class PPSStopper(InOutPositioner, LightpathInOutMixin):
    """
    PPS Stopper.

    Control of this device only available to PPS systems. This class merely
    interprets the summary of limit switches to let the controls system know
    the current position.

    Because naming conventions for the states are non-uniform this class allows
    you to enter the values at initialization.

    Parameters
    ----------
    prefix : str
        Full PPS Stopper PV.

    name : str
        Alias for the stopper.

    in_state : str, optional
        String associatted with in enum value.

    out_state : str, optional
        String associatted with out enum value.
    """

    state = Cpt(EpicsSignalRO, '', string=True, kind='hinted',
                doc=('Stopper state summary PV that tells us if it is in, '
                     'out, or inconsistent.'))
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
        """PPSStopper can not be commanded via EPICS."""
        raise PermissionError("PPSStopper can not be commanded via EPICS")


class PPSStopper2PV(BaseInterface, LightpathMixin):
    """
    PPS Stopper with two PVs defining the state together.

    One PV is the state of the IN limit switch, one is the state of the OUT
    limit switch.

    By default, these stoppers have IN/NOT_IN and OUT/NOT_OUT PVs with a PV
    suffix of 'INSUM' and 'OUTSUM', but often this is not true and there are
    init arguments to get around these inconsistencies.

    We have no direct control over these from the photon side,
    so this Device only serves as a way to check status and display in the
    lightpath.

    In addition to standard device args, note the following additions:

    Parameters
    ----------
    in_suffix : str, optional
        The suffix for the in_signal that tells us if the stopper is inserted
        or not. Defaults to 'INSUM'.
    out_suffix : str, optional
        The suffix for the out_signal that tells us if the stopper is removed
        or not. Defaults to 'OUTSUM'
    in_value : int, optional
        The value of the in_signal that tells us that the stopper is inserted.
        Defaults to 1.
    out_value : int, optional
        The value of the out_signal that tells us that the stopper is removed.
        Defaults to 1.
    """
    in_signal = FCpt(EpicsSignalRO, '{prefix}{in_suffix}', kind='hinted',
                     doc='Tells us if the stopper is IN or NOT_IN')
    out_signal = FCpt(EpicsSignalRO, '{prefix}{out_suffix}', kind='hinted',
                      doc='Tells us if the stopper is OUT or NOT_OUT')

    # QIcon for UX
    _icon = 'fa.times-circle'

    # Lightpath settings
    lightpath_cpts = ['in_signal', 'out_signal']

    def __init__(self, prefix, *, in_suffix='INSUM', out_suffix='OUTSUM',
                 in_value=1, out_value=1, **kwargs):
        self.in_suffix = in_suffix
        self.out_suffix = out_suffix
        self.in_value = in_value
        self.out_value = out_value
        super().__init__(prefix, **kwargs)

    def calc_lightpath_state(
        self, in_signal: int, out_signal: int
    ) -> LightpathState:
        self._inserted = (in_signal == self.in_value)
        self._removed = (out_signal == self.out_value)

        transmission = 0. if self._inserted else 1.0

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: transmission}
        )


PPSStopperL2SI = PPSStopper2PV
