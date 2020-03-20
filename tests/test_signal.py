import logging
from unittest.mock import Mock

from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from pcdsdevices.signal import AvgSignal, PytmcSignal

logger = logging.getLogger(__name__)


def test_pytmc_signal():
    logger.debug('test_pytmc_signal')
    # Just make sure the normal use cases aren't super broken
    rwsig = PytmcSignal('PREFIX', io='io')
    rosig = PytmcSignal('PREFIX', io='i')
    assert isinstance(rwsig, EpicsSignal)
    assert isinstance(rwsig, PytmcSignal)
    assert isinstance(rosig, EpicsSignalRO)
    assert isinstance(rosig, PytmcSignal)


def test_avg_signal():
    logger.debug('test_avg_signal')
    sig = Signal(name='raw')
    avg = AvgSignal(sig, 2, name='avg')

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
