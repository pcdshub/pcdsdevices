"""
Module to define positioners that move between discrete named states.
"""
from __future__ import annotations

import copy
import functools
import logging
from typing import Any, ClassVar, Dict, List, Optional

from ophyd.device import Component as Cpt
from ophyd.device import Device, required_for_connection
from ophyd.positioner import PositionerBase
from ophyd.signal import EpicsSignal
from ophyd.sim import fake_device_cache, make_fake_device
from ophyd.status import SubscriptionStatus
from ophyd.status import wait as status_wait

from .device import GroupDevice
from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .interface import MvInterface
from .signal import (EpicsSignalEditMD, MultiDerivedSignal, PVStateSignal,
                     PytmcSignal)
from .type_hints import SignalToValue
from .utils import HelpfulIntEnum
from .variety import set_metadata

logger = logging.getLogger(__name__)


class StatePositioner(MvInterface, Device, PositionerBase):
    """
    Base class for state-based positioners.

    ``Positioner`` that moves between discrete states rather than along a
    continuous axis.
%s
    Attributes
    ----------
    state : Signal
        This signal is the final authority on what state the object is in.

    states_list : list of str
        This no longer has to be provided if the state signal contains enum
        information, like an EPICS mbbi. If it is provided, it must be
        an exhaustive list of all possible states. This should be overridden in
        a subclass. 'Unknown' must be omitted in the class definition and will
        be added dynamically in position 0 when the object is created.

    states_enum : ~enum.Enum
        An enum that represents all possible states. This will be constructed
        for the user based on the contents of `states_list` and
        `_states_alias`, but it can also be overriden in a child class.

    _invalid_states : list of str
        States that cannot be moved to. This can be optionally overriden to be
        extended in a subclass. The `_unknown` state will be included
        automatically.

    _unknown : str
        The name of the unknown state, defaulting to 'Unknown'. This can be set
        to :keyword:`False` if there is no unknown state.

    _states_alias : dict
        Mapping of state names to lists of acceptable aliases. This can
        optionally be overriden in a child class.
    """

    __doc__ = __doc__ % basic_positioner_init

    state = None  # Override with Signal that represents state readback

    states_list = []  # Optional: override with an exhaustive list of states
    _invalid_states = []  # Override with states that cannot be set
    _states_alias = {}  # Override with a mapping {'STATE': ['ALIAS', ...]}
    _unknown = 'Unknown'  # Set False if no Unknown state, can also change str

    SUB_STATE = 'state'
    _default_sub = SUB_STATE
    _state_meta_sub = EpicsSignal.SUB_VALUE

    egu = 'state'

    def __init__(self, prefix, *, name, **kwargs):
        if self.__class__ is StatePositioner:
            raise TypeError(('StatePositioner must be subclassed with at '
                             'least a state signal'))
        self._state_initialized = False
        self._has_subscribed_state = False
        super().__init__(prefix, name=name, **kwargs)
        if self.states_list:
            self._state_init()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.state is not None and not cls.states_list:
            cls.state.sub_meta(cls._late_state_init)

    @required_for_connection
    def _state_init(self):
        if not self._state_initialized:
            self._valid_states = [state for state in self.states_list
                                  if state not in self._invalid_states
                                  and state is not None]
            if self._unknown:
                self.states_list = [self._unknown] + self.states_list
                self._invalid_states = [self._unknown] + self._invalid_states
            if not hasattr(self, 'states_enum'):
                self.states_enum = self._create_states_enum()
            self._state_initialized = True

    def _late_state_init(
        self,
        *args,
        enum_strs: Optional[List[str]] = None,
        **kwargs
    ):
        if enum_strs is not None and not self.states_list:
            self.states_list = list(enum_strs)
            # Unknown state reserved for slot zero, automatically added later
            # Removing and auto re-adding *feels* silly, but it was easy to do
            if self._unknown:
                self.states_list.pop(0)
            self._state_init()

    def move(self, position, moved_cb=None, timeout=None, wait=False):
        """
        Move to the desired state and return completion information.

        Parameters
        ----------
        position : int or str
            The enumerate state or the corresponding integer.

        moved_cb : callable, optional
            Function to call at the end of motion. i.e. ``moved_cb(obj=self)``
            will be called when move is complete.

        timeout : int or float, optional
            Move timeout in seconds.

        wait : bool, optional
            If `True`, do not return until the motion has completed.

        Returns
        -------
        status : StateStatus
            `Status` object that represents the move's progress.
        """

        status = self.set(position, moved_cb=moved_cb, timeout=timeout)
        if wait:
            status_wait(status)
        return status

    def set(self, position, moved_cb=None, timeout=None):
        """
        Move to the desired state and return completion information.

        This is the bare-bones implementation of the move with only motion,
        callbacks, and timeouts defined. Additional functional options are
        relegated to the `move` command and bells and whistles are relegated to
        a different interface.

        Parameters
        ----------
        position : int or str
            The enumerate state or the corresponding integer.

        moved_cb : callable, optional
            Function to call at the end of motion. i.e. ``moved_cb(obj=self)``
            will be called when move is complete.

        timeout : int or float, optional
            Move timeout in seconds.

        Returns
        -------
        status : StateStatus
            `Status` object that represents the move's progress.
        """

        logger.debug('set %s to position %s', self.name, position)
        state = self.check_value(position)

        if timeout is None:
            timeout = self._timeout

        status = StateStatus(self, position, timeout=timeout,
                             settle_time=self._settle_time)

        if moved_cb is not None:
            status.add_callback(functools.partial(moved_cb, obj=self))

        self._do_move(state)
        self._run_subs(sub_type=self.SUB_START)
        return status

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if event_type is None:
            event_type = self._default_sub
        if event_type == self.SUB_STATE and not self._has_subscribed_state:
            self.state.subscribe(self._run_sub_state, run=False)
            self._has_subscribed_state = True
        return cid

    def _run_sub_state(self, *args, **kwargs):
        kwargs.pop('sub_type')
        kwargs.pop('obj')
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)

    @property
    def position(self):
        """
        Name of the positioner's current state. If aliases were provided, the
        first alias will be used instead of the base name.
        """
        state = self.state.get()
        state = self.get_state(state).name
        try:
            alias = self._states_alias[state]
            if isinstance(alias, list):
                alias = alias[0]
            return alias
        except KeyError:
            return state

    def check_value(self, value):
        """
        Verify that a value is a valid set state, or raise an exception.

        Returns
        -------
        state : ~enum.Enum
            The corresponding Enum entry for this value. It has two
            meaningful fields, ``name`` and ``value``.
        """

        if not isinstance(value, (int, str)):
            raise TypeError('Valid states must be of type str or int')
        state = self.get_state(value)
        if state.name in self._invalid_states:
            raise ValueError(f'Cannot set the {state.name} state')
        return state

    def get_state(self, value):
        """
        Given an integer or string value, return the proper state entry.

        Returns
        -------
        state : ~enum.Enum
            The corresponding Enum entry for this value. It has two
            meaningful fields, ``name`` and ``value``.
        """

        # Check for a malformed string digit
        if isinstance(value, str) and value.isdigit():
            value = int(value)

        try:
            return self.states_enum.from_any(value)
        except ValueError:
            enum_names = [state.name for state in self.states_enum]
            enum_values = [state.value for state in self.states_enum]
            raise ValueError(
                f"{value} is not a valid state for {self.name}. "
                f"Valid state names are: {enum_names}, "
                f"and their corresponding values are {enum_values}."
            ) from None

    def _do_move(self, state):
        """
        Execute the move command.

        Override this if your move isn't a simple put to the state signal using
        the state value.

        Parameters
        ----------
        state : ~enum.Enum
            Object whose ``.name`` attribute is the string Enum name and whose
            ``.value`` attribute is the integer Enum value.
        """

        self.state.put(state.value)

    def _create_states_enum(self):
        """
        Create an enum that can be used to keep track of aliases, state names,
        and integer enum values.
        """
        state_def = {}
        state_count = 0
        for i, state in enumerate(self.states_list):
            # Skipped None states indicate a missing enum integer
            if state is None:
                continue
            state_count += 1
            state_def[state] = i
            try:
                aliases = self._states_alias[state]
            except KeyError:
                continue
            if isinstance(aliases, str):
                state_def[aliases] = i
            else:
                for alias in aliases:
                    state_def[alias] = i
        enum_name = self.__class__.__name__ + 'States'
        enum = HelpfulIntEnum(enum_name, state_def, start=0, module=__name__)
        if len(enum) != state_count:
            raise ValueError(('Bad states definition! Inconsistency in '
                              'states_list {} or _states_alias {}'
                              ''.format(self.states_list, self._states_alias)))
        return enum

    @property
    def stop(self):
        """
        Hide the stop method behind an AttributeError.

        This makes it so that other interfaces know that the stop method can't
        be run without needing to run it to find out.
        """
        raise AttributeError('StatePositioner has no stop method.')


