############
# Standard #
############
import logging
import time
###############
# Third Party #
###############
import pytest
from unittest.mock import Mock
##########
# Module #
##########
from .conftest import using_fake_epics_pv
from pcdsdevices.epics import IPM

logger = logging.getLogger(__name__)

@using_fake_epics_pv
@pytest.fixture(scope='function')
def ipm():
    return IPM("Test:My:IPM")


@using_fake_epics_pv
def test_ipm_states(ipm):
    ipm.target.state._read_pv.put('OUT')
    assert ipm.removed
    assert not ipm.inserted
    ipm.target.state._read_pv.put('TARGET1')
    assert not ipm.removed
    assert ipm.inserted


@using_fake_epics_pv
def test_ipm_motion(ipm):
    #Remove IPM Targets
    ipm.remove(wait=True, timeout=1.0)
    assert ipm.target.state._write_pv.get() == 'OUT'
    #Insert IPM Targets
    ipm.target_in(1)
    assert ipm.target.state._write_pv.get() == 'TARGET1'
    #Move diodes in 
    ipm.diode_in()
    assert ipm.diode.state._write_pv.get() == 'IN'
    ipm.diode_out()
    #Move diodes out
    assert ipm.diode.state._write_pv.get() == 'OUT'


@using_fake_epics_pv
def test_ipm_subscriptions(ipm):
    #Subscribe a pseudo callback
    cb = Mock()
    ipm.subscribe(cb, event_type=ipm.SUB_ST_CHG, run=False)
    #Change the target state
    ipm.target.state._read_pv.put('OUT')
    assert cb.called

