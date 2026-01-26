import functools
import logging
from typing import Callable, ClassVar, Optional

from ophyd.device import Component as Cpt
from ophyd.device import required_for_connection
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import EpicsSignal
from ophyd.status import MoveStatus
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import (AlarmSeverity, fmt_time,
                                   raise_if_disconnected)

from .doc_stubs import basic_positioner_init
from .epics_motor import (BeckhoffAxisPLC, EpicsMotorInterfaceAlarmFilter,
                          MotorDisabledError)
from .eps import EPS
from .interface import FltMvInterface
from .signal import PytmcSignal
from .variety import set_metadata

logger = logging.getLogger(__name__)


class TwinCATMotorInterface(FltMvInterface, PVPositioner):
    """
    A standard PVPositioner motor with PCDS interface conventions for TwinCAT axes.

    This class wraps a standard positioner device and implements PCDS preferences and interface patterns.
    It presents all critical motion and configuration PVs found in TwinCAT motors,
    as well as soft limit, status, and safety/diagnostic methods.

    Notes
    -----
    The PCDS interface preferences and design patterns implemented here are:

    1. Uses the `FltMvInterface` mixin for name aliases and advanced functionality, such as improved
       tab completion and convenient move/stop helpers.
    2. Implements all limits and soft limits via EPICS/TwinCAT NC soft limit records/tags (`NC:MinPos:Goal`, etc.),
       avoiding the internal `limits` cached by pyepics, which can become stale.
    3. Provides support for detecting disabled states,
       with appropriate error raising.
    4. Subscribes to all key status bits (moving, limit switches, homed, power, direction)
       for robust feedback and event-driven updates.
    5. Metadata and tab whitelisting enable rich Typhos and IPython display.
    6. Post-move error logs are only shown after motions initiated from this client session,
       not from others—by maintaining `_moved_in_session` and filtering logs accordingly.
    7. All IOCs differences are handled elsewhere; this interface is IOC-agnostic and can
       be used with any compliant TwinCAT axis IOC.
    """
    # Position
    setpoint = Cpt(PytmcSignal, "fPosition", io="io", kind="hinted", auto_monitor=True)
    readback = Cpt(PytmcSignal, "fActPosition", io="i", kind="hinted", auto_monitor=True)
    done = Cpt(PytmcSignal, "bDone", io="i", kind="normal", auto_monitor=True)
    actuate = Cpt(PytmcSignal, "bMoveCmd", io="io", kind="normal")
    stop_signal = Cpt(PytmcSignal, "bHalt", io="io", kind="normal")

    # Motion Configuration
    velocity = Cpt(PytmcSignal, "fVelocity", io="io", kind="config", auto_monitor=True)
    acceleration = Cpt(PytmcSignal, "fAcceleration", io="io", kind="config", auto_monitor=True)
    deceleration = Cpt(PytmcSignal, "fDeceleration", io="io", kind="config", auto_monitor=True)
    jerk = Cpt(PytmcSignal, "fJerk", io="io", kind="config", auto_monitor=True)
    enable_mode = Cpt(PytmcSignal, "eEnableMode", io="io", kind="config")
    brake_mode = Cpt(PytmcSignal, "eBrakeMode", io="io", kind="config")

    # Status Bits
    motor_is_moving = Cpt(PytmcSignal, "bMoving", io="i", kind="normal", auto_monitor=True)
    motor_is_moving_negative = Cpt(PytmcSignal, "bNegativeDirection", io="i", kind="normal", auto_monitor=True)
    motor_is_moving_positive = Cpt(PytmcSignal, "bPositiveDirection", io="i", kind="normal", auto_monitor=True)
    power_is_enabled = Cpt(PytmcSignal, "bPowerIsEnabled", io="i", kind="normal", auto_monitor=True)
    high_limit_switch = Cpt(PytmcSignal, "bLimitFwd", io="i", kind="normal", auto_monitor=True)
    low_limit_switch = Cpt(PytmcSignal, "bLimitBwd", io="i", kind="normal", auto_monitor=True)
    negative_dir_enabled = Cpt(PytmcSignal, "bNegativeMotionIsEnabled", io="i", kind="normal", auto_monitor=True)
    positive_dir_enabled = Cpt(PytmcSignal, "bPositiveMotionIsEnabled", io="i", kind="normal", auto_monitor=True)
    command = Cpt(PytmcSignal, "eCommand", io="i", kind="normal", auto_monitor=True)

    # Limits (configuration)
    low_limit_travel = Cpt(EpicsSignal, 'NC:MinPos:Val_RBV', write_pv='NC:MinPos:Goal', kind='config', auto_monitor=True)
    high_limit_travel = Cpt(EpicsSignal, 'NC:MaxPos:Val_RBV', write_pv='NC:MaxPos:Goal', kind='config', auto_monitor=True)
    low_limit_enable = Cpt(EpicsSignal, 'NC:SoftPosMinOn:Val_RBV', write_pv='NC:SoftPosMinOn:Goal', kind='config', auto_monitor=True)
    high_limit_enable = Cpt(EpicsSignal, 'NC:SoftPosMaxOn:Val_RBV', write_pv='NC:SoftPosMaxOn:Goal', kind='config', auto_monitor=True)

    tab_whitelist = [
        "velocity",
        "check_limit_switches",
        "get_low_limit", "set_low_limit",
        "get_high_limit", "set_high_limit"
    ]

    set_metadata(actuate, dict(variety='command', value=1))
    set_metadata(stop_signal, dict(variety='command-proc', value=1))
    # set_metadata(low_limit_enable, dict(variety='command', value=1))
    # set_metadata(high_limit_enable, dict(variety='command', value=1))
    set_metadata(done, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving_negative, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving_positive, dict(variety='bitmask', bits=1))
    set_metadata(negative_dir_enabled, dict(variety='bitmask', bits=1))
    set_metadata(positive_dir_enabled, dict(variety='bitmask', bits=1))
    set_metadata(power_is_enabled, dict(variety='bitmask', bits=1))
    set_metadata(high_limit_switch, dict(variety='bitmask', bits=1))
    set_metadata(low_limit_switch, dict(variety='bitmask', bits=1))

    tolerated_alarm = AlarmSeverity.NO_ALARM

    _alarm_filter_installed: ClassVar[bool] = False
    _moved_in_session: bool
    _egu: str

    def __init__(
        self,
        prefix="",
        *,
        name,
        kind=None,
        read_attrs=None,
        configuration_attrs=None,
        parent=None,
        **kwargs
    ):
        self._moved_in_session = False
        self._egu = ''
        super().__init__(
            prefix=prefix,
            name=name,
            kind=kind,
            read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs
        )
        self._install_motion_error_filter()

        self.readback.name = self.name

        def on_limit_changed(value, old_value, **kwargs):
            # Update EpicsSignal object when a limit CA monitor received from EPICS
            if self.connected and old_value is not None and value != old_value:
                self.setpoint._metadata_changed(
                    self.setpoint.pvname,
                    self.setpoint._read_pv.get_ctrlvars(),
                    from_monitor=True,
                    update=True,
                )

        self.low_limit_travel.subscribe(on_limit_changed)
        self.high_limit_travel.subscribe(on_limit_changed)

    @property
    def units(self):
        """The engineering units (units) for a position"""
        # return self.units.get()

    def move(self, position: float, wait: bool = True, **kwargs) -> MoveStatus:
        self._moved_in_session = True
        return super().move(position, wait=wait, **kwargs)

    def _get_epics_limits(self) -> tuple[float, float]:
        limits = self.setpoint.limits
        if limits is None or limits == (None, None):
            # Not initialized
            return (0, 0)
        return limits

    def _install_motion_error_filter(self) -> None:
        """Applies the class _motion_error_filter to self.log"""
        if not TwinCATMotorInterface._alarm_filter_installed:
            TwinCATMotorInterface._alarm_filter_installed = True
            self.log.logger.addFilter(EpicsMotorInterfaceAlarmFilter())

    @property
    @raise_if_disconnected
    def limits(self) -> tuple[float, float]:
        """Override the limits attribute"""
        return (
            self.low_limit_travel.get(),
            self.high_limit_travel.get(),
        )

    @limits.setter
    def limits(self, lims: tuple[float, float]):
        """
        Write to the epics limits on setattr

        Expects a tuple of two elements, the low and high limits to set.
        """
        # Wrong len is probably a bigger mistake
        if len(lims) != 2:
            raise ValueError("Limits should be a tuple of 2 values.")
        low = min(lims)
        high = max(lims)
        if low == high:
            # User probably meant to disable limits
            low = 0
            high = 0
        orig_high = self.high_limit_travel.get()
        if low > orig_high:
            # Set high first so we make room for low
            self.high_limit_travel.put(high)
            self.low_limit_travel.put(low)
        else:
            self.low_limit_travel.put(low)
            self.high_limit_travel.put(high)

    def check_limit_switches(self):
        """
        Check the limits switches.

        Returns
       ----
        limit_switch_indicator : str
            Indicate which limit switch is activated.
        """
        low = self.low_limit_switch.get()
        high = self.high_limit_switch.get()
        if low and high:
            return "Low [x] High [x]"
        elif low:
            return "Low [x] High []"
        elif high:
            return "Low [] High [x]"
        else:
            return "Low [] High []"

    def set_low_limit(self, value):
        """
        Set the low limit.

        Parameters
       -------
        value : float
            Limit of travel in the negative direction.

        Raises
       ---
        ValueError
            When motor in motion or position outside of limit.
        """
        if self.moving:
            raise ValueError('Motor is in motion, cannot set the low limit!')
        if value > self.position:
            raise ValueError(f'Could not set motor low limit to {value} at'
                             f' position {self.position}. Low limit must '
                             'be lower than the current position.')

        _current_high_limit = self.limits[1]
        if value > _current_high_limit:
            raise ValueError(f'Could not set motor low limit to {value}.'
                             'Low limit must be lower than the current'
                             f' high limit: {_current_high_limit}')

        # update EPICS limits
        self.low_limit_travel.put(value)

    def set_high_limit(self, value):
        """
        Limit of travel in the positive direction.

        Parameters
       -------
        value : float
            High limit value to be set.

        Raises
       ---
        ValueError
            When motor in motion or position outside of limit.
        """
        if self.moving:
            raise ValueError('Motor is in motion, cannot set the high limit!')

        if value < self.position:
            raise ValueError(f'Could not set motor high limit to {value} '
                             f'at position {self.position}. High limit '
                             'must be higher than the current position.')

        _current_low_limit = self.limits[0]
        if value < _current_low_limit:
            raise ValueError(f'Could not set motor high limit to {value}. '
                             'High limit must be higher than the current low '
                             f'limit: {_current_low_limit}')
        # update EPICS limits
        self.high_limit_travel.put(value)

    def clear_limits(self):
        """Set both low and high limits to 0."""
        self.high_limit_travel.put(0)
        self.low_limit_travel.put(0)

    @property
    @raise_if_disconnected
    def moving(self):
        """Whether or not the motor is moving

        Returns
       ----
        moving : bool
        """
        return bool(self.motor_is_moving.get(use_monitor=False))

    @property
    def homed(self):
        """Get the home status of the motor"""
        return bool(self.motor_is_homed.get())

    @raise_if_disconnected
    def stop(self, *, success=False):
        self.stop_signal.put(1, wait=False)
        super().stop(success=success)

    @property
    def enabled(self):
        """
        Returns
        -------
        bool
            True if power is enabled **and** either negative or positive direction is enabled.

        Explanation
        -----------
        - Returns True if:
            - Power is on (`power_is_enabled`)
            - At least one direction (`negative_dir_enabled` OR `positive_dir_enabled`) is enabled
        """
        return (
            bool(self.power_is_enabled.get())
            and (
                bool(self.negative_dir_enabled.get())
                or bool(self.positive_dir_enabled.get())
            )
        )

    @property
    @raise_if_disconnected
    def position(self):
        """The current position of the motor in its engineering units

        Returns
       ----
        position : float
        """
        return self.readback.get()

    def check_value(self, value):
        """
        Raise an exception if the motor cannot move to the given value.
        - Always call superclass logic.
        - If super() raises on out-of-bounds/disabled and BOTH soft limits are set but not enabled,
          provide a clear composite message.
        - Only check `self.enabled` if enable_mode is ALWAYS.
        """
        try:
            super().check_value(value)
        except Exception as e:
            limits_enabled = (
                bool(self.low_limit_enable.get()) and
                bool(self.high_limit_enable.get())
            )
            if not limits_enabled and any(self.limits):
                raise RuntimeError(
                    f"Soft limits set but not PLC-enabled (limits={self.limits}). {e}"
                ) from e
            raise

        # Only check enabled if enable_mode is ALWAYS
        enable_mode_value = self.enable_mode.get(as_string=True)
        if enable_mode_value == "ALWAYS":
            if self.enabled == 0:
                raise MotorDisabledError("Motor is not enabled. Motion requests ignored")
        # Else (DURING_MOTION or other): Skip enabled test before move.

    @required_for_connection
    @readback.sub_value
    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        """Callback from EPICS, indicating a change in position"""
        self._set_position(value)

    @required_for_connection
    @done.sub_value
    def _move_changed(self, timestamp=None, value=None, sub_type=None, **kwargs):
        """Callback from EPICS, indicating that movement status has changed"""
        was_moving = self._moving
        self._moving = value != 1

        started = False
        if not self._started_moving:
            started = self._started_moving = not was_moving and self._moving

        self.log.debug(
            "[ts=%s] %s moving: %s (value=%s)",
            fmt_time(timestamp),
            self,
            self._moving,
            value,
        )

        if started:
            self._run_subs(
                sub_type=self.SUB_START, timestamp=timestamp, value=value, **kwargs
            )

        if was_moving and not self._moving:
            success = True
            # Check if we are moving towards the low limit switch
            if self.motor_is_moving_negative.get() == 1:
                if self.low_limit_switch.get(use_monitor=False) == 1:
                    success = False
            # No, we are going to the high limit switch
            else:
                if self.high_limit_switch.get(use_monitor=False) == 1:
                    success = False

            # Check the severity of the alarm field after motion is complete.
            # If there is any alarm at all warn the user, and if the alarm is
            # greater than what is tolerated, mark the move as unsuccessful
            severity = self.readback.alarm_severity

            if severity != AlarmSeverity.NO_ALARM:
                status = self.readback.alarm_status
                if severity > self.tolerated_alarm:
                    self.log.error(
                        "Motion failed: %s is in an alarm state "
                        "status=%s severity=%s",
                        self.name,
                        status,
                        severity,
                    )
                    success = False
                else:
                    self.log.warning(
                        "Motor %s raised an alarm during motion "
                        "status=%s severity %s",
                        self.name,
                        status,
                        severity,
                    )
            self._done_moving(success=success, timestamp=timestamp, value=value)

    def _done_moving(self, value: Optional[int] = None, **kwargs) -> None:
        """
        Override _done_moving to always reset our _moved_in_session attribute.

        This is not possible through adding subscriptions because SUB_DONE
        is only run on success and _SUB_REQ_DONE is private and repeatedly
        cleared.
        """
        super()._done_moving(value=value, **kwargs)
        if value:
            self._reset_moved_in_session()

    def _reset_moved_in_session(self) -> None:
        """Mark that a move have not yet been requested in this session."""
        self._moved_in_session = False

    @property
    def report(self):
        try:
            rep = super().report
        except Exception:
            rep = {"position": "disconnected"}
        rep["pv"] = self.readback.pvname
        return rep