class PVStatePositioner(StatePositioner):
    """
    A `StatePositioner` that combines a set of PVs into a single state.

    The user can provide state logic and a move method if desired.
%s
    Attributes
    ----------
    _state_logic : dict
        Information dictionaries for each state of the following form:

        .. code::

            {
              "signal_name": {
                               0: "OUT",
                               1: "IN",
                               2: "Unknown",
                               3: "defer"
                             }
            }

        The dictionary defines the relevant signal names and how to interpret
        each of the states. These states will be evaluated in the dict's order,
        which may matter if ``_state_logic_mode == 'FIRST'``.

        This is for cases where the logic is simple. If there are more complex
        requirements, replace the `state` component.

    _state_logic_mode : {'ALL', 'FIRST'}
        This should be 'ALL' (default) if the pvs need to agree for a valid
        state. You can set this to 'FIRST' instead to use the first state
        found while traversing the `_state_logic` tree. This means an earlier
        state definition can mask a later state definition.

    _state_logic_set_ref : str or None
        An optional reference to the component that will be used to set some
        metadata on the state signal if provided.
    """

    __doc__ = __doc__ % basic_positioner_init

    state = Cpt(PVStateSignal, kind='hinted')

    _state_logic: ClassVar[Dict[str, Dict[Any, str]]] = {}
    _state_logic_mode: ClassVar[str] = 'ALL'
    _state_logic_set_ref: ClassVar[Optional[str]] = None

    def __init__(self, prefix, *, name, **kwargs):
        if self.__class__ is PVStatePositioner:
            raise TypeError(('PVStatePositioner must be subclassed, '
                             'adding signals and filling in the '
                             '_state_logic dict.'))
        if self._state_logic and not self.states_list:
            self.states_list = []
            for state_mapping in self._state_logic.values():
                for state_name in state_mapping.values():
                    if state_name not in (self._unknown, 'defer'):
                        if state_name not in self.states_list:
                            self.states_list.append(state_name)
        super().__init__(prefix, name=name, **kwargs)

    def _do_move(self, state):
        raise NotImplementedError(('Class must implement a _do_move method or '
                                   'override the move and set methods'))


