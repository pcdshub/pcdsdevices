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
from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics  import Reflaser

@using_fake_epics_pv
@pytest.fixture(scope='function')
def ref():
    ref = Reflaser("Test:Ref")
    ref.state.state._read_pv.enum_strs = ['IN', 'OUT']
    return ref

@using_fake_epics_pv
def test_ref_states(ref):
    #Inserted
    ref.state.state._read_pv.put("IN")
    assert ref.inserted
    assert not ref.removed
    #Removed
    ref.state.state._read_pv.put("OUT")
    assert not ref.inserted
    assert ref.removed

@using_fake_epics_pv
def test_ref_motion(ref):
    ref.remove()
    assert ref.state.state._write_pv.get() == 'OUT'

@using_fake_epics_pv
def test_ref_subscriptions(ref):
    #Subscribe a pseudo callback
    cb = Mock()
    ref.subscribe(cb, event_type=ref.SUB_STATE, run=False)
    #Change the target state
    ref.state.state._read_pv.put('OUT')
    assert cb.called

