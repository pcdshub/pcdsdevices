############
# Standard #
############
import logging
import time as ttime
###############
# Third Party #
###############
import pytest
from unittest.mock import Mock

##########
# Module #
##########
from .conftest import using_fake_epics_pv
from pcdsdevices.epics import GateValve, PPSStopper, Stopper, InterlockError

logger = logging.getLogger(__name__)


@using_fake_epics_pv
@pytest.fixture(scope='function')
def pps():
    return PPSStopper("PPS:H0:SUM")

@using_fake_epics_pv
@pytest.fixture(scope='function')
def stopper():
    return Stopper("STP:TST:")

@using_fake_epics_pv
@pytest.fixture(scope='function')
def valve():
    return GateValve("VGC:TST:")

@using_fake_epics_pv
def test_pps_states(pps):
    #Removed
    pps.summary.signal._read_pv.put(0)
    assert pps.removed
    assert not pps.inserted
    #Inserted
    pps.summary.signal._read_pv.put(4)
    assert pps.inserted
    assert not pps.removed

    #Can not remove the PPS Stopper
    with pytest.raises(PermissionError):
        pps.remove()

@using_fake_epics_pv
def test_pps_subscriptions(pps):
    #Subscribe a pseudo callback
    cb = Mock()
    pps.subscribe(cb, run=False)
    #Change readback state
    pps.summary.signal._read_pv.put(4)
    assert cb.called


@using_fake_epics_pv
def test_stopper_states(stopper):
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
def test_stopper_motion(stopper):
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
def test_stopper_subscriptions(stopper):
    #Subscribe a pseudo callback
    cb = Mock()
    stopper.subscribe(cb, run=False)
    #Change readback state
    stopper.limits.open_limit._read_pv.put(0)
    stopper.limits.closed_limit._read_pv.put(1)
    assert cb.called

@using_fake_epics_pv
def test_valve_motion(valve):
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

