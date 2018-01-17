from unittest.mock import Mock

import pytest

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.lens import XFLS

from .conftest import attr_wait_true


def fake_xfls():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    xfls = XFLS("TST:XFLS")
    xfls.wait_for_connection()
    return xfls


@using_fake_epics_pv
def test_xfls_states():
    xfls = fake_xfls()
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
def test_xfls_motion():
    xfls = fake_xfls()
    xfls.remove()
    assert xfls.state._write_pv.get() == 4

@using_fake_epics_pv
def test_xfls_subscriptions():
    xfls = fake_xfls()
    #Subscribe a pseudo callback
    cb = Mock()
    xfls.subscribe(cb, event_type=xfls.SUB_STATE, run=False)
    #Change readback state
    xfls.state._read_pv.put(4)
    attr_wait_true(cb, 'called')
    assert cb.called
