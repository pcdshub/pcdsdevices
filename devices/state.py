#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define records that act as state getter/setters for more complicated
devices.
"""
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

    STATE_CHANGED : string
        Subscriptions to STATE_CHANGED will be called if the value attribute
        changes.
    """
    STATE_CHANGED = "state_changed"
    _default_sub = STATE_CHANGED

    @property
    def value(self):
        raise NotImplementedError()

    @property
    def states(self):
        raise NotImplementedError()


class StatesPVsBase(State):
    """
    States that come from some arbitrary set of pvs
    """
    pass  # TODO everything


class StatesIOCBase(State):
    """
    States that come from the standardized lcls position states record
    """
    position_state = Component(EpicsSignal, "", ":GO")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.position_state.subscribe(self._update)  # TODO check params

    @property
    def value(self):
        return self.position_state.get(as_string=True, use_monitor=True)

    @property
    def states(self):
        pass  # TODO get these from something we set up in statesioc_class

    def _update(self):
        self._run_subs  # TODO check params


class StatesIOCPart(Device):
    at_state = Component(EpicsSignalRO, "")
    setpos = Component(EpicsSignal, "_SET")
    delta = Component(EpicsSignal, "_DELTA")


def statesioc_class(classname, *states):
    """
    Create a StatesIOC class for a particular device.
    """
    components = {}
    for state_name in states:
        components[state_name.lower()] = Component(StatesIOCPart, state_name)
    return type(classname, (StatesIOCBase,), components)


InOutStates = statesioc_class("InOutStates", "IN", "OUT")
