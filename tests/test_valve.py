import logging
from unittest.mock import Mock

import pytest
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.valve import GateValve, PPSStopper, Stopper, InterlockError

from .conftest import attr_wait_true, attr_wait_false

logger = logging.getLogger(__name__)


def fake_pps():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    pps = PPSStopper("PPS:H0:SUM", name="test_pps")
    pps.state._read_pv.put("INCONSISTENT")
    pps.wait_for_connection()
    return pps


def fake_stopper():
    stp = Stopper("STP:TST:", name="test_stopper")
    return stp


def fake_valve():
    vlv = GateValve("VGC:TST:", name="test_valve")
    vlv.interlock._read_pv.put(0)
    return vlv


@using_fake_epics_pv
def test_pps_states():
    pps = fake_pps()
    # Removed
    pps.state._read_pv.put("OUT")
    attr_wait_true(pps, 'removed')
    assert pps.removed
    assert not pps.inserted
    # Inserted
    pps.state._read_pv.put("IN")
    attr_wait_true(pps, 'inserted')
    assert pps.inserted
    assert not pps.removed


@using_fake_epics_pv
def test_pps_subscriptions():
    pps = fake_pps()
    # Subscribe a pseudo callback
    cb = Mock()
    pps.subscribe(cb, event_type=pps.SUB_STATE, run=False)
    # Change readback state
    pps.state._read_pv.put(4)
    attr_wait_true(cb, 'called')
    assert cb.called


@using_fake_epics_pv
def test_stopper_states():
    stopper = fake_stopper()
    # Removed
    stopper.open_limit._read_pv.put(1)
    stopper.closed_limit._read_pv.put(0)
    attr_wait_true(stopper, 'removed')
    assert stopper.removed
    assert not stopper.inserted
    # Inserted
    stopper.open_limit._read_pv.put(0)
    stopper.closed_limit._read_pv.put(1)
    # Moving
    stopper.open_limit._read_pv.put(0)
    stopper.closed_limit._read_pv.put(0)
    attr_wait_false(stopper, 'inserted')
    assert not stopper.inserted
    assert not stopper.removed


@using_fake_epics_pv
def test_stopper_motion():
    stopper = fake_stopper()
    # Check the status object
    status = stopper.close(wait=False)
    stopper.open_limit._read_pv.put(0)
    stopper.closed_limit._read_pv.put(1)
    status_wait(status, timeout=1)
    assert status.done and status.success
    # Remove
    stopper.open(wait=False)
    # Check write PV
    assert stopper.command.value == stopper.commands.open_valve.value


@using_fake_epics_pv
def test_stopper_subscriptions():
    stopper = fake_stopper()
    # Subscribe a pseudo callback
    cb = Mock()
    stopper.subscribe(cb, event_type=stopper.SUB_STATE, run=False)
    # Change readback state
    stopper.open_limit._read_pv.put(0)
    stopper.closed_limit._read_pv.put(1)
    attr_wait_true(cb, 'called')
    assert cb.called


@using_fake_epics_pv
def test_valve_motion():
    valve = fake_valve()
    # Remove
    valve.open(wait=False)
    # Check write PV
    assert valve.command.value == valve.commands.open_valve.value
    # Raises interlock
    valve.interlock._read_pv.put(1)
    assert valve.interlocked
    with pytest.raises(InterlockError):
        valve.open()
