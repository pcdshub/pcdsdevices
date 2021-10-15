import logging

import pytest
from ophyd.sim import make_fake_device

from ..movablestand import MovableStand

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_stand():
    FakeStand = make_fake_device(MovableStand)
    stand = FakeStand('STAND:NAME', name='stand')
    return stand


def test_movablestand_sanity(fake_stand):
    logger.debug('test_movablestand_sanity')
    with pytest.raises(NotImplementedError):
        fake_stand.move('OUT')


@pytest.mark.timeout(5)
def test_movablestand_disconnected():
    MovableStand('TST', name='tst')
