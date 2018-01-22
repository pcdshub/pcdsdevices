import logging

from unittest.mock import Mock
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.attenuator import Attenuator, FeeAtt, MAX_FILTERS

from .conftest import attr_wait_true, connect_rw_pvs

logger = logging.getLogger(__name__)


def fake_att():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    att = Attenuator("TST:ATT", MAX_FILTERS, name='test_att')
    att.wait_for_connection()
    att.readback._read_pv.put(1)
    for filt in att.filters:
        connect_rw_pvs(filt.state)
        filt.state.put('OUT')
    return att


@using_fake_epics_pv
def test_make_feeatt():
    logger.debug('test_make_feeatt')
    FeeAtt()


@using_fake_epics_pv
def test_attenuator_states():
    logger.debug('test_attenuator_states')
    att = fake_att()
    # Insert filters
    for filt in att.filters:
        filt.state.put('IN')
    assert not att.removed
    assert att.inserted
    # Remove filter
    for filt in att.filters:
        filt.state.put('OUT')
    assert att.removed
    assert not att.inserted


def fake_move_transition(att, status, dest, unk_trans=True):
    """
    Set to the PVs sort of like it would happen in the real world and check the
    status
    """
    assert not status.done
    if unk_trans:
        for filt in att.filters:
            filt.state._read_pv.put(filt._unknown)
    for filt in att.filters:
        filt.state.put(dest)
    status_wait(status)
    assert status.done
    assert status.success


@using_fake_epics_pv
def test_attenuator_motion():
    logger.debug('test_attenuator_motion')
    att = fake_att()
    # Set up the ceil and floor
    att.trans_ceil._read_pv.put(0.8001)
    att.trans_floor._read_pv.put(0.5001)
    # Move to ceil
    status = att.move(0.8)
    fake_move_transition(att, status, 'IN')
    assert att.setpoint.value == 0.8
    assert att.actuate_value == 2
    # Move to floor
    status = att.move(0.5)
    fake_move_transition(att, status, 'IN')
    assert att.setpoint.value == 0.5
    assert att.actuate_value == 3
    # Call remove method
    status = att.remove()
    fake_move_transition(att, status, 'OUT')
    assert att.setpoint.value == 1
    # Call insert method
    status = att.insert()
    fake_move_transition(att, status, 'IN')
    assert att.setpoint.value == 0
    # Call insert again, but don't set anything to unknown
    status = att.insert()
    fake_move_transition(att, status, 'IN', unk_trans=False)


@using_fake_epics_pv
def test_attenuator_subscriptions():
    logger.debug('test_attenuator_subscriptions')
    att = fake_att()
    cb = Mock()
    att.subscribe(cb, run=False)
    att.readback._read_pv.put(0.5)
    attr_wait_true(cb, 'called')
    assert cb.called
