"""
Utilities for undulator pointing.

ACR has undulator pointing scripts that expect:
- delta_x, delta_y in microns
- "go"

There is a server-side process that ACR can start up
if we'd like to point the undulators multiple times
in a shift. This process will listen to our requests
for delta_x, delta_y, and go.

Standard procedure are something like:
- Call ACR to set up the auto repointing
- Run one of the utilities here to either calibrate
  or realgn

This was originally provisioned in the mfx repo before moving here.
"""

import math
import time
from typing import Callable, Optional, Union

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.positioner import PositionerBase
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import MoveStatus

from pcdsdevices.interface import MvInterface
from pcdsdevices.signal import MultiDerivedSignal, UnitConversionDerivedSignal
from pcdsdevices.type_hints import SignalToValue

DEFAULT_DONE_MOVE_PV = "SIOC:SYS0:ML07:AO216"


def _get_2d_delta(mds: MultiDerivedSignal, items: SignalToValue) -> tuple[float, float]:
    # See polarity note below
    return tuple(-val for val in items.values())


def _put_2d_delta(mds: MultiDerivedSignal, value: tuple[float, float]) -> SignalToValue:
    # Note on the polarity:
    # Setting 50 to the delta PV causes the real value to move by -50
    # So, when you ask for 50 we'll put -50 to the delta PV instead, to move the real value by 50
    return {mds.signals[0]: -value[0], mds.signals[1]: -value[1]}


def coerce_input_to_tuple(
    position: Union[tuple[float, float], float], ypos: Optional[float]
) -> tuple[float, float]:
    """
    Utility to coerce user input like move(3, 4) to move((3, 4))
    """
    if isinstance(position, tuple):
        if len(position) == 2:
            return position
        raise ValueError(f"Expected tuple of length 2, got {position}")
    elif ypos is None:
        raise TypeError(f"Expected position to be a tuple, got {position}")
    return (position, ypos)


class UndPointDelta2D(PVPositioner):
    """
    Undulator pointing variant: delta move by (x, y).

    This is the raw interface provided by ACR.
    All other variants re-use these definitions.
    """

    setpoint = Cpt(
        MultiDerivedSignal,
        attrs=["delta_x", "delta_y"],
        calculate_on_get=_get_2d_delta,
        calculate_on_put=_put_2d_delta,
    )
    delta_x = Cpt(EpicsSignal, ":DELTA_X")
    delta_y = Cpt(EpicsSignal, ":DELTA_Y")
    actuate = Cpt(EpicsSignal, ":GO")
    done = FCpt(EpicsSignalRO, "{done_pvname}")

    actuate_value = 1
    done_value = 0

    def __init__(
        self,
        prefix: str,
        *,
        done_pvname: str = DEFAULT_DONE_MOVE_PV,
        name: str,
        **kwargs,
    ):
        self.done_pvname = done_pvname
        super().__init__(prefix, name=name, **kwargs)

    def move(
        self,
        position: Union[tuple[float, float], float],
        y_delta: Optional[float] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
        moved_cb: Optional[Callable] = None,
    ) -> MoveStatus:
        """
        Do a relative move of the undulator.

        Parameters
        ----------
        position : tuple[float, float] or float
            If a tuple, this is the x, y delta to move by.
            If a float, this is the x delta to move by, and y_delta should be given as the second argument.
        y_delta : float, optional
            If position is given as as float x value, this is the accompanying y value.
        wait : bool, optional
            Whether to wait for the move to complete, or not. Defaults to True.
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        """
        return super().move(
            coerce_input_to_tuple(position, y_delta),
            wait=wait,
            timeout=timeout,
            moved_cb=moved_cb,
        )

    def _setup_move(self, position: tuple[float, float]):
        # Also reset the actuate PV before we actuate
        self.actuate.put(1 - self.actuate_value)
        super()._setup_move(position)


