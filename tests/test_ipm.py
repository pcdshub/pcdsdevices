import logging
import pytest

from ophyd.sim import make_fake_device
from unittest.mock import Mock

from pcdsdevices.inout import InOutRecordPositioner
from pcdsdevices.ipm import (IPMMotion, IPM_IPIMB, IPM_Wave8, IPMTarget,
                             IPM, Wave8, IPIMB)

logger = logging.getLogger(__name__)


def fake_ipm(cls):
    """
    Setup a fake ipm, given a real class
    """
    FakeIPM = make_fake_device(cls)
    ipm = FakeIPM("Test:My:IPM", name='test_ipm')
    ipm.diode.state.state.sim_put(0)
    ipm.diode.state.state.sim_set_enum_strs(['Unknown'] +
                                            InOutRecordPositioner.states_list)
    ipm.target.state.sim_put(0)
    ipm.target.state.sim_set_enum_strs(['Unknown'] + IPMTarget.states_list)
    return ipm


@pytest.fixture(scope='function')
def fake_ipm_motion():
    """
    Test IPM_Motion
    """
    return fake_ipm(IPMMotion)


@pytest.fixture(scope='function', params=[IPM_Wave8, IPM_IPIMB])
def fake_ipm_with_box():
    """
    Test IPM_Wave8 and IPM_IPIMB
    """
    return fake_ipm(request.param)


def test_ipm_states(fake_ipm_motion):
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


def test_ipm_motion(fake_ipm_motion):
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


def test_ipm_subscriptions(fake_ipm_motion):
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
    assert isInstance(IPM('IPM', name='ipm'), IPMMotion)
    assert isInstance(IPM('IPM2', name='ipm2', prefix_ipimb='ipimb',
                          prefix_ioc='ioc'), IPM_IPIMB)
    assert isInstance(IPM('IPM3', name='ipm3', prefix_wave8='wave8'),
                      IPM_Wave8)


@pytest.mark.timeout(5)
def test_ipm_disconnected():
    IPMMotion('IPM', name='ipm')
    IPM_IPIMB('IPM2', name='ipm2', prefix_ipimb='ipimb', prefix_ioc='ioc')
    IPM_Wave8('IPM3', name='ipm3', prefix_wave8='wave8')


def test_bare_boxes():
    logger.debug('test_bare_boxes')
    IPIMB('IPM2', name='ipm2', prefix_ipimb='ipimb')
    Wave8('IPM3', name='ipm3', prefix_wave8='wave8', prefix_ioc='ioc')
