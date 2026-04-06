import pytest
from ophyd.sim import make_fake_device

from ..he_lodcm import HE_LODCMEnergy
from .test_epics_motor import motor_setup


@pytest.fixture(scope='function')
def fake_he_lodcmenergy():
    cls = make_fake_device(HE_LODCMEnergy)
    return cls('TST:LODCM', name='fake_lodcm_energy')


def test_real_positioners(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    assert energy.t1ty not in energy._real
    assert energy.t1ry in energy._real


def test_crystal(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    energy.t1ty.user_readback.sim_put(0)
    assert energy.get_crystal() is None
    energy.t1ty.user_readback.sim_put(0.5)
    assert energy.get_crystal() is HE_LODCMEnergy.Crystal.Si111
    energy.t1ty.user_readback.sim_put(1)
    assert energy.get_crystal() is None
    energy.t1ty.user_readback.sim_put(1.5)
    assert energy.get_crystal() is HE_LODCMEnergy.Crystal.Si220
