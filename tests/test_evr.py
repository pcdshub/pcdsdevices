from ophyd.sim import make_fake_device
import pytest

from pcdsdevices.device_types import Trigger


@pytest.fixture(scope='function')
def fake_trigger():
    cls = make_fake_device(Trigger)
    return cls('TST:EVR:TRIGA', name='trig_a')


def test_enable(fake_trigger):
    fake_trigger.enable()
    assert fake_trigger.enable_cmd.get() == 1
    fake_trigger.disable()
    assert fake_trigger.enable_cmd.get() == 0