class TwinCATAxis(TwinCATMotorInterface):
    """
    TwinCAT NC AXIS_REF motor device with error handling and homing.

    This class extends the TwinCATMotorInterface with:
        - Additional components (PLC diagnostics, homing command and mode).
        - end-of-move and error handling: move completion status is
          checked against PLC error and status codes, so that motion failures
          are accurately detected and reported.
        - A `clear_error` method to reset PLC motion errors from Python or GUI.
        - A `home()` method exposing all PLC-configured homing routines with
          proper mode setting, actuation, status, and timing.
        - Robust session-tracking and logging logic for post-move diagnostics.

    Attributes
   -------
    actuate_home : PytmcSignal
        PV to trigger a homing command.
    home_mode : PytmcSignal
        PV to select the homing mode (see HomeEnum).
    plc : BeckhoffAxisPLC
        Sub-device interface for further PLC status and diagnostics.

    """
    homed = Cpt(PytmcSignal, "bHomed", io="i", kind='normal', auto_monitor=True)
    home_mode = Cpt(PytmcSignal, "eHomeMode", io="io", kind="config")

    __doc__ += basic_positioner_init
    tab_whitelist = ['clear_error', 'home']

    plc = Cpt(BeckhoffAxisPLC, '', kind='normal',
              doc='PLC error handling and aux functions.')

    set_metadata(homed, dict(variety='bitmask', bits=1))

    def subscribe(
        self,
        callback: Callable,
        event_type: Optional[str] = None,
        run: bool = True,
    ) -> int:
        """
        Subscribe to events this event_type generates.

        See ophydobj.subscribe for full details.

        This is a thin wrapper over subscribe for custom error handling
        to intercept the normal end of move handler.

        Unlike during EpicsMotor's move, the move status will
        be set to the TwinCAT error message if there is one.
        The move will be marked as successful otherwise.

        Possibly this was unnecessary with an ophyd PR to allow me to
        customize the error handling, but without that this seems like
        the easiest way to sidestep the status._finished call and ignore
        the error logic in _move_changed.
        """
        # Mutate subscribe appropriately if this is the exact sub req done
        # Or if it's a similar one using non-deprecated set_finished
        # See PositionerBase.move
        if all((
            event_type == self._SUB_REQ_DONE,
            callback.__qualname__ in (
                'StatusBase._finished',
                'StatusBase.set_finished',
            ),
            not run,
        )):
            # Find the actual status object
            status = callback.__self__
            # Slip in the more specific end move handler
            return super().subscribe(
                functools.partial(self._end_move_cb, status),
                event_type=self._SUB_REQ_DONE,
                run=False,
            )
        # Otherwise, normal subscribe
        return super().subscribe(
            callback=callback,
            event_type=event_type,
            run=run,
        )

    def _end_move_cb(self, status: MoveStatus, **kwargs) -> None:
        """
        Special end of move handling to set the status for TwinCATAxis.

        If the TwinCATAxis has an error message, include it and mark failure.
        Otherwise, set success.

        Parameters
       -------
        status : MoveStatus
            The status that we need to update.
        """
        has_error = self.plc.err_bool.get()
        if has_error:
            error_message = self.plc.status.get()
            if not error_message:
                error_message = 'Unspecified error'
            error_code = self.plc.err_code.get()
            if error_code > 0:
                error_message = f"{hex(error_code)}: {error_message}"
            status.set_exception(RuntimeError(error_message))
        else:
            status.set_finished()

    def clear_error(self):
        """Clear any active motion errors on this axis."""
        self.plc.cmd_err_reset.put(1)

    def stage(self):
        """
        Stage the TwinCAT axis.

        This simply clears any errors. Stage is called at the start of most
        :mod:`bluesky` plans.
        """
        self.clear_error()
        return super().stage()

    @raise_if_disconnected
    def home(self, wait: bool = True, **kwargs):
        """
        Execute specified homing routine.

        Parameters
       -------
        mode : HomeMode
            Specifies homing mode *and* direction (see HomeMode).
        wait : bool
            If True, block until the homing completes.

        Returns
       ----
        status : MoveStatus
            Status object for move completion.
        """
        self._run_subs(sub_type=self._SUB_REQ_DONE, success=False)
        self._reset_sub(self._SUB_REQ_DONE)

        status = MoveStatus(self, self.plc.home_pos.get(),
                            timeout=None, settle_time=self._settle_time)

        self.plc.cmd_home.put(1)

        self.subscribe(status._finished, event_type=self._SUB_REQ_DONE,
                       run=False)

        try:
            if wait:
                status_wait(status)
        except KeyboardInterrupt:
            self.stop()
            raise

        return status

    @raise_if_disconnected
    def move(self, position: float, wait: bool = True, **kwargs) -> MoveStatus:
        """
        Move to the requested position using custom actuate+monitor sequence.

        Parameters
       -------
        position : float
            Target position.
        wait : bool
            Wait for move completion before returning.

        Returns
       ----
        status : MoveStatus
            Object to monitor asynchronous move completion.
        """
        # Indicate we're starting a move, for status/subscriptions
        self._run_subs(sub_type=self._SUB_REQ_DONE, success=False)
        self._reset_sub(self._SUB_REQ_DONE)

        # Make sure stop_signal is connected, if applicable (optional/defensive):
        if self.stop_signal is not None:
            self.stop_signal.wait_for_connection()

        # Call parent move to get status:
        status = super().move(position, wait=False)

        # Create status object for move monitoring
        status = MoveStatus(self, self.readback.get(),
                            timeout=None, settle_time=self._settle_time)

        # Subscribe status object to end-of-move event
        self.subscribe(status._finished, event_type=self._SUB_REQ_DONE, run=False)

        try:
            if wait:
                status_wait(status)
        except KeyboardInterrupt:
            self.stop()
            raise

        return status

    def check_value(self, pos: float) -> None:
        """
        Check that the motor can reach the position.

        Inherits limits and related checks from parent classes.
        Adds one additional check: the velocity must be nonzero
        for a move to succeed. Otherwise, the move fails silently.

        TwinCAT EPICS motors at LCLS that have never been initialized
        before default to a zero velocity for safety. This check
        lets the user know why the motor does not move.
        """
        super().check_value(pos)
        velo = self.velocity.get()
        if velo <= 0:
            raise RuntimeError(
                f'{self.name} velocity is {velo}, which is not valid. '
                'Please configure a nonzero, positive velocity.'
            )


class TwinCATAxisEPS(TwinCATAxis):
    """
    Extended TwinCATAxis with relevant EPS fields.

    This is to be used in TwinCATAxisEPS for cases when the motor
    has EPS considerations. Otherwise, these fields are not active
    in PLC logic and are distracting or confusing.
    """
    eps_forward = Cpt(EPS, "stEPSF:", doc="EPS forward enables.")
    eps_backward = Cpt(EPS, "stEPSB:", doc="EPS backward enables.")
    eps_power = Cpt(EPS, "stEPSP:", doc="EPS power enables.")
