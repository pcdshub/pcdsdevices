############
# Standard #
############
from unittest.mock import Mock

###############
# Third Party #
###############
import math
import pytest

##########
# Module #
##########
from pcdsdevices.epics.mirror import OffsetMirror, PointingMirror
from pcdsdevices.sim.pv       import using_fake_epics_pv

from .conftest import attr_wait_true, connect_rw_pvs


def fake_branching_mirror():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    m = PointingMirror("TST:M1H", prefix_xy="STEP:TST:M1H",
                       xgantry_prefix="GANTRY:M1H:X", name='Test Mirror',
                       mps_prefix="MIRR:M1H:MPS", in_lines=['MFX', 'MEC'],
                       out_lines= ['CXI'])
    m.state._read_pv.enum_strs = ['Unknown', 'IN', 'OUT']
    connect_rw_pvs(m.state)
    m.state._write_pv.put('Unknown')
    m.wait_for_connection()
    # Couple the gantry
    m.xgantry.decoupled._read_pv.put(0)
    return m

@using_fake_epics_pv
def test_nan_protection():
    branching_mirror = fake_branching_mirror()
    with pytest.raises(ValueError):
        branching_mirror.pitch.put(math.nan)

@using_fake_epics_pv
def test_mirror_init():
    bm = fake_branching_mirror()
    assert bm.pitch.prefix == 'MIRR:TST:M1H'
    assert bm.xgantry.prefix == 'STEP:TST:M1H:X:P'
    assert bm.xgantry.gantry_prefix == 'GANTRY:M1H:X'
    assert bm.ygantry.prefix == 'STEP:TST:M1H:Y:P'
    assert bm.ygantry.gantry_prefix == 'GANTRY:STEP:TST:M1H:Y'
    m = OffsetMirror('TST:M1H', name= "Test Mirror")
    assert m.pitch.prefix == 'MIRR:TST:M1H'
    assert m.xgantry.prefix == 'TST:M1H:X:P'
    assert m.xgantry.gantry_prefix == 'GANTRY:TST:M1H:X'
    assert m.ygantry.prefix == 'TST:M1H:Y:P'
    assert m.ygantry.gantry_prefix == 'GANTRY:TST:M1H:Y'

@using_fake_epics_pv
def test_branching_mirror_destination():
    branching_mirror = fake_branching_mirror()
    assert branching_mirror.branches == ['MFX', 'MEC', 'CXI']
    #Unknown
    branching_mirror.state._read_pv.put(0)
    assert branching_mirror.position == 'Unknown'
    assert not branching_mirror.removed
    assert not branching_mirror.inserted
    assert branching_mirror.destination == []
    #Inserted
    branching_mirror.state._read_pv.put(1)
    assert branching_mirror.inserted
    assert not branching_mirror.removed
    assert branching_mirror.destination == ['MFX', 'MEC']
    #Removed
    branching_mirror.state._read_pv.put(2)
    assert branching_mirror.removed
    assert not branching_mirror.inserted
    assert branching_mirror.destination == ['CXI']

@using_fake_epics_pv
def test_branching_mirror_moves():
    branching_mirror = fake_branching_mirror()
    print(branching_mirror.read())
    #With gantry decoupled, should raise PermissionError
    branching_mirror.xgantry.decoupled._read_pv.put(1)
    with pytest.raises(PermissionError):
        branching_mirror.remove()
    with pytest.raises(PermissionError):
        branching_mirror.insert()
    #Recouple gantry
    branching_mirror.xgantry.decoupled._read_pv.put(0)
    #Test removal
    branching_mirror.remove()
    assert branching_mirror.state._write_pv.value == 'OUT'
    #Finish simulated move manually
    branching_mirror.state._read_pv.put('OUT')
    #Insert 
    branching_mirror.insert()
    assert branching_mirror.state._write_pv.value == 'IN'

@using_fake_epics_pv
def test_epics_mirror_subscription():
    branching_mirror = fake_branching_mirror()
    #Subscribe a pseudo callback
    cb = Mock()
    branching_mirror.subscribe(cb, event_type=branching_mirror.SUB_STATE, run=False)
    #Change the target state
    branching_mirror.state._read_pv.put('IN')
    attr_wait_true(cb, 'called')
    assert cb.called
