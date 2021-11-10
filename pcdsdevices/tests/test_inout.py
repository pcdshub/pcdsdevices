import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..inout import (InOutPositioner, InOutPVStatePositioner,
                     InOutRecordPositioner, TwinCATInOutPositioner)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_inout():
    Fake = make_fake_device(InOutRecordPositioner)
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


def test_subcls_warning():
    logger.debug('test_subcls_warning')
    with pytest.raises(TypeError):
        InOutPositioner('prefix', name='name')
    with pytest.raises(TypeError):
        InOutPVStatePositioner('prefix', name='name')


@pytest.fixture(scope='function')
def fake_tcinout():
    FakeCls = make_fake_device(TwinCATInOutPositioner)
    device = FakeCls('FAKE:CLASS', name='faker')
    return device


def test_in_if_not_out(fake_tcinout):
    enums = ('Unknown', 'OUT', 'Fish')
    fake_tcinout.state._run_subs(sub_type=fake_tcinout.state.SUB_META,
                                 enum_strs=enums)
    fake_tcinout.state.sim_put(0)
    assert not fake_tcinout.inserted
    assert not fake_tcinout.removed
    fake_tcinout.state.sim_put(1)
    assert not fake_tcinout.inserted
    assert fake_tcinout.removed
    fake_tcinout.state.sim_put(2)
    assert fake_tcinout.inserted
    assert not fake_tcinout.removed
