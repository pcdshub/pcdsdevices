import logging

import pytest
from ophyd.sim import make_fake_device
from ophyd.utils import LimitError

from ..device_types import MPODApalisModule4Channel
from ..mpod_apalis import MPODApalisCrate

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_mpod_channel1():
    FakeMPODmodule = make_fake_device(MPODApalisModule4Channel)
    module = FakeMPODmodule("TEST:MPOD", name="TestPos1Module")
    c1 = module.c1
    module.limit_pos.sim_put(110)
    module.limit_neg.sim_put(0)
    # switch off
    c1.state.sim_put(0)
    c1.voltage.sim_put(50)
    c1.current.sim_put(0.02)
    c1.max_voltage.sim_put(100)
    c1.max_current.sim_put(0.1)
    return c1


@pytest.fixture(scope='function')
def fake_mpod_channel2():
    FakeMPODmodule = make_fake_device(MPODApalisModule4Channel)
    module = FakeMPODmodule("TEST:MPOD", name="TestPos2Module")
    c2 = module.c2
    # switch off
    module.limit_pos.sim_put(120)
    module.limit_neg.sim_put(0)
    # switch off
    c2.state.sim_put(0)
    c2.voltage.sim_put(90)
    c2.current.sim_put(0.01)
    c2.max_voltage.sim_put(100)
    c2.max_current.sim_put(0.1)
    return c2


@pytest.fixture(scope='function')
def fake_mpod_channel_neg():
    FakeMPODmodule = make_fake_device(MPODApalisModule4Channel)
    module = FakeMPODmodule("TEST:MPOD", name="TestNegativeModule")
    cn = module.c0
    # switch off
    module.limit_pos.sim_put(130)
    module.limit_neg.sim_put(0)
    cn.state.sim_put(0)
    cn.voltage.sim_put(-90)
    cn.current.sim_put(0.01)
    cn.max_voltage.sim_put(-100)
    cn.max_current.sim_put(0.1)
    return cn


@pytest.fixture(scope='function')
def fake_mpod_module4Channel():
    FakeMPODmodule = make_fake_device(MPODApalisModule4Channel)
    mpod_module4 = FakeMPODmodule('TEST:MPOD:MOD:4', name='TestM4')
    mpod_module4.voltage_ramp_speed.sim_put(10)
    mpod_module4.current_ramp_speed.sim_put(10)
    mpod_module4.faults.sim_put(0)
    return mpod_module4


@pytest.fixture(scope='function')
def fake_mpod_crate():
    FakeMPODCrate = make_fake_device(MPODApalisCrate)
    mpod = FakeMPODCrate('TEST:MPOD', name='test')
    # switch on
    mpod.power.sim_put(1)
    return mpod


def test_switch_on_off(fake_mpod_channel1):
    logger.debug('Testing MPOD Channel On/Off state')
    assert fake_mpod_channel1.state.get() == '0'
    fake_mpod_channel1.on()
    assert fake_mpod_channel1.state.get() == '1'


def test_channel_limits(fake_mpod_channel1, fake_mpod_channel2, fake_mpod_channel_neg):
    logger.debug('Testing MPOD Channel control limits')
    assert fake_mpod_channel1.voltage.limits == (0, 110)
    assert fake_mpod_channel1.current.limits == (0, 0.1)
    with pytest.raises(LimitError):
        fake_mpod_channel1.voltage.put(-1)
    with pytest.raises(LimitError):
        fake_mpod_channel1.voltage.put(150)
    with pytest.raises(LimitError):
        fake_mpod_channel1.current.put(-1)
    with pytest.raises(LimitError):
        fake_mpod_channel1.current.put(2)

    assert fake_mpod_channel_neg.voltage.limits == (-130, 0)
    with pytest.raises(LimitError):
        fake_mpod_channel_neg.voltage.put(1)
    with pytest.raises(LimitError):
        fake_mpod_channel_neg.voltage.put(-150)


