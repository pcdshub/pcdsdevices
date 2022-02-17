import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..pim import PIM, PIMY, PPM, XPIM, PIMWithBoth, PIMWithFocus, PIMWithLED

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_pim():
    FakePIM = make_fake_device(PIM)
    pim = FakePIM('Test:Yag', name='test')
    pim.state.state.sim_put(0)
    pim.state.state.sim_set_enum_strs(['Unknown'] + PIMY.states_list)
    pim.y.error_severity.sim_put(0)
    pim.y.bit_status.sim_put(0)
    pim.y.motor_spg.sim_put(2)
    return pim


@pytest.mark.timeout(5)
def test_pim_stage(fake_pim):
    logger.debug('test_pim_stage')
    pim = fake_pim
    # Should return to original position on unstage
    pim.remove()
    assert pim.removed
    pim.state.stage()
    pim.insert()
    assert pim.inserted
    pim.state.unstage()
    assert pim.removed
    pim.insert()
    assert pim.inserted
    pim.state.stage()
    pim.remove()
    assert pim.removed
    pim.state.unstage()
    assert pim.inserted


@pytest.mark.timeout(5)
def test_pim_init():
    logger.debug('test_pim_init')
    FakePIM = make_fake_device(PIM)
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_zoom='woosh')
    FakePIM('Test:Yag', name='test', prefix_det='potato')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato')
    FakePIM('Test:Yag', name='test')
    FakePIM = make_fake_device(PIMWithLED)
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_zoom='woosh',
            prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_det='potato')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato')
    FakePIM('Test:Yag', name='test')
    FakePIM = make_fake_device(PIMWithFocus)
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_zoom='woosh',
            prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato', prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_focus='blurry')
    FakePIM('Test:Yag', name='test', prefix_det='potato')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato')
    FakePIM('Test:Yag', name='test')
    FakePIM = make_fake_device(PIMWithBoth)
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_zoom='woosh',
            prefix_focus='blur', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_focus='blur',
            prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato', prefix_focus='blur',
            prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_focus='blurry', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_led='shiny')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_zoom='woosh',
            prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_det='potato', prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato', prefix_focus='blur')
    FakePIM('Test:Yag', name='test', prefix_focus='blurry')
    FakePIM('Test:Yag', name='test', prefix_det='potato')
    FakePIM('Test:Yag', name='test', prefix_zoom='potato')
    FakePIM('Test:Yag', name='test')


@pytest.mark.timeout(5)
def test_pim_subscription(fake_pim):
    logger.debug('test_pim_subscription')
    pim = fake_pim
    cb = Mock()
    pim.state.subscribe(cb, event_type=pim.state.SUB_STATE, run=False)
    pim.state.state.sim_put(2)
    assert cb.called


@pytest.mark.timeout(5)
def test_pim_disconnected():
    PIM('TST:YAG', name='tst', prefix_det='tstst')


@pytest.mark.timeout(5)
def test_ppm_disconnected():
    PPM('IM7S7:PPM', name='im7s7')


@pytest.mark.timeout(5)
def test_xpim_disconnected():
    XPIM('IM7S7:PPM', name='im7s7')
