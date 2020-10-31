import logging

import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.device_types import MPODChannelHV, MPODChannelLV

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_mpod_channel():
    FakeMPODChannel = make_fake_device(MPODChannelLV)
    mpod_channel = FakeMPODChannel('TEST:MPOD:CHANNEL', name='test')
    # switch Off
    mpod_channel.state.sim_put(0)
    mpod_channel.voltage.sim_put(20)
    return mpod_channel


@pytest.fixture(scope='function')
def fake_mpod_channel_high_voltage():
    FakeMPODChannel = make_fake_device(MPODChannelHV)
    mpod_channel_hv = FakeMPODChannel('TEST:MPOD:CHANNEL:HV', name='test')
    # switch Off
    mpod_channel_hv.voltage_rise_rate.sim_put(100)
    mpod_channel_hv.voltage_fall_rate.sim_put(100)
    return mpod_channel_hv


def test_switch_on_off(fake_mpod_channel):
    logger.debug('Testing MPOD Channel Switching On/Off')
    assert fake_mpod_channel.state.get() == 0
    fake_mpod_channel.on()
    assert fake_mpod_channel.state.get() == 1
    fake_mpod_channel.off()
    assert fake_mpod_channel.state.get() == 0


def test_set_voltage(fake_mpod_channel):
    logger.debug('Testing MPOD Channel Setting Voltage')
    assert fake_mpod_channel.voltage.get() == 20
    fake_mpod_channel.set_voltage(0)
    assert fake_mpod_channel.voltage.get() == 0
    fake_mpod_channel.set_voltage(23)
    assert fake_mpod_channel.voltage.get() == 23


def test_rise_fall_rate(fake_mpod_channel_high_voltage):
    logger.debug('Testing MPOD Channel Setting Voltage')
    assert fake_mpod_channel_high_voltage.voltage_fall_rate.get() == 100
    assert fake_mpod_channel_high_voltage.voltage_rise_rate.get() == 100


@pytest.mark.timeout(5)
def test_mpod_hv_channel_disconnected():
    MPODChannelHV('tst', name='tst')


@pytest.mark.timeout(5)
def test_mpod_lv_channel_disconnected():
    MPODChannelLV('tst', name='tst')
