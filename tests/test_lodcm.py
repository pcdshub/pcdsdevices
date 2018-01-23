import logging

from unittest.mock import Mock

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.lodcm import LODCM

from .conftest import attr_wait_true, connect_rw_pvs

logger = logging.getLogger(__name__)


def fake_lodcm():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    lodcm = LODCM('FAKE:LOM', name='fake_lom')
    connect_rw_pvs(lodcm.state)
    connect_rw_pvs(lodcm.yag.state)
    connect_rw_pvs(lodcm.dectris.state)
    connect_rw_pvs(lodcm.diode.state)
    connect_rw_pvs(lodcm.foil.state)
    lodcm.state.put('OUT')
    lodcm.yag.state.put('OUT')
    lodcm.dectris.state.put('OUT')
    lodcm.diode.state.put('OUT')
    lodcm.foil.state.put('OUT')
    lodcm.wait_for_connection()
    return lodcm


@using_fake_epics_pv
def test_lodcm_destination():
    logger.debug('test_lodcm_destination')
    lodcm = fake_lodcm()
    dest = lodcm.destination
    assert isinstance(dest, list)
    for d in dest:
        assert isinstance(d, str)

    lodcm.state.put('OUT')
    assert len(lodcm.destination) == 1
    lodcm.state.put('C')
    assert len(lodcm.destination) == 2
    # Block the mono line
    lodcm.yag.state.put('IN')
    assert len(lodcm.destination) == 1
    lodcm.state.put('Si')
    assert len(lodcm.destination) == 0
    lodcm.yag.state.put('OUT')
    assert len(lodcm.destination) == 1


@using_fake_epics_pv
def test_lodcm_branches():
    logger.debug('test_lodcm_branches')
    lodcm = fake_lodcm()
    branches = lodcm.branches
    assert isinstance(branches, list)
    for b in branches:
        assert isinstance(b, str)


@using_fake_epics_pv
def test_lodcm_remove_dia():
    logger.debug('test_lodcm_remove_dia')
    lodcm = fake_lodcm()
    lodcm.yag.insert(wait=True)
    cb = Mock()
    lodcm.remove_dia(moved_cb=cb, wait=True)
    attr_wait_true(cb, 'called')
    assert cb.called
    assert lodcm.yag.position == 'OUT'
