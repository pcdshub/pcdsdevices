import threading
import time

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.ophydobj import Kind
from ophyd.positioner import SoftPositioner
from ophyd.signal import AttributeSignal
from ophyd.sim import SynAxis

from .interface import FltMvInterface, tweak_base


class SynMotor(FltMvInterface, SynAxis):
    """
    `SynAxis` with the `FltMvInterface` additions.

    This can be used to test when you need the `readback_func` feature or if
    you just want your test motor to finish immediately. See the `SynAxis`
    documentation in ophyd.
    """

    def move(self, position, *args, **kwargs):
        return super().set(position)


ignore_kwargs = ('atol', 'n_bounces', 'invert')


class FastMotor(FltMvInterface, SoftPositioner, Device):
    """
    Instant motor with `FltMvInterface`.

    This is suitable to replace real motors in the `PseudoPositioner`
    subclasses. It does not have all of the `SynAxis` functionality.
    """

    user_readback = Cpt(AttributeSignal, 'position')
    user_setpoint = Cpt(AttributeSignal, 'position')

    def __init__(self, *args, init_pos=0, kind=Kind.hinted, **kwargs):
        for kw in ignore_kwargs:
            kwargs.pop(kw, None)
        super().__init__(init_pos=init_pos, kind=kind, **kwargs)

    def set_current_position(self, position):
        self._set_position(position)


class SlowMotor(FastMotor):
    """
    Simulated slow-moving motor.

    Unlike the `FastMotor`, this takes some time to reach the
    destination. Use this when you need some sort of delay.
    """

    def _setup_move(self, position, status):
        if self.position is None:
            # Initialize position during __init__'s set call
            self._set_position(position)
            self._done_moving(success=True)
            return

        def update_thread(positioner, goal):
            positioner._moving = True
            if positioner.position == goal:
                # if already at the requested position, mark success
                positioner._set_position(goal)  # needed for LiveTable format
                positioner._done_moving(success=True)
                return

            while positioner.position != goal and not self._stop:
                if goal - positioner.position > 1:
                    positioner._set_position(positioner.position + 1)
                elif goal - positioner.position < -1:
                    positioner._set_position(positioner.position - 1)
                else:
                    positioner._set_position(goal)
                    positioner._done_moving(success=True)
                    return
                time.sleep(0.1)
            positioner._done_moving(success=False)
        self.stop()
        self._started_moving = True
        self._stop = False
        t = threading.Thread(target=update_thread,
                             args=(self, position))
        t.start()

    def stop(self, *, success: bool = False):
        self._stop = True


class SimTwoAxis(Device):
    """Test assembly with two slow motors. Used to test 2D tweak."""
    x = Cpt(SlowMotor)
    y = Cpt(SlowMotor)

    def tweak(self):
        return tweak_base(self.x, self.y)
