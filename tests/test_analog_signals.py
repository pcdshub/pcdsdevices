import logging

import pytest
from ophyd.sim import make_fake_device

import pcdsdevices.utils as key_press
from pcdsdevices.analog_signals import (Acromag, Mesh, AcromagChannelInput,
                                        AcromagChannelOutput)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_acromag():
    FakeAcromag = make_fake_device(Acromag)
    acromag = FakeAcromag('Test:Acromag', name='test_acromag')
    acromag.ao1_0.sim_put(1.0)
    acromag.ao1_1.sim_put(1.0)
    acromag.ao1_2.sim_put(1.0)
    acromag.ao1_3.sim_put(1.0)
    acromag.ao1_4.sim_put(1.0)
    acromag.ao1_5.sim_put(1.0)
    acromag.ao1_6.sim_put(1.0)
    acromag.ao1_7.sim_put(1.0)
    acromag.ao1_8.sim_put(1.0)
    acromag.ao1_9.sim_put(1.0)
    acromag.ao1_10.sim_put(1.0)
    acromag.ao1_11.sim_put(1.0)
    acromag.ao1_12.sim_put(1.0)
    acromag.ao1_13.sim_put(1.0)
    acromag.ao1_14.sim_put(1.0)
    acromag.ao1_15.sim_put(1.0)

    acromag.ai1_0.sim_put(1.0)
    acromag.ai1_1.sim_put(1.0)
    acromag.ai1_2.sim_put(1.0)
    acromag.ai1_3.sim_put(1.0)
    acromag.ai1_4.sim_put(1.0)
    acromag.ai1_5.sim_put(1.0)
    acromag.ai1_6.sim_put(1.0)
    acromag.ai1_7.sim_put(1.0)
    acromag.ai1_8.sim_put(1.0)
    acromag.ai1_9.sim_put(1.0)
    acromag.ai1_10.sim_put(1.0)
    acromag.ai1_11.sim_put(1.0)
    acromag.ai1_12.sim_put(1.0)
    acromag.ai1_13.sim_put(1.0)
    acromag.ai1_14.sim_put(1.0)
    acromag.ai1_15.sim_put(1.0)
    return acromag


@pytest.fixture(scope='function')
def fake_acromag_in():
    FakeAcromagInputCh = make_fake_device(AcromagChannelInput)
    acromag_in = FakeAcromagInputCh(prefix='Test:Acromag:In', channel='10',
                                    name='test_acromag_in')
    acromag_in.channel.sim_put(0.23)
    return acromag_in


@pytest.fixture(scope='function')
def fake_acromag_out():
    FakeAcromagOutputCh = make_fake_device(AcromagChannelOutput)
    acromag_out = FakeAcromagOutputCh(prefix='Test:Acromag:Out', channel='10',
                                      name='test_acromag_out')
    acromag_out.channel.sim_put(0.33)
    return acromag_out


@pytest.fixture(scope='function')
def fake_mesh():
    FakeMesh = make_fake_device(Mesh)
    # Using SP channel = 1, RB channel = 2, scale = 1000
    mesh = FakeMesh('Test:Mesh', 1, 2)
    mesh.write_sig.sim_put(1.0)
    mesh.read_sig.sim_put(1.05)  # rb will be slightly off from sp
    return mesh


def test_acromag_readback(fake_acromag):
    assert fake_acromag.ao1_0.get() == 1.0
    assert fake_acromag.ai1_13.get() == 1.0


def test_acromag_ch_readback(fake_acromag_in, fake_acromag_out):
    assert fake_acromag_in.channel.get() == 0.23
    assert fake_acromag_out.channel.get() == 0.33
    fake_acromag_out.channel.put(8)
    assert fake_acromag_out.channel.get() == 8


def test_get_raw_mesh_voltage(fake_mesh):
    assert fake_mesh.get_raw_mesh_voltage() == 1.05


def test_get_mesh_voltage(fake_mesh):
    assert fake_mesh.get_mesh_voltage() == 1050.0


def test_set_mesh_voltage(fake_mesh):
    fake_mesh.set_mesh_voltage(1500.0)
    assert fake_mesh.write_sig.get() == 1.5


def test_set_rel_mesh_voltage(fake_mesh):
    fake_mesh.set_rel_mesh_voltage(500.0)
    assert fake_mesh.write_sig.get() == 1.5
    fake_mesh.set_rel_mesh_voltage(-500.0)
    assert fake_mesh.write_sig.get() == 1.0


def test_tweak_mesh_voltage(fake_mesh, monkeypatch):
    # Create mock user inputs for tweak up/down
    def mock_tweak_up():
        return '\x1b[C'  # arrow right

    def mock_tweak_down():
        return '\x1b[D'  # arrow left

    monkeypatch.setattr(key_press, 'get_input', mock_tweak_up)
    fake_mesh.tweak_mesh_voltage(500.0, test_flag=True)
    assert fake_mesh.write_sig.get() == 1.5
    monkeypatch.setattr(key_press, 'get_input', mock_tweak_down)
    fake_mesh.tweak_mesh_voltage(500.0, test_flag=True)
    assert fake_mesh.write_sig.get() == 1.0


@pytest.mark.timeout(5)
def test_acromag_disconnected():
    Acromag('Test:Acromag', name='test_acromag')


@pytest.mark.timeout(5)
def test_mesh_disconnected():
    Mesh('Test:Mesh', 1, 2)


@pytest.mark.timeout(5)
def test_acromag_ch_in_disconnected():
    AcromagChannelInput(prefix='Test:Acromag:In', channel='10',
                        name='test_acromag_in')


@pytest.mark.timeout(5)
def test_acromag_ch_out_disconnected():
    AcromagChannelOutput(prefix='Test:Acromag:Out', channel='10',
                         name='test_acromag_out')
