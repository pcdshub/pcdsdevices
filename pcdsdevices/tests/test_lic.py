import logging

import pytest

from ..lic import LaserInCoupling

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_lic_disconnected():
    logger.debug('test_lic_disconnected')
    LaserInCoupling('TST:WFS', name='tst')
