import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.lens import XFLS

from conftest import HotfixFakeEpicsSignal

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_xfls():
    FakeXFLS = make_fake_device(XFLS)
    FakeXFLS.state.cls = HotfixFakeEpicsSignal
    xfls = FakeXFLS('TST:XFLS', name='lens')
    xfls.state.sim_put(4)
    xfls.state.sim_set_enum_strs(('Unknown', 'LENS1', 'LENS2', 'LENS3', 'OUT'))
    return xfls


def test_xfls_states(fake_xfls):
    logger.debug('test_xfls_states')
    xfls = fake_xfls
    # Remove
    xfls.state.put(4)
    assert xfls.removed
    assert not xfls.inserted
    # Insert
    xfls.state.put(3)
    assert not xfls.removed
    assert xfls.inserted
    # Unknown
    xfls.state.put(0)
    assert not xfls.removed
    assert not xfls.inserted


def test_xfls_motion(fake_xfls):
    logger.debug('test_xfls_motion')
    xfls = fake_xfls
    xfls.remove()
    assert xfls.state.get() == 4


def test_xfls_subscriptions(fake_xfls):
    xfls = fake_xfls
    # Subscribe a pseudo callback
    cb = Mock()
    xfls.subscribe(cb, event_type=xfls.SUB_STATE, run=False)
    # Change readback state
    xfls.state.put(4)
    assert cb.called
