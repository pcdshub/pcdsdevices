import logging

import pytest
from ophyd.sim import make_fake_device

from ..dc_devices import ICT

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ICT():
    FakeICT = make_fake_device(ICT)
    PDU = FakeICT('TST:PDU:ICT', name='test')
    PDU.ch_1A.ch_status.sim_set_enum_strs(['ENABLED', 'DISABLED'])
    PDU.ch_1A.ch_status.sim_put('ENABLED')
    return PDU


def test_PDU_status(fake_ICT):
    logger.debug('test_ICT')
    PDU = fake_ICT
    assert PDU.ch_1A.ch_status.get() == 'ENABLED'
    PDU.ch_1A.off()
    assert PDU.ch_1A.ch_status.get() == 'DISABLED'
    PDU.ch_1A.on()
    assert PDU.ch_1A.ch_status.get() == 'ENABLED'


@pytest.mark.timeout(5)
def test_disconnected_ict():
    ICT('TST:PDU:ICT', name='test')
