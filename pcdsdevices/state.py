"""
Module to define positioners that move between discrete named states.
"""
import logging
import functools
from enum import Enum

from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait, SubscriptionStatus
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.device import Device, Component, FormattedComponent

from .doc_stubs import basic_positioner_init
from .mv_interface import MvInterface
from .signal import AggregateSignal

logger = logging.getLogger(__name__)


class StatePositioner(Device, PositionerBase, MvInterface):
    """
    Base class for a ``Positioner`` that moves between discrete states rather
    than along a continuout axis.
%s
    Attributes
    ----------
    state: ``Signal``
        This signal is the final authority on what state the object is in.

    _states_list: ``list of str``
        An exhaustive list of all possible states. This should be overridden in
        a base class. Unknown must be omitted in the class definition and will
        be added dynamically in position 0 when the object is created.
        If provided with type ``int``

    _dynamic_states: ``bool``
        An alternative to _states_list when the names of the states are
        variable, and the names can be grabbed from the `state` signal later.
        This list must be called ``state.enum_strs``.
        There is an assumption made that objects from a class with dynamic
        states has consistent behavior with the position index, even if
        the string names of the states vary.

    _states_enum: ``Enum``
        An enum that represents all possible states. This will be constructed
        for the user based on the contents of `_states_list`, _dynamic_states,
        and `_states_alias`, but it can also be overriden in a child class.

    _invalid_states: ``list of str`` or ``list of int``
        States that cannot be moved to. This can be optionally overriden to be
        extended in a base class. The `_unknown` state will be included
        automatically, unless `_dynamic_states` is ``True``, in which case the
        string held in the zero position of ``state.enum_strs`` is assumed to
        be the unknown state.

    _unknown: ``str``
        The name of the unknown state, defaulting to 'Unknown'. This can be set
        to ``False`` if there is no unknown state.

    _states_alias: ``dict``
        Mapping of state names to lists of acceptable aliases. This can
        optionally be overriden in a child class. If `_dynamic_states` is
        ``True``, this can be a mapping of index to aliases.
    """
    __doc__ = __doc__ % basic_positioner_init

    state = None  # Override with Signal that represents state readback

    _states_list = []  # Override with an exhaustive list of states
    _dynamic_states = False  # Alternative to _states_list
    _invalid_states = []  # Override with states that cannot be set
    _states_alias = {}  # Override with a mapping {'STATE': ['ALIAS', ...]}
    _unknown = 'Unknown'  # Set False if no Unknown state, can also change str

    SUB_STATE = 'state'
    _default_sub = SUB_STATE

    _default_read_attrs = ['state']

    egu = 'state'

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self._needs_state_init = True
        if not self._dynamic_states:
            self._init_states()
        self._has_subscribed_state = False

    @property
    def states_list(self):
        if self._needs_state_init:
            self._init_states()
        return self._states_list

    @property
    def states_enum(self):
        if self._needs_state_init:
            self._init_states()
        return self._states_enum

    def _init_states(self):
        if self._dynamic_states:
            self._states_list = list(self.state.enum_strs)
            self._invalid_states = self._states_list[0] + self._invalid_states
        elif self._unknown:
            self._states_list = [self._unknown] + self._states_list
            self._invalid_states = [self._unknown] + self._invalid_states
        self._valid_states = []
        for i, state in enumerate(self._states_list):
            if all(x not in self._invalid_states for x in (i, state)):
                self._valid_states.append(state)
        if not hasattr(self, '_states_enum'):
            self._states_enum = self._create_states_enum()
        self._states_list = [s for s in self._states_list if s is not None]
        self._needs_state_init = False

    def move(self, position, moved_cb=None, timeout=None, wait=False):
        """
        Move to the desired state and return completion information.

        Parameters
        ----------
        position: ``int`` or ``str``
            The enumerate state or the corresponding integer

        moved_cb: ``function``, optional
            moved_cb(obj=self) will be called at the end of motion

        timeout: ``int`` or ``float``, optional
            Move timeout in seconds

        wait: ``bool``, optional
            If True, do not return until the motion has completed.

        Returns
        -------
        status: ``StateStatus``
            ``Status`` object that represents the move's progress.
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
        position: ``int`` or ``str``
            The enumerate state or the corresponding integer

        moved_cb: ``function``, optional
            moved_cb(obj=self) will be called at the end of motion

        timeout: ``int`` or ``float``, optional
            Move timeout in seconds

        Returns
        -------
        status: ``StateStatus``
            ``Status`` object that represents the move's progress.
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
        """
        Subcribe a callback to be run on specific events.

        See the ``opyhd`` documentation for more information.
        """
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

    @property
    def hints(self):
        return {'fields': [self.state.name]}

    def check_value(self, value):
        """
        Verify that a value is a valid set state, or raise an exception.

        Returns
        -------
        state: ``Enum``
            The corresponding ``Enum`` entry for this value. It has two
            meaningful fields, ``name`` and ``value``.
        """
        if not isinstance(value, (int, str)):
            raise TypeError('Valid states must be of type str or int')
        state = self.get_state(value)
        if state.name == self._unknown:
            raise ValueError('Cannot set the Unknown state')
        return state

    def get_state(self, value):
        """
        Given an integer or string value, return the proper state entry.

        Returns
        -------
        state: ``Enum``
            The corresponding ``Enum`` entry for this value. It has two
            meaningful fields, ``name`` and ``value``.
        """
        try:
            return self.states_enum[value]
        except KeyError:
            try:
                return self.states_enum(value)
            except ValueError:
                err = ('{0} is not a valid state for {1}. Valid state names '
                       'are: {2}, and their corresponding values are {3}.')
                enum_names = [state.name for state in self.states_enum]
                enum_values = [state.value for state in self.states_enum]
                raise ValueError(err.format(value, self.name, enum_names,
                                            enum_values))

    def _do_move(self, state):
        """
        Execute the move command. Override this if your move isn't a simple put
        to the state signal using the state name.

        Parameters
        ----------
        state: ``Enum``
            Object whose ``name`` attribute is the string enum name and whose
            ``value`` attribute is the integer enum value.
        """
        self.state.put(state.name)

    def _create_states_enum(self):
        """
        Create an enum that can be used to keep track of aliases, state names,
        and integer enum values.
        """
        state_def = {}
        for i, state in enumerate(self.states_list):
            # Skipped None states indicate a missing enum integer
            if state is None:
                continue
            state_def[state] = i
            try:
                aliases = self._states_alias[state]
            except KeyError:
                try:
                    aliases = self._states_alias[i]
                except KeyError:
                    continue
            if isinstance(aliases, str):
                state_def[aliases] = i
            else:
                for alias in aliases:
                    state_def[alias] = i
        enum_name = self.__class__.__name__ + 'States'
        return Enum(enum_name, state_def, start=0)


class PVStateSignal(AggregateSignal):
    """
    Signal that implements the `PVStatePositioner` state logic.

    See `AggregateSignal` for more information.
    """
    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._sub_map = {}
        for signal_name in self.parent._state_logic.keys():
            sig = self.parent
            for part in signal_name.split('.'):
                sig = getattr(sig, part)
            self._sub_signals.append(sig)
            self._sub_map[signal_name] = sig

    def _calc_readback(self):
        state_value = None
        for signal_name, info in self.parent._state_logic.items():
            # Get last cached value
            value = self._cache[self._sub_map[signal_name]]
            try:
                signal_state = info[value]
            # Handle unaccounted readbacks
            except KeyError:
                state_value = self.parent._unknown
                break
            # Associate readback with device state
            if signal_state != 'defer':
                if state_value:
                    # Handle inconsistent readbacks
                    if signal_state != state_value:
                        state_value = self.parent._unknown
                        break
                else:
                    # Set state to first non-deferred value
                    state_value = signal_state
                    if self.parent._state_logic_mode == 'ALL':
                        continue
                    elif self.parent._state_logic_mode == 'FIRST':
                        break
        # If all states deferred, report as unknown
        return state_value or self.parent._unknown

    def put(self, value, **kwargs):
        """
        Move the PVStatePositioner
        """
        self.parent.move(value, **kwargs)


class PVStatePositioner(StatePositioner):
    """
    A `StatePositioner` that combines a set of PVs into a single state.

    The user can provide state logic and a move method if desired.
