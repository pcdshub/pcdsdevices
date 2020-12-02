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
    lodcm = FakeLODCM('FAKE:LOM', name='fake_lom',
                      # tower 1
                      z1_prefix='FAKE:Z1',
                      x1_prefix='FAKE:X1',
                      y1_prefix='FAKE:Y1',
                      th1_prefix='FAKE:TH1',
                      ch1_prefix='FAKE:CH1',
                      h1n_m_prefix='FAKE:H1N_M',
                      h1p_prefix='FAKE:H1P',
                      # tower 2
                      z2_prefix='FAKE:Z2',
                      x2_prefix='FAKE:X2',
                      y2_prefix='FAKE:Y2',
                      th2_prefix='FAKE:TH2',
                      ch2_prefix='FAKE:CH2',
                      h2n_prefix='FAKE:H2N',
                      diode2_prefix='FAKE:DIODE2',
                      # Diagnostic Tower
                      dh_prefix='FAKE:DH',
                      dv_prefix='FAKE:DV',
                      dr_prefix='FAKE:DR',
                      df_prefix='FAKE:DF',
                      dd_prefix='FAKE:DD',
                      yag_zoom_prefix='FAKE:ZOOM')
    lodcm.h1n.state.sim_put(1)
    lodcm.h1n.state.sim_set_enum_strs(['Unknown'] + H1N.states_list)
    lodcm.yag.state.sim_put(1)
    lodcm.yag.state.sim_set_enum_strs(['Unknown'] + YagLom.states_list)
    lodcm.dectris.state.sim_put(1)
    lodcm.dectris.state.sim_set_enum_strs(['Unknown'] + Dectris.states_list)
    lodcm.diode.state.sim_put(1)
    lodcm.diode.state.sim_set_enum_strs(['Unknown'] + Diode.states_list)
    lodcm.foil.state.sim_put(1)
    lodcm.foil.state.sim_set_enum_strs(['Unknown'] + Foil.states_list)
    lodcm.y1_state.state.sim_put(1)
    lodcm.y1_state.state.sim_set_enum_strs(['Unknown'] + Y1.states_list)
    lodcm.chi1_state.state.sim_put(1)
    lodcm.chi1_state.state.sim_set_enum_strs(['Unknown'] + CHI1.states_list)
    lodcm.y2_state.state.sim_put(1)
    lodcm.y2_state.state.sim_set_enum_strs(['Unknown'] + Y2.states_list)
    lodcm.chi2_state.state.sim_put(1)
    lodcm.chi2_state.state.sim_set_enum_strs(['Unknown'] + CHI2.states_list)
    lodcm.h2n_state.state.sim_put(1)
    lodcm.h2n_state.state.sim_set_enum_strs(['Unknown'] + H2N.states_list)

    lodcm.t1_c_ref.sim_put((1, 1, 1))
    lodcm.t1_si_ref.sim_put((1, 1, 1))
    lodcm.t2_c_ref.sim_put((2, 2, 2))
    lodcm.t2_si_ref.sim_put((2, 2, 2))

    return lodcm


def test_lodcm_destination(fake_lodcm):
    logger.debug('test_lodcm_destination')
    lodcm = fake_lodcm
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)

    lodcm.h1n.move('OUT')
    assert len(lodcm.destination) == 1
    lodcm.h1n.move('C')
    assert len(lodcm.destination) == 2
    # Block the mono line
    lodcm.yag.move('IN')
    assert len(lodcm.destination) == 1
    lodcm.h1n.move('Si')
    assert len(lodcm.destination) == 0
    lodcm.yag.move('OUT')
    assert len(lodcm.destination) == 1

    # Unknown state
    lodcm.h1n.state.sim_put('Unknown')
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
    lodcm.h1n.move('OUT')
    lodcm.y1_state.move('Si')
    lodcm.chi1_state.move('Si')
    assert lodcm._is_tower_1_si()
    lodcm.h1n.move('Si')
    assert lodcm._is_tower_1_si()
    # tower1 c: y1_state = C, chi1_state = C, h1n = C or Out
    lodcm.h1n.move('OUT')
    lodcm.y1_state.move('C')
    lodcm.chi1_state.move('C')
    assert lodcm._is_tower_1_c()
    lodcm.h1n.move('C')
    assert lodcm._is_tower_1_c()


def test_second_tower_crystal_type(fake_lodcm):
    lodcm = fake_lodcm
    # tower2 si: y2_state = Si, chi2_state = Si, h2n_state = Si
    lodcm.h2n_state.move('Si')
    lodcm.y2_state.move('Si')
    lodcm.chi2_state.move('Si')
    assert lodcm._is_tower_2_si()
    # tower2 c: y2_state = C, chi2_state = C, h2n_state = C
    lodcm.h2n_state.move('C')
    lodcm.y2_state.move('C')
    lodcm.chi2_state.move('C')
    assert lodcm._is_tower_2_c()


def test_get_reflection(fake_lodcm):
    lodcm = fake_lodcm
    # as of now tower 1: (1, 1, 1), tower 2: (2, 2, 2) - do not match
    with pytest.raises(ValueError):
        lodcm.get_reflection(as_tuple=True, check=False)
    lodcm.t2_c_ref.sim_put((1, 1, 1))
    lodcm.t2_si_ref.sim_put((1, 1, 1))
    res = lodcm.get_reflection(as_tuple=True, check=False)
    assert res == (1, 1, 1)
    res = lodcm.get_reflection(as_tuple=False, check=False)
    assert res == '111'
    res = lodcm.get_reflection(as_tuple=False, check=True)


def test_get_energy(fake_lodcm):
    lodcm = fake_lodcm
    lodcm.t2_c_ref.sim_put((1, 1, 1))
    lodcm.t2_si_ref.sim_put((1, 1, 1))
    # lodcm.th1_si.move('C')
    # print(lodcm.th1_si.wm())


@pytest.mark.timeout(5)
def test_lodcm_disconnected():
    LODCM('TST:LOM', name='test_lom',
          # tower 1
          z1_prefix='TST:Z1',
          x1_prefix='TST:X1',
          y1_prefix='TST:Y1',
          th1_prefix='TST:TH1',
          ch1_prefix='TST:CH1',
          h1n_m_prefix='TST:H1N_M',
          h1p_prefix='TST:H1P',
          # tower 2
          z2_prefix='TST:Z2',
          x2_prefix='TST:X2',
          y2_prefix='TST:Y2',
          th2_prefix='TST:TH2',
          ch2_prefix='TST:CH2',
          h2n_prefix='TST:H2N',
          diode2_prefix='TST:DIODE2',
          # Diagnostic Tower
          dh_prefix='TST:DH',
          dv_prefix='TST:DV',
          dr_prefix='TST:DR',
          df_prefix='TST:DF',
          dd_prefix='TST:DD',
          yag_zoom_prefix='TST:ZOOM')
