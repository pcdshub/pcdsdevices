import logging
from unittest.mock import Mock

import pytest
from ophyd.device import Component as Cpt
from ophyd.signal import Signal
from ophyd.sim import make_fake_device

from ..state import (PVStatePositioner, StatePositioner, StateRecordPositioner,
                     StateStatus)

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
    def _do_move(self, value):
        state = value.name
        if state == 'in':
            self.highlim.put(1)
            self.lowlim.put(0)
        elif state == 'out':
            self.highlim.put(0)
            self.lowlim.put(1)


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


def test_pvstate_positioner_describe():
    logger.debug('test_pvstate_positioner_describe')
    lim_obj = LimCls('BASE', name='test')
    # No smoke please
    desc = lim_obj.state.describe()[lim_obj.state.name]
    assert len(desc['enum_strs']) == 3  # In, Out, Unknown
    assert desc['dtype'] == 'string'


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


def test_basic_subscribe():
    logger.debug('test_basic_subscribe')
    lim_obj = LimCls('BASE', name='test')
    cb = Mock()
    lim_obj.subscribe(cb, run=False)
    lim_obj.lowlim.put(1)
    lim_obj.highlim.put(1)
    lim_obj.highlim.put(0)
    assert cb.called


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
