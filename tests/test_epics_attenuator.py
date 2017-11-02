import logging

import pytest
from unittest.mock import Mock

from pcdsdevices.sim.pv import  using_fake_epics_pv
from pcdsdevices.epics import FeeAtt

logger = logging.getLogger(__name__)

@using_fake_epics_pv
@pytest.fixture(scope='function')
def attenuator():
    return FeeAtt("Tst:ATT:")


@using_fake_epics_pv
def test_attenuator_states(attenuator):
    #Remove filters
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.OUT.value)
    assert attenuator.removed
    assert not attenuator.inserted
    #Insert filter
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.IN.value)
    assert not attenuator.removed
    assert attenuator.inserted


@using_fake_epics_pv
def test_attenuator_motion(attenuator):
    #Remove Attenuator Filters
    status = attenuator.remove(wait=False)
    #Check we wrote to the correct position
    assert attenuator.go_cmd.get() == 0
    #Remove filters
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.OUT.value)
    #Check status has been marked as completed
    assert status.done and status.success


@using_fake_epics_pv
def test_attenuator_subscriptions(attenuator):
    #Subscribe a pseudo callback
    cb = Mock()
    attenuator.subscribe(cb, event_type=attenuator.SUB_STATE,  run=False)
    #Change the target state
    attenuator.filter1.state_sig._read_pv.put(1)
    assert cb.called
