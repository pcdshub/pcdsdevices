import logging

import pytest
from ophyd.sim import make_fake_device
from unittest.mock import Mock

from pcdsdevices.lodcm import LODCM, YagLom, Dectris, Diode, Foil

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_lodcm():
    FakeLODCM = make_fake_device(LODCM)
    lodcm = FakeLODCM('FAKE:LOM', name='fake_lom')
    lodcm.state.sim_put(1)
    lodcm.state.sim_set_enum_strs(['Unknown'] + LODCM.states_list)
    lodcm.yag.state.sim_put(1)
    lodcm.yag.state.sim_set_enum_strs(['Unknown'] + YagLom.states_list)
    lodcm.dectris.state.sim_put(1)
    lodcm.dectris.state.sim_set_enum_strs(['Unknown'] + Dectris.states_list)
    lodcm.diode.state.sim_put(1)
    lodcm.diode.state.sim_set_enum_strs(['Unknown'] + Diode.states_list)
    lodcm.foil.state.sim_put(1)
    lodcm.foil.state.sim_set_enum_strs(['Unknown'] + Foil.states_list)
    return lodcm


def test_lodcm_destination(fake_lodcm):
    logger.debug('test_lodcm_destination')
    lodcm = fake_lodcm
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)

    lodcm.move('OUT')
    assert len(lodcm.destination) == 1
    lodcm.move('C')
    assert len(lodcm.destination) == 2
    # Block the mono line
    lodcm.yag.move('IN')
    assert len(lodcm.destination) == 1
    lodcm.move('Si')
    assert len(lodcm.destination) == 0
    lodcm.yag.move('OUT')
    assert len(lodcm.destination) == 1

    # Unknown state
    lodcm.state.sim_put('Unknown')
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
