import logging
import threading
import time
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import wait as status_wait
from pcdsdevices.attenuator import (MAX_FILTERS, AttBase, Attenuator,
                                    _att3_classes, _att_classes)

logger = logging.getLogger(__name__)


# Replace all the Attenuator classes with fake classes
for name, cls in _att_classes.items():
    _att_classes[name] = make_fake_device(cls)

for name, cls in _att3_classes.items():
    _att3_classes[name] = make_fake_device(cls)


@pytest.mark.timeout(5)
def test_attenuator_states(fake_att):
    logger.debug('test_attenuator_states')
    att = fake_att
    # Set no transmission
    att.readback.sim_put(0)
    assert not att.removed
    assert att.inserted
    # Set full transmission
    att.readback.sim_put(1)
    assert att.removed
    assert not att.inserted


def fake_move_transition(att, status, goal):
    """
    Set to the PVs sort of like it would happen in the real world and check the
    status
    """
    # Set status to "MOVING"
    att.done.sim_put(1)
    # Set transmission to the goal
    att.readback.sim_put(goal)
    # Set status to "OK"
    att.done.sim_put(0)
    # Check that the object responded properly
    status_wait(status, timeout=1)
    assert status.done
    assert status.success


@pytest.mark.timeout(5)
def test_attenuator_motion(fake_att):
    logger.debug('test_attenuator_motion')
    att = fake_att
    # Set up the ceil and floor
    att.trans_ceil.sim_put(0.8001)
    att.trans_floor.sim_put(0.5001)
    # Move to ceil
    status = att.move(0.8, wait=False)
    fake_move_transition(att, status, 0.8001)
    assert att.setpoint.value == 0.8
    assert att.actuate_value == 3
    # Move to floor
    status = att.move(0.5, wait=False)
    fake_move_transition(att, status, 0.5001)
    assert att.setpoint.value == 0.5
    assert att.actuate_value == 2
    # Call remove method
    status = att.remove(wait=False)
    fake_move_transition(att, status, 1)
    assert att.setpoint.value == 1
    # Call insert method
    status = att.insert(wait=False)
    fake_move_transition(att, status, 0)
    assert att.setpoint.value == 0


@pytest.mark.timeout(5)
def test_attenuator_subscriptions(fake_att):
    logger.debug('test_attenuator_subscriptions')
    att = fake_att
    cb = Mock()
    att.subscribe(cb, run=False)
    att.readback.sim_put(0.5)
    assert cb.called
    state_cb = Mock()
    att.subscribe(state_cb, event_type=att.SUB_STATE, run=False)
    att.readback.sim_put(0.6)
    assert not state_cb.called
    att.done.sim_put(1)
    att.done.sim_put(0)
    assert state_cb.called


@pytest.mark.timeout(5)
def test_attenuator_calcpend(fake_att):
    logger.debug('test_attenuator_calcpend')
    att = fake_att
    att.calcpend.sim_put(1)
    # Initialize to any value
    att.setpoint.sim_put(1)
    att.trans_ceil.sim_put(1)
    att.trans_floor.sim_put(1)

    def wait_put(sig, val, delay):
        time.sleep(delay)
        sig.sim_put(val)
    t = threading.Thread(target=wait_put, args=(att.calcpend, 0, 0.4))
    t.start()
    start = time.time()
    # Waits for calcpend to be 0
    att.actuate_value
    assert 0.1 < time.time() - start < 1
    att.calcpend.sim_put(1)
    # Gives up after one second
    start = time.time()
    att.actuate_value
    assert time.time() - start >= 1


@pytest.mark.timeout(5)
def test_attenuator_set_energy(fake_att):
    logger.debug('test_attenuator_set_energy')
    att = fake_att
    att.set_energy()
    assert att.eget_cmd.get() == 6
    energy = 1000
    att.set_energy(energy)
    assert att.eget_cmd.get() == 0
    assert att.user_energy.get() == energy


def test_attenuator_transmission(fake_att):
    logger.debug('test_attenuator_transmission')
    att = fake_att
    assert att.transmission == att.position


@pytest.mark.timeout(5)
def test_attenuator_staging(fake_att):
    logger.debug('test_attenuator_staging')
    att = fake_att
    # Set up at least one invalid state
    att.filter1.state.sim_put(att.filter1._unknown)
    att.stage()
    for filt in att.filters:
        filt.insert(wait=True)
    att.unstage()
    for filt in att.filters:
        assert filt.removed


def test_attenuator_third_harmonic():
    logger.debug('test_attenuator_third_harmonic')
    att = Attenuator('TRD:ATT', MAX_FILTERS-1, name='third', use_3rd=True)
    att.wait_for_connection()


@pytest.mark.timeout(5)
def test_attenuator_disconnected():
    AttBase('TST:ATT', name='test_att')
