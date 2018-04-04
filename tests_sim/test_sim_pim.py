import time
from collections import OrderedDict
import pytest

import numpy as np

from pcdsdevices.sim.pim import (PIMPulnixDetector, PIMMotor, PIM)

# PIMPulnixDetector Tests

def test_PIMPulnixDetector_instantiates():
    assert(PIMPulnixDetector("TEST", name="test"))

def test_PIMPulnixDetector_runs_ophyd_functions():
    pim_pdet = PIMPulnixDetector("TEST", name="test")
    assert(isinstance(pim_pdet.read(), OrderedDict))
    assert(isinstance(pim_pdet.describe(), OrderedDict))
    assert(isinstance(pim_pdet.describe_configuration(), OrderedDict))
    assert(isinstance(pim_pdet.read_configuration(), OrderedDict))

def test_PIMPulnixDetector_stats_plugin_reads():
    pim_pdet = PIMPulnixDetector("TEST", name="test")
    assert(isinstance(pim_pdet.stats2.read(), OrderedDict))

def test_PIMPulnixDetector_centroid_noise():
    pim_pdet = PIMPulnixDetector("TEST", name="test", noise_x=5, noise_y=20)
    pim_pdet.stats2.centroid.x.put(300)
    pim_pdet.stats2.centroid.y.put(400)
    test_x = 300 + int(np.round(np.random.uniform(-1,1)*5))
    test_y = 400 + int(np.round(np.random.uniform(-1,1)*20))
    assert(pim_pdet.centroid_x == test_x or 
           np.isclose(pim_pdet.centroid_x, 300, atol=5))
    assert(pim_pdet.centroid_y == test_y or 
           np.isclose(pim_pdet.centroid_y, 400, atol=20))
    
def test_PIMPulnixDetector_centroid_override():
    pim_pdet = PIMPulnixDetector("TEST", name="test")
    def centroid_override_x():
        val = pim_pdet.stats2.centroid.x._raw_readback + (
          pim_pdet.stats2.centroid.x._raw_readback or 5)
        pim_pdet.stats2.centroid.x._raw_readback = val
        return val
    pim_pdet._get_readback_centroid_x = centroid_override_x    
    assert(pim_pdet.centroid_x == 5)
    assert(pim_pdet.centroid_x == 10)
    assert(pim_pdet.centroid_x == 20)
    def centroid_override_y():
        val = pim_pdet.stats2.centroid.y._raw_readback - (
          pim_pdet.stats2.centroid.y._raw_readback or -3)
        pim_pdet.stats2.centroid.y._raw_readback = val
        return val
    pim_pdet._get_readback_centroid_y = centroid_override_y
    assert(pim_pdet.centroid_y == 3)
    assert(pim_pdet.centroid_y == 0)
    assert(pim_pdet.centroid_y == 3)

def test_PIMPulnixDetector_zeros_centroid_outside_yag():
    pim_pdet = PIMPulnixDetector("TEST", name="test", zero_outside_yag=True)
    pim_pdet.stats2.centroid.x.put(300)
    pim_pdet.stats2.centroid.y.put(400)
    assert(pim_pdet.centroid_x == 300)
    assert(pim_pdet.centroid_y == 400)
    # Left side
    pim_pdet.stats2.centroid.x.put(-100)
    assert(pim_pdet.centroid_x == 0)
    assert(pim_pdet.centroid_y == 0)
    # Reset
    pim_pdet.stats2.centroid.x.put(300)
    assert(pim_pdet.centroid_x == 300)
    assert(pim_pdet.centroid_y == 400)
    # Right side
    pim_pdet.stats2.centroid.x.put(pim_pdet.cam.size.size_x.value + 100)
    assert(pim_pdet.centroid_x == 0)
    assert(pim_pdet.centroid_y == 0)
    # Reset
    pim_pdet.stats2.centroid.x.put(300)
    assert(pim_pdet.centroid_x == 300)
    assert(pim_pdet.centroid_y == 400)
    # Below
    pim_pdet.stats2.centroid.y.put(-100)
    assert(pim_pdet.centroid_x == 0)
    assert(pim_pdet.centroid_y == 0)
    # Reset
    pim_pdet.stats2.centroid.y.put(400)
    assert(pim_pdet.centroid_x == 300)
    assert(pim_pdet.centroid_y == 400)
    # Right side
    pim_pdet.stats2.centroid.y.put(pim_pdet.cam.size.size_y.value + 200)
    assert(pim_pdet.centroid_x == 0)
    assert(pim_pdet.centroid_y == 0)
    # Reset
    pim_pdet.stats2.centroid.y.put(400)
    assert(pim_pdet.centroid_x == 300)
    assert(pim_pdet.centroid_y == 400)
    