class UndPointAbs2D(MvInterface, Device, PositionerBase):
    """
    Undulator pointing variant: absolute move by (x, y)
    """

    xpos = Cpt(
        UnitConversionDerivedSignal,
        "x_raw_rbv",
        derived_units="um",
        original_units="mm",
        kind="hinted",
        add_prefix=(),
    )
    ypos = Cpt(
        UnitConversionDerivedSignal,
        "y_raw_rbv",
        derived_units="um",
        original_units="mm",
        kind="hinted",
        add_prefix=(),
    )

    x_raw_rbv = FCpt(EpicsSignalRO, "{x_abs_pvname}", kind="omitted")
    y_raw_rbv = FCpt(EpicsSignalRO, "{y_abs_pvname}", kind="omitted")
    delta_xy = FCpt(
        UndPointDelta2D,
        "{prefix}",
        done_pvname="{done_pvname}",
        add_prefix=("suffix", "done_pvname"),
    )

    def __init__(
        self,
        prefix: str,
        *,
        name: str,
        done_pvname: str = DEFAULT_DONE_MOVE_PV,
        x_abs_pvname: str = "BPMS:UNDH:4690:XOFF.D",
        y_abs_pvname: str = "BPMS:UNDH:4690:YOFF.D",
        **kwargs,
    ):
        self.done_pvname = done_pvname
        self.x_abs_pvname = x_abs_pvname
        self.y_abs_pvname = y_abs_pvname
        self._xpos_cache = None
        self._ypos_cache = None
        super().__init__(prefix, name=name, **kwargs)
        # Alias
        self.dxy = self.delta_xy

    def move(
        self,
        position: Union[tuple[float, float], float],
        y_abs: Optional[float] = None,
        wait: bool = True,
        timeout: Optional[float] = None,
        moved_cb: Optional[Callable] = None,
    ):
        """
        Do an absolute move of the undulator.

        Parameters
        ----------
        position : tuple[float, float] or float
            If a tuple, this is the x, y position to move to.
            If a float, this is the x position to move to, and y_abs should be given as the second argument.
        y_abs : float, optional
            If position is given as as float x value, this is the accompanying y value.
        wait : bool, optional
            Whether to wait for the move to complete, or not. Defaults to True.
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        """
        return self.delta_xy.move(
            self.get_delta_from_abs(coerce_input_to_tuple(position, y_abs)),
            wait=wait,
            timeout=timeout,
            moved_cb=moved_cb,
        )

    def get_delta_from_abs(self, position: tuple[float, float]) -> tuple[float, float]:
        """
        Convert the absolute position request to a delta move.

        This is needed because our raw moves are deltas and we
        need absolute positions for the optimizer.
        """
        return (position[0] - self.position[0], position[1] - self.position[1])

    @xpos.sub_value
    def _new_xpos(self, value: float, **kwargs):
        self._xpos_cache = value
        self._update_pos(**kwargs)

    @ypos.sub_value
    def _new_ypos(self, value: float, **kwargs):
        self._ypos_cache = value
        self._update_pos(**kwargs)

    def _update_pos(self, **kwargs):
        if None not in self.position:
            kwargs.pop("sub_type")
            self._run_subs(
                sub_type=self.SUB_READBACK,
                timestamp=kwargs.pop("timestamp"),
                value=self.position,
                **kwargs,
            )

    @property
    def position(self) -> tuple[float, float]:
        return (self._xpos_cache, self._ypos_cache)


class UndPointAbs2DHutch(UndPointAbs2D):
    """
    Undulator pointing with Hutch PV defaults.

    You can do:
    undp = UndPointAbs2DHutch("mfx")
    """

    def __init__(
        self,
        hutch: str,
        **kwargs,
    ):
        prefix = f"{hutch.upper()}:USER:MCC:UND"
        name = kwargs.pop("name")
        if name is None:
            name = f"{hutch.lower()}_undp"
        super().__init__(prefix, name=name, **kwargs)


