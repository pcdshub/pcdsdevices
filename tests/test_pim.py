import logging
import pytest
from unittest.mock import Mock

from ophyd.device import Component as Cpt
from ophyd.signal import Signal
from ophyd.sim import make_fake_device

from pcdsdevices.areadetector.detectors import PCDSDetector
from pcdsdevices.pim import PIM, PIMMotor

from .conftest import HotfixFakeEpicsSignal

logger = logging.getLogger(__name__)


# OK, we have to screw with the class def here. I'm sorry. It's ophyd's fault
# for checking an epics signal value in the __init__ statement.
for comp in (PCDSDetector.image, PCDSDetector.stats):
    plugin_class = comp.cls
    plugin_class.plugin_type = Cpt(Signal, value=plugin_class._plugin_type)


@pytest.fixture(scope='function')
def fake_pim():
    FakePIM = make_fake_device(PIMMotor)
    FakePIM.state.cls = HotfixFakeEpicsSignal
    pim = FakePIM('Test:Yag', name='test')
    pim.state.sim_put(0)
    pim.state.sim_set_enum_strs(['Unknown'] + PIMMotor.states_list)
    return pim


@pytest.mark.timeout(5)
def test_pim_stage(fake_pim):
    logger.debug('test_pim_stage')
    pim = fake_pim
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
def test_pim_det():
    logger.debug('test_pim_det')
    FakePIM = make_fake_device(PIM)
    FakePIM('Test:Yag', name='test', prefix_det='potato')
    FakePIM('Test:Yag', name='test')


@pytest.mark.timeout(5)
def test_pim_subscription(fake_pim):
    logger.debug('test_pim_subscription')
    pim = fake_pim
    cb = Mock()
    pim.subscribe(cb, event_type=pim.SUB_STATE, run=False)
    pim.state.sim_put(2)
    assert cb.called
