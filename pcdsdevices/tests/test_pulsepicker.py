import logging
import threading
import time
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device
from ophyd.status import wait as status_wait

from ..inout import InOutRecordPositioner
from ..pulsepicker import PulsePickerInOut

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_picker():
    """
    Picker starts IN and OPEN
    """
    FakePicker = make_fake_device(PulsePickerInOut)
    picker = FakePicker('TST:SB1:MMS:35', name='picker')
    picker.inout.state.sim_put(0)
    picker.inout.state.sim_set_enum_strs(['Unknown'] +
                                         InOutRecordPositioner.states_list)
    picker.blade.sim_put(0)
    picker.mode.sim_put(0)
    return picker


@pytest.mark.timeout(5)
def test_picker_states(fake_picker):
    logger.debug('test_picker_states')
    picker = fake_picker
    # Insert and OPEN
    picker.inout.state.put('IN')
    picker.blade.sim_put(0)
    assert not picker.inserted
    assert picker.removed
    assert picker.position == 'OPEN'
    # CLOSE it
    picker.blade.sim_put(1)
    assert picker.inserted
    assert not picker.removed
    assert picker.position == 'CLOSED'
    # Take it OUT
    picker.inout.state.put('OUT')
    assert not picker.inserted
    assert picker.removed
    assert picker.position == 'OUT'


@pytest.mark.timeout(5)
def test_picker_motion(fake_picker):
    logger.debug('test_picker_motion')
    picker = fake_picker
    # Light interface
    status = picker.insert(wait=False)
    picker.blade.sim_put(1)
    status_wait(status, timeout=1)
    assert status.done
    assert status.success
    assert picker.inserted
    assert not picker.removed
    status = picker.remove(wait=False)
    status_wait(status, timeout=1)
    assert status.done
    assert status.success
    assert not picker.inserted
    assert picker.removed
    # Full move set
    status = picker.move('CLOSED', wait=False)
    status_wait(status, timeout=1)
    assert status.done
    assert status.success
    assert picker.inserted
    assert not picker.removed
    assert picker.position == 'CLOSED'
    status = picker.move('OPEN', wait=False)
    picker.blade.sim_put(0)
    status_wait(status, timeout=1)
    assert status.done
    assert status.success
    assert not picker.inserted
    assert picker.removed
    assert picker.position == 'OPEN'
    status = picker.move('OUT', wait=False)
    status_wait(status, timeout=1)
    assert status.done
    assert status.success
    assert not picker.inserted
    assert picker.removed
    assert picker.position == 'OUT'


def put_soon(sig, val):
    def inner():
        time.sleep(0.2)
        sig.sim_put(val)
    t = threading.Thread(target=inner, args=())
    t.start()


@pytest.mark.timeout(5)
def test_picker_mode(fake_picker):
    logger.debug('test_picker_mode')
    picker = fake_picker
    picker.mode.sim_put(1)
    put_soon(picker.mode, 0)
    picker.reset(wait=True)
    assert picker.cmd_reset.get() == 1
    picker.open(wait=False)
    assert picker.cmd_open.get() == 1
    picker.close(wait=False)
    assert picker.cmd_close.get() == 1
    picker.flipflop(wait=False)
    assert picker.cmd_flipflop.get() == 1
    picker.burst(wait=False)
    assert picker.cmd_burst.get() == 1
    picker.follower(wait=False)
    assert picker.cmd_follower.get() == 1


@pytest.mark.timeout(5)
def test_picker_mode_wait(fake_picker):
    logger.debug('test_picker_mode_waits')
    picker = fake_picker

    put_soon(picker.blade, 0)
    picker.open(wait=True)
    put_soon(picker.blade, 1)
    picker.close(wait=True)

    put_soon(picker.mode, 2)
    picker.flipflop(wait=True)
    picker.mode.sim_put(0)
    put_soon(picker.mode, 3)
    picker.burst(wait=True)
    picker.mode.sim_put(0)
    put_soon(picker.mode, 6)
    picker.follower(wait=True)
    picker.mode.sim_put(0)


@pytest.mark.timeout(5)
def test_picker_subs(fake_picker):
    logger.debug('test_picker_subs')
    picker = fake_picker
    # Subscribe a pseudo callback
    cb = Mock()
    picker.subscribe(cb, event_type=picker.SUB_STATE, run=False)
    # Change the target state
    picker.insert()
    assert cb.called


@pytest.mark.timeout(5)
def test_picker_disconnected():
    PulsePickerInOut('TST:SB1:MMS:35', name='picker')
