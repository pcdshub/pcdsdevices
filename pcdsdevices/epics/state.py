#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
from threading import RLock
from keyword import iskeyword
from .signal import EpicsSignal, EpicsSignalRO
from ..component import Component
from .device import Device
from .iocdevice import IocDevice


class State(IocDevice):
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
        self._lock = RLock()

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


class PVState(State):
    """
    State that comes from some arbitrary set of pvs
    """
    _states = {}

    def __init__(self, prefix, *, ioc="", read_attrs=None, name=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = self.states
        super().__init__(prefix, ioc=ioc, read_attrs=read_attrs, name=name,
                         **kwargs)
        for device in self._sub_devices:
            device.subscribe(self._update, event_type=self.state.SUB_VALUE)

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


def pvstate_class(classname, states, doc="", setter=None):
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
    """
    components = dict(_states=states, __doc__=doc, _setter=setter)
    for state_name, info in states.items():
        if iskeyword(state_name):
            raise ValueError("State name '{}' is invalid".format(state_name) +
                             "because this is a reserved python keyword.")
        components[state_name] = Component(EpicsSignalRO, info["pvname"])
    return type(classname, (PVState,), components)


class DeviceStatesRecord(State):
    """
    States that come from the standardized lcls device states record
    """
    state = Component(EpicsSignal, "", write_pv=":GO", string=True)

    def __init__(self, prefix, *, ioc="", read_attrs=None, name=None,
                 **kwargs):
        if read_attrs is None:
            read_attrs = ["state"]
        super().__init__(prefix, ioc=ioc, read_attrs=read_attrs, name=name,
                         **kwargs)
        self.state.subscribe(self._update, event_type=self.state.SUB_VALUE)

    @property
    def value(self):
        return self.state.get(use_monitor=True)

    @value.setter
    def value(self, value):
        self.state.put(value)


class DeviceStatesPart(Device):
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
    return type(classname, (DeviceStatesRecord,), components)


inoutdoc = "Standard LCLS states record with an IN state and an OUT state."
InOutStates = statesrecord_class("InOutStates", ":IN", ":OUT", doc=inoutdoc)
inoutccmdoc = "Standard LCLS states record with IN, OUT, and CCM states."
InOutCCMStates = statesrecord_class("InOutCCMStates", ":IN", ":OUT", ":CCM",
                                    doc=inoutccmdoc)
