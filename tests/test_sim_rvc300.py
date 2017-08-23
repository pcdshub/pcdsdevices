############
# Standard #
############
import time
from collections import OrderedDict

###############
# Third Party #
###############
import pytest
import numpy as np

##########
# Module #
##########
from pcdsdevices.sim import rvc300

tmo = 10

@pytest.mark.timeout(tmo)
def test_RVC300_instantiates():
    assert(rvc300.RVC300("TEST"))

@pytest.mark.timeout(tmo)
def test_RVC300_runs_ophyd_functions():
    rvc = rvc300.RVC300("TEST")
    assert(isinstance(rvc.read(), OrderedDict))
    assert(isinstance(rvc.describe(), OrderedDict))
    assert(isinstance(rvc.describe_configuration(), OrderedDict))
    assert(isinstance(rvc.read_configuration(), OrderedDict))

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("mode", ["FLOW", "PRESS"])
@pytest.mark.parametrize("m", ["move", "mv", "set"])    
@pytest.mark.parametrize("pos", [10, 20, 30])
def test_RVC300_changes_pressure_properly(pos, m, mode):
    rvc = rvc300.RVC300("TEST")
    rvc.mode = mode
    status = getattr(rvc, m)(pos)
    assert(status.success)
    if mode == "FLOW":
        assert(rvc.position == pos*10)
    else:
        assert(rvc.position == pos)

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("pos", [-10, "TEST", True, np.nan, np.inf])
def test_RVC300_raises_ValueError_on_invalid_moves(pos):
    rvc = rvc300.RVC300("TEST")
    rvc.mode = "PRESS"
    with pytest.raises(ValueError):
        status = rvc.move(pos)

@pytest.mark.timeout(tmo)
@pytest.mark.parametrize("pos", [10, 20, 30])
def test_RVC300_pid_properties_work_correctly():
    rvc = rvc300.RVC300("TEST")
    assert(rvc.kp != 10)
    rvc.kp = 10
    assert(rvc.kp == 10)
    assert(rvc.p_gain.value == 10)
    
    assert(rvc.tn != 10)
    rvc.tn = 10
    assert(rvc.tn == 10)
    assert(rvc.reset_time.value == 10)

    assert(rvc.tv != 10)
    rvc.tv = 10
    assert(rvc.tv == 10)
    assert(rvc.derivative_time.value == 10)
    
    
    
