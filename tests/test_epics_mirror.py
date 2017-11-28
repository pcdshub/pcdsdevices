############
# Standard #
############
from unittest.mock import Mock

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.epics.mirror import PointingMirror
from pcdsdevices.sim.pv       import using_fake_epics_pv

from .conftest import attr_wait_true, connect_rw_pvs


def fake_branching_mirror():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    m = PointingMirror("MIRR:TST:M1H", "GANTRY:TST:M1H",
                     mps_prefix="MIRR:M1H:MPS", state_prefix="TST:M1H",
                     in_lines=['MFX', 'MEC'], out_lines= ['CXI'])
    m.state.state._read_pv.enum_strs = ['Unknown', 'IN', 'OUT']
    connect_rw_pvs(m.state.state)
    m.state.state._write_pv.put('Unknown')
    m.state.out_state.at_state._read_pv.put(2)
    m.state.in_state.at_state._read_pv.put(2)
    m.wait_for_connection()
    return m

@using_fake_epics_pv
def test_branching_mirror():
    branching_mirror = fake_branching_mirror()
    assert branching_mirror.branches == ['MFX', 'MEC', 'CXI']
    #Unknown
    branching_mirror.state.state._read_pv.put(0)
    assert branching_mirror.destination == []
    #Inserted
    branching_mirror.state.state._read_pv.put(1)
    assert branching_mirror.inserted
    assert branching_mirror.destination == ['MFX', 'MEC']
    #Removed
    branching_mirror.state.state._read_pv.put(2)
    assert branching_mirror.removed
    assert branching_mirror.destination == ['CXI']

@using_fake_epics_pv
def test_branching_mirror_moves():
    branching_mirror = fake_branching_mirror()
    #With gantry decoupled, should raise RuntimeError
    branching_mirror.x_gantry_decoupled._read_pv.put(1)
    with pytest.raises(RuntimeError):
        branching_mirror.remove()
    with pytest.raises(RuntimeError):
        branching_mirror.insert()
    #Recouple gantry
    branching_mirror.x_gantry_decoupled._read_pv.put(0)
    #Test removal
    branching_mirror.remove()
    assert branching_mirror.state.state._write_pv.value == 'OUT'
    #Finish simulated move manually
    branching_mirror.state.state._read_pv.put('OUT')
    #Insert 
    branching_mirror.insert()
    assert branching_mirror.state.state._write_pv.value == 'IN'

@using_fake_epics_pv
def test_epics_mirror_subscription():
    branching_mirror = fake_branching_mirror()
    #Subscribe a pseudo callback
    cb = Mock()
    branching_mirror.subscribe(cb, event_type=branching_mirror.SUB_STATE, run=False)
    #Change the target state
    branching_mirror.state.state._read_pv.put('IN')
    attr_wait_true(cb, 'called')
    assert cb.called
