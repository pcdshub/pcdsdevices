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