class SafeUndPointAbs2D(UndPointAbs2D):
    """
    Absolute undulator pointing with safe segmented moves (both axes per step).
    """

    def move(
        self,
        position: Union[tuple[float, float], float],
        y_abs: Optional[float] = None,
        wait: bool = True,
        max_step: Optional[float] = 50.0,
        sleep_between: float = 2.0,
        timeout: Optional[float] = None,
        moved_cb: Optional[Callable] = None,
    ):
        """
        Do an absolute move with optional segmentation.

        If max_step is set, split the total move into segments on both axes,
        each segment clamped to max_step in magnitude. Otherwise, perform a
        single absolute move via the base class.
        """
        target_abs = coerce_input_to_tuple(position, y_abs)
        dx_total, dy_total = self.get_delta_from_abs(target_abs)

        # no segmentation requested or unnecessary: do a single absolute move
        if max_step is None or (
            abs(dx_total) <= max_step and abs(dy_total) <= max_step
        ):
            return super().move(
                position=target_abs, wait=wait, timeout=timeout, moved_cb=moved_cb
            )

        # for segmented moves, we require synchronous execution
        if not wait:
            raise ValueError("Safe chunked move requires wait=True.")

        # determine number of equal segments so each per-axis step magnitude <= max_step
        n_x = (
            int(math.ceil(abs(dx_total) / max_step))
            if max_step and abs(dx_total) > 0
            else 1
        )
        n_y = (
            int(math.ceil(abs(dy_total) / max_step))
            if max_step and abs(dy_total) > 0
            else 1
        )
        n_steps = max(n_x, n_y, 1)
        if n_steps == 1:
            return super().move(
                position=target_abs, wait=wait, timeout=timeout, moved_cb=moved_cb
            )

        # compute equal-sized steps for each axis
        step_x = dx_total / n_steps
        step_y = dy_total / n_steps
        last_status = None
        # perform the segmented moves
        for i in range(n_steps):
            # correct the final step to hit the target exactly
            if i == n_steps - 1:
                corr_x = dx_total - step_x * (n_steps - 1)
                corr_y = dy_total - step_y * (n_steps - 1)
                move_dx, move_dy = float(corr_x), float(corr_y)
            else:
                move_dx, move_dy = float(step_x), float(step_y)
            last_status = self.delta_xy.move(
                (move_dx, move_dy), wait=True, timeout=timeout
            )
            # sleep between moves to allow motors to settle
            if sleep_between > 0:
                time.sleep(sleep_between)

        # call the callback if provided
        if moved_cb is not None:
            try:
                moved_cb(obj=self)
            except TypeError:
                moved_cb(self)
        return last_status


class SafeUndPointAbs2DHutch(SafeUndPointAbs2D):
    """
    Safe segmented variant with Hutch PV defaults.

    You can do:
    undp = SafeUndPointAbs2DHutch("mfx")
    """

    def __init__(
        self,
        hutch: str,
        **kwargs,
    ):
        prefix = f"{hutch.upper()}:USER:MCC:UND"
        name = kwargs.pop("name")
        if name is None:
            name = f"{hutch.lower()}_undp"
        super().__init__(prefix, name=name, **kwargs)


class UndPointDelta2DSim(UndPointDelta2D):
    """
    Test version of the raw delta und pointing logic using no PVs.
    """

    delta_x = Cpt(Signal)
    delta_y = Cpt(Signal)
    actuate = Cpt(Signal)
    done = FCpt(Signal)

    # Extra signals: keep track of how much we've moved
    _raw_x = Cpt(Signal)
    _raw_y = Cpt(Signal)

    @actuate.sub_value
    def _sim_new_move(self, value: int, **_):
        """
        Simulate what ACR does when we ask for a move
        """
        if value != self.actuate_value:
            return
        self.done.put(1 - self.done_value)
        # It's fairly likely that delta_x and delta_y aren't updated yet somehow
        time.sleep(0.2)
        self._raw_x.put(self._raw_x.get() + (-self.delta_x.get() / 1000))
        self._raw_y.put(self._raw_y.get() + (-self.delta_y.get() / 1000))
        self.actuate.put(1 - self.actuate_value)
        self.done.put(self.done_value)


class UndPointAbs2DSim(UndPointAbs2D):
    """
    Test version of the abs und pointing logic using no PVs.
    """

    x_raw_rbv = Cpt(Signal)
    y_raw_rbv = Cpt(Signal)
    delta_xy = Cpt(UndPointDelta2DSim, "")

    def __init__(self, prefix="", *, name="sim_2d_abs", **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.delta_xy._raw_x.subscribe(self._new_raw_x)
        self.delta_xy._raw_y.subscribe(self._new_raw_y)
        # Using the real positions at the moment in time I made this class
        self.delta_xy._raw_x.put(0.123402)
        self.delta_xy._raw_y.put(-0.393441)

    def _new_raw_x(self, value: float, **_):
        self.x_raw_rbv.put(value)

    def _new_raw_y(self, value: float, **_):
        self.y_raw_rbv.put(value)


class SafeUndPointAbs2DSim(UndPointAbs2DSim, SafeUndPointAbs2D):
    """
    Test version of the segmented moving logic using no PVs
    """
    ...
