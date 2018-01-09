"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
import time
import logging
from threading import RLock
from keyword import iskeyword

from ophyd.positioner import PositionerBase
from ophyd.status import wait as status_wait, SubscriptionStatus
from ophyd import Device, Component, EpicsSignal, EpicsSignalRO

logger = logging.getLogger(__name__)


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
                self._run_subs(sub_type=self.SUB_STATE)
                self._prev_value = self.value


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
    def value(self):
        """
        Current state of the object
        """
        state_value = None
        for state, info in self._states.items():
            #Gather signal
            state_signal = getattr(self, state)
            #Get raw EPICS readback
            pv_value = state_signal.get(use_monitor=True)
            try:
                #Associate readback with device state
                signal_state = info[pv_value]
                if signal_state != 'defer':
                    if state_value:
                        assert signal_state == state_value
                    #Update state
                    state_value = signal_state

            #Handle unaccounted readbacks 
            except (KeyError, AssertionError):
                state_value = 'unknown'
                break

        #If all states deferred, report as unknown
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


class DeviceStatesRecord(State, PositionerBase):
    """
    States that come from the standardized lcls device states record
    """
    state = Component(EpicsSignal, "", write_pv=":GO", string=True,
                      auto_monitor=True, limits=False, put_complete=True)
    SUB_RBK_CHG = 'state_readback_changed'
    SUB_SET_CHG = 'state_setpoint_changed'
    _default_sub = SUB_RBK_CHG

    def __init__(self, prefix, *, read_attrs=None, name=None, timeout=None,
                 **kwargs):
        self._move_requested = False
        # Initialize device
        if read_attrs is None:
            read_attrs = ["state"]
        super().__init__(prefix, read_attrs=read_attrs, name=name,
                         timeout=timeout, **kwargs)
        # Add subscriptions
        self.state.subscribe(self._setpoint_changed,
                             event_type=self.state.SUB_SETPOINT,
                             run=False)
        self.state.subscribe(self._read_changed,
                             event_type=self.state.SUB_VALUE,
                             run=False)

    def move(self, position, moved_cb=None, timeout=None, wait=False,
             **kwargs):
        status = super().move(position, moved_cb=moved_cb, timeout=timeout,
                              **kwargs)
        self._move_requested = True

        if self.position != position:
            self.state.put(position, wait=False)
        else:
            status._finished(success=True)

        if wait:
            status_wait(status)
        
        return status

    def check_value(self, value):
        enums = self.state.enum_strs
        if value in enums or value in range(len(enums)):
            return
        else:
            raise StateError("Value {} invalid. Enums are {}".format(value,
                                                                     enums))

    @property
    def position(self):
        return self.value

    @property
    def value(self):
        return self.state.get(use_monitor=True)

    @value.setter
    def value(self, value):
        self.state.put(value)

    def _setpoint_changed(self, **kwargs):
        # Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        # Run subscriptions
        self._run_subs(sub_type=self.SUB_SET_CHG, **kwargs)

    def _read_changed(self, **kwargs):
        # Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        # Run subscriptions
        self._run_subs(sub_type=self.SUB_RBK_CHG, **kwargs)

        # Handle move status
        if self._move_requested:
            readback = self.value
            if readback != "Unknown":
                self._move_requested = False
                setpoint = self.state.get_setpoint(as_string=True)
                success = setpoint == readback
                timestamp = kwargs.pop("timestamp", time.time())
                self._done_moving(success=success, timestamp=timestamp,
                                  value=readback)


class DeviceStatesPart(Device):
    """
    Device to manipulate a specific set position.
    """
    at_state = Component(EpicsSignalRO, "", string=True)
    setpos = Component(EpicsSignal, "_SET")
    delta = Component(EpicsSignal, "_DELTA")


def statesrecord_class(classname, *states, doc=""):
    """
    Create a DeviceStatesRecord class for a particular device.
    """
    components = dict(states=states, __doc__=doc)
    for state_name in states:
        name = state_name.lower().replace(":", "") + "_state"
        components[name] = Component(DeviceStatesPart, state_name)
    components['raw'] = Component(EpicsSignalRO, states[0] + "_CALC.A")
    bases = (DeviceStatesRecord,)
    return type(classname, bases, components)


inoutdoc = "Standard PCDS states record with an IN state and an OUT state."
InOutStates = statesrecord_class("InOutStates", ":IN", ":OUT", doc=inoutdoc)
inoutccmdoc = "Standard PCDS states record with IN, OUT, and CCM states."
InOutCCMStates = statesrecord_class("InOutCCMStates", ":IN", ":OUT", ":CCM",
                                    doc=inoutccmdoc)

class StateError(Exception):
    pass


class StateStatus(SubscriptionStatus):
    """
    Status produced by state request

    The status relies on two methods of the device, first the attribute
    `.value` should reflect the current state. Second, the status will call the
    built-in method `subscribe` with the `event_type` explicitly set to
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
        #Make a quick check_state callable
        def check_state(*args, **kwargs):
            return device.value == desired_state
        
        #Start timeout and subscriptions
        super().__init__(device, check_state, event_type=device.SUB_STATE,
                         timeout=timeout, settle_time=settle_time)
