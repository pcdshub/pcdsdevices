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
from .conftest import using_fake_epics_pv
from pcdsdevices.epics import PickerBlade

logger = logging.getLogger(__name__)

@using_fake_epics_pv
@pytest.fixture(scope='function')
def pickerblade():
    return PickerBlade("Tst:ATT:")


@using_fake_epics_pv
def test_pickerblade_states(pickerblade):
    #Remove pickerblade
    pickerblade.simple_state._read_pv.put(0)
    assert pickerblade.removed
    assert not pickerblade.inserted
    #Insert pickerblade
    pickerblade.simple_state._read_pv.put(1)
    assert not pickerblade.removed
    assert pickerblade.inserted


@using_fake_epics_pv
def test_pickerblade_motion(pickerblade):
    #Remove pulsepicker
    status = pickerblade.remove(wait=False)
    #Check we wrote to the correct position
    pickerblade.force_close.get() == 1
    #Adjust readback
    pickerblade.simple_state._read_pv.put(0)
    #Check status has been marked as completed
    assert status.done and status.success


@using_fake_epics_pv
def test_pickerblade_subscriptions(pickerblade):
    #Subscribe a pseudo callback
    cb = Mock()
    pickerblade.subscribe(cb, run=False)
    #Change the target state
    pickerblade.simple_state._read_pv.put(1)
    assert cb.called
