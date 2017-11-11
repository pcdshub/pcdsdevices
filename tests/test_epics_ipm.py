############
# Standard #
############
import logging
###############
# Third Party #
###############
import pytest
from unittest.mock import Mock
##########
# Module #
##########
from pcdsdevices.sim.pv import  using_fake_epics_pv
from pcdsdevices.epics import IPMMotors

from .conftest import connect_rw_pvs, attr_wait_true

logger = logging.getLogger(__name__)


def fake_ipm():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    ipm = IPMMotors("Test:My:IPM")
    diode_states = ['Unknown', 'OUT', 'IN']
    ipm.diode.state._read_pv.enum_strs = diode_states
    ipm.diode.state._write_pv.enum_strs = diode_states
    target_states = ['Unknown', 'OUT', 'TARGET1', 'TARGET2', 'TARGET3',
                     'TARGET4']
    ipm.target.state._read_pv.enum_strs = target_states
    ipm.target.state._write_pv.enum_strs = target_states
    connect_rw_pvs(ipm.diode.state)
    connect_rw_pvs(ipm.target.state)
    ipm.diode.state._write_pv.put('Unknown')
    ipm.target.state._write_pv.put('Unknown')
    return ipm


@using_fake_epics_pv
def test_ipm_states():
    logger.debug('test_ipm_states')
    ipm = fake_ipm()
    ipm.target.state._read_pv.put('OUT')
    assert ipm.removed
    assert not ipm.inserted
    ipm.target.state._read_pv.put('TARGET1')
    assert not ipm.removed
    assert ipm.inserted


@using_fake_epics_pv
def test_ipm_motion():
    logger.debug('test_ipm_motion')
    ipm = fake_ipm()
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
def test_ipm_subscriptions():
    logger.debug('test_ipm_subscriptions')
    ipm = fake_ipm()
    #Subscribe a pseudo callback
    cb = Mock()
    ipm.subscribe(cb, event_type=ipm.SUB_STATE, run=False)
    #Change the target state
    ipm.target.state._read_pv.put('OUT')
    attr_wait_true(cb, 'called')
    assert cb.called

