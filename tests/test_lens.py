import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.lens import XFLS, LensStack, SimLensStack

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


def test_LensStack_align(presets, monkeypatch):
    logger.debug('test_LensStack_align')

    def mocktweak(self):
        lens.x.move(lens.x.position+1)
        lens.y.move(lens.y.position+1)
    lens = SimLensStack(name='test',
                        x_prefix='x_motor',
                        y_prefix='y_motor',
                        z_prefix='z_motor')
    monkeypatch.setattr(LensStack, 'tweak', mocktweak)
    lens.align(0)
    assert lens.z.position == 0
    assert lens.x.position == 1.5
    assert lens.y.position == 1.5
