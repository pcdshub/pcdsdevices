from unittest.mock import Mock

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.inout import InOutRecordPositioner

from .conftest import attr_wait_true, connect_rw_pvs


def fake_ref():
    ref = InOutRecordPositioner("Test:Ref", name="test")
    connect_rw_pvs(ref.state)
    ref.state._write_pv.put('Unknown')
    ref.wait_for_connection()
    return ref


@using_fake_epics_pv
def test_ref_states():
    ref = fake_ref()
    # Inserted
    ref.state.put("IN")
    assert ref.inserted
    assert not ref.removed
    # Removed
    ref.state.put("OUT")
    assert not ref.inserted
    assert ref.removed


@using_fake_epics_pv
def test_ref_motion():
    ref = fake_ref()
    ref.remove()
    assert ref.position == 'OUT'
    ref.insert()
    assert ref.position == 'IN'


@using_fake_epics_pv
def test_ref_subscriptions():
    ref = fake_ref()
    # Subscribe a pseudo callback
    cb = Mock()
    ref.subscribe(cb, event_type=ref.SUB_STATE, run=False)
    # Change the target state
    ref.state.put('OUT')
    attr_wait_true(cb, 'called')
    assert cb.called
