############
# Standard #
############
from unittest.mock import Mock

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.epics import PIMMotor
from pcdsdevices.sim.pv import  using_fake_epics_pv

@using_fake_epics_pv
@pytest.fixture(scope='function')
def pim():
    return PIMMotor('Test:Yag')


@using_fake_epics_pv
def test_pim_subscription(pim):
    cb = Mock()
    pim.subscribe(cb, event_type=pim.SUB_STATE, run=False)
    pim.states.state._read_pv.put(4)
    assert cb.called
