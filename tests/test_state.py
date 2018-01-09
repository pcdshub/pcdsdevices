#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import time as ttime
from ophyd.signal import Signal

from pcdsdevices import state
from pcdsdevices.state import StateStatus


class PrefixSignal(Signal):
    def __init__(self, prefix, **kwargs):
        super().__init__(**kwargs)

@pytest.fixture(scope='function')
def lim_info():
    return dict(lowlim={"pvname": "LOW",
                         0: "in",
                         1: "defer"},
                highlim={"pvname": "HIGH",
                         0: "out",
                         1: "defer"})

def test_pvstate_class(lim_info):
    """
    Make sure all the internal logic works as expected. Use fake signals
    instead of EPICS signals with live hosts.
    """
    # Define the class
    LimCls = state.pvstate_class("LimCls", lim_info, signal_class=PrefixSignal)
    lim_obj = LimCls("BASE", name="test")

    # Check the state machine
    #Limits are defered
    lim_obj.lowlim.put(1)
    lim_obj.highlim.put(1)
    assert(lim_obj.value == "unknown")
    #Limits are out
    lim_obj.highlim.put(0)
    assert(lim_obj.value == "out")
    #Limits are in
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    assert(lim_obj.value == "in")
    #Limits are in conflicting state
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(0)
    assert(lim_obj.value == "unknown")

    assert("lowlim" in lim_obj.states)
    assert("highlim" in lim_obj.states)

    # Now let's check the setter and doc kwargs
    def limsetter(self, value):
        if value == "in":
            self.highlim.put(1)
            self.lowlim.put(0)
        elif value == "out":
            self.highlim.put(0)
            self.lowlim.put(1)
        else:
            self.highlim.put(1)
            self.lowlim.put(1)

    LimCls2 = state.pvstate_class("LimCls2", lim_info, setter=limsetter,
                                  signal_class=PrefixSignal, doc="testnocrash")
    lim_obj2 = LimCls2("BASE", name="test")
    lim_obj2.value = "asdfe"
    assert(lim_obj2.value == "unknown")
    lim_obj2.value = "out"
    assert(lim_obj2.value == "out")
    lim_obj2.value = "in"
    assert(lim_obj2.value == "in")


def test_state_status(lim_info):
    # Define the class
    LimCls = state.pvstate_class("LimCls", lim_info, signal_class=PrefixSignal)
    lim_obj = LimCls("BASE", name="test")
    #Create a status for 'in'
    status = StateStatus(lim_obj, 'in')
    #Put readback to 'in'
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    assert status.done and status.success
    #Check our callback was cleared
    assert status.check_value not in lim_obj._callbacks[lim_obj.SUB_STATE]


def test_statesrecord_class():
    """
    Nothing special can be done without live hosts, just make sure we can
    create a class.
    """
    state.statesrecord_class("Classname", "state0", "state1", "state2")


