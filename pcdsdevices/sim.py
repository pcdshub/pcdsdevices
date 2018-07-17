import time
import threading

from ophyd.device import Device, Component as Cpt
from ophyd.positioner import SoftPositioner
from ophyd.signal import AttributeSignal
from ophyd.sim import SynAxis

from pcdsdevices.mv_interface import FltMvInterface


class SynMotor(FltMvInterface, SynAxis):
    """
    SynAxis with the FltMvInterface additions.

    This can be used to test when you need the readback_func feature or if you
    just want your test motor to finish immediately.
    """
    def move(self, position, *args, **kwargs):
        return super().set(position)


class SlowMotor(FltMvInterface, SoftPositioner, Device):
    """
    Simulated slow-moving motor.

    Unlike the SynAxis built into ophyd, this takes some time to reach the
    destination. Use this when you need some sort of delay.
    """
    user_readback = Cpt(AttributeSignal, 'position')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_position(0)

    def _setup_move(self, position, status):
        def update_thread(positioner, goal):
            positioner._moving = True
            while positioner.position != goal and not self._stop:
                if goal - positioner.position > 1:
                    positioner._set_position(positioner.position + 1)
                elif goal - positioner.position < -1:
                    positioner._set_position(positioner.position - 1)
                else:
                    positioner._set_position(goal)
                    positioner._done_moving()
                    return
                time.sleep(0.1)
            positioner._done_moving(success=False)
        self.stop()
        self._started_moving = True
        self._stop = False
        t = threading.Thread(target=update_thread,
                             args=(self, position))
        t.start()

    def stop(self):
        self._stop = True


class SimTwoAxis(Device):
    """
    Test assembly with two motors
    """
    x = Cpt(SlowMotor)
    y = Cpt(SlowMotor)

    # def tweak(self):
    #     return tweak_2d(self.x, self.y)
