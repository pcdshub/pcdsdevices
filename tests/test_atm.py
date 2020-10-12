import logging

import pytest

from pcdsdevices.atm import ArrivalTimeMonitor

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_atm_disconnected():
    logger.debug('test_atm_disconnected')
    ArrivalTimeMonitor('TST:ATM', name='tst')
