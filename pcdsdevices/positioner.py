import time

import numpy as np
from ophyd.positioner import SoftPositioner
from ophyd.signal import EpicsSignal, Signal

from .interface import FltMvInterface
from .utils import schedule_task


class FuncPositioner(FltMvInterface, SoftPositioner):
    """
    Class for hacking together a positioner-like object.

    Before you use this, make sure your use case cannot be easily handled by a
    PVPositioner or by a PseudoPositioner.

    This should be fast to set up, but has the following limitations:
    - Inspection tools will not work properly, in general
    - typhos, happi, and similar tools will not work
    - It is not possible to know ahead of time if any control layer signals
      poked by this device are connected.
    - Metadata about the control layer will not be provided.
    - It's not possible to intelligently subscribe to control layer signals.
      Everything will be periodic polls on background threads.
    - Session performance may be negatively impacted by slow polling functions.
    """
    def __init__(self, *, name, mv, wm, done=None, check_value=None,
                 egu='', limits=None, update_rate=1, timeout=60,
                 notepad_pv=None):
        self._move = mv
        self._get_pos = wm
        self._done = done
        self._check = check_value
        self._last_update = 0
        self._goal = None
        self.update_rate = 1
        if notepad_pv is None:
            self.notepad_signal = Signal()
        else:
            self.notepad_signal = EpicsSignal(notepad_pv)
        super().__init__(name=name, egu=egu, limits=limits, source='func',
                         timeout=timeout)

    def _setup_move(self, position, status):
        self._run_subs(sub_type=self.SUB_START, timestamp=time.time())
        self._goal = position
        self._started_moving = True
        self._moving = True
        self._new_update()
        self._update_loop()
        self._move(position)

    def _new_update(self, status):
        schedule_task(
            self._update_task, args=(status,), delay=self.update_rate
            )

    def _update_task(self, status):
        self._update_position()
        if self._check_finished():
            status.set_finished()
        elif not status.done:
            self._new_update()
        if status.done:
            self._started_moving = False
            self._moving = False

    @property
    def position(self):
        self._update_position()
        return self._position

    def _update_position(self):
        if time.time() - self._last_update > self.update_rate:
            self._last_update = time.time()
            pos = self._get_pos()
            self._set_position(pos)
            self.notepad_signal.put(pos)

    def _check_finished(self):
        if self._done is None:
            finished = np.is_close(self._goal, self.position)
        else:
            finished = self._done()
        if finished:
            self._done_moving()
        return finished

    def check_value(self, pos):
        super().check_value(pos)
        if self._check is not None:
            self._check(pos)


# Legacy name from old code
VirtualMotor = FuncPositioner
