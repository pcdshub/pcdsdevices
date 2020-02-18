import logging
import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.gasdet import Acqiris, AcqirisChannel, GasDet

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_acq():
    logger.debug('test_acqiris')
    FakeAcq = make_fake_device(Acqiris)
    acq = FakeAcq('TEST:ACQ', '000')
    acq.run_state.sim_set_enum_strs(['RUNNING', 'STOPPED'])
    acq.run_state.sim_put('RUNNING')
    assert acq.run_state.get() == 'RUNNING'
    acq.stop()
    assert acq.run_state.get() == 'STOPPED'
    acq.start()
    assert acq.run_state.get() == 'RUNNING'
    return acq


@pytest.mark.timout(5)
def test_acqiris_channel():
    logger.debug('test_acqiris_channel')
    FakeAcq = make_fake_device(AcqirisChannel)
    FakeAcq('TEST:ACQ', name='test')


@pytest.mark.timeout(5)
def test_gasdet():
    logger.debug('test_gasdet')
    FakeGasDet = make_fake_device(GasDet)
    FakeGasDet('TEST:GASDET', name='gasdet')


@pytest.mark.timeout(5)
def test_gasdet_disconnected():
    GasDet('TRO:LOL:LOL', name='tst')


@pytest.mark.timeout(5)
def test_acq_disconnected():
    Acqiris('ECS:RULEZ', '666', name='tst')
