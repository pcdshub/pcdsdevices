import logging

import pytest
from unittest.mock import Mock
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import  using_fake_epics_pv
from pcdsdevices.pulsepicker import PickerBlade

from .conftest import attr_wait_true

logger = logging.getLogger(__name__)

def fake_pickerblade():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    picker = PickerBlade("Tst:ATT:")
    picker.wait_for_connection()
    return picker


@using_fake_epics_pv
def test_pickerblade_states():
    pickerblade = fake_pickerblade()
    #Remove pickerblade
    pickerblade.simple_state._read_pv.put(0)
    assert pickerblade.removed
    assert not pickerblade.inserted
    #Insert pickerblade
    pickerblade.simple_state._read_pv.put(1)
    assert not pickerblade.removed
    assert pickerblade.inserted


@using_fake_epics_pv
def test_pickerblade_motion():
    pickerblade = fake_pickerblade()
    #Remove pulsepicker
    status = pickerblade.remove(wait=False)
    #Check we wrote to the correct position
    pickerblade.force_close.get() == 1
    #Adjust readback
    pickerblade.simple_state._read_pv.put(0)
    #Check status has been marked as completed
    status_wait(status, timeout=1)
    assert status.done and status.success


@using_fake_epics_pv
def test_pickerblade_subscriptions():
    pickerblade = fake_pickerblade()
    #Subscribe a pseudo callback
    cb = Mock()
    pickerblade.subscribe(cb, event_type=pickerblade.SUB_STATE, run=False)
    #Change the target state
    pickerblade.simple_state._read_pv.put(1)
    attr_wait_true(cb, 'called')
    assert cb.called
