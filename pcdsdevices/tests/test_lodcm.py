import logging
from unittest.mock import Mock, patch

import numpy as np
import pytest
from ophyd.sim import make_fake_device

from ..epics_motor import OffsetMotor
from ..lodcm import (CHI1, CHI2, H1N, H2N, LODCM, Y1, Y2, Dectris, Diode, Foil,
                     LODCMEnergyC, LODCMEnergySi, SimFirstTower, SimLODCM,
                     SimSecondTower, YagLom)

logger = logging.getLogger(__name__)


def motor_setup(mot, pos=0):
    mot.user_readback.sim_put(0)
    mot.user_setpoint.sim_put(0)
    mot.user_setpoint.sim_set_limits((0, 0))
    mot.motor_spg.sim_put(2)


def make_fake_offset_ims(prefix, motor_pos=0, user_offset=0):
    class MyOffsetIMS(OffsetMotor):
        def set_current_position(self, position):
            # TODO: is this supposed to be:
            # position - motor.position
            # or the way i have it here?
            logger.debug('Set current position to %d', position)
            new_offset = self.motor.position - position
            self.user_offset.sim_put(new_offset)

    fake_ims = make_fake_device(MyOffsetIMS)('PREFIX',
                                             motor_prefix='MOTOR:PREFIX',
                                             name='fake_ims')

    motor_setup(fake_ims.motor, pos=motor_pos)
    fake_ims.user_offset.sim_put(user_offset)
    return fake_ims


@pytest.fixture(scope='function')
def fake_lodcm():
    FakeLODCM = make_fake_device(SimLODCM)

    # After the fake_lodcm setup:
    # fake_lodcm will have get_material() = 'C' by default
    # and get_reflection() = (1, 1, 1) by default

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
    # set y1_state and chi1_state to 'C'
    lodcm.y1_state.state.sim_put(1)
    lodcm.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    lodcm.chi1_state.state.sim_put(1)
    lodcm.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)

    # additional states for Crystal Tower 2
    # set y2_state, chi2_state and h2_state to 'C'
    lodcm.y2_state.state.sim_put(1)
    lodcm.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    lodcm.chi2_state.state.sim_put(1)
    lodcm.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    lodcm.h2n_state.state.sim_put(1)
    lodcm.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)

    # set the reflection to default to (1, 1, 1) for both towers and both
    # materials
    lodcm.tower1.diamond_reflection.sim_put((1, 1, 1))
    lodcm.tower1.silicon_reflection.sim_put((1, 1, 1))
    lodcm.tower2.diamond_reflection.sim_put((1, 1, 1))
    lodcm.tower2.silicon_reflection.sim_put((1, 1, 1))

    lodcm.th1Si = make_fake_offset_ims('TH1SI:PREFIX', user_offset=-23)
    lodcm.th2Si = make_fake_offset_ims('TH2C:PREFIX', user_offset=-23)
    lodcm.th1C = make_fake_offset_ims('TH1C:PREFIX')
    lodcm.th2C = make_fake_offset_ims('TH2C:PREFIX')

    lodcm.z1Si = make_fake_offset_ims('TH1SI:PREFIX')
    lodcm.z2Si = make_fake_offset_ims('TH2C:PREFIX')
    lodcm.z1C = make_fake_offset_ims('TH1C:PREFIX')
    lodcm.z2C = make_fake_offset_ims('TH2C:PREFIX')

    lodcm.tower2.x2_retry_deadband.sim_put(-1)
    lodcm.tower2.z2_retry_deadband.sim_put(-1)

    return lodcm


# Crystal Tower 1 Setup - usefull for testing CrystalTower1 independently
@pytest.fixture(scope='function')
def fake_tower1():
    FakeLODCM = make_fake_device(SimFirstTower)
    tower1 = FakeLODCM('FAKE:TOWER1', name='fake_t1')

    tower1.diamond_reflection.sim_put((1, 1, 1))
    tower1.silicon_reflection.sim_put((1, 1, 1))
    # set h1n_state to 'OUT'
    tower1.h1n_state.state.sim_put(1)
    tower1.h1n_state.state.sim_set_enum_strs(
        ['Unknown'] + H1N.states_list)
    # set y1_state to 'C'
    tower1.y1_state.state.sim_put(1)
    tower1.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    # set chi1_state to 'C'
    tower1.chi1_state.state.sim_put(1)
    tower1.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)
    return tower1


