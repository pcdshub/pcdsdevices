#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
import threading
from ophyd import Device, Component, EpicsSignal, EpicsSignalRO


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

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        self._prev_value = None
        self._lock = threading.RLock()
    __init__.__doc__ = Device.__init__.__doc__

    def _update(self, *args, **kwargs):
        """
        Callback that is run each time any component that contributes to the
        state's value changes. Determines if the state has changed since the
        last call to _update, and if so, runs all subscriptions to SUB_STATE.
        """
        with self._lock:
            if self.value != self._prev_value:
                self._run_subs(sub_type=self.SUB_STATE)
                self._pref_value = self.value


class StatesPVsBase(State):
    """
    States that come from some arbitrary set of pvs
    """
    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        for device in self._sub_devices:
            device.subscribe(self._update, event_type=self.state.SUB_VALUE)
    __init__.__doc__ = State.__init__.__doc__

    @property
    def states(self):
        return list(self._states.keys())

    @property
    def value(self):
        for state, info in self._states.items():
            state_signal = getattr(self, state)
            pv_value = state_signal.get(use_monitor=True)
            state_value = info.get(pv_value, "unknown")
            if state_value != "defer":
                return state_value
        return "unknown"

    @value.setter
    def value(self, value):
        self._setter(self, value)


def statespv_class(classname, states, doc="", setter=None):
    """
    Create a subclass of StatesPVsBase for a particular device.

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
    """
    components = dict(_states=states, __doc__=doc, _setter=setter)
    for state_name, info in states.items():
        components[state_name] = Component(EpicsSignalRO, info["pvname"])
    return type(classname, (StatesPVsBase,), components)


class StatesIOCBase(State):
    """
    States that come from the standardized lcls position states record
    """
    state = Component(EpicsSignal, "", ":GO")

    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, **kwargs)
        self.state.subscribe(self._update, event_type=self.state.SUB_VALUE)
    __init__.__doc__ = State.__init__.__doc__

    @property
    def value(self):
        return self.state.get(as_string=True, use_monitor=True)

    @value.setter
    def value(self, value):
        self.state.put(value)


class StatesIOCPart(Device):
    at_state = Component(EpicsSignalRO, "")
    setpos = Component(EpicsSignal, "_SET")
    delta = Component(EpicsSignal, "_DELTA")


def statesioc_class(classname, *states, doc=""):
    """
    Create a StatesIOC class for a particular device.
    """
    components = dict(states=states, __doc__=doc)
    for state_name in states:
        components[state_name.lower()] = Component(StatesIOCPart, state_name)
    return type(classname, (StatesIOCBase,), components)


InOutStates = statesioc_class("InOutStates", "IN", "OUT")