def test_set_voltage(fake_mpod_channel1, fake_mpod_channel2, fake_mpod_channel_neg):
    logger.debug('Testing MPOD Channel Setting Voltage')
    assert fake_mpod_channel1.voltage.get() == 50
    fake_mpod_channel1.set_voltage(0)
    assert fake_mpod_channel1.voltage.get() == 0
    assert fake_mpod_channel2.voltage.get() == 90
    fake_mpod_channel2.set_voltage(140)
    assert fake_mpod_channel2.voltage.get() == 120
    fake_mpod_channel2.set_voltage(-140)
    assert fake_mpod_channel1.voltage.get() == 0
    fake_mpod_channel_neg.set_voltage(-20)
    assert fake_mpod_channel_neg.voltage.get() == -20
    fake_mpod_channel_neg.set_voltage(20)
    assert fake_mpod_channel_neg.voltage.get() == 0
    fake_mpod_channel_neg.set_voltage(-2000000)
    assert fake_mpod_channel_neg.voltage.get() == -130


def test_limit_percents(fake_mpod_channel1):
    logger.debug("Test limits scaling")
    module = fake_mpod_channel1.biological_parent
    fake_mpod_channel1.max_voltage.sim_put(100)

    # starting with (0, 110)
    assert fake_mpod_channel1.voltage.limits == (0, 110)
    assert module.limit_percents == (0, 110)

    module.limit_pos.sim_put(0)
    module.limit_neg.sim_put(5)
    assert fake_mpod_channel1.voltage.limits == (-5, 0)
    assert module.limit_percents == (-5, 0)

    # small changes have no effect
    module.limit_neg.sim_put(5.1)
    assert fake_mpod_channel1.voltage.limits == (-5, 0)
    assert module.limit_percents == (-5, 0)

    # Ignoring the model warning numbers
    module.limit_pos.sim_put(50)
    module.limit_neg.sim_put(50)
    assert fake_mpod_channel1.voltage.limits == (-50, 50)
    assert module.limit_percents == (-50, 50)


def test_set_current(fake_mpod_channel1, fake_mpod_channel2):
    logger.debug('Testing MPOD Channel Setting Current')
    assert fake_mpod_channel2.current.get() == 0.01
    fake_mpod_channel2.set_current(0.04)
    assert fake_mpod_channel2.current.get() == 0.04
    assert fake_mpod_channel1.current.get() == 0.02
    fake_mpod_channel1.set_current(0.4)
    assert fake_mpod_channel1.current.get() == 0.1
    fake_mpod_channel1.set_current(-0.4)
    assert fake_mpod_channel1.current.get() == 0


def test_clear_faults(fake_mpod_module4Channel):
    logger.debug('Testing MPOD Module Clearing Faults')
    assert fake_mpod_module4Channel.faults.get() == '0'
    fake_mpod_module4Channel.clear_faults()
    assert fake_mpod_module4Channel.faults.get() == '1'


def test_set_voltage_ramp_speed(fake_mpod_module4Channel):
    logger.debug('Testing MPOD Module Setting Voltage Ramp speed')
    assert fake_mpod_module4Channel.voltage_ramp_speed.get() == 10
    fake_mpod_module4Channel.set_voltage_ramp_speed(30)
    assert fake_mpod_module4Channel.voltage_ramp_speed.get() == 30


def test_set_current_ramp_speed(fake_mpod_module4Channel):
    logger.debug('Testing MPOD Module Setting Current Ramp speed')
    assert fake_mpod_module4Channel.current_ramp_speed.get() == 10
    fake_mpod_module4Channel.set_current_ramp_speed(30)
    assert fake_mpod_module4Channel.current_ramp_speed.get() == 30


def test_power_cycle(fake_mpod_crate):
    logger.debug('Testing MPOD crate power cycling')
    power_values = []

    def accumulate_values(value, **kawrgs):
        power_values.append(value)

    fake_mpod_crate.power.subscribe(accumulate_values)
    fake_mpod_crate.power_cycle()
    assert power_values == [1, 0, 1]


@pytest.mark.timeout(5)
def test_mpod_module_disconnected():
    logger.debug('test_mpod_module_disconnected')
    MPODApalisModule4Channel('tst', name='tst')


@pytest.mark.timeout(5)
def test_mpod_crate_disconnected():
    logger.debug('test_mpod_crate_disconnected')
    MPODApalisCrate('tst', name='tst')
