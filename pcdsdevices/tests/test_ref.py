import logging

import pytest

from ..ref import ReflaserL2SI

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_ref_disconnected():
    logger.debug('test_ref_disconnected')
    ReflaserL2SI('TST:WFS', name='tst')
