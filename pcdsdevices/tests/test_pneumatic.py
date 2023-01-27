import pytest
from ophyd.sim import make_fake_device

from ..pneumatic import BeckhoffPneumatic


@pytest.fixture(scope='function')
def fake_stopper():
    FakeStopper = make_fake_device(BeckhoffPneumatic)
    stopper = FakeStopper('TST:ST1', name="Test Stopper")
    stopper.insert_ok.sim_put(1)
    stopper.retract_ok.sim_put(1)
    stopper.done.sim_put(1)
    stopper.error.sim_put(0)
    return stopper


def test_stopper_inserted(fake_stopper):
    status = fake_stopper.insert(wait=True)
    assert status.success
    assert status.done


def test_stopper_removed(fake_stopper):
    status = fake_stopper.remove(wait=True)
    assert status.success
    assert status.done
