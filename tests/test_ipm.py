import logging

import pytest
from ophyd.sim import make_fake_device
from unittest.mock import Mock

from pcdsdevices.inout import InOutRecordPositioner
from pcdsdevices.ipm import IPM, IPMTarget

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ipm():
    FakeIPM = make_fake_device(IPM)
    ipm = FakeIPM("Test:My:IPM", name='test_ipm')
    ipm.diode.state.sim_put(0)
    ipm.diode.state.sim_set_enum_strs(['Unknown'] +
                                      InOutRecordPositioner.states_list)
    ipm.target.state.sim_put(0)
    ipm.target.state.sim_set_enum_strs(['Unknown'] + IPMTarget.states_list)
    return ipm


def test_ipm_states(fake_ipm):
    logger.debug('test_ipm_states')
    ipm = fake_ipm
    ipm.target.state.put(5)
    assert ipm.removed
    assert not ipm.inserted
    ipm.target.state.put(1)
    assert not ipm.removed
    assert ipm.inserted


def test_ipm_motion(fake_ipm):
    logger.debug('test_ipm_motion')
    ipm = fake_ipm
    # Remove IPM Targets
    ipm.remove(wait=True, timeout=1.0)
    assert ipm.target.state.get() == 5
    # Insert IPM Targets
    ipm.target.set(1)
    assert ipm.target.state.get() == 1
    # Move diodes in
    ipm.diode.insert()
    assert ipm.diode.state.get() == 1
    ipm.diode.remove()
    # Move diodes out
    assert ipm.diode.state.get() == 2


def test_ipm_subscriptions(fake_ipm):
    logger.debug('test_ipm_subscriptions')
    ipm = fake_ipm
    # Subscribe a pseudo callback
    cb = Mock()
    ipm.target.subscribe(cb, event_type=ipm.target.SUB_STATE, run=False)
    # Change the target state
    ipm.target.state.put(2)
    assert cb.called


@pytest.mark.timeout(5)
def test_ipm_disconnected():
    IPM('IPM', name='ipm')