%s
    Attributes
    ----------
    _state_logic: ``dict``
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

    _state_logic_mode: ``str``, ``'ALL'`` or ``'FIRST'``
        This should be ``ALL`` (default) if the pvs need to agree for a valid
        state. You can set this to 'FIRST' to instead use the first state
        found while traversing the state_logic tree. This means an earlier
        state definition can mask a later state definition.
    """
    __doc__ = __doc__ % basic_positioner_init

    state = Component(PVStateSignal)

    _state_logic = {}
    _state_logic_mode = 'ALL'

    def __init__(self, prefix, *, name, **kwargs):
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


class StateRecordPositioner(StatePositioner):
    """
    A `StatePositioner` for an EPICS states record.

    Dynamically allocates the enums based on what EPICS says. An additional
    ``settings`` ``list``  must be provided to get a readback, and in the
    future this parameter will be used to configure the set positions.

    Parameters
    ----------
    settings: ``list of str``, optional if `_default_settings` defined.
        A list of strings that match the IOC's configuration PVs. This can vary
        from IOC to IOC, even controlling the same device.

    Attributes
    ----------
    _default_settings: ``list of str``
        Set this to the default settings argument for a particular subclass.
    """
    state = Component(EpicsSignal, '', write_pv=':GO')
    readback = FormattedComponent(EpicsSignalRO, '{self._readback}')

    _dynamic_states = True
    _default_settings = None

    _default_read_attrs = ['state', 'readback']

    def __init__(self, prefix, *, name, settings=None, **kwargs):
        if settings is None:
            settings = self._default_settings
        if settings is None:
            raise TypeError('Missing settings and _default_settings')
        self._readback = '{}:{}_CALC.A'.format(prefix, settings[0])
        super().__init__(prefix, name=name, **kwargs)
        self._has_subscribed_readback = False

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subcribe a callback to be run on specific events.

        See the ``opyhd`` documentation for more information.
        """
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if (event_type == self.SUB_READBACK and not
                self._has_subscribed_readback):
            self.readback.subscribe(self._run_sub_readback, run=False)
            self._has_subscribed_readback = True
        return cid

    def _run_sub_readback(self, *args, **kwargs):
        kwargs.pop('sub_type')
        kwargs.pop('obj')
        self._run_subs(sub_type=self.SUB_READBACK, obj=self, **kwargs)


class StateStatus(SubscriptionStatus):
    """
    ``Status`` produced by state request

    The status relies on two methods of the device, first the attribute
    ``.position`` should reflect the current state. Second, the status will
    call the built-in method ``subscribe`` with the ``event_type`` explicitly
    set to ``device.SUB_STATE``. This will cause the ``StateStatus`` to
    process whenever the device changes state to avoid unnecessary polling
    of the associated EPICS variables

    Parameters
    ----------
    device : `StatePositioner`
        The relevant states device

    desired_state : ``str``
        Requested state

    timeout : ``float``, optional
        The default timeout to wait to mark the request as a failure

    settle_time : ``float``, optional
        Time to wait after completion until running callbacks
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

    def _finished(self, success=True, **kwargs):
        self.device._done_moving(success=success)
        super()._finished(success=success, **kwargs)
