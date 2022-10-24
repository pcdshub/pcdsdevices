import math
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..mirror import KBOMirror, OffsetMirror, PointingMirror


@pytest.fixture(scope='function')
def fake_branching_mirror():
    FakeMirror = make_fake_device(PointingMirror)
    m = FakeMirror("TST:M1H", prefix_xy="STEP:TST:M1H",
                   xgantry_prefix="GANTRY:M1H:X", name='Test Mirror',
                   in_lines=['MFX', 'MEC'], out_lines=['CXI'])
    m.state.sim_put(0)
    m.state.sim_set_enum_strs(['Unknown'] + PointingMirror.states_list)
    # Couple the gantry
    m.xgantry.decoupled.sim_put(0)
    # Make the pitch look reasonable
    m.pitch.motor_egu.sim_put('urad')
    # Limits are enabled, pick something for the test
    m.xgantry.setpoint.sim_set_limits((-100, 100))
    return m


@pytest.fixture(scope='function')
def fake_offset_mirror():
    FakeOffset = make_fake_device(OffsetMirror)
    return FakeOffset('TST:M1H', name="Test Mirror")


def test_nan_protection(fake_branching_mirror):
    with pytest.raises(ValueError):
        fake_branching_mirror.pitch.check_value(math.nan)


def test_ommotor_positioner_egu(fake_branching_mirror):
    assert fake_branching_mirror.pitch.egu == 'urad'


def test_mirror_init(fake_branching_mirror, fake_offset_mirror,
                     fake_kbo_mirror):
    bm = fake_branching_mirror
    assert bm.pitch.prefix == 'MIRR:TST:M1H'
    assert bm.xgantry.prefix == 'STEP:TST:M1H:X:P'
    assert bm.xgantry.gantry_prefix == 'GANTRY:M1H:X'
    assert bm.ygantry.prefix == 'STEP:TST:M1H:Y:P'
    assert bm.ygantry.gantry_prefix == 'GANTRY:TST:M1H:Y'
    m = fake_offset_mirror
    assert m.pitch.prefix == 'MIRR:TST:M1H'
    assert m.xgantry.prefix == 'TST:M1H:X:P'
    assert m.xgantry.gantry_prefix == 'GANTRY:TST:M1H:X'
    assert m.ygantry.prefix == 'TST:M1H:Y:P'
    assert m.ygantry.gantry_prefix == 'GANTRY:TST:M1H:Y'
    km = fake_kbo_mirror
    assert km.x.prefix == 'TST:M1H:MMS:X'
    assert km.y.prefix == 'TST:M1H:MMS:Y'
    assert km.pitch.prefix == 'TST:M1H:MMS:PITCH'
    assert km.bender_us.prefix == 'TST:M1H:MMS:BEND:US'
    assert km.bender_ds.prefix == 'TST:M1H:MMS:BEND:DS'


def test_offsetmirror_lighpath(fake_offset_mirror):
    m = fake_offset_mirror
    assert m.inserted
    assert not m.removed


def test_branching_mirror_destination(fake_branching_mirror):
    branching_mirror = fake_branching_mirror
    assert branching_mirror.branches == ['MFX', 'MEC', 'CXI']
    # Unknown
    branching_mirror.state.sim_put(0)
    assert branching_mirror.position == 'Unknown'
    assert not branching_mirror.removed
    assert not branching_mirror.inserted
    assert branching_mirror.destination == []
    # Inserted
    branching_mirror.state.sim_put(2)
    assert branching_mirror.inserted
    assert not branching_mirror.removed
    assert branching_mirror.destination == ['MFX', 'MEC']
    # Removed
    branching_mirror.state.sim_put(1)
    assert branching_mirror.removed
    assert not branching_mirror.inserted
    assert branching_mirror.destination == ['CXI']


def test_branching_mirror_moves(fake_branching_mirror):
    branching_mirror = fake_branching_mirror
    # With gantry decoupled, should raise PermissionError
    branching_mirror.xgantry.decoupled.sim_put(1)
    with pytest.raises(PermissionError):
        branching_mirror.xgantry.move(0.1, wait=False)
    with pytest.raises(PermissionError):
        branching_mirror.remove()
    with pytest.raises(PermissionError):
        branching_mirror.insert()
    # Recouple gantry
    branching_mirror.xgantry.decoupled.sim_put(0)
    # Test small move
    branching_mirror.xgantry.move(0.2, wait=False)
    assert branching_mirror.xgantry.setpoint.get() == 0.2
    # Test removal
    branching_mirror.remove()
    assert branching_mirror.state.get() == 1
    # Finish simulated move manually
    branching_mirror.state.sim_put(2)
    # Insert
    branching_mirror.insert()
    assert branching_mirror.state.get() == 2


def test_epics_mirror_subscription(fake_branching_mirror):
    branching_mirror = fake_branching_mirror
    # Subscribe a pseudo callback
    cb = Mock()
    branching_mirror.subscribe(cb, event_type=branching_mirror.SUB_STATE,
                               run=False)
    # Change the target state
    branching_mirror.state.put('IN')
    assert cb.called


@pytest.mark.timeout(5)
def test_mirror_disconnected():
    PointingMirror("TST:M1H", prefix_xy="STEP:TST:M1H",
                   xgantry_prefix="GANTRY:M1H:X", name='Test Mirror',
                   in_lines=['MFX', 'MEC'], out_lines=['CXI'])


@pytest.fixture(scope='function')
def fake_kbo_mirror():
    FakeKBO = make_fake_device(KBOMirror)
    return FakeKBO('TST:M1H', name="Test Mirror",
                   input_branches=['X0'], output_branches=['X0', 'X1'])


def test_kbomirror_lighpath(fake_kbo_mirror):
    km = fake_kbo_mirror
    lp_state = km.get_lightpath_state()
    assert lp_state.inserted
    assert not lp_state.removed
