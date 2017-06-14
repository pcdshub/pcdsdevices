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

def test_OMMotor_fake_sleep_move_time():
    ommotor = OMMotor("TEST")
    diff = 1
    next_pos = ommotor.position + diff
    ommotor.velocity.put(0)    
    ommotor.fake_sleep = 1
    t0 = time.time()
    status = ommotor.move(next_pos)
    t1 = time.time() - t0
    assert(np.isclose(t1, ommotor.fake_sleep + 0.1, rtol=0.1))
    assert(ommotor.position == next_pos)
    assert(status.success)

def test_OMMotor_noise_on_read():
    ommotor = OMMotor("TEST", noise=0.1)
    status = ommotor.move(5)
    assert(status.success)
    assert(ommotor.user_setpoint.value == 5)
    assert(ommotor.position !=  5 and np.isclose(ommotor.position, 5, atol=0.1))
    assert(ommotor.read()['TEST']['value'] !=  5 and np.isclose(
        ommotor.read()['TEST']['value'], 5, atol=0.1))

def test_OMMotor_noise_changes_every_read():
    ommotor = OMMotor("TEST", noise=0.1)
    status = ommotor.move(5)
    assert(status.success)
    pos = [ommotor.position for i in range(10)]
    assert(len(pos) == len(set(pos)))
    read = [ommotor.read()['TEST']['value']]
    assert(len(read) == len(set(read)))
    
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
    om = OffsetMirror("TEST", x=5, y=5, z=5, alpha=5, noise_x=0.1, noise_y=0.1, 
                      noise_z=0.1, noise_alpha=0.1)
    assert(om._x != 5 and np.isclose(om._x, 5, atol=0.1))
    assert(om._y != 5 and np.isclose(om._y, 5, atol=0.1))
    assert(om._z != 5 and np.isclose(om._z, 5, atol=0.1))
    assert(om._alpha != 5 and np.isclose(om._alpha, 5, atol=0.1))
    for key in om.read().keys():
        assert(om.read()[key]['value'] != 5 and np.isclose(
            om.read()[key]['value'], 5, atol=0.1))

def test_OffsetMirror_noise_changes_on_every_read():
    om = OffsetMirror("TEST", x=5, y=5, z=5, alpha=5, noise_x=0.1, noise_y=0.1, 
                      noise_z=0.1, noise_alpha=0.1)
    reads = [om.read() for i in range(10)]
    # Check read vars (x and alpha)
    for key in reads[0].keys():
        vals = [reads[i][key]['value'] for i in range(len(reads))]
        assert(len(vals) == len(set(vals)))
    # Check y and z
    y_vals = [om._y for i in range(10)]
    assert(len(y_vals) == len(set(y_vals)))
    z_vals = [om._z for i in range(10)]
    assert(len(z_vals) == len(set(z_vals)))
    

    
    
    
