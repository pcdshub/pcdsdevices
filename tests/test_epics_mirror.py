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

def fake_branching_mirror():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    m = PointingMirror("MIRR:TST:M1H", "GANTRY:TST:M1H",
                     mps_prefix="MIRR:M1H:MPS", state_prefix="TST:M1H",
                     in_lines=['MFX', 'MEC'], out_lines= ['CXI'])
    m.state.state._read_pv.enum_strs = ['IN', 'OUT']
    return m

@using_fake_epics_pv
def test_branching_mirror():
    branching_mirror = fake_branching_mirror()
    assert branching_mirror.branches == ['MFX', 'MEC', 'CXI']
    #Unknown
    assert branching_mirror.destination == []
    #Inserted
    branching_mirror.state.out_state.at_state._read_pv.put(0)
    branching_mirror.state.in_state.at_state._read_pv.put(1)
    assert branching_mirror.inserted
    assert branching_mirror.destination == ['MFX', 'MEC']
    #Removed
    branching_mirror.state.out_state.at_state._read_pv.put(1)
    branching_mirror.state.in_state.at_state._read_pv.put(0)
    assert branching_mirror.removed
    assert branching_mirror.destination == ['CXI']

@using_fake_epics_pv
def test_branching_mirror_moves():
    branching_mirror = fake_branching_mirror()
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
    assert cb.called
