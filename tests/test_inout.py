import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.inout import InOutRecordPositioner

from .conftest import HotfixFakeEpicsSignal

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_inout():
    Fake = make_fake_device(InOutRecordPositioner)
    Fake.state.cls = HotfixFakeEpicsSignal
    inout = Fake('Test:Ref', name='test')
    inout.state.sim_put(0)
    inout.state.sim_set_enum_strs(('Unknown', 'IN', 'OUT'))
    return inout


def test_inout_states(fake_inout):
    logger.debug('test_inout_states')
    inout = fake_inout
    inout.state.put('IN')
    assert inout.inserted
    assert not inout.removed
    inout.state.put('OUT')
    assert not inout.inserted
    assert inout.removed


def test_inout_trans(fake_inout):
    logger.debug('test_inout_trans')
    inout = fake_inout
    inout.state.put('IN')
    assert inout.transmission == 0
    inout.state.put('OUT')
    assert inout.transmission == 1


def test_inout_motion(fake_inout):
    logger.debug('test_inout_motion')
    inout = fake_inout
    inout.remove()
    assert inout.position == 'OUT'
    # Remove twice for branch coverage
    inout.remove()
    assert inout.position == 'OUT'
    inout.insert()
    assert inout.position == 'IN'


def test_inout_subscriptions(fake_inout):
    logger.debug('test_inout_subscriptions')
    inout = fake_inout
    # Subscribe a pseudo callback
    cb = Mock()
    inout.subscribe(cb, event_type=inout.SUB_STATE, run=False)
    # Change the target state
    inout.state.put('OUT')
    assert cb.called
