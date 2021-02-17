import logging
from unittest.mock import Mock, patch

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.lodcm import (H1N, LODCM, Dectris, Diode, Foil, YagLom, Y1,
                               CHI1, Y2, CHI2, H2N, SimFirstTower,
                               SimSecondTower, LODCMEnergySi, LODCMEnergyC)

logger = logging.getLogger(__name__)


def motor_setup(mot, pos=0):
    mot.user_readback.sim_put(0)
    mot.user_setpoint.sim_put(0)
    mot.user_setpoint.sim_set_limits((0, 0))
    mot.motor_spg.sim_put(2)


@pytest.fixture(scope='function')
def fake_lodcm():
    FakeLODCM = make_fake_device(LODCM)

    # def get_material(self, check):
    #     return "C"
    # monkeypatch.setattr(LODCMEnergy, 'get_material', get_material)

    lodcm = FakeLODCM('FAKE:LOM', name='fake_lom')
    lodcm.h1n_state.state.sim_put(1)
    lodcm.h1n_state.state.sim_set_enum_strs(['Unknown'] + H1N.states_list)
    lodcm.yag.state.sim_put(1)
    lodcm.yag.state.sim_set_enum_strs(['Unknown'] + YagLom.states_list)
    lodcm.dectris.state.sim_put(1)
    lodcm.dectris.state.sim_set_enum_strs(['Unknown'] + Dectris.states_list)
    lodcm.diode.state.sim_put(1)
    lodcm.diode.state.sim_set_enum_strs(['Unknown'] + Diode.states_list)
    lodcm.foil.state.sim_put(1)
    lodcm.foil.state.sim_set_enum_strs(['Unknown'] + Foil.states_list)
    lodcm.h1n_state.state.sim_put(1)

    # additional states for Crystal Tower 1
    lodcm.y1_state.state.sim_put(1)
    lodcm.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    lodcm.chi1_state.state.sim_put(1)
    lodcm.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)

    # additional states for Crystal Tower 2
    lodcm.y2_state.state.sim_put(1)
    lodcm.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    lodcm.chi2_state.state.sim_put(1)
    lodcm.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    lodcm.h2n_state.state.sim_put(1)
    lodcm.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)

    lodcm.tower1.diamond_reflection.sim_put((1, 1, 1))
    lodcm.tower1.silicon_reflection.sim_put((1, 1, 1))
    lodcm.tower2.diamond_reflection.sim_put((1, 1, 1))
    lodcm.tower2.silicon_reflection.sim_put((1, 1, 1))

    motor_setup(lodcm.energy_si.th1.motor)
    motor_setup(lodcm.energy_si.th2.motor)
    motor_setup(lodcm.energy_si.z1.motor)
    motor_setup(lodcm.energy_si.z2.motor)
    motor_setup(lodcm.energy_si.dr)

    return lodcm


# Crystal Tower 1 Setup
@pytest.fixture(scope='function')
def fake_tower1():
    FakeLODCM = make_fake_device(SimFirstTower)
    tower1 = FakeLODCM('FAKE:TOWER1', name='fake_t1')

    tower1.diamond_reflection.sim_put((1, 1, 1))
    tower1.silicon_reflection.sim_put((1, 1, 1))
    # 1 = 'C'
    tower1.h1n_state.state.sim_put(1)
    tower1.h1n_state.state.sim_set_enum_strs(
        ['Unknown'] + H1N.states_list)
    tower1.y1_state.state.sim_put(1)
    tower1.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    tower1.chi1_state.state.sim_put(1)
    tower1.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)

    return tower1


# Crystal Tower 2 Setup
@pytest.fixture(scope='function')
def fake_tower2():
    FakeLODCM = make_fake_device(SimSecondTower)
    tower2 = FakeLODCM('FAKE:TOWER2', name='fake_t2')

    tower2.diamond_reflection.sim_put((2, 2, 2))
    tower2.silicon_reflection.sim_put((2, 2, 2))

    tower2.y2_state.state.sim_put(1)
    tower2.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    tower2.chi2_state.state.sim_put(1)
    tower2.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    tower2.h2n_state.state.sim_put(1)
    tower2.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)

    return tower2


@pytest.fixture(scope='function')
def fake_energy_si(monkeypatch):

    def get_material(self, check=True):
        return "Si"
    monkeypatch.setattr(LODCMEnergySi, 'get_material', get_material)

    FakeLODCMEnergy = make_fake_device(LODCMEnergySi)
    energy = FakeLODCMEnergy('FAKE:ENERGY:SI', name='fake_energy_si')

    motor_setup(energy.th1.motor)
    motor_setup(energy.th2.motor)
    motor_setup(energy.z1.motor)
    motor_setup(energy.z2.motor)
    motor_setup(energy.dr)

    return energy


