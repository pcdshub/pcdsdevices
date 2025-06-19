import pytest
from ophyd.sim import make_fake_device

from pcdsdevices.slits import SL2K4Slits

FakeSL2K4Slits = make_fake_device(SL2K4Slits)


@pytest.fixture
def fake_slits():
    FakeSlits = make_fake_device(SL2K4Slits)
    return FakeSlits(prefix='SL2K4:SCATTER', cam='IM6K4:PPM:CAM',
                     data_source='IMAGE2',
                     name='sl2k4_slits')


def test_slits_initialization(fake_slits):
    sp = 4.0
    fake_slits.xwidth.setpoint.put(sp)
    xwidth_sp = fake_slits.xwidth.setpoint.get()
    assert pytest.approx(xwidth_sp, 0.1) == sp
