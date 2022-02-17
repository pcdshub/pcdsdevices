import logging
import threading
from unittest.mock import Mock

import pytest
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.sim import FakeEpicsSignal

from .. import signal as signal_module
from ..signal import (AvgSignal, PytmcSignal, SignalEditMD,
                      UnitConversionDerivedSignal)

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
    assert avg.get() == 1
    sig.put(3)
    assert avg.get() == 2
    sig.put(2)
    assert avg.get() == 2.5

    avg.averages = 3

    sig.put(1)
    assert avg.get() == 1
    sig.put(3)
    assert avg.get() == 2
    sig.put(2)
    assert avg.get() == 2

    cb = Mock()
    avg.subscribe(cb)
    sig.put(0)
    assert cb.called


class MockCallbackHelper:
    """
    Simple helper for getting a callback, setting an event, and checking args.

    Use __call__ as the hook and inspect/verify ``mock`` or ``call_kwargs``.
    """

    def __init__(self):
        self.event = threading.Event()
        self.mock = Mock()

    def __call__(self, *args, **kwargs):
        self.mock(*args, **kwargs)
        self.event.set()

    def wait(self, timeout=1.0):
        """Wait for the callback to be called."""
        self.event.wait(timeout)

    @property
    def call_kwargs(self):
        """Call keyword arguments."""
        _, kwargs = self.mock.call_args
        return kwargs


@pytest.fixture(scope='function')
def unit_conv_signal():
    orig = FakeEpicsSignal('sig', name='orig')
    if 'units' not in orig.metadata_keys:
        # HACK: This will need to be fixed upstream in ophyd as part of
        # upstreaming UnitConversionDerivedSignal
        orig._metadata_keys = orig.metadata_keys + ('units', )

    orig.sim_put(5)

    return UnitConversionDerivedSignal(
        derived_from=orig,
        original_units='m',
        derived_units='mm',
        name='converted',
    )


def test_unit_conversion_signal_units(unit_conv_signal):
    assert unit_conv_signal.original_units == 'm'
    assert unit_conv_signal.derived_units == 'mm'
    assert unit_conv_signal.describe()[unit_conv_signal.name]['units'] == 'mm'


def test_unit_conversion_signal_get_put(unit_conv_signal):
    assert unit_conv_signal.get() == 5_000
    unit_conv_signal.put(10_000, wait=True)
    assert unit_conv_signal.derived_from.get() == 10


def test_unit_conversion_signal_value_sub(unit_conv_signal):
    helper = MockCallbackHelper()
    unit_conv_signal.subscribe(helper, run=False)
    unit_conv_signal.derived_from.put(20, wait=True)
    helper.wait(1)
    helper.mock.assert_called_once()

    assert helper.call_kwargs['value'] == 20_000
    assert unit_conv_signal.get() == 20_000


def test_unit_conversion_signal_metadata_sub(unit_conv_signal):
    helper = MockCallbackHelper()
    unit_conv_signal.subscribe(helper, run=True, event_type='meta')
    helper.wait(1)
    helper.mock.assert_called_once()
    assert helper.call_kwargs['units'] == 'mm'


def test_optional_epics_signal(monkeypatch):
    monkeypatch.setattr(signal_module, 'EpicsSignal', FakeEpicsSignal)
    opt = signal_module._OptionalEpicsSignal('test', name='opt')

    opt._epics_signal.put(123)

    # 1. Prior to connection: use internal value
    assert not opt.should_use_epics_signal()
    opt.put(1)
    assert opt.get() == 1
    opt.wait_for_connection()

    # 2. Simulate a connection callback:
    opt._epics_signal._run_subs(sub_type='meta', connected=True)
    # After connection: use the fake epics signal
    assert opt.should_use_epics_signal()
    assert opt.get() == 123

    st = opt.set(45)
    st.wait(timeout=1)

    assert opt.get() == 45

    opt._epics_signal.precision = 10
    assert opt.precision == 10

    opt._epics_signal._metadata['connected'] = False
    opt._epics_signal._run_subs(sub_type='meta', connected=False)

    # If disconnected, we still should use the EPICS signal
    assert opt.should_use_epics_signal()
    # And reflect its disconnected status:
    assert not opt.connected


def test_pvnotepad_signal(monkeypatch):
    monkeypatch.setattr(signal_module, 'EpicsSignal', FakeEpicsSignal)
    sig = signal_module.NotepadLinkedSignal(
        read_pv='__abc123',
        attr_name='sig',  # pretend this was created with a component
        name='sig',
        notepad_metadata={'my': 'metadata'},
    )
    assert sig.notepad_metadata['dotted_name'] == 'sig'
    assert sig.notepad_metadata['read_pv'] == '__abc123'
    assert sig.notepad_metadata['my'] == 'metadata'
    # PV obviously will not connect:
    assert not sig.should_use_epics_signal()
    sig.destroy()


def test_editmd_signal():
    sig = SignalEditMD(name='sig')
    cache = {}
    ev = threading.Event()

    def add_call(*args, **kwargs):
        cache.update(**kwargs)
        ev.set()

    sig.subscribe(add_call, event_type=sig.SUB_META)

    assert sig.metadata['precision'] is None
    assert not cache
    ev.clear()
    sig._override_metadata(precision=4)
    assert sig.metadata['precision'] == 4
    # Metadata updates are threaded! Need to wait a moment!
    ev.wait(timeout=1)
    assert cache['precision'] == 4
