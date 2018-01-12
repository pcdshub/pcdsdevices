"""
Module to define positioners that move between discrete named states.
"""
import logging
import functools
from enum import Enum
from threading import RLock

from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait, SubscriptionStatus
from ophyd.signal import Signal, EpicsSignal, EpicsSignalRO
from ophyd.device import Device, Component, FormattedComponent

logger = logging.getLogger(__name__)


class StatePositioner(Device, PositionerBase):
    """
    Base class for a Positioner that moves between discrete states rather than
    along a continuout axis.

    Attributes
    ----------
    state: Signal
        This signal is the final authority on what state the object is in.

    states_list: list of str
        An exhaustive list of all possible states. This should be overridden in
        a base class. Unknown must be omitted in the class definition and will
        be added dynamically in position 0 when the object is created.

    states_enum: Enum
        An enum that represents all possible states. This will be constructed
        for the user based on the contents of `states_list` and
        `_states_alias`, but it can also be overriden in the base class.
    """
    state = None  # Override with Signal that represents state readback

    states_list = []  # Override with an exhaustive list of states
    _invalid_states = []  # Override with states that cannot be set
    _states_alias = {}  # Override with a mapping {'STATE': ['ALIAS', ...]}

    SUB_STATE = 'state'
    _default_sub = SUB_STATE

    _default_read_attrs = ['state']

    def __init__(self, prefix, *, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self._valid_states = [state for state in self.states_list
                              if state not in self._invalid_states]
        self.states_list = ['Unknown'] + self.states_list
        self._invalid_states = ['Unknown'] + self._invalid_states
        if not hasattr(self, 'states_enum'):
            self.states_enum = self._create_states_enum()
        self._has_subscribed_state = False

    def move(self, position, moved_cb=None, timeout=None, wait=False):
        """
        Move to the desired state. This is intended to be the interactive move
        for command-line sessions.

        Parameters
        ----------
        position: int or str
            The enumerate state or the corresponding integer

        moved_cb: function, optional
            moved_cb(obj=self) will be called at the end of motion

        timeout: int or float, optional
            Move timeout in seconds

        wait: bool, optional
            If True, do not return until the motion has completed.
        """
        status = self.set(position, moved_cb=moved_cb, timeout=timeout)
        if wait:
            status_wait(status)

    def set(self, position, moved_cb=None, timeout=None):
        """
        Move to the desired state and return completion information.

        Parameters
        ----------
        position: int or str
            The enumerate state or the corresponding integer

        moved_cb: function, optional
            moved_cb(obj=self) will be called at the end of motion

        timeout: int or float, optional
            Move timeout in seconds

        Returns
        -------
        status: StateStatus
            Status object that represents the move's progress.
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
        if isinstance(state, int):
            state = self.states_enum(state).name
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
        state: Enum entry
            The corresponding Enum entry for this value. It has two meaningful
            fields, `name` and `value`.
        """
        bad_value = False
        if isinstance(value, int):
            try:
                state = self.states_enum(value)
            except ValueError:
                bad_value = True
        elif isinstance(value, str):
            try:
                state = self.states_enum[value]
            except KeyError:
                bad_value = True
        else:
            raise TypeError('Valid states must be of type str or int')
        if bad_value:
            err = ('{0} is not a valid move state for {1}. Valid state names '
                   'are: {2}, and their corresponding values are {3}.')
            enum_values = [self.states_enum[state].value
                           for state in self._valid_states]
            raise ValueError(err.format(value, self.name, self._valid_states,
                                        enum_values))
        return state

    def _do_move(self, state):
        """
        Execute the move command. Override this if your move isn't a simple put
        to the state signal using the state name.

        Parameters
        ----------
        state: Enum entry
            Object whose `name` attribute is the string enum name and whose
            `value` attribute is the integer enum value.
        """
        self.state.put(state.name)

    def _create_states_enum(self):
        """
        Create an enum that can be used to keep track of aliases, state names,
        and integer enum values.
        """
        state_def = {}
        for i, state in enumerate(self.states_list):
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
        return Enum(enum_name, state_def, start=0)


class PVStateSignal(Signal):
    """
    Signal that implements the PVStatePositioner state and subscription logic.
    This may seem overly complicated, but it's necessary to avoid calling EPICS
    routines inside of callbacks.
    """
    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._cache = {}
        self._has_subscribed = False
        self._lock = RLock()

    def _insert_value(self, signal_name, value):
        """
        Update the cache with one value and recalculate
        """
        with self._lock:
            self._cache[signal_name] = value
            self._update_state()
            return self._readback

    def _update_state(self):
        """
        Calculate the current state
        """
        with self._lock:
            state_value = None
            for signal_name, info in self.parent._state_logic.items():
                # Get last cached value
                value = self._cache[signal_name]
                try:
                    signal_state = info[value]
                # Handle unaccounted readbacks
                except KeyError:
                    state_value = 'Unknown'
                    break
                # Associate readback with device state
                if signal_state != 'defer':
                    if state_value:
                        # Handle inconsistent readbacks
                        if signal_state != state_value:
                            state_value = 'Unknown'
                            break
                    else:
                        # Set state to first non-deferred value
                        state_value = signal_state
            # If all states deferred, report as unknown
            self._readback = state_value or 'Unknown'

    def get(self, **kwargs):
        """
        Update all values and recalculate
        """
        with self._lock:
            for signal_name in self.parent._state_logic.keys():
                signal = getattr(self.parent, signal_name)
                self._cache[signal_name] = signal.get(**kwargs)
            self._update_state()
            return self._readback

    def put(self, value, **kwargs):
        """
        Move the PVStatePositioner
        """
        self.parent.move(value, **kwargs)

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        if event_type in (None, self.SUB_VALUE) and not self._has_subscribed:
            # We need to subscribe to ALL relevant signals!
            for signal_name in self.parent._state_logic.keys():
                signal = getattr(self.parent, signal_name)
                signal.subscribe(self._run_sub_value, run=False)
            self.get()  # Ensure we have a full cache
        return cid

    def _run_sub_value(self, *args, **kwargs):
        kwargs.pop('sub_type')
        sig = kwargs.pop('obj')
        kwargs.pop('old_value')
        value = kwargs['value']
        with self._lock:
            old_value = self._readback
            signal_name = sig.name
            if signal_name.startswith(self.parent.name):
                signal_name = signal_name[len(self.parent.name)+1:]
            # Update just one value and assume the rest are cached
            # This allows us to run subs without EPICS gets
            value = self._insert_value(signal_name, value)
            self._run_subs(sub_type=self.SUB_VALUE, obj=self, value=value,
                           old_value=old_value)


class PVStatePositioner(StatePositioner):
    """
    A StatePositioner that combines some number of arbitrary state PVs into a
    single device state. The user can provide state logic and a move method if
    desired.

    Attributes
    ----------
    _state_logic: dict
        Information dictionaries for each state of the following form:
        {
          "signal_name": {
                           0: "OUT",
                           1: "IN",
                           2: "Unknown",
                           3: "defer"
                         }
        }
        The dictionary defines the relevant signal names and how to interpret
        each of the states. These states will be evaluated in the dict's order.
        If the order matters, you should pass in an OrderedDict.

        This is for cases where the logic is simple. If there are more complex
        requirements, replace the `state` component.
    """
    state = Component(PVStateSignal)

    _state_logic = {}

    def __init__(self, prefix, *, name, **kwargs):
        if self._state_logic and not self.states_list:
            states_set = set()
            for state_mapping in self._state_logic.values():
                for state_name in state_mapping.values():
                    if state_name not in ('Unknown', 'defer'):
                        states_set.add(state_name)
            self.states_list = list(states_set)
        super().__init__(prefix, name=name, **kwargs)

    def _do_move(self):
        raise NotImplementedError(('Class must implement a _do_move method or '
                                   'override the move and set methods'))


class StateRecordPositioner(StatePositioner):
    """
    A StatePositioner that relies on an EPICS States record to process the
    device state. The `states_list` must match the order of the EPICS enum.
    """
    state = Component(EpicsSignal, '', write_pv=':GO')
    readback = FormattedComponent(EpicsSignalRO, '{self._readback}')

    _default_read_attrs = ['state', 'readback']

    def __init__(self, prefix, *, name, **kwargs):
        some_state = self.states_list[0]
        self._readback = '{}:{}_CALC.A'.format(prefix, some_state)
        super().__init__(prefix, name=name, **kwargs)
        self._has_subscribed_readback = False

    def subscribe(self, cb, event_type=None, run=True):
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
    Status produced by state request

    The status relies on two methods of the device, first the attribute
    `.position` should reflect the current state. Second, the status will call
    the built-in method `subscribe` with the `event_type` explicitly set to
    "device.SUB_STATE". This will cause the StateStatus to process whenever the
    device changes state to avoid unnecessary polling of the associated EPICS
    variables

    Parameters
    ----------
    device : obj
        Device with `value` attribute that returns a state string

    desired_state : str
        Requested state

    timeout : float, optional
        The default timeout to wait to mark the request as a failure

    settle_time : float, optional
        Time to wait after completion until running callbacks
    """
    def __init__(self, device, desired_state,
                 timeout=None, settle_time=None):
        # Make a quick check_state callable
        def check_state(*, value, **kwargs):
            return value == desired_state

        # Start timeout and subscriptions
        super().__init__(device, check_state, event_type=device.SUB_STATE,
                         timeout=timeout, settle_time=settle_time)

    def _finished(self, success=True, **kwargs):
        self.device._done_moving(success=success)
        super()._finished(success=success, **kwargs)
