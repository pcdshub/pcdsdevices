import logging
import pytest

from ophyd.sim import make_fake_device
from pcdsdevices.analog_signals import Acromag, Mesh

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
def fake_mesh():
    FakeMesh = make_fake_device(Mesh)
    # Using SP channel = 1, RB channel = 2, scale = 1000
    mesh = FakeMesh('Test:Mesh', 1, 2)
    mesh.write_cpt.sim_put(1.0)
    mesh.read_cpt.sim_put(1.05) # rb will be slightly off from sp
    return mesh


def test_acromag_readback(fake_acromag):
    assert fake_acromag.ao1_0.get() == 1.0
    assert fake_acromag.ai1_13.get() == 1.0


def test_get_raw_mesh_voltage(fake_mesh):
    assert fake_mesh.get_raw_mesh_voltage() == 1.05


def test_get_mesh_voltage(fake_mesh):
    assert fake_mesh.get_mesh_voltage() == 1050.0


def test_set_mesh_voltage(fake_mesh):
    fake_mesh.set_mesh_voltage(1500.0)
    assert fake_mesh.write_cpt.get() == 1.5


def test_set_rel_mesh_voltage(fake_mesh):
    fake_mesh.set_rel_mesh_voltage(500.0)
    assert fake_mesh.write_cpt.get() == 1.5
    fake_mesh.set_rel_mesh_voltage(-500.0)
    assert fake_mesh.write_cpt.get() == 1.0
