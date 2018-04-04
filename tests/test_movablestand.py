import logging

import pytest

from pcdsdevices.movablestand import MovableStand
from pcdsdevices.sim.pv import using_fake_epics_pv

logger = logging.getLogger(__name__)


def fake_stand():
    stand = MovableStand('STAND:NAME', name='stand')
    stand.wait_for_connection()
    return stand


@using_fake_epics_pv
def test_movablestand_sanity():
    logger.debug('test_movablestand_sanity')
    stand = fake_stand()
    with pytest.raises(NotImplementedError):
        stand.move('OUT')
