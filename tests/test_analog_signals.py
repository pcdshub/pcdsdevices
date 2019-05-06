import logging
import pytest

from ophyd.sim import make_fake_device
from pcdsdevices.analog_signals import Acromag

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_acromag():
    FakeAcromag = make_fake_device(Acromag)
    acromag = FakeAcromag('Test:Acromag', name='test_acromag')
    return acromag


def test_fixture_setup(fake_acromag):
    pass
