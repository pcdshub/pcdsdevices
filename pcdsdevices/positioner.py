import inspect
import time

import numpy as np
from ophyd.positioner import SoftPositioner
from ophyd.signal import EpicsSignal, Signal
from ophyd.utils import InvalidState

from .interface import FltMvInterface
from .utils import schedule_task


class FuncPositioner(FltMvInterface, SoftPositioner):
    """
    Class for hacking together a positioner-like object.

    Before you use this, make sure your use case cannot be easily handled by a
    `PVPositioner` or by a `PseudoPositioner`.

    This should be fast to set up, but has the following limitations:
    - Inspection tools will not work properly, in general
    - typhos, happi, and similar tools will not work
    - It is not possible to know ahead of time if any control layer signals
      poked by this device are connected.
    - Metadata about the control layer will not be provided.
    - It's not possible to intelligently subscribe to control layer signals.
      Everything will be periodic polls on background threads.
    - Session performance may be negatively impacted by slow polling functions.

    Parameters
    ----------
    name : str, keyword-only
        The name to use when we refer to this positioner.

    move : func, keyword-only
        The function to call to cause the device to move.
        The signature must be def fn(position)

    get_pos : func, keyword-only
        The function to call to check the device's position.
        The signature must be def fn()

    set_pos : func, optional, keyword-only
        If provided, the function to call to change the device's shown
        position without moving it. The signature must be def fn(position)

    stop : func, optional, keyword-only
        If provided, the function to call to stop the motor.
        The signature must be def fn()

    done : func, optional, keyword-only
        If provided, the function to call to check if the device
        is done moving. The signature must be def fn() -> bool, and it
        must return True when motion is complete and false otherwise.

    check_value : func, optional, keyword-only
        If provided, an extra function to call to check if it is safe to
        move. The signature must be def fn(position) -> raise ValueError

    info : func, optional, keyword-only
        If provided, an extra function to add data to the ipython console
        pretty-print. The signature must be def fn() -> dict{str: value}.

    egu : str, optional
        If provided, the metadata units for the positioner.

    limits : tuple of floats, optional
        If provided, we'll raise an exception to reject moves outside of this
        range.

    update_rate : float, optional
        How often to update the position and check for move completion during a
        move. Defaults to 1 second.

    timeout : float, optional
        How long to wait before marking an in-progress move as failed.
        Defaults to 60 seconds.

    notepad_pv : str, optional
        If provided, a PV to put to whenever we move. This can be used to allow
        other elements in the control system to see what this positioner is
        doing.
    """
    def __init__(
            self, *, name, move, get_pos, set_pos=None, stop=None, done=None,
            check_value=None, info=None, egu='', limits=None, update_rate=1,
            timeout=60, notepad_pv=None, parent=None, kind=None,
            **kwargs
            ):
        self._check_signature('move', move, 1)
        self._move = move
        self._check_signature('get_pos', get_pos, 0)
        self._get_pos = get_pos
        self._check_signature('set_pos', set_pos, 1)
        self._set_pos = set_pos
        self._check_signature('stop', stop, 0)
        self._stop = stop
        self._check_signature('done', done, 0)
        self._done = done
        self._check_signature('check_value', check_value, 1)
        self._check = check_value
        self._info = info
        self._last_update = 0
        self._goal = None
        self.update_rate = 1
        notepad_name = name + '_notepad'
        if notepad_pv is None:
            self.notepad_signal = Signal(name=notepad_name)
        else:
            self.notepad_signal = EpicsSignal(notepad_pv, name=notepad_name)
        if parent is None and kind is None:
            kind = 'hinted'
        super().__init__(name=name, egu=egu, limits=limits, source='func',
                         timeout=timeout, parent=parent, kind=kind, **kwargs)

    def _check_signature(self, name, func, nargs):
        if func is None:
            return
        sig = inspect.signature(func)
        try:
            sig.bind(*(0,) * nargs)
        except TypeError:
            raise ValueError(
                f'FuncPositioner recieved {name} with an incorrect. '
                f'signature. Must be able to take {nargs} args.'
                ) from None

    def _setup_move(self, position, status):
        self._run_subs(sub_type=self.SUB_START, timestamp=time.time())
        self._goal = position
        self._started_moving = True
        self._moving = True
        self._finished = False
        self._move(position)
        self._new_update(status)

    def _new_update(self, status):
        schedule_task(
            self._update_task, args=(status,), delay=self.update_rate
            )

    def _update_task(self, status):
        self._update_position()
        if self._check_finished():
            try:
                status.set_finished()
            except InvalidState:
                pass
        if status.done:
            self._started_moving = False
            self._moving = False
        else:
            self._new_update(status)

    @property
    def position(self):
        self._update_position()
        return self._position

    def _update_position(self):
        if time.monotonic() - self._last_update > self.update_rate:
            self._last_update = time.monotonic()
            pos = self._get_pos()
            self._set_position(pos)
            self.notepad_signal.put(pos)

    def _check_finished(self):
        if self._done is None:
            finished = np.isclose(self._goal, self.position)
        else:
            finished = self._done()
        if finished:
            self._done_moving()
        return finished

    def set_position(self, position):
        if self._set_pos is None:
            raise NotImplementedError(
                f'FuncPositioner {self.name} was not '
                'given a set_pos argument.'
                )
        else:
            self._set_pos(position)

    def stop(self, *args, **kwargs):
        if self._stop is None:
            # Often called by bluesky, don't throw an exception
            self.log.warning(
                f'Called stop on FuncPositioner {self.name}, '
                'but was not given a stop argument.'
                )
        else:
            self._stop()
        super().stop(*args, **kwargs)

    def check_value(self, pos):
        super().check_value(pos)
        if self._check is not None:
            self._check(pos)

    def status_info(self):
        info = super().status_info()
        if self._info is not None:
            info.update(self._info())
        return info


# Legacy name from old code
VirtualMotor = FuncPositioner
