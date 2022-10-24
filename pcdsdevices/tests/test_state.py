import logging
import threading
from unittest.mock import Mock

import pytest
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import Signal
from ophyd.sim import make_fake_device

from ..device import UpdateComponent as UpCpt
from ..state import (TWINCAT_MAX_STATES, PVStatePositioner, StatePositioner,
                     StateRecordPositioner, StateStatus,
                     TwinCATStatePositioner, state_config_dotted_names)

logger = logging.getLogger(__name__)


class PrefixSignal(Signal):
    def __init__(self, prefix, **kwargs):
        super().__init__(**kwargs)


# Define the class
class LimCls(PVStatePositioner):
    lowlim = Cpt(PrefixSignal, 'lowlim')
    highlim = Cpt(PrefixSignal, 'highlim')

    _state_logic = {'lowlim': {0: 'in',
                               1: 'defer'},
                    'highlim': {0: 'out',
                                1: 'defer'}}

    _states_alias = {'in': 'IN', 'out': 'OUT'}


# Override the setter
class LimCls2(LimCls):
    mover = Cpt(PrefixSignal, 'mover', value=0)
    _state_logic_set_ref = 'mover'

    def _do_move(self, value):
        self.mover.put(1)
        state = value.name
        if state == 'in':
            self.highlim.put(1)
            self.lowlim.put(0)
        elif state == 'out':
            self.highlim.put(0)
            self.lowlim.put(1)
        self.mover.put(0)


# For additional tests
class IntState(StatePositioner):
    state = Cpt(PrefixSignal, 'int', value=2)
    states_list = [None, 'UNO', 'OUT']
    _states_alias = {'UNO': ['IN', 'in']}


def test_state_positioner_basic():
    logger.debug('test_state_positioner_basic')
    states = IntState('INT', name='int')
    assert states.position == 'IN'
    states.hints
    states.move(3)
    assert states.position == 'OUT'
    states.move('2')
    assert states.position == 'IN'


def test_pvstate_positioner_logic():
    """
    Make sure all the internal logic works as expected. Use fake signals
    instead of EPICS signals with live hosts.
    """
    logger.debug('test_pvstate_positioner')
    lim_obj = LimCls('BASE', name='test')

    # Check the state machine
    # Limits are defered
    lim_obj.lowlim.put(1)
    lim_obj.highlim.put(1)
    assert(lim_obj.position == 'Unknown')
    # Limits are out
    lim_obj.highlim.put(0)
    assert(lim_obj.position == 'OUT')
    # Limits are in
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    assert(lim_obj.position == 'IN')
    # Limits are in conflicting state
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(0)
    assert(lim_obj.position == 'Unknown')

    with pytest.raises(NotImplementedError):
        lim_obj.move('IN')

    lim_obj.states_enum['IN']
    lim_obj.states_enum['OUT']
    lim_obj.states_enum['Unknown']
    with pytest.raises(KeyError):
        lim_obj.states_enum['defer']
    lim_obj.destroy()


def test_pvstate_positioner_describe():
    logger.debug('test_pvstate_positioner_describe')
    lim_obj = LimCls('BASE', name='test')
    # No smoke please
    desc = lim_obj.state.describe()[lim_obj.state.name]
    assert len(desc['enum_strs']) == 3  # In, Out, Unknown
    assert desc['dtype'] == 'string'
    lim_obj.destroy()


def test_pvstate_positioner_metadata():
    logger.debug('test_pvstate_positioner_metadata')
    lim_basic = LimCls('BASE', name='lim')
    lim_mover = LimCls2('MOVER', name='mover')
    objs = (lim_basic, lim_mover)

    cache = {}
    # Need threading synchronization to avoid potential race conditions
    # Metadata callbacks run in a background thread
    events = {obj.state.name: threading.Event() for obj in objs}

    def update_md_cache(*args, obj, **kwargs):
        cache[obj.name] = kwargs
        events[obj.name].set()

    # Pick one obj to get its values prior to our sub
    lim_basic.lowlim.put(1)
    lim_basic.highlim.put(0)

    for obj in objs:
        obj.state.subscribe(
            update_md_cache,
            event_type=obj.state.SUB_META,
        )

    # Pick one obj to get its values after our sub
    lim_mover.lowlim.put(0)
    lim_mover.highlim.put(1)

    for obj in objs:
        assert events[obj.state.name].wait(timeout=1.0), 'Did not update md'
        obj_enums = tuple(obj.states_list)
        state_enums = obj.state.enum_strs
        md_enums = obj.state.metadata['enum_strs']
        cached_enum = cache[obj.state.name]['enum_strs']
        assert obj_enums == state_enums == md_enums == cached_enum

    assert lim_mover.state.metadata['write_access']
    assert lim_mover.mover.metadata['write_access']

    events[lim_mover.state.name].clear()
    lim_mover.mover._metadata['write_access'] = False
    lim_mover.mover._run_metadata_callbacks()
    events[lim_mover.state.name].wait(timeout=1.0)

    assert not lim_mover.state.metadata['write_access']
    assert not lim_mover.mover.metadata['write_access']


def test_pvstate_positioner_sets():
    logger.debug('test_pvstate_positioner_sets')
    lim_obj2 = LimCls2('BASE', name='test')
    with pytest.raises(ValueError):
        lim_obj2.move('asdfe')
    with pytest.raises(ValueError):
        lim_obj2.move('Unknown')
    cb = Mock()
    lim_obj2.move('OUT', moved_cb=cb).wait(timeout=1)
    assert(cb.called)
    assert(lim_obj2.position == 'OUT')
    lim_obj2.move('IN', wait=True)
    assert(lim_obj2.position == 'IN')

    lim_obj2.move(2)
    assert(lim_obj2.position == 'OUT')

    with pytest.raises(TypeError):
        lim_obj2.move(123.456)

    lim_obj2.state.put('IN')
    assert(lim_obj2.position == 'IN')
    lim_obj2.destroy()


