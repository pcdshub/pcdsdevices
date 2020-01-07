import logging
import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.dc_devices import ICT

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ICT():
    FakeICT = make_fake_device(ICT)
    PDU = FakeICT('TST:PDU:ICT', name='test')
    PDU.ch1A.ch_status.sim_set_enum_strs(['ENABLED', 'DISABLED'])
    PDU.ch1A.ch_status.sim_put('ENABLED')
    return PDU


def test_PDU_status(fake_ICT):
    logger.debug('test_ICT')
    PDU = fake_ICT
    assert PDU.ch1A.ch_status.get() == 'ENABLED'
    PDU.ch1A.off()
    assert PDU.ch1A.ch_status.get() == 'DISABLED'
    PDU.ch1A.on()
    assert PDU.ch1A.ch_status.get() == 'ENABLED'
