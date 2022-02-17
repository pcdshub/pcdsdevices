import logging

import pytest
from ophyd.sim import make_fake_device

from ..device_types import MPODApalisModule4Channel
from ..mpod_apalis import MPODApalisChannel, MPODApalisCrate

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_mpod_channel1():
    FakeMPODChannel = make_fake_device(MPODApalisChannel)
    C1 = FakeMPODChannel('TEST:MPOD:CHANNEL1', name='TestC1')
    # switch off
    C1.state.sim_put(0)
    C1.voltage.sim_put(50)
    C1.current.sim_put(0.02)
    C1.max_voltage.sim_put(100)
    C1.max_current.sim_put(0.1)
    return C1


@pytest.fixture(scope='function')
def fake_mpod_channel2():
    FakeMPODChannel = make_fake_device(MPODApalisChannel)
    C2 = FakeMPODChannel('TEST:MPOD:CHANNEL2', name='TestC2')
    # switch off
    C2.state.sim_put(0)
    C2.voltage.sim_put(90)
    C2.current.sim_put(0.01)
    C2.max_voltage.sim_put(100)
    C2.max_current.sim_put(0.1)
    return C2


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


def test_set_voltage(fake_mpod_channel1, fake_mpod_channel2):
    logger.debug('Testing MPOD Channel Setting Voltage')
    assert fake_mpod_channel1.voltage.get() == 50
    fake_mpod_channel1.set_voltage(0)
    assert fake_mpod_channel1.voltage.get() == 0
    assert fake_mpod_channel2.voltage.get() == 90
    fake_mpod_channel2.set_voltage(140)
    assert fake_mpod_channel2.voltage.get() == 100


def test_set_current(fake_mpod_channel1, fake_mpod_channel2):
    logger.debug('Testing MPOD Channel Setting Current')
    assert fake_mpod_channel2.current.get() == 0.01
    fake_mpod_channel2.set_current(0.04)
    assert fake_mpod_channel2.current.get() == 0.04
    assert fake_mpod_channel1.current.get() == 0.02
    fake_mpod_channel1.set_current(0.4)
    assert fake_mpod_channel1.current.get() == 0.1


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
