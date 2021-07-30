import logging

import pytest
from unittest.mock import patch
from ophyd.sim import make_fake_device
from pcdsdevices.device_types import MPODApalisModule4Channel, MPODApalisModule8Channel, MPODApalisModule16Channel, MPODApalisModule24Channel
from pcdsdevices.mpod import MPODApalisChannel, MPODApalisModule, MPODApalisCrate

logger = logging.getLogger(__name__)

@pytest.fixture(scope='function')
def fake_mpod_channel1():
    FakeMPODChannel = make_fake_device(MPODApalisChannel)
    C1 = FakeMPODChannel('TEST:MPOD:CHANNEL1', name='TestC1')
    C1 = C1.state.sim_put(0) #switch off
    C1.voltage.sim_put(50)
    C1.current.sim_put(1)
    C1.max_voltage.sim_put(100)
    C1.max_current.sim_put(0.1)
    return C1

def fake_mpod_channel2():
    FakeMPODChannel = make_fake_device(MPODApalisChannel)
    C2 = FakeMPODChannel('TEST:MPOD:CHANNEL2', name='TestC2')
    C2 = C2.state.sim_put(0) #switch off
    C2.voltage.sim_put(150)
    C2.current.sim_put(0.01)
    C2.max_voltage.sim_put(100)
    C2.max_current.sim_put(0.1)
    return C2

@pytest.fixture(scope='function')
def fake_mpod_module4Channel():
    FakeMPODmodule = make_fake_device(MPODApalisModule4Channel)
    mpod_module4 = FakeMPODmodule('TEST:MPOD:MOD:4', name = 'TestM4')
    

@pytest.fixture(scope='function')
def fake_mpod_module8Channel():
    FakeMPODmodule = make_fake_device(MPODApalisModule8Channel)
    mpod_module8 = FakeMPODmodule('TEST:MPOD:MOD:8', name = 'TestM8')

@pytest.fixture(scope='function')
def fake_mpod_module16Channel():
    FakeMPODmodule = make_fake_device(MPODApalisModule16Channel)
    mpod_module16 = FakeMPODmodule('TEST:MPOD:MOD:16', name = 'TestM16')

@pytest.fixture(scope='function')
def fake_mpod_module24Channel():
    FakeMPODmodule = make_fake_device(MPODApalisModule24Channel)
    mpod_module24 = FakeMPODmodule('TEST:MPOD:MOD:24', name = 'TestM24')

@pytest.fixture(scope='function')    
def fake_mpod_crate():
    FakeMPODCrate = make_fake_device(MPODApalisCrate)
    mpod = FakeMPODCrate('TEST:MPOD', name = 'test')
    #switch on
    mpod.power.sim_put(1)
    return mpod  


def test_switch_on_off(...):

def test_set_voltage(...):

def test_set_current(...)

def test_clear_faults(...):

def test_set_voltage_ramp_speed(...):

def test_set_current_ramp_speed(...):

def test_power_cycle(...):
