"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
import logging
import functools
from threading import RLock
from keyword import iskeyword
from enum import Enum

from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait, SubscriptionStatus
from ophyd import (Device, EpicsSignal, EpicsSignalRO,
                   Component, FormattedComponent)

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
        a base class.

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

    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        self._valid_states = [state for state in self.states_list
                              if state not in self._invalid_states]
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


class PVStatePositioner(StatePositioner):
    pass


class StateRecordPositioner(StatePositioner):
    state = Component(EpicsSignal, '', write_pv=':GO')
    readback = FormattedComponent(EpicsSignalRO, '{self._readback}')

    _default_read_attrs = ['state', 'readback']

    def __init__(self, prefix, *, name, **kwargs):
        some_state = self.states_list[0]
        self._readback = '{}:{}_CALC.A'.format(prefix, some_state)
        self.states_list = ['Unknown'] + self.states_list
        self._invalid_states = ['Unknown'] + self._invalid_states
        super().__init__(name=name, **kwargs)
        self.prefix = prefix
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


class State(Device):
    """
    Base class for any state device.

    Attributes
    ----------
    value : string
        The current state.

    states : list of string
        A list of the available states. Does not include invalid and unknown
        states.

    SUB_STATE : string
        Subscriptions to SUB_STATE will be called if the value attribute
        changes.
    """
    position = None
    value = None
    states = None
    SUB_STATE = "state_changed"
    _default_sub = SUB_STATE

    egu = 'state'

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        self._prev_value = None
        self._lock = RLock()

    def _update(self, *args, **kwargs):
        """
        Callback that is run each time any component that contributes to the
        state's value changes. Determines if the state has changed since the
        last call to _update, and if so, runs all subscriptions to SUB_STATE.
        """
        with self._lock:
            if self.value != self._prev_value:
                logger.debug("State of %s has changed from %s to %s",
                             self.name or self, self._prev_value, self.value)
                self._run_subs(sub_type=self.SUB_STATE, value=self.value)
                self._prev_value = self.value

    def _done_moving(*args, **kwargs):
        pass


class PVState(State):
    """
    State that comes from some arbitrary set of pvs
    """
    _states = {}

    def __init__(self, prefix, *, read_attrs=None, name=None, **kwargs):
        if read_attrs is None:
            read_attrs = self.states
        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)
        # TODO: Don't subscribe to child signals unless someone is subscribed
        # to us
        for sig_name in self.component_names:
            obj = getattr(self, sig_name)
            obj.subscribe(self._update, event_type=obj.SUB_VALUE)

    @property
    def states(self):
        """
        A list of possible states
        """
        return list(self._states.keys())

    @property
    def position(self):
        return self.value

    @property
    def value(self):
        """
        Current state of the object
        """
        state_value = None
        for state, info in self._states.items():
            # Gather signal
            state_signal = getattr(self, state)
            # Get raw EPICS readback
            pv_value = state_signal.get(use_monitor=True)
            try:
                # Associate readback with device state
                signal_state = info[pv_value]
                if signal_state != 'defer':
                    if state_value:
                        assert signal_state == state_value
                    # Update state
                    state_value = signal_state

            # Handle unaccounted readbacks
            except (KeyError, AssertionError):
                state_value = 'unknown'
                break

        # If all states deferred, report as unknown
        return state_value or 'unknown'

    @value.setter
    def value(self, value):
        logger.debug("Changing state of %s from %s to %s",
                     self, self.value, value)
        self._setter(value)


def pvstate_class(classname, states, doc="", setter=None,
                  signal_class=EpicsSignalRO):
    """
    Create a subclass of PVState for a particular device.

    Parameters
    ----------
    classname : string
        The name of the new subclass
    states : dict
        Information dictionaries for each state of the following form:
        {
          alias : {
                     pvname : ":PVNAME",
                     0 : "out",
                     1 : "in",
                     2 : "unknown",
                     3 : "defer"
                  }
        }
        The dictionary defines the pv names and how to interpret each of the
        states. These states will be evaluated in the dict's order. If the
        order matters, you should pass in an OrderedDict.
    doc : string, optional
        Docstring of the new subclass
    setter : function, optional
        Function that defines how to change the state of the physical device.
        Takes two arguments: self, and the new state value.
    signal_class: class, optional
        Hook to use a different signal class than EpicsSignalRO for testing.

    Returns
    -------
    cls: class
    """
    components = dict(_states=states, __doc__=doc, _setter=setter)
    for state_name, info in states.items():
        if iskeyword(state_name):
            raise ValueError("State name '{}' is invalid".format(state_name) +
                             "because this is a reserved python keyword.")
        components[state_name] = Component(signal_class, info["pvname"])
    bases = (PVState,)
    return type(classname, bases, components)


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
