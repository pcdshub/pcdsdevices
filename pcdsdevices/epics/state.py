#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
import logging
from threading import RLock
from keyword import iskeyword

from .signal import EpicsSignal, EpicsSignalRO
from .component import Component
from .device import Device
from .iocdevice import IocDevice

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
        for sig_name in self.signal_names:
            obj = getattr(self, sig_name)
            obj.subscribe(self._update, event_type=obj.SUB_VALUE)

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
        logger.debug("Changing state of %s from %s to %s",
                     self, self.value, value)
        self._setter(value)


def pvstate_class(classname, states, doc="", setter=None, has_ioc=False,
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
    has_ioc: bool, optional
        If True, this class will expect an ioc argument for the iocadmin pvname
        prefix. Defaults to False.
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
    if has_ioc:
        bases = (PVState, IocDevice)
    else:
        bases = (PVState,)
    return type(classname, bases, components)


class DeviceStatesRecord(State):
    """
    States that come from the standardized lcls device states record
    """
    state = Component(EpicsSignal, "", write_pv=":GO", string=True,
                      auto_monitor=True, limits=False)

    def __init__(self, prefix, *, read_attrs=None, name=None, **kwargs):
        if read_attrs is None:
            read_attrs = ["state"]
        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)
        self._subbed_to_state = False

    def subscribe(self, *args, **kwargs):
        if not self._subbed_to_state:
            self.state.subscribe(self._update, event_type=self.state.SUB_VALUE)
            self._subbed_to_state = True
        super().subscribe(*args, **kwargs)

    @property
    def value(self):
        return self.state.get(use_monitor=True)

    @value.setter
    def value(self, value):
        self.state.put(value)


class DeviceStatesPart(Device):
    """
    Device to manipulate a specific set position.
    """
    at_state = Component(EpicsSignalRO, "", string=True) 
    setpos = Component(EpicsSignal, "_SET")
    delta = Component(EpicsSignal, "_DELTA")


def statesrecord_class(classname, *states, doc="", has_ioc=False):
    """
    Create a DeviceStatesRecord class for a particular device.
    """
    components = dict(states=states, __doc__=doc)
    for state_name in states:
        name = state_name.lower().replace(":", "") + "_state"
        components[name] = Component(DeviceStatesPart, state_name)
    if has_ioc:
        bases = (DeviceStatesRecord, IocDevice)
    else:
        bases = (DeviceStatesRecord,)
    return type(classname, bases, components)


inoutdoc = "Standard PCDS states record with an IN state and an OUT state."
InOutStates = statesrecord_class("InOutStates", ":IN", ":OUT", doc=inoutdoc)
InOutStatesIoc = statesrecord_class("InOutStatesIoc", ":IN", ":OUT",
                                    doc=inoutdoc, has_ioc=True)
inoutccmdoc = "Standard PCDS states record with IN, OUT, and CCM states."
InOutCCMStates = statesrecord_class("InOutCCMStates", ":IN", ":OUT", ":CCM",
                                    doc=inoutccmdoc)
InOutCCMStatesIoc = statesrecord_class("InOutCCMStatesIoc", ":IN", ":OUT",
                                       ":CCM", doc=inoutccmdoc, has_ioc=True)