@pytest.fixture(scope='function')
def fake_energy_c(monkeypatch):

    def get_material(self, check=True):
        return "C"
    monkeypatch.setattr(LODCMEnergyC, 'get_material', get_material)

    FakeLODCMEnergy = make_fake_device(LODCMEnergyC)
    energy = FakeLODCMEnergy('FAKE:ENERGY:C', name='fake_energy_c')

    motor_setup(energy.th1.motor, pos=77)
    motor_setup(energy.th2.motor)
    motor_setup(energy.z1.motor)
    motor_setup(energy.z2.motor)
    motor_setup(energy.dr)

    return energy


def test_lodcm_destination(fake_lodcm):
    logger.debug('test_lodcm_destination')
    lodcm = fake_lodcm
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)

    lodcm.h1n_state.move('OUT')
    assert len(lodcm.destination) == 1
    lodcm.h1n_state.move('C')
    assert len(lodcm.destination) == 2
    # Block the mono line
    lodcm.yag.move('IN')
    assert len(lodcm.destination) == 1
    lodcm.h1n_state.move('Si')
    assert len(lodcm.destination) == 0
    lodcm.yag.move('OUT')
    assert len(lodcm.destination) == 1

    # Unknown state
    lodcm.h1n_state.state.sim_put('Unknown')
    assert len(lodcm.destination) == 0


def test_lodcm_branches(fake_lodcm):
    logger.debug('test_lodcm_branches')
    lodcm = fake_lodcm
    branches = lodcm.branches
    assert isinstance(branches, list)
    for b in branches:
        assert isinstance(b, str)


def test_lodcm_remove_dia(fake_lodcm):
    logger.debug('test_lodcm_remove_dia')
    lodcm = fake_lodcm
    lodcm.yag.insert(wait=True)
    cb = Mock()
    lodcm.remove_dia(moved_cb=cb, wait=True)
    assert cb.called
    assert lodcm.yag.position == 'OUT'


def test_hutch_foils():
    FakeFoil = make_fake_device(Foil)
    assert 'Zn' in FakeFoil('XPP', name='foil').in_states
    assert 'Ge' in FakeFoil('XCS', name='foil').in_states


def test_tower1_crystal_type(fake_tower1):
    tower1 = fake_tower1
    # tower1 si: y1_state = Si, chi1_state = Si, h1n = Si or Out
    tower1.h1n_state.move('OUT')
    tower1.y1_state.move('Si')
    tower1.chi1_state.move('Si')
    assert tower1.is_silicon()
    tower1.h1n_state.move('Si')
    assert tower1.is_silicon()
    # tower1 c: y1_state = C, chi1_state = C, h1n = C or Out
    tower1.h1n_state.move('OUT')
    tower1.y1_state.move('C')
    tower1.chi1_state.move('C')
    assert tower1.is_diamond()
    tower1.h1n_state.move('C')
    assert tower1.is_diamond()


def test_tower2_crystal_type(fake_tower2):
    tower2 = fake_tower2
    # tower2 si: y2_state = Si, chi2_state = Si, h2n_state = Si
    tower2.h2n_state.move('Si')
    tower2.y2_state.move('Si')
    tower2.chi2_state.move('Si')
    assert tower2.is_silicon()
    # tower2 c: y2_state = C, chi2_state = C, h2n_state = C
    tower2.h2n_state.move('C')
    tower2.y2_state.move('C')
    tower2.chi2_state.move('C')
    assert tower2.is_diamond()


def test_get_reflection_tower1(fake_tower1):
    tower1 = fake_tower1
    res = tower1.get_reflection(as_tuple=True)
    assert res == (1, 1, 1)


def test_get_reflection_tower2(fake_tower2):
    tower2 = fake_tower2
    res = tower2.get_reflection(as_tuple=True)
    assert res == (2, 2, 2)


def test_get_reflection_lodcm(fake_lodcm):
    lodcm = fake_lodcm
    # as of now tower 1: (1, 1, 1), tower 2: (1, 1, 1) - match
    res = lodcm.get_reflection(as_tuple=True)
    assert res == (1, 1, 1)
    # change tower 2: (2, 2, 2) - should not match
    lodcm.tower2.diamond_reflection.sim_put((2, 2, 2))
    lodcm.tower2.silicon_reflection.sim_put((2, 2, 2))
    with pytest.raises(ValueError):
        lodcm.get_reflection(as_tuple=True, check=True)


def test_calc_energy_c(fake_energy_c):
    energy = fake_energy_c
    logger.info('Testing with C, (1, 1, 1)')
    # with patch('pcdsdevices.lodcm.LODCMEnergy.get_material',
    #            return_value='C'):
    with patch('pcdsdevices.lodcm.LODCMEnergyC.get_reflection',
               return_value=(1, 1, 1)):
        th, z = energy.calc_energy(energy=10)
        assert th == 17.51878596767417
        assert z == 427.8469911590626
        th, z = energy.calc_energy(energy=6)
        assert th == 30.112367750143974
        assert z == 171.63966796710216

    logger.info('Testing with C, (2, 2, 0)')
    with patch('pcdsdevices.lodcm.LODCMEnergyC.get_reflection',
               return_value=(2, 2, 0)):
        th, z = energy.calc_energy(energy=10)
        assert th == 29.443241721774093
        assert z == 181.06811018121837
        th, z = energy.calc_energy(energy=6)
        assert th == 55.01163934185574
        assert z == -109.32912449140694


