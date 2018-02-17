import time
from collections import OrderedDict

import pytest
import numpy as np
from ophyd.utils import LimitError

from pcdsdevices.sim.mirror import (OMMotor, OffsetMirror)

# OMMotor Tests

def test_OMMotor_instantiates():
    assert(OMMotor("TEST"))

def test_OMMotor_runs_ophyd_functions():
    ommotor = OMMotor("TEST")
    assert(isinstance(ommotor.read(), OrderedDict))
    assert(isinstance(ommotor.describe(), OrderedDict))
    assert(isinstance(ommotor.describe_configuration(), OrderedDict))
    assert(isinstance(ommotor.read_configuration(), OrderedDict))

def test_OMMotor_moves_properly():
    ommotor = OMMotor("TEST")
    status = ommotor.move(10)
    assert(ommotor.position == 10)
    assert(status.success)
    
def test_OMMotor_velocity_move_time():
    ommotor = OMMotor("TEST")
    diff = 1
    next_pos = ommotor.position + diff
    ommotor.velocity.put(0.5)    
    t0 = time.time()
    status = ommotor.move(next_pos)
    t1 = time.time() - t0
    assert(np.isclose(t1, diff/ommotor.velocity.value  + 0.1, rtol=0.1))
    assert(ommotor.position == next_pos)
    assert(status.success)

def test_OMMotor_settle_time():
    ommotor = OMMotor("TEST", settle_time=1)
    t0 = time.time()
    status = ommotor.move(1)
    t1 = time.time() - t0
    assert(np.isclose(t1, ommotor.settle_time,  rtol=0.1))
    assert(ommotor.position == 1)
    assert(status.success)

def test_OMMotor_raises_value_error_on_invalid_positions():
    ommotor = OMMotor("TEST")
    with pytest.raises(ValueError):   
        ommotor.move(None)
    with pytest.raises(ValueError):   
        ommotor.move(np.nan)
    with pytest.raises(ValueError):   
        ommotor.move(np.inf)

def test_OMMotor_raises_limit_error_on_oob_positions():
    ommotor = OMMotor("TEST")
    ommotor.limits = (-10, 10)
    with pytest.raises(ValueError):   
        ommotor.move(-11)
    with pytest.raises(ValueError):   
        ommotor.move(11)
    assert(ommotor.move(0))
    
# OffsetMirror tests

def test_OffsetMirror_instantiates():
    assert(OffsetMirror("TEST", "TEST_XY"))

def test_OffsetMirror_motors_all_read():
    om = OffsetMirror("TEST", "TEST_XY")
    assert(isinstance(om.gan_x_p.read(), OrderedDict))
    assert(isinstance(om.gan_y_p.read(), OrderedDict))
    assert(isinstance(om.pitch.read(), OrderedDict))

def test_OffsetMirror_runs_ophyd_functions():
    om = OffsetMirror("TEST", "TEST_XY")
    assert(isinstance(om.read(), OrderedDict))
    assert(isinstance(om.describe(), OrderedDict))
    assert(isinstance(om.describe_configuration(), OrderedDict))
    assert(isinstance(om.read_configuration(), OrderedDict))

def test_OffsetMirror_move_method():
    om = OffsetMirror("TEST", "TEST_XY")
    om.move(10)
    assert(om.position == 10)
    assert(om.pitch.position == 10)

def test_OffsetMirror_noise():
    om = OffsetMirror("TEST", "TEST_XY", x=5, y=10, z=15, alpha=20, 
                      noise_x=True, noise_y=True, noise_z=True, 
                      noise_alpha=True, noise_kwargs={"scale":0.25}, 
                      noise_type="uni")
    # import ipdb; ipdb.set_trace()
    assert(om.sim_x.value != 5 and np.isclose(om.sim_x.value, 5, atol=0.25))
    assert(om.sim_y.value != 10 and np.isclose(om.sim_y.value, 10, atol=0.25))
    assert(om.sim_z.value != 15 and np.isclose(om.sim_z.value, 15, atol=0.25))
    assert(om.sim_alpha.value != 20 and np.isclose(om.sim_alpha.value, 20, 
                                                   atol=0.25))

def test_OffsetMirror_noise_changes_on_every_read():
    om = OffsetMirror("TEST", "TEST_XY", x=5, y=5, z=5, alpha=5, noise_x=0.1, 
                      noise_y=0.1, noise_z=0.1, noise_alpha=0.1)
    x_vals = [om.sim_x.value for i in range(10)]
    assert(len(x_vals) == len(set(x_vals)))
    y_vals = [om.sim_y.value for i in range(10)]
    assert(len(y_vals) == len(set(y_vals)))
    z_vals = [om.sim_z.value for i in range(10)]
    assert(len(z_vals) == len(set(z_vals)))
    alpha_vals = [om.sim_alpha.value for i in range(10)]
    assert(len(alpha_vals) == len(set(alpha_vals)))    

def test_OffsetMirror_raises_value_error_on_invalid_positions():
    om = OffsetMirror("TEST", "TEST_XY")
    with pytest.raises(ValueError):   
        om.move(None)
    with pytest.raises(ValueError):   
        om.move(np.nan)
    with pytest.raises(ValueError):   
        om.move(np.inf)

def test_OffsetMirror_raises_limit_error_on_oob_positions():
    om = OffsetMirror("TEST", "TEST_XY")
    om.limits = (-10, 10)
    with pytest.raises(ValueError):   
        om.move(-11)
    with pytest.raises(ValueError):   
        om.move(11)
    assert(om.move(0))

def test_OffsetMirror_timeout():
    tmo = 1.0
    om = OffsetMirror("TEST", "TEST_XY", timeout=tmo)
    om.move(42)
    assert(om.pitch.timeout == tmo)