class StateRecordPositionerBase(StatePositioner, GroupDevice):
    """
    A `StatePositioner` for an EPICS states record.

    `states_list` does not have to be provided.
    """

    state = Cpt(EpicsSignal, '', write_pv=':GO', kind='hinted')

    # Moving a state positioner puts to state
    stage_group = [state]

    _has_subscribed_readback: bool
    _has_checked_state_enum: bool

    def __init__(self, prefix, *, name, **kwargs):
        self._has_subscribed_readback = False
        self._has_checked_state_enum = False
        super().__init__(prefix, name=name, **kwargs)

    def _run_sub_readback(self, *args, **kwargs):
        kwargs.pop('sub_type')
        kwargs.pop('obj')
        self._run_subs(sub_type=self.SUB_READBACK, obj=self, **kwargs)

    def get_state(self, value):
        if not self._has_checked_state_enum:
            # Add the real enum as the first alias
            for enum_val, state in zip(self.state.enum_strs, self.states_list):
                aliases = self._states_alias.get(state, [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                self._states_alias[state] = [enum_val] + aliases
            self.states_enum = self._create_states_enum()
            self._has_checked_state_enum = True
        return super().get_state(value)


class StateRecordPositioner(StateRecordPositionerBase):
    """
    A `StatePositioner` for an EPICS states record.

    Includes a `motor` attribute for motor level access on single axis
    positioners.

    `states_list` does not have to be provided.
    """

    motor = Cpt(IMS, ':MOTOR', kind='normal')

    tab_whitelist = ['motor']

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if (event_type == self.SUB_READBACK and not
                self._has_subscribed_readback):
            self.motor.user_readback.subscribe(self._run_sub_readback,
                                               run=False)
            self._has_subscribed_readback = True
        return cid

    def stop(self, *, success: bool = False):
        return self.motor.stop(success=success)


class CombinedStateRecordPositioner(StateRecordPositionerBase):
    """
    A `StatePositioner` for an X/Y combined state positioner EPICS record.

    Includes `x_motor` and `y_motor` attributes for motor level access on
    two-axis positioners.

    `states_list` does not have to be provided.
    """

    x_motor = Cpt(IMS, ':X:MOTOR', kind='normal')
    y_motor = Cpt(IMS, ':Y:MOTOR', kind='normal')

    tab_whitelist = ['x_motor', 'y_motor']

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if (event_type == self.SUB_READBACK and not
                self._has_subscribed_readback):
            self.x_motor.user_readback.subscribe(self._run_sub_readback,
                                                 run=False)
            self.y_motor.user_readback.subscribe(self._run_sub_readback,
                                                 run=False)
            self._has_subscribed_readback = True
        return cid


# See MOTION_GVL.MAX_STATES in lcls-twincat-motion
TWINCAT_MAX_STATES = 9


class TwinCATStateConfigOne(Device):
    """
    Configuration of a single state position in TwinCAT.

    Designed to be used with the records from ``lcls-twincat-motion``.
    Corresponds with ``DUT_PositionState``.
    """

    state_name = Cpt(PytmcSignal, ':NAME', io='i', kind='config', string=True,
                     doc='The defined state name.')
    setpoint = Cpt(PytmcSignal, ':SETPOINT', io='io', kind='config',
                   doc='The corresponding motor set position.')
    delta = Cpt(PytmcSignal, ':DELTA', io='io', kind='config',
                doc='The deviation from setpoint that still counts '
                    'as at the position.')
    velo = Cpt(PytmcSignal, ':VELO', io='io', kind='config',
               doc='Velocity to move to the state at.')
    accl = Cpt(PytmcSignal, ':ACCL', io='io', kind='omitted',
               doc='Acceleration to move to the state with.')
    dccl = Cpt(PytmcSignal, ':DCCL', io='io', kind='omitted',
               doc='Deceleration to move to the state with.')
    move_ok = Cpt(PytmcSignal, ':MOVE_OK', io='i', kind='omitted',
                  doc='True if a move to this state is allowed.')
    locked = Cpt(PytmcSignal, ':LOCKED', io='i', kind='omitted',
                 doc='True if the PLC will not permit config edits here.')
    valid = Cpt(PytmcSignal, ':VALID', io='i', kind='omitted',
                doc='True if the state is defined (not empty).')


class TwinCATStateConfigDynamic(Device):
    """
    Configuration of a variable number of TwinCAT states.

    This will become an instance with a number of config states based on the
    input "count" keyword-only required argument.

    Under the hood, this creates classes dynamically and stores them for later
    use. Classes created here will pass an
    isinstance(cls, TwinCATStateConfigDynamic) check, and two devices with
    the same number of states will use the same class from the registry.
    """
    _state_config_registry: ClassVar[
        dict[int, TwinCATStateConfigDynamic]
    ] = {}
    _config_cls: ClassVar[type] = TwinCATStateConfigOne
    _class_prefix: ClassVar[str] = 'StateConfig'

    def __new__(
        cls,
        prefix: str,
        *,
        state_count: int,
        **kwargs
    ):
        try:
            new_cls = cls._state_config_registry[state_count]
        except KeyError:
            new_cls = type(
                f'{cls._class_prefix}{state_count}',
                (cls,),
                {
                    get_dynamic_state_attr(num):
                    Cpt(
                        cls._config_cls,
                        f':{num:02}',
                        kind='config',
                    )
                    for num in range(1, state_count + 1)
                }
            )
            cls._state_config_registry[state_count] = new_cls
        return super().__new__(new_cls)

    def __init__(self, *args, state_count, **kwargs):
        # This is unused, but it can't be allowed to pass into **kwargs
        self.state_count = state_count
        super().__init__(*args, **kwargs)


class FakeTwinCATStateConfigDynamic(TwinCATStateConfigDynamic):
    """
    Proper fake device class for TwinCATStateConfigDynamic.

    Useful in test suites.
    """
    _state_config_registry: ClassVar[
        dict[int, FakeTwinCATStateConfigDynamic]
    ] = {}
    _config_cls: ClassVar[type] = make_fake_device(TwinCATStateConfigOne)
    _class_prefix: ClassVar[str] = 'FakeStateConfig'


# Import-time editing of fake_device_cache!
# This forces fake devices that include TwinCATStateConfigDynamic
# to use our special fake class instead.
# This is needed because the make_fake_device won't find our
# dynamic subclasses.
fake_device_cache[TwinCATStateConfigDynamic] = FakeTwinCATStateConfigDynamic


def get_dynamic_state_attr(state_index: int) -> str:
    """
    Get the attr string associated with a single state index.

    For example, the 5th state should create an attribute on
    TwinCATStateConfigDynamic called "state05". Therefore,
    get_dynamic_state_attr(5) == "state05".

    This is only applicable for integers between 1
    and the TWINCAT_MAX_STATES global variable, inclusive.

    Parameters
    ----------
    state_index : int
        The index of the state.

    Returns
    -------
    state_attr : str
        The corresponding attribute name.
    """
    return f'state{state_index:02}'


def state_config_dotted_names(state_count: int) -> list[Optional[str]]:
    """
    Returns the full dotted names of the state config state_name components.

    This includes None for the Unknown state and is valid for use in
    EpicsSignalEditMD's enum_attrs argument, matching the structure found in
    TwinCATStatePositioner.

    Parameters
    ----------
    state_count : int
        The number of known states used by the device.

    Returns
    -------
    dotted_names : list of str or None
        The full dotted names in state enum order.
    """
    return [None] + [
        f'config.{get_dynamic_state_attr(num)}.state_name'
        for num in range(1, state_count + 1)
    ]


def state_config_dotted_velos(state_count: int) -> list[Optional[str]]:
    """
    Returns the full dotted names of the state config velo components.

    This does not include any entry for the unknown state and can be
    passed directly into the velocity summary MultiDerivedSignal attrs.

    Parameters
    ----------
    state_count : int
        The number of known states used by the device.

    Returns
    -------
    dotted_names : list of str
        The full dotted names in state enum order.
    """
    return [
        f'config.{get_dynamic_state_attr(num)}.velo'
        for num in range(1, state_count + 1)
    ]


class TwinCATStatePositioner(StatePositioner):
    """
    A `StatePositioner` from Beckhoff land.

    This comes from the state record PVs included in the
    ``lcls-twincat-motion`` TwinCAT library. It can be used for any function
    block that follows the pattern set up by ``FB_EpicsInOut``.

    Use `TwinCATInOutPositioner` instead if the device has clear inserted and
    removed states.

    Does not need to be subclassed to be used.
    `states_list` does not have to be provided in a subclass.

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
    state = Cpt(
        EpicsSignalEditMD,
        ":GET_RBV",
        write_pv=":SET",
        enum_attrs=state_config_dotted_names(TWINCAT_MAX_STATES),
        kind="hinted",
        doc="Setpoint and readback for TwinCAT state position.",
    )
    set_metadata(state, dict(variety='command-enum'))

    error = Cpt(PytmcSignal, ':ERR', io='i', kind='normal',
                doc='True if we have an error.')
    error_id = Cpt(PytmcSignal, ':ERRID', io='i', kind='normal',
                   doc='Error code.')
    error_message = Cpt(PytmcSignal, ':ERRMSG', io='i', kind='normal',
                        string=True, doc='Error message')
    busy = Cpt(PytmcSignal, ':BUSY', io='i', kind='normal',
               doc='True if we have an ongoing move.')
    done = Cpt(PytmcSignal, ':DONE', io='i', kind='normal',
               doc='True if we completed the last move.')
    reset_cmd = Cpt(EpicsSignal, ':RESET', kind='normal',
                    doc='Command to reset an error.')

    config = Cpt(
        TwinCATStateConfigDynamic,
        '',
        state_count=TWINCAT_MAX_STATES,
        kind='omitted',
        doc='Configuration of state positions, deltas, etc.',
    )

    def _get_state_velo(
        self, mds: MultiDerivedSignal, items: SignalToValue
    ) -> float:
        """For state_velo, calculate the velocity to show."""
        return max(value for value in items.values())

    def _set_state_velo(
        self, mds: MultiDerivedSignal, value: float
    ) -> SignalToValue:
        """For state_velo, distribute the puts to all fields."""
        return {sig: value for sig in mds.signals}

    state_velo = Cpt(
        MultiDerivedSignal,
        attrs=[
            name for name in
            state_config_dotted_velos(TWINCAT_MAX_STATES)
        ],
        calculate_on_get=_get_state_velo,
        calculate_on_put=_set_state_velo,
        kind='config',
        # Real PV has no unit info yet, assume mm/s
        metadata={'units': 'mm/s'},
        doc=(
            'State mover velocity. Displays the highest velocity of all the '
            'state move destinations and allows bulk writes to all of these '
            'velocity settings. Note that this velocity only applies to '
            'moves done using the state selector box.'
        ),
    )

    set_metadata(error_id, dict(variety='scalar', display_format='hex'))
    set_metadata(reset_cmd, dict(variety='command', value=1))

    def __init_subclass__(cls, **kwargs):
        # We need to adjust the state enum_attrs appropriately if
        # state_count was updated.
        state_count = cls.config.kwargs['state_count']
        parent_count = cls.mro()[1].config.kwargs['state_count']
        if state_count != parent_count:
            cls.state = copy.deepcopy(cls.state)
            cls.state.kwargs['enum_attrs'] = (
                state_config_dotted_names(state_count)
            )
            cls.state_velo = copy.deepcopy(cls.state_velo)
            cls.state_velo.kwargs['attrs'] = [
                name for name in
                state_config_dotted_velos(state_count)
            ]
        # This includes the Device initialization, which assumes our
        # Component instances are finalized.
        # Therefore, do it last
        super().__init_subclass__(**kwargs)

    def clear_error(self):
        self.reset_cmd.put(1)


class StateStatus(SubscriptionStatus):
    """
    `Status` produced by state request.

    The status relies on two methods of the device: First, the attribute
    `~StatePositioner.position` should reflect the current state.
    Second, the status will call the built-in method `subscribe` with the
    `event_type` explicitly set to ``device.SUB_STATE``. This will cause the
    StateStatus to process whenever the device changes state to avoid
    unnecessary polling of the associated EPICS variables.

    Parameters
    ----------
    device : StatePositioner
        The relevant states device.

    desired_state : str
        Requested state.

    timeout : float, optional
        The default timeout to wait to mark the request as a failure.

    settle_time : float, optional
        Time to wait after completion until running callbacks.
    """

    def __init__(self, device, desired_state,
                 timeout=None, settle_time=None):
        # Make a quick check_state callable
        def check_state(*, value, **kwargs):
            value = device.get_state(value)
            desired = device.get_state(desired_state)
            return value == desired

        # Start timeout and subscriptions
        super().__init__(device, check_state, event_type=device.SUB_STATE,
                         timeout=timeout, settle_time=settle_time)

    def set_finished(self, **kwargs):
        self.device._done_moving(success=True)
        super().set_finished(**kwargs)

    def set_exception(self, exc):
        self.device._done_moving(success=False)
        super().set_exception(exc)