def test_calc_energy_si(fake_energy_si):
    energy = fake_energy_si
    logger.info('Testing with Si, (1, 1, 1)')
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        th, z = energy.calc_energy(energy=10)
        assert th == 11.402710639982848
        assert z == 713.4828146545175
        th, z = energy.calc_energy(energy=6)
        assert th == 19.23880622548293
        assert z == 377.45432488131866

    logger.info('Testing with Si, (2, 2, 0)')
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(2, 2, 0)):
        th, z = energy.calc_energy(energy=10)
        assert th == 18.835297041786244
        assert z == 388.56663653387835
        th, z = energy.calc_energy(energy=6)
        assert th == 32.55312408478254
        assert z == 139.21560118646275


def test_get_energy_c(fake_energy_c, monkeypatch):
    energy = fake_energy_c
    energy.th1.set_current_position(-23)

    with patch("pcdsdevices.lodcm.LODCMEnergyC.get_reflection",
               return_value=(1, 1, 1)):
        # with patch('pcdsdevices.lodcm.LODCMEnergy.get_material',
        #            return_value='C'):
        # offset of 23, motor position 0
        # current th1.wm() should be 23
        res = energy.get_energy()
        # TODO: why is this NONE?
        assert res == 7.7039801344046515


def test_get_energy_si(fake_energy_si, monkeypatch):
    energy = fake_energy_si

    energy.th1.set_current_position(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        # offset of 23, motor position 0
        # current th1.wm() should be 23
        res = energy.get_energy()
        assert res == 5.059840436879476


def test_move_energy_c(fake_energy_c, monkeypatch):
    energy = fake_energy_c
    with patch("pcdsdevices.lodcm.LODCMEnergyC.get_reflection",
               return_value=(1, 1, 1)):
        # with patch('pcdsdevices.lodcm.LODCMEnergy.get_material',
        #            return_value='C'):
        energy.move(10, wait=False)
        assert energy.th1.wm() == 17.51878596767417
        assert energy.th2.wm() == 17.51878596767417
        assert energy.z1.wm() == -427.8469911590626
        assert energy.z2.wm() == 427.8469911590626
        assert energy.th1.pseudo_motor.position == 17.51878596767417
        assert energy.th1.user_offset.get() == -17.51878596767417


def test_move_energy_si(fake_energy_si, monkeypatch):
    energy = fake_energy_si
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        # with patch('pcdsdevices.lodcm.LODCMEnergy.get_material',
        #            return_value='Si'):
        energy.move(10, wait=False)
        assert energy.th1.wm() == 11.402710639982848
        assert energy.th2.wm() == 11.402710639982848
        assert energy.z1.wm() == -713.4828146545175
        assert energy.z2.wm() == 713.4828146545175
        # TODO: why is this 0?
        # print(f'dr.position: {energy.dr.wm()}')
        assert energy.th1.pseudo_motor.position == 11.402710639982848
        assert energy.th1.user_offset.get() == -11.402710639982848


# def test_lodcm_energy(fake_lodcm):
#     lodcm = fake_lodcm
#     # res = lodcm.get_reflection(as_tuple=True)
#     # assert res == (1, 1, 1)
#     # res = lodcm.get_material(check=True)
#     # assert res == 'C'

#     # relflections should not match:
#     with patch("pcdsdevices.lodcm.LODCMEnergy.get_reflection",
#                return_value=(1, 1, 1)):
#         with patch('pcdsdevices.lodcm.LODCMEnergy.get_material',
#                    return_value='Si'):
#             res = lodcm.calc_energy(10)
#             res2 = lodcm.energy.calc_energy(10)
#             assert res == res2
#             assert res == (11.402710639982848, 713.4828146545175)


# def test_others(fake_lodcm):
#     lodcm = fake_lodcm
#    # setup_energy_motor(lodcm.energy)
#     with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
#                return_value=(1, 1, 1)):
#         # with patch('pcdsdevices.lodcm.LODCM.get_material',
#         #            return_value='Si'):
#         # print(lodcm)
#         # print(lodcm.energy_si)
#         #  print(lodcm.energy)
#         lodcm.energy_si.move(6, wait=False)
#         assert lodcm.energy.th1.wm() == 19.23880622548293


@pytest.mark.timeout(5)
def test_lodcm_disconnected():
    # def get_material(self):
    #     return "C"
    # monkeypatch.setattr(LODCMEnergy, 'get_material', get_material)
    LODCM('TST:LOM', name='test_lom')