# Crystal Tower 2 Setup - usefull for testing CrystalTower1 independently
@pytest.fixture(scope='function')
def fake_tower2():
    FakeLODCM = make_fake_device(SimSecondTower)
    tower2 = FakeLODCM('FAKE:TOWER2', name='fake_t2')

    tower2.diamond_reflection.sim_put((2, 2, 2))
    tower2.silicon_reflection.sim_put((2, 2, 2))
    # set y2_state to 'C'
    tower2.y2_state.state.sim_put(1)
    tower2.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    # set chi2_state to 'C'
    tower2.chi2_state.state.sim_put(1)
    tower2.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    # set h2n_state to 'C'
    tower2.h2n_state.state.sim_put(1)
    tower2.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)

    return tower2


# LODCM Energy Si - usefull for testing LODCMEnergySi independently
@pytest.fixture(scope='function')
def fake_energy_si():
    FakeLODCMEnergy = make_fake_device(LODCMEnergySi)
    energy = FakeLODCMEnergy('FAKE:ENERGY:SI', name='fake_energy_si')

    motor_setup(energy.th1Si.motor)
    motor_setup(energy.th2Si.motor)
    motor_setup(energy.z1Si.motor)
    motor_setup(energy.z2Si.motor)
    motor_setup(energy.dr)

    return energy


# LODCM Energy C - usefull for testing LODCMEnergyC independently
@pytest.fixture(scope='function')
def fake_energy_c():
    FakeLODCMEnergy = make_fake_device(LODCMEnergyC)
    energy = FakeLODCMEnergy('FAKE:ENERGY:C', name='fake_energy_c')

    motor_setup(energy.th1C.motor)
    motor_setup(energy.th2C.motor)
    motor_setup(energy.z1C.motor)
    motor_setup(energy.z2C.motor)
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
    assert lodcm.main_line in lodcm.destination

    lodcm.h1n_state.move('C')
    assert lodcm.main_line in lodcm.destination
    assert lodcm.mono_line in lodcm.destination
    assert len(lodcm.destination) == 2

    # Block the mono line
    lodcm.yag.move('IN')
    assert len(lodcm.destination) == 1
    assert lodcm.mono_line not in lodcm.destination
    assert lodcm.main_line in lodcm.destination
    lodcm.h1n_state.move('Si')
    assert len(lodcm.destination) == 0
    lodcm.yag.move('OUT')
    assert len(lodcm.destination) == 1
    assert lodcm.mono_line in lodcm.destination

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


def test_move_energy(fake_lodcm):
    lom = fake_lodcm
    # with material 'Si' and reflection as (1, 1, 1)
    with patch('pcdsdevices.lodcm.LODCM.get_material',
               return_value='Si'):
        lom.energy.move(10, wait=False)
        assert np.isclose(lom.energy.th1Si.wm(), 11.402710639982848)
        assert np.isclose(lom.energy.th2Si.wm(), 11.402710639982848)
        assert np.isclose(lom.energy.z1Si.wm(), -713.4828146545175)
        assert np.isclose(lom.energy.z2Si.wm(), 713.4828146545175)
        assert np.isclose(lom.energy.dr.wm(), 22.805421279965696)


def test_tweak_x(fake_lodcm):
    lom = fake_lodcm
    # with th2Si == 23 (init_pos) in fake_lodcm setup
    # with x = 3 => z = 2.897066324421222
    lom.tweak_x(3, 'Si', wait=False)
    assert lom.x2.wm() == 3
    assert np.isclose(lom.z2.wm(), 2.897066324421222)
    # should move relative to current position
    # x2 = 3, z2 = 2.897066324421222
    lom.tweak_x(10, 'Si', wait=False)
    # x = 10 + current position
    # z = 9.656887748070739 + current position
    assert lom.x2.wm() == 13
    assert np.isclose(lom.z2.wm(), 9.656887748070739 + 2.897066324421222)


def test_tweak_parallel(fake_lodcm):
    lom = fake_lodcm
    # with th2Si == 23 (init_pos) in fake_lodcm setup
    # with Si, x2 = 0, z2 = 0 (init_pos)
    # x2.mvr(p * np.sin(th * np.pi / 180)) => 0 + 1.1721933854678213
    # z2.mvr(p * np.cos(th * np.pi / 180)) => 24 + 2.761514560357321
    with patch('pcdsdevices.lodcm.LODCM.get_material',
               return_value='Si'):
        lom.tweak_parallel(3)
        assert np.isclose(lom.x2.wm(), 1.1721933854678213)
        assert np.isclose(lom.z2.wm(), 2.761514560357321)
        lom.tweak_parallel(3)
        # with now x2 = 1.1721933854678213, z2 = 2.761514560357321
        assert np.isclose(lom.x2.wm(), 1.1721933854678213 * 2)
        assert np.isclose(lom.z2.wm(), 2.761514560357321 * 2)


