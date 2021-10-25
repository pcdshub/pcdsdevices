import logging

import pytest
from ophyd.sim import make_fake_device

from ..pump import IonPump, IonPumpBase, IonPumpWithController

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ionpump():
    FakeIonPump = make_fake_device(IonPumpBase)
    pump = FakeIonPump('Test:pump', name='test')
    pump.state.sim_set_enum_strs(['OFF', 'ON'])
    pump.state.sim_put(1)
    pump._pressure.sim_put(99.)
    return pump


def test_pump_pressure(fake_ionpump):
    logger.debug('test_ionpump')
    pump = fake_ionpump
    assert pump.state.get() == 'ON'
    pump.off()
    assert pump.state.get() == 'OFF'
    assert pump.pressure() == -1.
    pump.on()
    assert pump.state.get() == 'ON'
    assert pump.pressure() == 99.


def test_ionpump_factory():
    m = IonPump('TST:MY:PIP:01', name='test_pump', prefix_controller='gamma')
    assert isinstance(m, IonPumpWithController)
    m = IonPump('TST:MY:PIP:01', name='test_pump')
    assert isinstance(m, IonPumpBase)


@pytest.mark.timeout(5)
def test_ionpump_disconnected():
    IonPumpWithController('tst', name='tst', prefix_controller='gamma')
