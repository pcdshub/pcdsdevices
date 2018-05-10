import logging
from unittest.mock import Mock

from ophyd.signal import Signal

from pcdsdevices.signal import AvgSignal

logger = logging.getLogger(__name__)


def test_avg_signal():
    logger.debug('test_avg_signal')
    sig = Signal(name='raw')
    avg = AvgSignal(sig, 2, name='avg')

    assert sig.value is None
    assert avg.value is None
    assert avg.averages == 2

    sig.put(1)
    assert avg.value == 1
    sig.put(3)
    assert avg.value == 2
    sig.put(2)
    assert avg.value == 2.5

    avg.averages = 3

    sig.put(1)
    assert avg.value == 1
    sig.put(3)
    assert avg.value == 2
    sig.put(2)
    assert avg.value == 2

    cb = Mock()
    avg.subscribe(cb)
    sig.put(0)
    assert cb.called