def test_set_energy(fake_lodcm, monkeypatch):
    lom = fake_lodcm
    lom.set_energy(10, material='Si', reflection=(1, 1, 1))

    assert np.isclose(lom.th1Si.wm(), 11.402710639982848)
    assert np.isclose(lom.th2Si.wm(), 11.402710639982848)
    assert np.isclose(lom.z1Si.wm(), -713.4828146545175)
    assert np.isclose(lom.z2Si.wm(), 713.4828146545175)


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
    # tower1 non matching states:
    tower1.h1n_state.move('OUT')
    tower1.y1_state.move('C')
    tower1.chi1_state.move('Si')
    with pytest.raises(ValueError):
        tower1.get_material()


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
    # tower2 non matching states:
    tower2.h2n_state.move('C')
    tower2.y2_state.move('Si')
    tower2.chi2_state.move('Si')
    with pytest.raises(ValueError):
        tower2.get_material()


def test_get_reflection_tower1(fake_tower1):
    tower1 = fake_tower1
    # defalts to (1, 1, 1), see fake_tower1 setup
    # we also have C as the material
    res = tower1.get_reflection()
    assert res == (1, 1, 1)
    tower1.diamond_reflection.sim_put((2, 2, 2))
    res = tower1.get_reflection()
    assert res == (2, 2, 2)
    with patch('pcdsdevices.lodcm.CrystalTower1.is_diamond',
               return_value=None):
        with patch('pcdsdevices.lodcm.CrystalTower1.is_silicon',
                   return_value=None):
            with pytest.raises(ValueError):
                tower1.get_reflection()


def test_get_reflection_tower2(fake_tower2):
    tower2 = fake_tower2
    # defalts to (2, 2, 2), see fake_tower2 setup
    # we also have C as the material
    res = tower2.get_reflection()
    assert res == (2, 2, 2)
    tower2.diamond_reflection.sim_put((2, 0, 0))
    res = tower2.get_reflection()
    assert res == (2, 0, 0)
    with patch('pcdsdevices.lodcm.CrystalTower2.is_diamond',
               return_value=None):
        with patch('pcdsdevices.lodcm.CrystalTower2.is_silicon',
                   return_value=None):
            with pytest.raises(ValueError):
                tower2.get_reflection()


def test_get_reflection_lodcm(fake_lodcm):
    lodcm = fake_lodcm
    # as of now tower 1: (1, 1, 1), tower 2: (1, 1, 1) - match
    res = lodcm.get_reflection()
    assert res == (1, 1, 1)
    # change tower 2: (2, 2, 2) - should not match
    lodcm.tower2.diamond_reflection.sim_put((2, 2, 2))
    lodcm.tower2.silicon_reflection.sim_put((2, 2, 2))
    with pytest.raises(ValueError):
        lodcm.get_reflection()


def test_get_material_lodcm(fake_lodcm):
    lom = fake_lodcm
    # defaults to C, in fake_lodcm stup
    assert lom.get_material() == 'C'

    # change the material for one of the towers so that it does not match
    # CrystalTower2 = 'Si', CrystalTower1 = 'C' - do not match
    lom.tower2.h2n_state.move('Si')
    lom.tower2.y2_state.move('Si')
    lom.tower2.chi2_state.move('Si')

    with pytest.raises(ValueError):
        lom.get_material()


def test_calc_geometry_c(fake_energy_c):
    energy = fake_energy_c
    logger.info('Testing with C, (1, 1, 1)')
    with patch('pcdsdevices.lodcm.LODCMEnergyC.get_reflection',
               return_value=(1, 1, 1)):
        th, z = energy.calc_geometry(energy=10)
        assert np.isclose(th, 17.51878596767417)
        assert np.isclose(z, 427.8469911590626)
        th, z = energy.calc_geometry(energy=6)
        assert np.isclose(th, 30.112367750143974)
        assert np.isclose(z, 171.63966796710216)

    logger.info('Testing with C, (2, 2, 0)')
    with patch('pcdsdevices.lodcm.LODCMEnergyC.get_reflection',
               return_value=(2, 2, 0)):
        th, z = energy.calc_geometry(energy=10)
        assert np.isclose(th, 29.443241721774093)
        assert np.isclose(z, 181.06811018121837)
        th, z = energy.calc_geometry(energy=6)
        assert np.isclose(th, 55.01163934185574)
        assert np.isclose(z, -109.32912449140694)


