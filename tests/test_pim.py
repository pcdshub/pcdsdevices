import logging
import pytest
from unittest.mock import Mock

from ophyd.device import Component as Cmp
from ophyd.signal import Signal

from pcdsdevices.areadetector.detectors import DefaultAreaDetector
from pcdsdevices.pim import PIM, PIMMotor
from pcdsdevices.sim.pv import using_fake_epics_pv

from .conftest import attr_wait_true, connect_rw_pvs

logger = logging.getLogger(__name__)


# OK, we have to screw with the class def here. I'm sorry. It's ophyd's fault
# for checking an epics signal value in the __init__ statement.
for comp in (DefaultAreaDetector.image, DefaultAreaDetector.stats):
    plugin_class = comp.cls
    plugin_class.plugin_type = Cmp(Signal, value=plugin_class._plugin_type)


def fake_pim():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    pim = PIMMotor('Test:Yag', name='test')
    connect_rw_pvs(pim.state)
    pim.wait_for_connection()
    pim.state.put(0, wait=True)
    pim.state._read_pv.enum_strs = ['Unknown'] + PIMMotor.states_list
    return pim


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_pim_stage():
    logger.debug('test_pim_stage')
    pim = fake_pim()
    # Should return to original position on unstage
    pim.move('OUT', wait=True)
    assert pim.removed
    pim.stage()
    pim.move('IN', wait=True)
    assert pim.inserted
    pim.unstage()
    assert pim.removed
    pim.move('IN', wait=True)
    assert pim.inserted
    pim.stage()
    pim.move('OUT', wait=True)
    assert pim.removed
    pim.unstage()
    assert pim.inserted


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_pim_det():
    logger.debug('test_pim_det')
    pim = PIM('Test:Yag', name='test', prefix_det='potato')
    pim.wait_for_connection()
    pim = PIM('Test:Yag', name='test')
    pim.wait_for_connection()


@pytest.mark.timeout(5)
@using_fake_epics_pv
def test_pim_subscription():
    logger.debug('test_pim_subscription')
    pim = fake_pim()
    cb = Mock()
    pim.subscribe(cb, event_type=pim.SUB_STATE, run=False)
    pim.state._read_pv.put(2)
    attr_wait_true(cb, 'called')
    assert cb.called
