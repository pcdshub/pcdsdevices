from unittest.mock import Mock

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.inout import InOutPositioner

from .conftest import attr_wait_true


def fake_ref():
    ref = InOutPositioner("Test:Ref", name="test")
    ref.state._read_pv.put('Unknown')
    ref.wait_for_connection()
    return ref


@using_fake_epics_pv
def test_ref_states():
    ref = fake_ref()
    # Inserted
    ref.state._read_pv.put("IN")
    assert ref.inserted
    assert not ref.removed
    # Removed
    ref.state._read_pv.put("OUT")
    assert not ref.inserted
    assert ref.removed


@using_fake_epics_pv
def test_ref_motion():
    ref = fake_ref()
    ref.remove()
    assert ref.state._write_pv.get() == 'OUT'


@using_fake_epics_pv
def test_ref_subscriptions():
    ref = fake_ref()
    # Subscribe a pseudo callback
    cb = Mock()
    ref.subscribe(cb, event_type=ref.SUB_STATE, run=False)
    # Change the target state
    ref.state._read_pv.put('OUT')
    attr_wait_true(cb, 'called')
    assert cb.called