def test_calc_geometry_si(fake_energy_si):
    energy = fake_energy_si
    logger.info('Testing with Si, (1, 1, 1)')
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        th, z = energy.calc_geometry(energy=10)
        assert np.isclose(th, 11.402710639982848)
        assert np.isclose(z, 713.4828146545175)
        th, z = energy.calc_geometry(energy=6)
        assert np.isclose(th, 19.23880622548293)
        assert np.isclose(z, 377.45432488131866)

    logger.info('Testing with Si, (2, 2, 0)')
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(2, 2, 0)):
        th, z = energy.calc_geometry(energy=10)
        assert np.isclose(th, 18.835297041786244)
        assert np.isclose(z, 388.56663653387835)
        th, z = energy.calc_geometry(energy=6)
        assert np.isclose(th, 32.55312408478254)
        assert np.isclose(z, 139.21560118646275)


def test_get_energy_c(fake_energy_c):
    energy = fake_energy_c
    energy.th1C.user_offset.sim_put(-23)

    with patch("pcdsdevices.lodcm.LODCMEnergyC.get_reflection",
               return_value=(1, 1, 1)):
        # offset of 23, motor position 0
        # current th1C.wm() should be 23
        assert energy.th1C.wm() == 23
        res = energy.get_energy()
        assert np.isclose(res, 7.7039801344046515)


def test_get_energy_si(fake_energy_si):
    energy = fake_energy_si

    energy.th1Si.user_offset.sim_put(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        # offset of 23, motor position 0
        # current th1Si.wm() should be 23
        assert energy.th1Si.wm() == 23
        res = energy.get_energy()
        assert np.isclose(res, 5.059840436879476)


def test_forward_si(fake_energy_si):
    energy = fake_energy_si

    energy.th1Si.user_offset.sim_put(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        res = energy.get_energy()
        assert np.isclose(res, 5.059840436879476)
        res = energy.forward(5.059840436879476)
        assert np.isclose(res.dr, 46)
        assert np.isclose(res.th1Si, 23)
        assert np.isclose(res.th2Si, 23)
        assert np.isclose(res.z1Si, -289.70663244212216)
        assert np.isclose(res.z2Si, 289.70663244212216)


def test_forward_c(fake_energy_c):
    energy = fake_energy_c

    energy.th1C.user_offset.sim_put(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergyC.get_reflection",
               return_value=(1, 1, 1)):
        res = energy.get_energy()
        assert np.isclose(res, 7.7039801344046515)
        res = energy.forward(7.7039801344046515)
        assert np.isclose(res.dr, 46)
        assert np.isclose(res.th1C, 23)
        assert np.isclose(res.th2C, 23)
        assert np.isclose(res.z1C, -289.70663244212216)
        assert np.isclose(res.z2C, 289.70663244212216)


def test_inverse_si(fake_energy_si):
    energy = fake_energy_si
    energy.th1Si.user_offset.sim_put(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        res = energy.inverse(23)
        assert np.isclose(res[0], 5.05984044)


def test_inverse_c(fake_energy_c):
    energy = fake_energy_c
    energy.th1C.user_offset.sim_put(-23)
    with patch("pcdsdevices.lodcm.LODCMEnergyC.get_reflection",
               return_value=(1, 1, 1)):
        res = energy.inverse(23)
        assert np.isclose(res[0], 7.7039801344046515)


def test_lodcm_move_energy_si(fake_lodcm):
    lodcm = fake_lodcm
    # with material 'Si', defaulted in fake_lodcm setup
    with patch("pcdsdevices.lodcm.LODCMEnergySi.get_reflection",
               return_value=(1, 1, 1)):
        with patch('pcdsdevices.lodcm.LODCM.get_material',
                   return_value='Si'):
            lodcm.energy_si.move(10, wait=False)
            assert np.isclose(lodcm.energy.th1Si.wm(), 11.402710639982848)
            assert np.isclose(lodcm.energy.th2Si.wm(), 11.402710639982848)
            assert np.isclose(lodcm.energy.dr.wm(), 11.402710639982848*2)
            assert np.isclose(lodcm.energy.z1Si.wm(), -713.4828146545175)
            assert np.isclose(lodcm.energy.z2Si.wm(), 713.4828146545175)


@pytest.mark.timeout(5)
def test_lodcm_disconnected():
    LODCM('TST:LOM', name='test_lom')