# PIMMotor Tests

def test_PIMMotor_instantiates():
    assert(PIMMotor("TEST", name="test"))

def test_PIMMotor_runs_ophyd_functions():
    pmotor = PIMMotor("TEST", name="test")
    assert(isinstance(pmotor.read(), OrderedDict))
    assert(isinstance(pmotor.describe(), OrderedDict))
    assert(isinstance(pmotor.describe_configuration(), OrderedDict))
    assert(isinstance(pmotor.read_configuration(), OrderedDict))

def test_PIMMotor_transitions_states_correctly():
    pmotor = PIMMotor("TEST", name="test")
    status = pmotor.move("OUT")
    assert(pmotor.position == "OUT")
    assert(status.success)
    status = pmotor.move("IN")
    assert(pmotor.position == "IN")
    assert(status.success)
    status = pmotor.move("DIODE")
    assert(pmotor.position == "DIODE")
    assert(status.success)

def test_PIMMotor_noise_on_read():
    pmotor = PIMMotor("TEST", name="test", pos_in=5, noise=True, noise_kwargs={'scale':0.1})
    status = pmotor.move("IN")
    assert(status.success)
    assert(pmotor._pos.value !=  5 and np.isclose(
        pmotor._pos.value, 5, atol=0.1))

def test_PIMMotor_noise_changes_every_read():
    pmotor = PIMMotor("TEST", name="test", pos_in=5, noise=True, noise_kwargs={'scale':0.1})
    status = pmotor.move("IN")
    assert(status.success)
    pos = [pmotor._pos.value for i in range(10)]
    assert(len(pos) == len(set(pos)))

# PIM Tests

def test_PIM_instantiates():
    assert(PIM("TEST", name="test"))

def test_PIM_runs_ophyd_functions():
    pim = PIM("TEST", name="test")
    assert(isinstance(pim.read(), OrderedDict))
    assert(isinstance(pim.describe(), OrderedDict))
    assert(isinstance(pim.describe_configuration(), OrderedDict))
    assert(isinstance(pim.read_configuration(), OrderedDict))
    
def test_PIM_has_centroid():
    pim = PIM("TEST", name="test")
    assert(isinstance(pim.detector.stats2.centroid.x.read(), dict))
    assert(isinstance(pim.detector.stats2.centroid.y.read(), dict))
    
def test_PIM_settle_time():
    pim = PIM("TEST", name="test")
    pim.move("OUT")
    pim.settle_time = 1
    t0 = time.time()
    status = pim.move("IN")
    t1 = time.time() - t0
    assert(np.isclose(t1, pim.settle_time + 0.1, rtol=0.1))
    assert(pim.position == "IN")
    assert(status.success)

def test_PIM_noise():
    pim = PIM("TEST", name="test", y=5, noise=True, noise_kwargs={'scale':0.1})
    status = pim.move("IN")
    assert(status.success)
    assert(pim.sim_y.value != 5 and np.isclose(pim.sim_y.value, 5, atol=0.1))

def test_PIMMotor_stage():
    pim = PIMMotor("TEST", name="test", pos_in=5)
    pim.move_out(wait=True)
    pim.stage()
    assert(pim.position == "OUT")
    pim.move_in(wait=True)
    assert(pim.position == "IN")
    pim.unstage()
    time.sleep(0.2)
    assert(pim.position == "OUT")

@pytest.mark.skipif(True, reason="No proper states sim class yet")
def test_PIM_timeout():
    tmo = 1.0
    pim = PIM("TEST", name="test", timeout=tmo)
    pim.move_in()
    assert(pim.states.timeout == tmo)
