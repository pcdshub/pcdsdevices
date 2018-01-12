import pytest
import logging

from ophyd.device import Component as Cmp
from ophyd.signal import Signal

from pcdsdevices.state import (StateStatus, PVStatePositioner,
                               StateRecordPositioner)
from pcdsdevices.sim.pv import using_fake_epics_pv

logger = logging.getLogger(__name__)


class PrefixSignal(Signal):
    def __init__(self, prefix, **kwargs):
        super().__init__(**kwargs)


lim_info = dict(lowlim={0: 'IN',
                        1: 'defer'},
                highlim={0: 'OUT',
                         1: 'defer'})


# Define the class
class LimCls(PVStatePositioner):
    lowlim = Cmp(PrefixSignal, 'lowlim')
    highlim = Cmp(PrefixSignal, 'highlim')

    _state_logic = lim_info


# Override the setter
class LimCls2(LimCls):
    def _do_move(self, value):
        state = value.name
        if state == 'IN':
            self.highlim.put(1)
            self.lowlim.put(0)
        elif state == 'OUT':
            self.highlim.put(0)
            self.lowlim.put(1)


def test_pvstate_class():
    """
    Make sure all the internal logic works as expected. Use fake signals
    instead of EPICS signals with live hosts.
    """
    logger.debug('test_pvstate_class')
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

    assert('IN' in lim_obj.states_list)
    assert('OUT' in lim_obj.states_list)
    assert('Unknown' in lim_obj.states_list)
    assert('defer' not in lim_obj.states_list)

    lim_obj2 = LimCls2('BASE', name='test')
    with pytest.raises(ValueError):
        lim_obj2.move('asdfe')
    lim_obj2.move('OUT')
    assert(lim_obj2.position == 'OUT')
    lim_obj2.move('IN')
    assert(lim_obj2.position == 'IN')


def test_state_status():
    logger.debug('test_state_status')
    lim_obj = LimCls('BASE', name='test')
    # Create a status for 'in'
    status = StateStatus(lim_obj, 'IN')
    # Put readback to 'in'
    lim_obj.lowlim.put(0)
    lim_obj.highlim.put(1)
    assert status.done and status.success
    # Check our callback was cleared
    assert status.check_value not in lim_obj._callbacks[lim_obj.SUB_STATE]


@using_fake_epics_pv
def test_statesrecord_class():
    """
    Nothing special can be done without live hosts, just make sure we can
    create a class.
    """
    logger.debug('test_statesrecord_class')

    class MyStates(StateRecordPositioner):
        states_list = ['YES', 'NO', 'MAYBE', 'SO']

    MyStates('A:PV', name='test')
