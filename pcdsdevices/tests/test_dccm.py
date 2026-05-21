from math import isnan

import pytest
from ophyd.sim import make_fake_device

from ..dccm import DCCM, CrystalIndex
from .test_epics_motor import motor_setup


@pytest.fixture(scope='function')
def fake_dccm():
    cls = make_fake_device(DCCM)
    return cls('TST:SP1T0', hutch='TST2', acr_status_suffix='AO804', acr_status_pv_index='9', name='fake_dccm')


def test_acr_energy_params(fake_dccm):
    assert fake_dccm.energy_with_vernier.acr_energy.prefix == fake_dccm.hutch
    assert fake_dccm.energy_with_acr_status.acr_energy.acr_status_suffix == fake_dccm.acr_status_suffix
    assert fake_dccm.energy_with_acr_status.acr_energy.pv_index == fake_dccm.acr_status_pv_index


def test_limits(fake_dccm):
    assert fake_dccm.energy.high_limit_travel.get() == fake_dccm.energy.energy.high_limit
    assert fake_dccm.energy.low_limit_travel.get() == fake_dccm.energy.energy.low_limit


def test_crystal_switch(fake_dccm):
    assert fake_dccm.energy.crystal_index_name.get() == CrystalIndex.Si111.name
    assert fake_dccm.energy.crystal_index.get() == CrystalIndex.Si111
    motor_setup(fake_dccm.energy.th1)
    motor_setup(fake_dccm.energy.th2)
    fake_dccm.energy.switch_crystal_index.put(0)
    assert fake_dccm.energy.crystal_index_name.get() == CrystalIndex.Si333.name
    assert fake_dccm.energy.crystal_index.get() == CrystalIndex.Si333


def test_energy_update(fake_dccm):
    motor_setup(fake_dccm.energy.th1)
    fake_dccm.energy.th1.user_readback.sim_put(10)
    motor_setup(fake_dccm.energy.th2)
    assert not isnan(fake_dccm.energy.energy.readback.get())
    fake_dccm.energy.th1.user_readback.sim_put(8.746)
    assert not isnan(fake_dccm.energy.energy.readback.get())
    assert abs(fake_dccm.energy.energy.readback.get() - 13.0022) < 0.001
    assert abs(fake_dccm.energy.forward(13).th1 - 8.7475) < 0.0001
