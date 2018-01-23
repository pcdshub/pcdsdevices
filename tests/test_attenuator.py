import logging
import time
import threading
import pytest

from unittest.mock import Mock
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.attenuator import Attenuator, MAX_FILTERS

from .conftest import attr_wait_true, attr_wait_value, connect_rw_pvs

logger = logging.getLogger(__name__)


def fake_att():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    logger.debug('start making fake_att')
    att = Attenuator("TST:ATT", MAX_FILTERS-1, name='test_att')
    att.wait_for_connection()
    att.readback._read_pv.put(1)
    att.done._read_pv.put(0)
    att.calcpend._read_pv.put(0)
    for filt in att.filters:
        connect_rw_pvs(filt.state)
        filt.state.put('OUT')
    attr_wait_value(att.readback, 'value', 1)
    attr_wait_value(att.done, 'value', 0)
    attr_wait_value(att.calcpend, 'value', 0)
    logger.debug('done making fake_att')
    return att


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_attenuator_states():
    logger.debug('test_attenuator_states')
    att = fake_att()
    # Set no transmission
    att.readback._read_pv.put(0)
    attr_wait_value(att, 'position', 0)
    assert not att.removed
    assert att.inserted
    # Set full transmission
    att.readback._read_pv.put(1)
    attr_wait_value(att, 'position', 1)
    assert att.removed
    assert not att.inserted


def fake_move_transition(att, status, goal):
    """
    Set to the PVs sort of like it would happen in the real world and check the
    status
    """
    # Sanity check
    assert not status.done
    # Set status to "MOVING"
    att.done._read_pv.put(1)
    attr_wait_true(att, '_moving')  # This transition is important
    # Set transmission to the goal
    att.readback._read_pv.put(goal)
    # Set status to "OK"
    att.done._read_pv.put(0)
    # Check that the object responded properly
    status_wait(status, timeout=1)
    assert status.done
    assert status.success


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_attenuator_motion():
    logger.debug('test_attenuator_motion')
    att = fake_att()
    # Set up the ceil and floor
    att.trans_ceil._read_pv.put(0.8001)
    att.trans_floor._read_pv.put(0.5001)
    # Move to ceil
    status = att.move(0.8, wait=False)
    fake_move_transition(att, status, 0.8001)
    assert att.setpoint.value == 0.8
    assert att.actuate_value == 2
    # Move to floor
    status = att.move(0.5, wait=False)
    fake_move_transition(att, status, 0.5001)
    assert att.setpoint.value == 0.5
    assert att.actuate_value == 3
    # Call remove method
    status = att.remove(wait=False)
    fake_move_transition(att, status, 1)
    assert att.setpoint.value == 1
    # Call insert method
    status = att.insert(wait=False)
    fake_move_transition(att, status, 0)
    assert att.setpoint.value == 0


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_attenuator_subscriptions():
    logger.debug('test_attenuator_subscriptions')
    att = fake_att()
    cb = Mock()
    att.subscribe(cb, run=False)
    att.readback._read_pv.put(0.5)
    attr_wait_true(cb, 'called')
    assert cb.called


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_attenuator_calcpend():
    logger.debug('test_attenuator_calcpend')
    att = fake_att()
    att.calcpend._read_pv.put(1)

    def wait_put(sig, val, delay):
        time.sleep(delay)
        sig._read_pv.put(val)
    t = threading.Thread(target=wait_put, args=(att.calcpend, 0, 0.4))
    t.start()
    start = time.time()
    # Waits for calcpend to be 0
    att.actuate_value
    assert 0.1 < time.time() - start < 1
