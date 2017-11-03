import logging

import pytest
from unittest.mock import Mock
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics import FeeAtt

logger = logging.getLogger(__name__)


def fake_att():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    return FeeAtt("Tst:ATT:")


@using_fake_epics_pv
def test_attenuator_states():
    attenuator = fake_att()
    # Remove filters
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.OUT.value)
    assert attenuator.removed
    assert not attenuator.inserted
    # Insert filter
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.IN.value)
    assert not attenuator.removed
    assert attenuator.inserted


@using_fake_epics_pv
def test_attenuator_motion():
    attenuator = fake_att()
    # Call remove method
    status = attenuator.remove(wait=False)
    # Check we wrote to the correct position
    assert attenuator.go_cmd.get() == 0
    # Remove fake pv filters (IOC normally does this)
    for filt in attenuator.filters:
        filt.state_sig._read_pv.put(filt.filter_states.OUT.value)
    # Not guaranteed that callback comes in right away
    status_wait(status, timeout=1)
    # Check status has been marked as completed
    assert status.done and status.success


@using_fake_epics_pv
def test_attenuator_subscriptions():
    attenuator = fake_att()
    # Subscribe a pseudo callback
    cb = Mock()
    attenuator.subscribe(cb, event_type=attenuator.SUB_STATE,  run=False)
    # Change the target state
    attenuator.filter1.state_sig._read_pv.put(1)
    # Not guaranteed that callback comes in right away
    tmo = 1
    while not cb.called and tmo > 0:
        tmo -= 0.1
    assert cb.called
