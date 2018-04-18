import logging
from unittest.mock import Mock

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.inout import InOutRecordPositioner

from .conftest import attr_wait_true, connect_rw_pvs

logger = logging.getLogger(__name__)


def fake_inout():
    inout = InOutRecordPositioner('Test:Ref', name='test')
    connect_rw_pvs(inout.state)
    inout.state._write_pv.put('Unknown')
    inout.state._read_pv.enum_strs = ('Unknown', 'IN', 'OUT')
    inout.wait_for_connection()
    return inout


@using_fake_epics_pv
def test_inout_states():
    logger.debug('test_inout_states')
    inout = fake_inout()
    inout.state.put('IN')
    assert inout.inserted
    assert not inout.removed
    inout.state.put('OUT')
    assert not inout.inserted
    assert inout.removed


@using_fake_epics_pv
def test_inout_trans():
    logger.debug('test_inout_trans')
    inout = fake_inout()
    inout.state.put('IN')
    assert inout.transmission == 0
    inout.state.put('OUT')
    assert inout.transmission == 1


@using_fake_epics_pv
def test_inout_motion():
    logger.debug('test_inout_motion')
    inout = fake_inout()
    inout.remove()
    assert inout.position == 'OUT'
    # Remove twice for branch coverage
    inout.remove()
    assert inout.position == 'OUT'
    inout.insert()
    assert inout.position == 'IN'


@using_fake_epics_pv
def test_inout_subscriptions():
    logger.debug('test_inout_subscriptions')
    inout = fake_inout()
    # Subscribe a pseudo callback
    cb = Mock()
    inout.subscribe(cb, event_type=inout.SUB_STATE, run=False)
    # Change the target state
    inout.state.put('OUT')
    attr_wait_true(cb, 'called')
    assert cb.called
