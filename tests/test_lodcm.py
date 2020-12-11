import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.lodcm import (H1N, LODCM, Dectris, Diode, Foil, YagLom, Y1,
                               CHI1, Y2, CHI2, H2N, SIMOffsetIMS,
                               CrystalTower1, CrystalTower2, LODCMEnergy)

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_lodcm():
    FakeLODCM = make_fake_device(LODCM)
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

    return lodcm


@pytest.fixture(scope='function')
def fake_tower1():
    FakeLODCM = make_fake_device(CrystalTower1)
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


@pytest.fixture(scope='function')
def fake_tower2():
    FakeLODCM = make_fake_device(CrystalTower2)
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
def fake_calc():
    FakeLODCM = make_fake_device(LODCMEnergy)
    calc = FakeLODCM('FAKE:CALC', name='fake_lom')
    calc.first_tower.h1n_state.state.sim_put(1)
    calc.first_tower.y1_state.state.sim_put(1)
    calc.first_tower.chi1_state.state.sim_put(1)
    calc.second_tower.y2_state.state.sim_put(1)
    calc.second_tower.chi2_state.state.sim_put(1)
    calc.second_tower.h2n_state.state.sim_put(1)
    calc.first_tower.h1n_state.state.sim_put(1)
    calc.first_tower.h1n_state.state.sim_set_enum_strs(
        ['Unknown'] + H1N.states_list)
    calc.first_tower.y1_state.state.sim_put(1)
    calc.first_tower.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    calc.first_tower.chi1_state.state.sim_put(1)
    calc.first_tower.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)
    calc.second_tower.y2_state.state.sim_put(1)
    calc.second_tower.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    calc.second_tower.chi2_state.state.sim_put(1)
    calc.second_tower.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    calc.second_tower.h2n_state.state.sim_put(1)
    calc.second_tower.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)

    calc.first_tower.diamond_reflection.sim_put((1, 1, 1))
    calc.first_tower.silicon_reflection.sim_put((1, 1, 1))
    calc.second_tower.diamond_reflection.sim_put((2, 2, 2))
    calc.second_tower.silicon_reflection.sim_put((2, 2, 2))

    return calc


@pytest.fixture(scope='function')
def fake_offset_ims():
    FakeOffsetIms = make_fake_device(SIMOffsetIMS)
    off_ims = FakeOffsetIms('FAKE:OFFSET:IMS', name='fake_offset_ims')
    off_ims.motor.move(4)
    off_ims.offset.mv(0)

    return off_ims


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


def test_first_tower_crystal_type(fake_tower1):
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


def test_second_tower_crystal_type(fake_tower2):
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


def test_get_material(fake_calc):
    calc = fake_calc
    res = calc.get_material()
    assert res == 'C'
    # make first tower `Si`
    # they won't match so Value Error
    calc.first_tower.h1n_state.move('OUT')
    calc.first_tower.y1_state.move('Si')
    calc.first_tower.chi1_state.move('Si')
    with pytest.raises(ValueError):
        calc.get_material()


def test_get_reflection_first_tower(fake_tower1):
    tower1 = fake_tower1
    res = tower1.get_reflection()
    assert res == (1, 1, 1)


def test_get_reflection_second_tower(fake_tower2):
    tower2 = fake_tower2
    res = tower2.get_reflection()
    assert res == (2, 2, 2)


def test_get_reflection_lodcm(fake_calc):
    calc = fake_calc
    # as of now tower 1: (1, 1, 1), tower 2: (2, 2, 2) - do not match
    # C material
    with pytest.raises(ValueError):
        calc.get_reflection(check=True)
    # make second tower have same reflection (1, 1, 1)
    calc.second_tower.diamond_reflection.sim_put((1, 1, 1))
    calc.second_tower.silicon_reflection.sim_put((1, 1, 1))
    res = calc.get_reflection()
    assert res == (1, 1, 1)


def test_offset_ims(fake_offset_ims):
    ims = fake_offset_ims
    # motor position: 4
    # offset: 0
    assert ims.motor.position == 4
    ims.move(2)
    assert ims.motor.position == 6
    assert ims.offset.notepad_setpoint.get() == 2
    ims.move(1)
    assert ims.motor.position == 7
    assert ims.offset.notepad_setpoint.get() == 1
    ims.motor.move(10)


@pytest.mark.timeout(5)
def test_lodcm_disconnected():
    LODCM('TST:LOM', name='test_lom')
