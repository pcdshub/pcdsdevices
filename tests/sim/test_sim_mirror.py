############
# Standard #
############
import time
from collections import OrderedDict

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
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
    assert(np.isclose(t1, ommotor.settle_time + 0.1, rtol=0.1))
    assert(ommotor.position == 1)
    assert(status.success)
    
# OffsetMirror tests

def test_OffsetMirror_instantiates():
    assert(OffsetMirror("TEST"))

def test_OffsetMirror_motors_all_read():
    om = OffsetMirror("TEST")
    assert(isinstance(om.gan_x_p.read(), OrderedDict))
    assert(isinstance(om.gan_x_s.read(), OrderedDict))
    assert(isinstance(om.gan_y_p.read(), OrderedDict))
    assert(isinstance(om.gan_y_s.read(), OrderedDict))
    assert(isinstance(om.pitch.read(), OrderedDict))

def test_OffsetMirror_runs_ophyd_functions():
    om = OffsetMirror("TEST")
    assert(isinstance(om.read(), OrderedDict))
    assert(isinstance(om.describe(), OrderedDict))
    assert(isinstance(om.describe_configuration(), OrderedDict))
    assert(isinstance(om.read_configuration(), OrderedDict))

def test_OffsetMirror_move_method():
    om = OffsetMirror("TEST")
    om.move(10)
    assert(om.position == 10)
    assert(om.pitch.position == 10)

def test_OffsetMirror_noise():
    om = OffsetMirror("TEST", x=5, y=10, z=15, alpha=20, noise_x=0.1, 
                      noise_y=0.1, noise_z=0.1, noise_alpha=0.1)
    assert(om.sim_x.value != 5 and np.isclose(om.sim_x.value, 5, atol=0.1))
    assert(om.sim_y.value != 10 and np.isclose(om.sim_y.value, 10, atol=0.1))
    assert(om.sim_z.value != 15 and np.isclose(om.sim_z.value, 15, atol=0.1))
    assert(om.sim_alpha.value != 20 and np.isclose(om.sim_alpha.value, 20, 
                                                   atol=0.1))

def test_OffsetMirror_noise_changes_on_every_read():
    om = OffsetMirror("TEST", x=5, y=5, z=5, alpha=5, noise_x=0.1, noise_y=0.1, 
                      noise_z=0.1, noise_alpha=0.1)
    x_vals = [om.sim_x.value for i in range(10)]
    assert(len(x_vals) == len(set(x_vals)))
    y_vals = [om.sim_y.value for i in range(10)]
    assert(len(y_vals) == len(set(y_vals)))
    z_vals = [om.sim_z.value for i in range(10)]
    assert(len(z_vals) == len(set(z_vals)))
    alpha_vals = [om.sim_alpha.value for i in range(10)]
    assert(len(alpha_vals) == len(set(alpha_vals)))
    

    
    
    
