import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..timetool import Timetool, TimetoolWithNav

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function', params=[Timetool, TimetoolWithNav])
def fake_timetool(request):
    FakeTT = make_fake_device(request.param)
    tt = FakeTT('TST:TT', name='test_tt', prefix_det='click')
    tt.state.sim_set_enum_strs(('Unknown', 'OUT', 'LENS1', 'LENS2', 'LENS3'))
    tt.state.sim_put(1)
    return tt


def test_timetool_states(fake_timetool):
    logger.debug('test_timetool_states')
    timetool = fake_timetool
    # Remove
    timetool.state.put(1)
    assert timetool.removed
    assert not timetool.inserted
    # Insert
    timetool.state.put(2)
    assert not timetool.removed
    assert timetool.inserted
    # Unknown
    timetool.state.put(0)
    assert not timetool.removed
    assert not timetool.inserted


def test_timetool_motion(fake_timetool):
    logger.debug('test_timetool_motion')
    timetool = fake_timetool
    timetool.insert()
    assert timetool.state.get() == 2
    timetool.remove()
    assert timetool.state.get() == 1


def test_timetool_subscriptions(fake_timetool):
    logger.debug('test_timetool_subscriptions')
    timetool = fake_timetool
    # Subscribe a pseudo callback
    cb = Mock()
    timetool.subscribe(cb, event_type=timetool.SUB_STATE, run=False)
    # Change readback state
    timetool.state.put(1)
    assert cb.called


@pytest.mark.timeout(5)
def test_timetool_disconnected():
    logger.debug('test_timetool_disconnected')
    Timetool('TST', name='test', prefix_det='click')
    TimetoolWithNav('TST2', name='test2', prefix_det='click')
