#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from ophyd.signal import Signal

from pcdsdevices.epics import state

from conftest import requires_epics


class PrefixSignal(Signal):
    def __init__(self, prefix, **kwargs):
        super().__init__(**kwargs)


def test_pvstate_class():
    """
    Make sure all the internal logic works as expected. Use fake signals
    instead of EPICS signals with live hosts.
    """
    # Define the info and the class
    lim_info = dict(lowlim={"pvname": "LOW",
                            0: "in",
                            1: "defer"},
                    highlim={"pvname": "HIGH",
                             0: "out",
                             1: "defer"})
    LimCls = state.pvstate_class("LimCls", lim_info, signal_class=PrefixSignal)
    lim_obj = LimCls("BASE")

    # Check the state machine
    lim_obj.lowlim.put(1)
    lim_obj.highlim.put(1)
    assert(lim_obj.value == "unknown")
    lim_obj.highlim.put(0)
    assert(lim_obj.value == "out")
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    assert(lim_obj.value == "in")
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
    lim_obj2 = LimCls2("BASE")
    lim_obj2.value = "asdfe"
    assert(lim_obj2.value == "unknown")
    lim_obj2.value = "out"
    assert(lim_obj2.value == "out")
    lim_obj2.value = "in"
    assert(lim_obj2.value == "in")


def test_statesrecord_class():
    """
    Nothing special can be done without live hosts, just make sure we can
    create a class.
    """
    state.statesrecord_class("Classname", "state0", "state1", "state2")


@requires_epics
@pytest.mark.timeout(3)
def test_statesrecord_class_reads():
    """
    Instantiate one if we can and make sure value makes sense.
    """
    inout = state.InOutStates("XCS:SB2:IPM6:DIODE")
    assert(inout.value in ("IN", "OUT", "Unknown"))
