import logging

from pcdsdevices.beam_stats import BeamStats
from pcdsdevices.sim.pv import using_fake_epics_pv

logger = logging.getLogger(__name__)


@using_fake_epics_pv
def test_beam_stats():
    logger.debug('test_beam_stats')
    stats = BeamStats()
    stats.wait_for_connection()
    stats.read()
    stats.hints


@using_fake_epics_pv
def test_beam_stats_avg():
    logger.debug('test_beam_stats_avg')
    stats = BeamStats()
    stats.mj._read_pv.put(-1)
    stats.wait_for_connection()

    assert stats.mj_buffersize.value == 120

    stats.mj_buffersize.put(10)

    with stats.mj._read_pv._lock:
        for i in range(10):
            stats.mj._read_pv._value = i
            stats.mj._read_pv.run_callbacks()

        assert stats.mj_avg.value == sum(range(10))/10

    stats.configure(dict(mj_buffersize=20))
    cfg = stats.read_configuration()

    assert cfg['beam_stats_mj_buffersize']['value'] == 20
