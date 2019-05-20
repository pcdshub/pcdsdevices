import logging
import pytest
import pcdsdevices.utils as key_press

from ophyd.sim import make_fake_device
from pcdsdevices.analog_signals import AO, AI, Mesh

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ao():
    FakeAO = make_fake_device(AO)
    ao = FakeAO('Test:AO', name='test_ao')
    ao.ao1_0.sim_put(1.0)
    ao.ao1_1.sim_put(1.0)
    ao.ao1_2.sim_put(1.0)
    ao.ao1_3.sim_put(1.0)
    ao.ao1_4.sim_put(1.0)
    ao.ao1_5.sim_put(1.0)
    ao.ao1_6.sim_put(1.0)
    ao.ao1_7.sim_put(1.0)
    ao.ao1_8.sim_put(1.0)
    ao.ao1_9.sim_put(1.0)
    ao.ao1_10.sim_put(1.0)
    ao.ao1_11.sim_put(1.0)
    ao.ao1_12.sim_put(1.0)
    ao.ao1_13.sim_put(1.0)
    ao.ao1_14.sim_put(1.0)
    ao.ao1_15.sim_put(1.0)
    return ao


@pytest.fixture(scope='function')
def fake_ai():
    FakeAI = make_fake_device(AI)
    ai = FakeAI('Test:AI', name='test_ai')
    ai.ai1_0.sim_put(1.0)
    ai.ai1_1.sim_put(1.0)
    ai.ai1_2.sim_put(1.0)
    ai.ai1_3.sim_put(1.0)
    ai.ai1_4.sim_put(1.0)
    ai.ai1_5.sim_put(1.0)
    ai.ai1_6.sim_put(1.0)
    ai.ai1_7.sim_put(1.0)
    ai.ai1_8.sim_put(1.0)
    ai.ai1_9.sim_put(1.0)
    ai.ai1_10.sim_put(1.0)
    ai.ai1_11.sim_put(1.0)
    ai.ai1_12.sim_put(1.0)
    ai.ai1_13.sim_put(1.0)
    ai.ai1_14.sim_put(1.0)
    ai.ai1_15.sim_put(1.0)
    return ai


@pytest.fixture(scope='function')
def fake_mesh():
    FakeMesh = make_fake_device(Mesh)
    # Using SP channel = 1, RB channel = 2, scale = 1000
    mesh = FakeMesh('Test:Mesh', 1, 2, verbose=True)
    mesh.write_sig.sim_put(1.0)
    mesh.read_sig.sim_put(1.05)  # rb will be slightly off from sp
    return mesh


def test_ao_readback(fake_ao):
    assert fake_ao.ao1_0.get() == 1.0


def test_ai_readback(fake_ai):
    assert fake_ai.ai1_13.get() == 1.0


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
