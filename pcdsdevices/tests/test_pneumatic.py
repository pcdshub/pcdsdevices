import pytest
from ophyd.sim import make_fake_device

from ..pneumatic import BeckhoffPneumatic


@pytest.fixture(scope='function')
def fake_stopper():
    FakeStopper = make_fake_device(BeckhoffPneumatic)
    stopper = FakeStopper('TST:ST1', name="Test Stopper")
    stopper.insert_ok.sim_put(1)
    stopper.retract_ok.sim_put(1)
    return stopper


def test_stopper_inserted(fake_stopper):
    status = fake_stopper.insert()
    assert status.success
    assert status.done
    assert fake_stopper.limit_switch_in
    assert not fake_stopper.limit_switch_out


def test_stopper_removed(fake_stopper):
    status = fake_stopper.remove()
    assert status.success
    assert status.done
    assert fake_stopper.limit_switch_out
    assert not fake_stopper.limit_switch_in
