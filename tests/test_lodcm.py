import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.lodcm import (H1N, LODCM, Dectris, Diode, Foil, YagLom, Y1,
                               CHI1, Y2, CHI2, H2N)

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
    # 1 = 'C'
    lodcm.t1_state.y1_state.state.sim_put(1)
    lodcm.t1_state.y1_state.state.sim_set_enum_strs(
        ['Unknown'] + Y1.states_list)
    lodcm.t1_state.chi1_state.state.sim_put(1)
    lodcm.t1_state.chi1_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI1.states_list)
    lodcm.t2_state.y2_state.state.sim_put(1)
    lodcm.t2_state.y2_state.state.sim_set_enum_strs(
        ['Unknown'] + Y2.states_list)
    lodcm.t2_state.chi2_state.state.sim_put(1)
    lodcm.t2_state.chi2_state.state.sim_set_enum_strs(
        ['Unknown'] + CHI2.states_list)
    lodcm.t2_state.h2n_state.state.sim_put(1)
    lodcm.t2_state.h2n_state.state.sim_set_enum_strs(
        ['Unknown'] + H2N.states_list)
    lodcm.t1_state.h1n_state.state.sim_put(1)
    lodcm.t1_state.h1n_state.state.sim_set_enum_strs(
        ['Unknown'] + H1N.states_list)

    lodcm.t1_state.diamond_reflection.sim_put((1, 1, 1))
    lodcm.t1_state.silicon_reflection.sim_put((1, 1, 1))
    lodcm.t2_state.diamond_reflection.sim_put((2, 2, 2))
    lodcm.t2_state.silicon_reflection.sim_put((2, 2, 2))

    return lodcm


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


def test_first_tower_crystal_type(fake_lodcm):
    lodcm = fake_lodcm
    # tower1 si: y1_state = Si, chi1_state = Si, h1n = Si or Out
    lodcm.t1_state.h1n_state.move('OUT')
    lodcm.t1_state.y1_state.move('Si')
    lodcm.t1_state.chi1_state.move('Si')
    assert lodcm.t1_state.is_silicon()
    lodcm.t1_state.h1n_state.move('Si')
    assert lodcm.t1_state.is_silicon()
    # tower1 c: y1_state = C, chi1_state = C, h1n = C or Out
    lodcm.t1_state.h1n_state.move('OUT')
    lodcm.t1_state.y1_state.move('C')
    lodcm.t1_state.chi1_state.move('C')
    assert lodcm.t1_state.is_diamond()
    lodcm.t1_state.h1n_state.move('C')
    assert lodcm.t1_state.is_diamond()


def test_second_tower_crystal_type(fake_lodcm):
    lodcm = fake_lodcm
    # tower2 si: y2_state = Si, chi2_state = Si, h2n_state = Si
    lodcm.t2_state.h2n_state.move('Si')
    lodcm.t2_state.y2_state.move('Si')
    lodcm.t2_state.chi2_state.move('Si')
    assert lodcm.t2_state.is_silicon()
    # tower2 c: y2_state = C, chi2_state = C, h2n_state = C
    lodcm.t2_state.h2n_state.move('C')
    lodcm.t2_state.y2_state.move('C')
    lodcm.t2_state.chi2_state.move('C')
    assert lodcm.t2_state.is_diamond()


# def test_get_material(fake_lodcm):
#     lodcm = fake_lodcm
#     # both should be diamond
#     res = lodcm.calc.get_material()
#     assert res == 'C'
#     # make first tower `Si`
#     # lodcm.t1_state.h1n_state.move('OUT')
#     # lodcm.t1_state.y1_state.move('Si')
#     # lodcm.t1_state.chi1_state.move('Si')
#     # with pytest.raises(ValueError):
#     #     lodcm.calc.get_material()


def test_get_reflection_first_tower(fake_lodcm):
    lodcm = fake_lodcm
    res = lodcm.t1_state.get_reflection()
    assert res == (1, 1, 1)


def test_get_reflection_second_tower(fake_lodcm):
    lodcm = fake_lodcm
    res = lodcm.t2_state.get_reflection()
    assert res == (2, 2, 2)


# def test_get_reflection_lodcm(fake_lodcm):
#     lodcm = fake_lodcm
#     # as of now tower 1: (1, 1, 1), tower 2: (2, 2, 2) - do not match
#     # C material
#     with pytest.raises(ValueError):
#         lodcm.calc.get_reflection(check=True)
#     lodcm.t2_state.diamond_reflection.sim_put((1, 1, 1))
#     lodcm.t2_state.silicon_reflection.sim_put((1, 1, 1))
#     res = lodcm.calc.get_reflection()
#     assert res == (1, 1, 1)


@pytest.mark.timeout(5)
def test_lodcm_disconnected():
    LODCM('TST:LOM', name='test_lom')
