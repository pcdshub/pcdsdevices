import pytest

# modules under test
from pcdsdevices.lamp_motion import LAMP, LAMPMagneticBottle

MOTOR1 = 'TMO:LAMP:MMS:01'
MOTOR2 = 'TMO:LAMP:MMS:02'
MOTOR3 = 'TMO:LAMP:MMS:03'
MOTOR4 = 'TMO:LAMP:MMS:04'
MOTOR5 = 'TMO:LAMP:MMS:05'
MOTOR6 = 'TMO:LAMP:MMS:06'
MOTOR7 = 'TMO:LAMP:MMS:07'
MOTOR8 = 'TMO:LAMP:MMS:08'
MOTOR9 = 'TMO:LAMP:MMS:09'
MOTOR10 = 'TMO:LAMP:MMS:10'

def test_lamp():
    """Make sure we have assigned correct motors pvs we expect"""
    lamp = LAMP(prefix='TMO:LAMP', name='test')
    assert getattr(lamp, 'gas_jet_x').prefix == MOTOR1
    assert getattr(lamp, 'gas_jet_y').prefix == MOTOR2
    assert getattr(lamp, 'gas_jet_z').prefix == MOTOR3
    assert getattr(lamp, 'gas_needle_x').prefix == MOTOR4
    assert getattr(lamp, 'gas_needle_y').prefix == MOTOR5
    assert getattr(lamp, 'gas_needle_z').prefix == MOTOR6
    assert getattr(lamp, 'sample_paddle_x').prefix == MOTOR7
    assert getattr(lamp, 'sample_paddle_y').prefix == MOTOR8
    assert getattr(lamp, 'sample_paddle_z').prefix == MOTOR9

def test_lamp_magnetic_bottle():
    """Make sure we have assigned correct motors pvs we expect"""
    lamp = LAMPMagneticBottle(prefix='TMO:LAMP', name='test')
    assert getattr(lamp, 'gas_needle_x').prefix == MOTOR2
    assert getattr(lamp, 'gas_needle_y').prefix == MOTOR1
    assert getattr(lamp, 'gas_needle_z').prefix == MOTOR3
    assert getattr(lamp, 'gas_needle_theta').prefix == MOTOR10
    assert getattr(lamp, 'magnet_x').prefix == MOTOR5
    assert getattr(lamp, 'magnet_y').prefix == MOTOR6
    assert getattr(lamp, 'magnet_z').prefix == MOTOR4

