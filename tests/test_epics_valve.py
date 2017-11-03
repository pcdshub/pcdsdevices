############
# Standard #
############
import logging
import time as ttime
from unittest.mock import Mock

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.sim.pv import  using_fake_epics_pv
from pcdsdevices.epics import GateValve, PPSStopper, Stopper, InterlockError

from .conftest import attr_wait_true

logger = logging.getLogger(__name__)


def fake_pps():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    pps = PPSStopper("PPS:H0:SUM")
    pps.summary._read_pv.put("INCONSISTENT")
    return pps

def fake_stopper():
    return Stopper("STP:TST:")

def fake_valve():
    return GateValve("VGC:TST:")

@using_fake_epics_pv
def test_pps_states():
    pps = fake_pps()
    #Removed
    pps.summary._read_pv.put("OUT")
    assert pps.removed
    assert not pps.inserted
    #Inserted
    pps.summary._read_pv.put("IN")
    assert pps.inserted
    assert not pps.removed

@using_fake_epics_pv
def test_pps_subscriptions():
    pps = fake_pps()
    #Subscribe a pseudo callback
    cb = Mock()
    pps.subscribe(cb, event_type=pps.SUB_STATE, run=False)
    #Change readback state
    pps.summary._read_pv.put(4)
    attr_wait_true(cb, 'called')
    assert cb.called


@using_fake_epics_pv
def test_stopper_states():
    stopper = fake_stopper()
    #Removed
    stopper.limits.open_limit._read_pv.put(1)
    stopper.limits.closed_limit._read_pv.put(0)
    assert stopper.removed
    assert not stopper.inserted
    #Inserted
    stopper.limits.open_limit._read_pv.put(0)
    stopper.limits.closed_limit._read_pv.put(1)
    #Moving
    stopper.limits.open_limit._read_pv.put(0)
    stopper.limits.closed_limit._read_pv.put(0)
    assert not stopper.inserted
    assert not stopper.removed


@using_fake_epics_pv
def test_stopper_motion():
    stopper = fake_stopper()
    #Remove
    status = stopper.remove(wait=False)
    #Check write PV
    assert stopper.command.value == stopper.commands.open_valve.value
    #Force state to check status object
    stopper.limits.open_limit._read_pv.put(1)
    stopper.limits.closed_limit._read_pv.put(0)
    #Let state thread catch-up
    ttime.sleep(0.1)
    assert status.done and status.success
    #Close
    status = stopper.close(wait=False)
    #Check write PV
    assert stopper.command.value == stopper.commands.close_valve.value
    #Force state to check status object
    stopper.limits.open_limit._read_pv.put(0)
    stopper.limits.closed_limit._read_pv.put(1)
    #Let state thread catch-up
    ttime.sleep(0.1)
    assert status.done and status.success


@using_fake_epics_pv
def test_stopper_subscriptions():
    stopper = fake_stopper()
    #Subscribe a pseudo callback
    cb = Mock()
    stopper.subscribe(cb, event_type=stopper.SUB_STATE, run=False)
    #Change readback state
    stopper.limits.open_limit._read_pv.put(0)
    stopper.limits.closed_limit._read_pv.put(1)
    attr_wait_true(cb, 'called')
    assert cb.called

@using_fake_epics_pv
def test_valve_motion():
    valve = fake_valve()
    #Remove
    status = valve.remove(wait=False)
    #Check write PV
    assert valve.command.value == valve.commands.open_valve.value
    #Force state to check status object
    valve.limits.open_limit._read_pv.put(1)
    valve.limits.closed_limit._read_pv.put(0)
    assert status.done and status.success
    #Raises interlock
    valve.interlock._read_pv.put(1)
    assert valve.interlocked
    with pytest.raises(InterlockError):
        valve.open()

