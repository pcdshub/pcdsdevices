#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define the interface to the lcls positioner states record and to more
general device states defined by collections of PVs.
"""
from ophyd import Device, Component, EpicsSignal, EpicsSignalRO

class State(Device):
    """
    Base class for any sub-device that defines a state.
    """
    STATE_CHANGED = "state_changed"
    states = []

    def __init__(self, prefix, **kwargs):
        super().__init__(self, prefix, **kwargs)
        self.state.subscribe

class StatesIOC(State):
    state = Component(EpicsSignal, "", ":GO")

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
        components[state_name] = Component(StatesIOCPart, state_name)
    return type(classname, (StatesIOC,), components)

InOutStates = statesioc_class("InOutStates", "IN", "OUT")
