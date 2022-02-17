import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..valve import GateValve, InterlockError, PPSStopper, Stopper

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_pps():
    FakePPS = make_fake_device(PPSStopper)
    pps = FakePPS("PPS:H0:SUM", name="test_pps")
    pps.state.sim_set_enum_strs(['Unknown', 'IN', 'OUT'])
    pps.state.sim_put('OUT')
    return pps


@pytest.fixture(scope='function')
def fake_stopper():
    FakeStopper = make_fake_device(Stopper)
    stp = FakeStopper("STP:TST:", name="test_stopper")
    return stp


@pytest.fixture(scope='function')
def fake_valve():
    FakeValve = make_fake_device(GateValve)
    vlv = FakeValve("VGC:TST:", name="test_valve")
    vlv.interlock.sim_put(1)
    return vlv


def test_pps_states(fake_pps):
    pps = fake_pps
    # Removed
    pps.state.sim_put("OUT")
    assert pps.removed
    assert not pps.inserted
    # Inserted
    pps.state.sim_put("IN")
    assert pps.inserted
    assert not pps.removed


def test_pps_motion(fake_pps):
    pps = fake_pps
    with pytest.raises(PermissionError):
        pps.insert()
    pps.state.sim_put("IN")
    with pytest.raises(PermissionError):
        pps.remove()


def test_pps_subscriptions(fake_pps):
    pps = fake_pps
    # Subscribe a pseudo callback
    cb = Mock()
    pps.subscribe(cb, event_type=pps.SUB_STATE, run=False)
    # Change readback state
    pps.state.sim_put(4)
    assert cb.called


def test_stopper_states(fake_stopper):
    stopper = fake_stopper
    # Removed
    stopper.open_limit.sim_put(1)
    stopper.closed_limit.sim_put(0)
    assert stopper.removed
    assert not stopper.inserted
    # Inserted
    stopper.open_limit.sim_put(0)
    stopper.closed_limit.sim_put(1)
    # Moving
    stopper.open_limit.sim_put(0)
    stopper.closed_limit.sim_put(0)
    assert not stopper.inserted
    assert not stopper.removed


def test_stopper_motion(fake_stopper):
    stopper = fake_stopper
    # Check the status object
    status = stopper.close(wait=False)
    stopper.open_limit.sim_put(0)
    stopper.closed_limit.sim_put(1)
    status.wait(timeout=1)
    assert status.done and status.success
    # Remove
    stopper.open(wait=False)
    # Check write PV
    assert stopper.command.get() == stopper.commands.open_valve.value


def test_stopper_subscriptions(fake_stopper):
    stopper = fake_stopper
    # Subscribe a pseudo callback
    cb = Mock()
    stopper.subscribe(cb, event_type=stopper.SUB_STATE, run=False)
    # Change readback state
    stopper.open_limit.sim_put(0)
    stopper.closed_limit.sim_put(1)
    assert cb.called


def test_valve_motion(fake_valve):
    valve = fake_valve
    # Remove
    valve.open(wait=False)
    # Check write PV
    assert valve.command.get() == valve.commands.open_valve.value
    # Raises interlock
    valve.interlock.sim_put(0)
    assert valve.interlocked
    with pytest.raises(InterlockError):
        valve.open()


@pytest.mark.parametrize('cls', [GateValve, PPSStopper, Stopper])
@pytest.mark.timeout(5)
def test_valve_disconnected(cls):
    cls('TST', name='tst')
