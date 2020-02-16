import logging
import pytest
from unittest.mock import Mock
from ophyd.sim import make_fake_device
from pcdsdevices.gasdet import acqiris, acqiris_channel, gasdet

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_acq():
    FakeAcq = make_fake_device(acqiris)
    acq = FakeAcq('TEST:ACQ', '000')
    acq.stop()
    assert acq.run_state == 1
    acq.start()
    assert acq.run_state == 0
    return acq

@pytest.mark.timout(5)
def test_acqiris_channel():
    logger.debug('test_acqiris_channel')
    FakeAcq = make_fake_device(acqiris_channel)
    FakeAcq('TEST:ACQ', name='test')

@pytest.mark.timeout(5)
def test_gasdet():
    logger.debug('test_gasdet')
    FakeGasDet = make_fake_device(gasdet)
    FakeGasDet('TEST:GASDET', name='gasdet')

@pytest.mark.timeout(5)
def test_acq_subscription(fake_acq):
    logger.debug('test_acqiris_subscriptions')
    acq = fake_acq
    cb = Mock()
    acq.subscribe(cb, event_type=acq.SUB_STATE, run=False)
    acq.run_state.sim_put(0)
    assert cb.called

@pytest.mark.timeout(5)
def test_acq_disconnected():
    acqiris('ECS:RLZ', name='tst', '666')
