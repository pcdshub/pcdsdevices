import numpy as np
import pytest
from ophyd.sim import make_fake_device

from ..he_lodcm import SI111, SI220, HE_LODCMEnergy
from .test_epics_motor import motor_setup


@pytest.fixture(scope='function')
def fake_he_lodcmenergy():
    cls = make_fake_device(HE_LODCMEnergy)
    return cls('TST:LODCM', name='fake_lodcm_energy')


@pytest.fixture(scope='function')
def target_states():
    states = ['Unknown', 'OUT', 'TARGET1a', 'TARGET1b']
    return states


def test_real_positioners(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    assert energy.t1ty not in energy._real
    assert energy.t2ty1 not in energy._real
    assert energy.t2ty2 not in energy._real
    assert energy.t1ry in energy._real
    assert energy.t2ry in energy._real
    assert energy.t2tz in energy._real


def test_crystal_si111(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(5)
    energy.t2ty1.user_readback.sim_put(5)
    energy.t2ty2.user_readback.sim_put(5)
    assert energy.get_crystal() is SI111


def test_crystal_si220(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(-5)
    energy.t2ty1.user_readback.sim_put(-5)
    energy.t2ty2.user_readback.sim_put(-5)
    assert energy.get_crystal() is SI220


def test_crystal_mismatch_t1(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(5)
    energy.t2ty1.user_readback.sim_put(-5)
    energy.t2ty2.user_readback.sim_put(-5)
    with pytest.raises(RuntimeError):
        energy.get_crystal()


def test_crystal_invalid_t1(fake_he_lodcmenergy):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(20)
    energy.t2ty1.user_readback.sim_put(5)
    energy.t2ty2.user_readback.sim_put(5)
    with pytest.raises(RuntimeError):
        energy.get_crystal()


def test_forward_si111(fake_he_lodcmenergy, target_states):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(5)
    energy.t2ty1.user_readback.sim_put(5)
    energy.t2ty2.user_readback.sim_put(5)
    energy.beam_splitter.target._late_state_init(enum_strs=target_states)
    energy.beam_splitter.target.state.sim_put(2)
    energy.beam_splitter.target.config.state03.state_name.sim_put('TARGET1a')
    energy.beam_splitter.target.config.state03.setpoint.sim_put(33.105)
    result = energy.forward(10)
    assert np.isclose(result.t1ry, 11.391782080118041, rtol=1e-6)
    assert np.isclose(result.t2ry, 11.391782080118041, rtol=1e-6)
    assert np.isclose(result.t2tz, 1408.3672341113784, rtol=1e-6)


def test_forward_si220(fake_he_lodcmenergy, target_states):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(-5)
    energy.t2ty1.user_readback.sim_put(-5)
    energy.t2ty2.user_readback.sim_put(-5)
    energy.beam_splitter.target._late_state_init(enum_strs=target_states)
    energy.beam_splitter.target.state.sim_put(2)
    energy.beam_splitter.target.config.state03.state_name.sim_put('TARGET1a')
    energy.beam_splitter.target.config.state03.setpoint.sim_put(33.105)
    result = energy.forward(10)
    assert np.isclose(result.t1ry, 18.82430505389254, rtol=1e-6)
    assert np.isclose(result.t2ry, 18.82430505389254, rtol=1e-6)
    assert np.isclose(result.t2tz, 765.1788462217432, rtol=1e-6)


def test_inverse_si111(fake_he_lodcmenergy, target_states):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    motor_setup(energy.t1ry)
    energy.t1ty.user_readback.sim_put(5)
    energy.t2ty1.user_readback.sim_put(5)
    energy.t2ty2.user_readback.sim_put(5)
    energy.t1ry.user_readback.sim_put(10)
    energy.beam_splitter.target._late_state_init(enum_strs=target_states)
    energy.beam_splitter.target.state.sim_put(2)
    energy.beam_splitter.target.config.state03.state_name.sim_put('TARGET1a')
    energy.beam_splitter.target.config.state03.setpoint.sim_put(33.105)
    result = energy.inverse(energy.RealPosition(t1ry=10, t2ry=10, t2tz=0))
    assert np.isclose(result.energy, 11.374486057438158, rtol=1e-6)


def test_inverse_si220(fake_he_lodcmenergy, target_states):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    motor_setup(energy.t1ry)
    energy.t1ty.user_readback.sim_put(-5)
    energy.t2ty1.user_readback.sim_put(-5)
    energy.t2ty2.user_readback.sim_put(-5)
    energy.t1ry.user_readback.sim_put(10)
    energy.beam_splitter.target._late_state_init(enum_strs=target_states)
    energy.beam_splitter.target.state.sim_put(2)
    energy.beam_splitter.target.config.state03.state_name.sim_put('TARGET1a')
    energy.beam_splitter.target.config.state03.setpoint.sim_put(33.105)
    result = energy.inverse(energy.RealPosition(t1ry=10, t2ry=10, t2tz=0))
    assert np.isclose(result.energy, 18.581244771168045, rtol=1e-6)


def test_roundtrip(fake_he_lodcmenergy, target_states):
    energy = fake_he_lodcmenergy
    motor_setup(energy.t1ty)
    motor_setup(energy.t2ty1)
    motor_setup(energy.t2ty2)
    energy.t1ty.user_readback.sim_put(5)
    energy.t2ty1.user_readback.sim_put(5)
    energy.t2ty2.user_readback.sim_put(5)
    energy.beam_splitter.target._late_state_init(enum_strs=target_states)
    energy.beam_splitter.target.state.sim_put(2)
    energy.beam_splitter.target.config.state03.state_name.sim_put('TARGET1a')
    energy.beam_splitter.target.config.state03.setpoint.sim_put(33.105)
    target_energy = 10
    real_pos = energy.forward(target_energy)
    result = energy.inverse(real_pos)
    assert np.isclose(result.energy, target_energy)
