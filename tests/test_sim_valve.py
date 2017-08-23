############
# Standard #
############
import time
from collections import OrderedDict

###############
# Third Party #
###############
import pytest

##########
# Module #
##########
from pcdsdevices.sim import valve
from pcdsdevices.epics.valve import InterlockError

tmo=10

# ValveBase

@pytest.mark.timeout(tmo)
def test_ValveBase_instantiates():
    assert(valve.ValveBase("TEST"))

@pytest.mark.timeout(tmo)
def test_ValveBase_runs_ophyd_functions():
    v = valve.ValveBase("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("m", ["move", "mv", "set"])    
@pytest.mark.parametrize("pos", ["OPEN", "CLOSE", 1, 0])
def test_ValveBase_moves_properly(pos, m):
    v = valve.ValveBase("TEST")
    status = getattr(v, m)(pos)
    assert(status.success)
    if pos == 1 or pos == "OPEN":
        assert(v.command.value == 1)
    else:
        assert(v.command.value == 0)

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("pos", ["OPN", 5.0, -10, True])            
def test_ValveBase_move_raises_ValueError_on_invalid_positions(pos):
    v = valve.ValveBase("TEST")
    with pytest.raises(ValueError):
        status = v.move(pos)

@pytest.mark.timeout(tmo)
def test_ValveBase_open_method():
    v = valve.ValveBase("TEST")
    status = v.open()
    assert(status.success)
    assert(v.command.value == 1)

@pytest.mark.timeout(tmo)
def test_ValveBase_close_method():
    v = valve.ValveBase("TEST")
    status = v.close()
    assert(status.success)
    assert(v.command.value == 0)

@pytest.mark.timeout(tmo)
def test_ValveBase_does_not_open_when_interlocked():
    v = valve.ValveBase("TEST")
    v.interlock.value = 1
    with pytest.raises(InterlockError):
        status = v.move(1)
    
# PositionValve        

@pytest.mark.timeout(tmo)
def test_PositionValve_instantiates():
    assert(valve.PositionValve("TEST"))

@pytest.mark.timeout(tmo)
def test_PositionValve_runs_ophyd_functions():
    v = valve.PositionValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

@pytest.mark.timeout(tmo)
def test_PositionValve_position_reads_correctly():
    v = valve.PositionValve("TEST")
    v.move("CLOSE")
    assert(v.position == 0)    
    v.move("OPEN")
    assert(v.position == 1)
    
# BypassValve

@pytest.mark.timeout(tmo)
def test_BypassValve_instantiates():
    assert(valve.BypassValve("TEST"))

@pytest.mark.timeout(tmo)
def test_BypassValve_runs_ophyd_functions():
    v = valve.BypassValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

def test_BypassValve_bypass_attrs_work_correctly():
    v = valve.BypassValve("TEST")
    v.bypass = True
    assert(v.bypass == True)
    v.bypass = False
    assert(v.bypass == False)
    
# OverrideValve

@pytest.mark.timeout(tmo)
def test_OverrideValve_instantiates():
    assert(valve.OverrideValve("TEST"))

@pytest.mark.timeout(tmo)
def test_OverrideValve_runs_ophyd_functions():
    v = valve.OverrideValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

def test_OverrideValve_override_attrs_work_correctly():
    v = valve.OverrideValve("TEST")
    v.override = True
    assert(v.override == True)
    v.override = False
    assert(v.override == False)

# N2CutoffValve

@pytest.mark.timeout(tmo)
def test_N2CutoffValve_instantiates():
    assert(valve.N2CutoffValve("TEST"))

@pytest.mark.timeout(tmo)
def test_N2CutoffValve_runs_ophyd_functions():
    v = valve.N2CutoffValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

# ApertureValve

@pytest.mark.timeout(tmo)
def test_ApertureValve_instantiates():
    assert(valve.ApertureValve("TEST"))

@pytest.mark.timeout(tmo)
def test_ApertureValve_runs_ophyd_functions():
    v = valve.ApertureValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))
    
# ReadbackValve

@pytest.mark.timeout(tmo)
def test_ReadbackValve_instantiates():
    assert(valve.ReadbackValve("TEST"))

@pytest.mark.timeout(tmo)
def test_ReadbackValve_runs_ophyd_functions():
    v = valve.ReadbackValve("TEST")
    assert(isinstance(v.read(), OrderedDict))
    assert(isinstance(v.describe(), OrderedDict))
    assert(isinstance(v.describe_configuration(), OrderedDict))
    assert(isinstance(v.read_configuration(), OrderedDict))

    