def test_basic_subscribe():
    logger.debug('test_basic_subscribe')
    lim_obj = LimCls('BASE', name='test')
    cb = Mock()
    lim_obj.subscribe(cb, run=False)
    lim_obj.lowlim.put(1)
    lim_obj.highlim.put(1)
    lim_obj.highlim.put(0)

    assert len(lim_obj.state._signals) == 2
    for sig, info in lim_obj.state._signals.items():
        assert info.value_cbid is not None, f"{sig.name} not subscribed"
    assert cb.called
    lim_obj.destroy()
    for sig, info in lim_obj.state._signals.items():
        assert info.value_cbid is None, f"{sig.name} not unsubscribed"


def test_staterecord_positioner():
    """
    Nothing special can be done without live hosts, just make sure we can
    create a class and call methods for coverage.
    """
    logger.debug('test_staterecord_positioner')

    FakeState = make_fake_device(StateRecordPositioner)

    class MyStates(FakeState):
        states_list = ['YES', 'NO', 'MAYBE', 'SO']

    state = MyStates('A:PV', name='test')
    cb = Mock()
    state.subscribe(cb, event_type=state.SUB_READBACK, run=False)
    state.motor.user_readback.sim_put(1.23)
    assert cb.called
    state.destroy()


def test_state_status():
    logger.debug('test_state_status')
    lim_obj = LimCls('BASE', name='test')
    # Create a status for 'in'
    status = StateStatus(lim_obj, 'IN')
    # Put readback to 'in'
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    status.wait(timeout=1)
    assert status.done and status.success
    # Check our callback was cleared
    assert status.check_value not in lim_obj._callbacks[lim_obj.SUB_STATE]
    lim_obj.destroy()


class InconsistentState(StatePositioner):
    states_list = ['Unknown', 'IN', 'OUT']
    _states_alias = {'IN': 'OUT', 'OUT': 'IN'}


def test_state_error():
    logger.debug('test_state_error')
    with pytest.raises(ValueError):
        InconsistentState('prefix', name='bad')


def test_subcls_warning():
    logger.debug('test_subcls_warning')
    with pytest.raises(TypeError):
        StatePositioner('prefix', name='name')
    with pytest.raises(TypeError):
        PVStatePositioner('prefix', name='name')


class InOutSignal(Signal):
    _metadata_keys = (Signal._core_metadata_keys + ('enum_strs',))


class NoStatesList(StatePositioner):
    state = Cpt(InOutSignal)


def test_auto_states():
    logger.debug('test_auto_states')
    states = NoStatesList(prefix='NOSTATE', name='no_state')
    enum_strs = ('Unknown', 'IN', 'OUT')
    states.state._run_subs(sub_type=states.state.SUB_META, enum_strs=enum_strs)
    assert states.states_list == list(enum_strs)


def test_twincat_state_config_dynamic():
    logger.debug('test_twincat_state_config_dynamic')

    def check_class(cls, state_count):
        assert cls.config.kwargs['state_count'] == state_count, (
            f"Found the wrong state count for {cls}, "
            "must be some error related to UpdateComponent."
        )
        assert len(cls.state.kwargs['enum_attrs']) == state_count + 1, (
            f"Found the wrong number of enum_attrs for {cls}, something "
            "must have gone wrong in __init_subclass__."
        )

    # Check the base class first, to make sure it hasn't been broken.
    check_class(TwinCATStatePositioner, TWINCAT_MAX_STATES)

    # Make some classes that use the dynamic states and update state_count
    # We will instantiate real and fake versions

    class StandaloneStates(TwinCATStatePositioner):
        config = UpCpt(state_count=2)

    check_class(StandaloneStates, 2)

    class EmbStates(TwinCATStatePositioner):
        config = UpCpt(state_count=3)

    check_class(EmbStates, 3)

    class DeviceWithStates(Device):
        state = Cpt(EmbStates, 'TST', kind='normal')

    FakeStandaloneStates = make_fake_device(StandaloneStates)
    FakeDeviceWithStates = make_fake_device(DeviceWithStates)

    all_states = TwinCATStatePositioner('ALL:STATES', name='all_states')
    for name in state_config_dotted_names(TWINCAT_MAX_STATES):
        if name is None:
            continue
        name = name.split('.')[-2]
        assert name in all_states.config.component_names
        getattr(all_states.config, name)

    states2 = StandaloneStates('STATES2:', name='states2')
    for name in ('state01', 'state02'):
        assert name in states2.config.component_names
        getattr(states2.config, name)
    with pytest.raises(AttributeError):
        states2.config.state03

    states3 = DeviceWithStates('STATES3:', name='states3')
    for name in ('state01', 'state02', 'state03'):
        assert name in states3.state.config.component_names
        getattr(states3.state.config, name)
    with pytest.raises(AttributeError):
        states3.state.config.state04

    fake_states2 = FakeStandaloneStates('STATES2:', name='fake_states2')
    for name in ('state01', 'state02'):
        assert name in fake_states2.config.component_names
        getattr(fake_states2.config, name)
    with pytest.raises(AttributeError):
        fake_states2.config.state03

    fake_states3 = FakeDeviceWithStates('STATES3:', name='fake_states3')
    for name in ('state01', 'state02', 'state03'):
        assert name in fake_states3.state.config.component_names
        getattr(fake_states3.state.config, name)
    with pytest.raises(AttributeError):
        fake_states3.state.config.state04

    all_states.destroy()
