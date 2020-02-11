import logging
import pytest

from ophyd.sim import make_fake_device
from unittest.mock import Mock

from pcdsdevices.inout import InOutRecordPositioner
from pcdsdevices.ipm import (IPMMotion, IPM_IPIMB, IPM_Wave8, IPMTarget,
                             IPM, Wave8, IPIMB)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ipm():
    """
    Setup a fake ipm, given a real class
    """
    FakeIPM = make_fake_device(IPMMotion)
    ipm = FakeIPM("Test:My:IPM", name='test_ipm')
    ipm.diode.state.state.sim_put(0)
    ipm.diode.state.state.sim_set_enum_strs(['Unknown'] +
                                            InOutRecordPositioner.states_list)
    ipm.target.state.sim_put(0)
    ipm.target.state.sim_set_enum_strs(['Unknown'] + IPMTarget.states_list)
    return ipm


@pytest.fixture(scope='function', params=[IPM_IPIMB, IPM_Wave8])
def fake_ipm_with_box(request):
    """
    Test IPM_Wave8 and IPM_IPIMB
    """
    """
    Setup a fake ipm, given a real class
    """
    FakeIPM = make_fake_device(request.param)
    if request.param is IPM_IPIMB:
        ipm = FakeIPM("Test:My:IPM", name='test_ipm',
                      prefix_ipimb='test_ipimb')
    else:
        ipm = FakeIPM("Test:My:IPM", name='test_ipm',
                      prefix_wave8='test_wave8')
    ipm.diode.state.state.sim_put(0)
    ipm.diode.state.state.sim_set_enum_strs(['Unknown'] +
                                            InOutRecordPositioner.states_list)
    ipm.target.state.sim_put(0)
    ipm.target.state.sim_set_enum_strs(['Unknown'] + IPMTarget.states_list)
    return ipm


def test_ipm_states(fake_ipm):
    logger.debug('test_ipm_states')
    ipm = fake_ipm
    # Remove IPM Targets
    ipm.target.state.put(5)
    assert ipm.removed
    assert not ipm.inserted
    # Insert IPM Targets
    ipm.target.state.put(1)
    assert not ipm.removed
    assert ipm.inserted
    # Remove IPM Diode
    ipm.diode.remove()
    assert not ipm.diode.inserted
    assert ipm.diode.removed
    # Insert IPM Diode
    ipm.diode.insert()
    assert ipm.diode.inserted
    assert not ipm.diode.removed


def test_ipm_motion(fake_ipm):
    logger.debug('test_ipm_motion')
    ipm = fake_ipm
    # Remove IPM Targets
    ipm.target.remove(wait=True, timeout=1.0)
    assert ipm.target.state.get() == 5
    # Insert IPM Targets
    ipm.target.set(1)
    assert ipm.target.state.get() == 1
    # Insert IPM Diode
    ipm.diode.insert()
    assert ipm.diode.state.state.get() == 1
    # Remove IPM Diode
    ipm.diode.remove()
    assert ipm.diode.state.state.get() == 2


def test_ipm_subscriptions(fake_ipm):
    logger.debug('test_ipm_subscriptions')
    ipm = fake_ipm
    # Subscribe a pseudo callback
    cb = Mock()
    ipm.target.subscribe(cb, event_type=ipm.target.SUB_STATE, run=False)
    # Change the target state
    ipm.target.state.put(2)
    assert cb.called


def test_ipm_box_readback(fake_ipm_with_box):
    logger.debug('test_ipm_ipimb_readback')
    ipm = fake_ipm_with_box
    ipm.isum()
    ipm.xpos()
    ipm.ypos()
    ipm.channel()
    ipm.channels()
    ipm.transmission


def test_ipm_factory():
    logger.debug('test_ipm_factory')
    assert isinstance(IPM('IPM', name='ipm'), IPMMotion)
    assert isinstance(IPM('IPM2', name='ipm2', prefix_ipimb='ipimb',
                          prefix_ioc='ioc'), IPM_IPIMB)
    assert isinstance(IPM('IPM3', name='ipm3', prefix_wave8='wave8'),
                      IPM_Wave8)


@pytest.mark.timeout(5)
def test_ipm_disconnected():
    IPMMotion('IPM', name='ipm')
    IPM_IPIMB('IPM2', name='ipm2', prefix_ipimb='ipimb', prefix_ioc='ioc')
    IPM_Wave8('IPM3', name='ipm3', prefix_wave8='wave8')


def test_bare_boxes():
    logger.debug('test_bare_boxes')
    IPIMB('ipimb1', name='ipm1')
    IPIMB('ipimb2', name='ipm2', prefix_ioc='ioc')
    Wave8('wave81', name='ipm3')
    Wave8('wave82', name='ipm4', prefix_ioc='ioc')
