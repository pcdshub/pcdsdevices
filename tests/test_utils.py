import logging

import pytest
from ophyd.device import (Device, Component as Cpt,
                          FormattedComponent as FCpt,
                          DynamicDeviceComponent as DDCpt)
from ophyd.signal import Signal, EpicsSignal, EpicsSignalRO
from ophyd.utils import ReadOnlyError, LimitError, DisconnectedError

from pcdsdevices.utils import (make_fake_class, FakeEpicsSignal,
                               FakeEpicsSignalRO)

logger = logging.getLogger(__name__)


class SampleNested(Device):
    yolk = Cpt(EpicsSignal, ':YOLK')
    whites = Cpt(EpicsSignalRO, ':WHITES')


class Sample(Device):
    egg = Cpt(SampleNested, ':EGG')
    butter = Cpt(EpicsSignal, ':BUTTER')
    flour = Cpt(EpicsSignalRO, ':FLOUR')
    sink = FCpt(EpicsSignal, '{self.sink_location}:SINK')
    fridge = DDCpt({'milk': (EpicsSignal, ':MILK', {}),
                    'cheese': (EpicsSignalRO, ':CHEESE', {})})
    nothing = Cpt(Signal)

    sink_location = 'COUNTER'


def test_make_fake_class():
    logger.debug('test_make_fake_class')
    assert make_fake_class(EpicsSignal) == FakeEpicsSignal
    assert make_fake_class(EpicsSignalRO) == FakeEpicsSignalRO

    FakeSample = make_fake_class(Sample)
    my_fake = FakeSample('KITCHEN', name='kitchen')
    assert isinstance(my_fake, Sample)

    # Skipped
    assert my_fake.nothing.__class__ is Signal

    # Normal
    assert isinstance(my_fake.butter, FakeEpicsSignal)
    assert isinstance(my_fake.flour, FakeEpicsSignalRO)
    assert isinstance(my_fake.sink, FakeEpicsSignal)

    # Nested
    assert isinstance(my_fake.egg.yolk, FakeEpicsSignal)
    assert isinstance(my_fake.egg.whites, FakeEpicsSignalRO)

    # Dynamic
    assert isinstance(my_fake.fridge.milk, FakeEpicsSignal)
    assert isinstance(my_fake.fridge.cheese, FakeEpicsSignalRO)

    my_fake.read()


def test_do_not_break_real_class():
    logger.debug('test_do_not_break_real_class')

    make_fake_class(Sample)
    assert Sample.butter.cls is EpicsSignal
    assert Sample.egg.cls is SampleNested
    assert SampleNested.whites.cls is EpicsSignalRO
    assert Sample.fridge.defn['milk'][0] is EpicsSignal

    with pytest.raises(DisconnectedError):
        my_real = Sample('KITCHEN', name='kitchen')
        my_real.read()


def test_fake_epics_signal():
    logger.debug('test_fake_epics_signals')
    sig = FakeEpicsSignal('PVNAME', name='sig', limits=True)
    sig.sim_limits((0, 10))
    with pytest.raises(LimitError):
        sig.put(11)
    sig.put(4)
    assert sig.get() == 4
    sig.sim_put(5)
    assert sig.get() == 5
    sig.sim_set_putter(lambda x: sig.sim_put(x + 1))
    sig.put(6)
    assert sig.get() == 7
    sig.sim_set_getter(lambda: 2.3)
    assert sig.get() == 2.3


def test_fake_epics_signal_ro():
    logger.debug('test_fake_epics_signal_ro')
    sig = FakeEpicsSignalRO('PVNAME', name='sig')
    with pytest.raises(ReadOnlyError):
        sig.put(3)
    with pytest.raises(ReadOnlyError):
        sig.put(4)
    with pytest.raises(ReadOnlyError):
        sig.set(5)
    sig.sim_put(1)
    assert sig.get() == 1
