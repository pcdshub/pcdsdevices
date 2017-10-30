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
from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics  import XFLS


@using_fake_epics_pv
@pytest.fixture(scope='function')
def xfls():
    return XFLS("TST:XFLS")


@using_fake_epics_pv
def test_xfls_states(xfls):
    #Remove
    xfls.state._read_pv.put(4)
    assert xfls.removed
    assert not xfls.inserted
    #Insert
    xfls.state._read_pv.put(3)
    assert not xfls.removed
    assert xfls.inserted
    #Unknown
    xfls.state._read_pv.put(0)
    assert not xfls.removed
    assert not xfls.inserted

@using_fake_epics_pv
def test_xfls_motion(xfls):
    xfls.remove()
    assert xfls.state._write_pv.get() == 4

@using_fake_epics_pv
def test_xfls_subscriptions(xfls):
    #Subscribe a pseudo callback
    cb = Mock()
    xfls.subscribe(cb, event_type=xfls.SUB_STATE, run=False)
    #Change readback state
    xfls.state._read_pv.put(4)
    assert cb.called
