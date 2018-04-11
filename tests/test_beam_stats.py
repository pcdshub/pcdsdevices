import logging

from pcdsdevices.beam_stats import BeamStats
from pcdsdevices.sim import using_fake_epics_pv

logger = logging.getLogger(__name__)


@using_fake_epics_pv
def test_beam_stats():
    logger.debug('test_beam_stats')
    stats = BeamStats()
    stats.read()
    stats.hints
