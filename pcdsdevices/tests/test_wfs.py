import logging

import pytest

from ..wfs import WaveFrontSensorTarget

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_wfs_disconnected():
    logger.debug('test_wfs_disconnected')
    WaveFrontSensorTarget('TST:WFS', name='tst')
