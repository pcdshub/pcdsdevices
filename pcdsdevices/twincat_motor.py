import functools
import logging
from typing import Callable, ClassVar, Optional

from ophyd.device import Component as Cpt
from ophyd.device import required_for_connection
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import DerivedSignal, EpicsSignal, EpicsSignalRO
from ophyd.sim import FakeEpicsSignalRO, fake_device_cache
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


class InvertedBoolEpicsSignal(DerivedSignal):
    def inverse(self, value: bool):
        """Convert motor limit enable to switch state: it's the inverse."""
        return not value


class EnabledDisabledSignal(EpicsSignal):
    """
    EpicsSignal for longin/longout enable records that lack ONAM/ZNAM.

    Presents the underlying 0/1 channel as an enum-like signal with strings
    'DISABLE' / 'ENABLE'. ``enum_strs`` is advertised through the signal's
    metadata and ``describe()`` so Typhos selects an enum widget rather than
    a raw integer line edit.

    Used where the soft-limit enable PVs (e.g. NC:SoftPosMinOn) are plain
    longin records without ONAM/ZNAM string fields.
    """
    _enum_strs = ('DISABLE', 'ENABLE')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Advertise the synthetic enum strings via metadata so consumers
        # (Typhos widget selector, ophyd describe()) treat this as an enum.
        self._metadata['enum_strs'] = tuple(self._enum_strs)

    def _int_to_str(self, value):
        try:
            return self._enum_strs[int(value)]
        except (ValueError, IndexError, TypeError):
            return value

    def _str_to_int(self, value):
        if isinstance(value, str):
            try:
                return self._enum_strs.index(value)
            except ValueError:
                pass
        return value

    def get(self, as_string=False, **kwargs):
        raw = super().get(**kwargs)
        if as_string:
            return self._int_to_str(raw)
        return raw

    def put(self, value, **kwargs):
        super().put(self._str_to_int(value), **kwargs)

    def describe(self):
        desc = super().describe()
        for key in desc:
            desc[key]['enum_strs'] = list(self._enum_strs)
        return desc


fake_device_cache[InvertedBoolEpicsSignal] = FakeEpicsSignalRO
fake_device_cache[EnabledDisabledSignal] = FakeEpicsSignalRO


class TwinCATMotorInterface(FltMvInterface, PVPositioner):
    """
    A standard PVPositioner motor with PCDS interface conventions for TwinCAT axes.

    This class wraps a standard positioner device and implements PCDS preferences and interface patterns.
    It presents all critical motion and configuration PVs found in TwinCAT motors,
    as well as soft limit, status, and safety/diagnostic methods.

    Many methods and their core logic in this class (e.g., limits, move, check_value,
    limit setter/clearer, stop, status change subscriptions, error filtering) are
    directly reused or adapted from the legacy EpicsMotorInterface to ensure
    API and UX consistency across PCDS motor controls. See each method's
    docstring for duplication/adaptation notes.

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
    5. Post-move error logs are only shown after motions initiated from this client session,
       not from others—by maintaining `_moved_in_session` and filtering logs accordingly.
    6. All IOCs differences are handled elsewhere; this interface is IOC-agnostic and can
       be used with any compliant TwinCAT axis IOC.
    """
    # Position
    setpoint = Cpt(PytmcSignal, ":fPosition", io="io", kind="hinted", auto_monitor=True)
    readback = Cpt(PytmcSignal, ":fActPosition", io="i", kind="hinted", auto_monitor=True)
    done = Cpt(PytmcSignal, ":bDone", io="i", kind="normal", auto_monitor=True)
    actuate = Cpt(PytmcSignal, ":bMoveCmd", io="io", kind="normal")
    stop_signal = Cpt(PytmcSignal, ":bHalt", io="io", kind="normal")
    reset_signal = Cpt(PytmcSignal, ":bReset", io="io", kind="normal")

    # Motion Configuration
    velocity = Cpt(PytmcSignal, ":fVelocity", io="io", kind="config", auto_monitor=True)
    acceleration = Cpt(PytmcSignal, ":fAcceleration", io="io", kind="config", auto_monitor=True)
    deceleration = Cpt(PytmcSignal, ":fDeceleration", io="io", kind="config", auto_monitor=True)
    jerk = Cpt(PytmcSignal, ":fJerk", io="io", kind="config", auto_monitor=True)
    enable_mode = Cpt(PytmcSignal, ":eEnableMode", io="io", kind="config")
    brake_mode = Cpt(PytmcSignal, ":eBrakeMode", io="io", kind="config")

    # Status Bits
    motor_is_moving = Cpt(PytmcSignal, ":bMoving", io="i", kind="normal", auto_monitor=True)
    motor_is_moving_negative = Cpt(PytmcSignal, ":bNegativeDirection", io="i", kind="normal", auto_monitor=True)
    motor_is_moving_positive = Cpt(PytmcSignal, ":bPositiveDirection", io="i", kind="normal", auto_monitor=True)
    power_is_enabled = Cpt(PytmcSignal, ":bPowerIsEnabled", io="i", kind="normal", auto_monitor=True)
    fwd_enabled = Cpt(PytmcSignal, ":bForwardEnabled", io="i", kind="normal", auto_monitor=True)
    bwd_enabled = Cpt(PytmcSignal, ":bBackwardEnabled", io="i", kind="normal", auto_monitor=True)
    high_limit_switch = Cpt(InvertedBoolEpicsSignal, "fwd_enabled", kind="normal", add_prefix=())
    low_limit_switch = Cpt(InvertedBoolEpicsSignal, "bwd_enabled", kind="normal", add_prefix=())
    negative_dir_enabled = Cpt(PytmcSignal, ":bNegativeMotionIsEnabled", io="i", kind="normal", auto_monitor=True)
    positive_dir_enabled = Cpt(PytmcSignal, ":bPositiveMotionIsEnabled", io="i", kind="normal", auto_monitor=True)
    command = Cpt(PytmcSignal, ":eCommand", io="i", kind="normal", auto_monitor=True)
    motor_egu = Cpt(PytmcSignal, ":NC:Eu:Val", io="i", kind="normal", string=True, auto_monitor=True)

    # Limits (configuration)
    low_limit_travel = Cpt(EpicsSignal, ':NC:MinPos:Val_RBV', write_pv=':NC:MinPos:Goal', kind='config', auto_monitor=True)
    high_limit_travel = Cpt(EpicsSignal, ':NC:MaxPos:Val_RBV', write_pv=':NC:MaxPos:Goal', kind='config', auto_monitor=True)
    low_limit_enable = Cpt(EnabledDisabledSignal, ':NC:SoftPosMinOn:Val_RBV', write_pv=':NC:SoftPosMinOn:Goal', kind='config', auto_monitor=True)
    high_limit_enable = Cpt(EnabledDisabledSignal, ':NC:SoftPosMaxOn:Val_RBV', write_pv=':NC:SoftPosMaxOn:Goal', kind='config', auto_monitor=True)

    # Position correction / backlash
    pos_correction = Cpt(EnabledDisabledSignal, ':NC:PosCorr:Val_RBV', write_pv=':NC:PosCorr:Goal', kind='config', auto_monitor=True)
    backlash = Cpt(EpicsSignal, ':NC:Backlash:Val_RBV', write_pv=':NC:Backlash:Goal', kind='config', auto_monitor=True)
    pos_cor_status = Cpt(PytmcSignal, ":bBacklashStatus", io="i", kind="normal", auto_monitor=True)

    # Homing status/config
    homed = Cpt(PytmcSignal, ":bHomed", io="i", kind='normal', auto_monitor=True)
    home_mode = Cpt(PytmcSignal, ":eHomeMode", io="io", kind="config")

    tab_whitelist = [
        "reset",
        "set_low_limit",
        "set_high_limit",
        "clear_limits",
        "check_limit_switches",
        "enabled",
        "homed",
        "Position"
    ]

    set_metadata(actuate, dict(variety='command', value=1))
    set_metadata(stop_signal, dict(variety='command-proc', value=1))
    set_metadata(done, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving_negative, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving_positive, dict(variety='bitmask', bits=1))
    set_metadata(negative_dir_enabled, dict(variety='bitmask', bits=1))
    set_metadata(positive_dir_enabled, dict(variety='bitmask', bits=1))
    set_metadata(power_is_enabled, dict(variety='bitmask', bits=1))
    set_metadata(high_limit_switch, dict(variety='bitmask', bits=1))
    set_metadata(low_limit_switch, dict(variety='bitmask', bits=1))
    set_metadata(homed, dict(variety='bitmask', bits=1))

    tolerated_alarm = AlarmSeverity.NO_ALARM

    _alarm_filter_installed: ClassVar[bool] = False
    _moved_in_session: bool
    _egu = ''

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
        """
        Initialization adapted from EpicsMotorInterface.

        Ensures log filters are installed, .name is set on readback for UI/logs,
        and sets up default metadata for the session.
        """
        self._moved_in_session = False
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
        self.motor_egu.subscribe(self._cache_egu)
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
    @raise_if_disconnected
    def position(self):
        """The current position of the motor in its engineering units

        Returns
        -------
        position : float
        """
        return self.readback.get()

    def _cache_egu(self, value=None, **kwargs):
        """Cache motor engineering unit string."""
        if value is not None:
            self._egu = value

    @property
    def egu(self):
        """
        The engineering units (EGU) for this motor. Updated via the motor_egu PV.
        """
        return self._egu

    def move(self, position: float, wait: bool = True, **kwargs) -> MoveStatus:
        """
        Reused from EpicsMotorInterface:
        Sets _moved_in_session True, then calls superclass move.
        """
        self._moved_in_session = True
        return super().move(position, wait=wait, **kwargs)

    def _get_epics_limits(self) -> tuple[float, float]:
        """
        Nearly identical to EpicsMotorInterface._get_epics_limits.
        Returns tuple (low_limit, high_limit), or (0,0) if uninitialized.
        """
        limits = self.setpoint.limits
        if limits is None or limits == (None, None):
            # Not initialized
            return (0, 0)
        return limits

    def _instance_error_filter(self, record: logging.LogRecord) -> bool:
        """
        Instance-specific motion error filter.

        Logic directly reused from EpicsMotorInterface.
        Filters alarm log messages unless a move is requested in this session.
        """
        return self._moved_in_session or ' alarm ' not in record.msg

    def _install_motion_error_filter(self) -> None:
        """
        Applies the class _motion_error_filter to self.log.
        Pattern adapted from EpicsMotorInterface, now installed per instance.
        """
        if not self._alarm_filter_installed:
            self.log.logger.addFilter(EpicsMotorInterfaceAlarmFilter())
            self._alarm_filter_installed = True

    @property
    @raise_if_disconnected
    def limits(self) -> tuple[float, float]:
        """
        Override limits property to always return the latest values from
        the soft limit PVs (low_limit_travel and high_limit_travel).

        This ensures no stale/cached values are reported.
        """
        return (
            self.low_limit_travel.get(),
            self.high_limit_travel.get(),
        )

    @limits.setter
    def limits(self, lims: tuple[float, float]):
        """
        Write to the epics limits on setattr.

        Duplicated from EpicsMotorInterface for API consistency:
        Expects a tuple of two elements, the low and high limits to set.
        """
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
        Check the limit switches.

        Logic structure reused from EpicsMotorInterface for API consistency.
        Returns a string summary.
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
        Set the low limit. Adapted from EpicsMotorInterface.

        Parameters
        -------
        value : float
            Limit of travel in the negative direction.

        Raises
        ---
        ValueError
            When in motion or position outside of limit.
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
        Limit of travel in the positive direction. Adapted from EpicsMotorInterface.

        Parameters
        -------
        value : float
            High limit value to be set.

        Raises
        ---
        ValueError
            When in motion or position outside of limit.
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
        """
        Set both low and high limits to 0.

        Duplicated from EpicsMotorInterface for function and API consistency.
        """
        self.high_limit_travel.put(0)
        self.low_limit_travel.put(0)

    @property
    @raise_if_disconnected
    def moving(self):
        """
        Whether or not the motor is moving.

        Duplicated logic from EpicsMotorInterface for API consistency.

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

    @raise_if_disconnected
    def reset(self, *, success=False):
        self.reset.put(1, wait=False)

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
        """
        Callback from EPICS, indicating a change in position.
        Signature and structure reused from EpicsMotorInterface.
        """
        self._set_position(value)

    @required_for_connection
    @done.sub_value
    def _move_changed(self, timestamp=None, value=None, sub_type=None, **kwargs):
        """
        Callback from EPICS, indicating that movement status has changed.

        Signature and event logic reused from EpicsMotorInterface.
        """
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

        Logic reused from EpicsMotorInterface for session state reset.
        """
        super()._done_moving(value=value, **kwargs)
        if value:
            self._moved_in_session = False

    @property
    def report(self):
        """
        Report status. Adapted from EpicsMotorInterface for PV inclusion.
        """
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
   Note
    ----
    Some methods in this class are identical or adapted from BeckhoffAxis,
    to ensure the error-handling, staging, homing, and value checking logic
    behaves identically.

    Attributes
    -------
    actuate_home : PytmcSignal
        PV to trigger a homing command.
    home_mode : PytmcSignal
        PV to select the homing mode (see HomeEnum).
    plc : BeckhoffAxisPLC
        Sub-device interface for further PLC status and diagnostics.

    """
    # homed and home_mode are defined on TwinCATMotorInterface (PLC signals).
    __doc__ += basic_positioner_init
    tab_whitelist = ['clear_error', 'home', 'stage']

    plc = Cpt(BeckhoffAxisPLC, ':', kind='normal',
              doc='PLC error handling and aux functions.')

    def subscribe(
        self,
        callback: Callable,
        event_type: Optional[str] = None,
        run: bool = True,
    ) -> int:
        """
        Mostly adapted from BeckhoffAxis.subscribe.

        This is a thin wrapper over subscribe for custom error handling
        to intercept the normal end of move handler.

        See documentation in BeckhoffAxis.subscribe for complete details.
        """
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
        Adapted nearly verbatim from BeckhoffAxis._end_move_cb.

        Checks for errors via PLC, attaches error message/details/code
        to the MoveStatus if an error is detected. Otherwise, signals
        success.
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
        """
        Identical to BeckhoffAxis.clear_error.
        Clears any active motion/plc errors on this axis.
        """
        self.plc.cmd_err_reset.put(1)

    def stage(self):
        """
        Stage the TwinCAT axis.

        Implementation identical to BeckhoffAxis.stage and EpicsMotorInterface.stage:
        Simply clears any errors, then calls parent stage.
        """
        self.clear_error()
        return super().stage()

    @raise_if_disconnected
    def home(self, wait: bool = True, **kwargs):
        """
        Adapted from BeckhoffAxis.home.

        Executes the PLC-programmed home routine.
        For hardware where only one homing method may be active/configured.
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
        Functionally adapted from BeckhoffAxis.move.

        Sets up tailored end-of-move handler and error capture, as in BeckhoffAxis.
        Prepares a new MoveStatus for custom error interpretation.
        """
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
        Functionally identical/adapted from BeckhoffAxis.check_value.

        Checks both limits and velocity (must be nonzero) before permitting a move.
        """
        super().check_value(pos)
        velo = self.velocity.get()
        if velo <= 0:
            raise RuntimeError(
                f'{self.name} velocity is {velo}, which is not valid. '
                'Please configure a nonzero, positive velocity.'
            )


class TwinCATMREAxis(TwinCATAxis):
    """
    Motor-Record Edition of :class:`TwinCATAxis`.

    Identical behavior and interface to :class:`TwinCATAxis`, but every
    process variable is bound to an EPICS ``tcmotor`` record dot-notation
    field (``.VAL``, ``.RBV``, ``.DMOV``, ``.VELO``, ``.MSTA`` ...) instead
    of the raw TwinCAT PLC pytmc tags (``fPosition``, ``bDone`` ...).

    This exists because the firmware moved to a motor-record-compatible
    presentation while existing user interfaces still depend on the original
    :class:`TwinCATAxis`. Use :class:`TwinCATAxis` for the legacy PLC-tag
    layout and :class:`TwinCATMREAxis` for motor-record IOCs.

    Only the component bindings differ from :class:`TwinCATAxis`; all motion,
    limit, status, homing, and error-handling logic is inherited unchanged
    except where a record field demands a different access pattern (see
    :meth:`home` and :meth:`check_value`).

    Notes
    -----
    The PLC sub-device (``plc``) and the deceleration/jerk/enable-mode/
    direction-status tags have no ``tcmotor`` record equivalent, so they
    continue to use :class:`PytmcSignal` against the PLC PVs.
    """
    # Position: tcmotor record dot-notation fields
    setpoint = Cpt(EpicsSignal, ".VAL", kind="hinted",
                   auto_monitor=True, doc="Desired position (tcmotor.VAL)")
    readback = Cpt(EpicsSignal, ".RBV", kind="hinted",
                   auto_monitor=True, doc="Actual position readback (tcmotor.RBV)")
    done = Cpt(EpicsSignalRO, ".DMOV", kind="normal",
               auto_monitor=True, doc="Done moving (tcmotor.DMOV)")
    stop_signal = Cpt(EpicsSignal, ".STOP", kind="normal",
                      doc="Stop command (tcmotor.STOP)")
    # actuate overrides , MRE owns the actuation now
    actuate = None

    # Motion configuration: tcmotor record fields
    velocity = Cpt(EpicsSignal, ".VELO", kind="config",
                   auto_monitor=True, doc="Velocity (tcmotor.VELO)")
    velocity_base = Cpt(EpicsSignal, ".VBAS", kind="config",
                        auto_monitor=True,
                        doc="Base velocity (tcmotor.VBAS -> fVelocityBase)")
    velocity_max = Cpt(EpicsSignal, ".VMAX", kind="config",
                       auto_monitor=True,
                       doc="Max velocity (tcmotor.VMAX -> fVelocityMax)")
    acceleration = Cpt(EpicsSignal, ".ACCS", kind="config",
                       auto_monitor=True, doc="Acceleration (tcmotor.ACCS)")
    # deceleration, jerk, enable_mode, brake_mode: inherited unchanged from
    # TwinCATMotorInterface (PLC tags, no tcmotor record equivalent).

    # Status bits: tcmotor fields where available
    motor_is_moving = Cpt(EpicsSignal, ".MOVN", kind="normal",
                          auto_monitor=True, doc="Motor is moving (tcmotor.MOVN)")
    # motor_is_moving_negative/positive and power_is_enabled: inherited unchanged.
    # tcmotor already presents limit switch state directly via HLS/LLS, so no
    # InvertedBoolEpicsSignal indirection is needed here. The fwd_enabled /
    # bwd_enabled components that the legacy class used as the inversion source
    # are removed (set to None) so they do not populate the Typhos screen.
    fwd_enabled = None
    bwd_enabled = None
    high_limit_switch = Cpt(EpicsSignalRO, ".HLS", kind="normal",
                            auto_monitor=True,
                            doc="Forward (high) limit switch (tcmotor.HLS)")
    low_limit_switch = Cpt(EpicsSignalRO, ".LLS", kind="normal",
                           auto_monitor=True,
                           doc="Backward (low) limit switch (tcmotor.LLS)")
    # negative_dir_enabled, positive_dir_enabled, command: inherited unchanged.
    motor_egu = Cpt(EpicsSignal, ".EGU", kind="normal", string=True,
                    auto_monitor=True, doc="Engineering units (tcmotor.EGU)")

    # SPMG state machine and MSTA status word (tcmotor)
    spmg = Cpt(EpicsSignal, ".SPMG", kind="normal",
               auto_monitor=True, string=True,
               doc="Stop/Pause/Move/Go (tcmotor.SPMG)")
    msta = Cpt(EpicsSignal, ".MSTA", kind="normal",
               auto_monitor=True, doc="Motor status word (tcmotor.MSTA)")

    # Soft limits: tcmotor record fields
    # HLM/LLM write to NC:MaxPos:Goal / NC:MinPos:Goal via tcmotor OUT_HLM/OUT_LLM
    low_limit_travel = Cpt(EpicsSignal, ".LLM", kind="config",
                           auto_monitor=True,
                           doc="Low soft limit (tcmotor.LLM -> NC:MinPos:Goal)")
    high_limit_travel = Cpt(EpicsSignal, ".HLM", kind="config",
                            auto_monitor=True,
                            doc="High soft limit (tcmotor.HLM -> NC:MaxPos:Goal)")
    # low/high_limit_enable inherited from TwinCATMotorInterface
    # (EnabledDisabledSignal on the shared NC:SoftPos*On records).

    # Backlash via tcmotor .BDST (writes to NC:Backlash:Goal via OUT_BDST).
    # pos_correction and pos_cor_status have no tcmotor record equivalent and
    # are inherited from TwinCATMotorInterface.
    backlash = Cpt(EpicsSignal, '.BDST', kind='config',
                   auto_monitor=True,
                   doc='Backlash correction (tcmotor.BDST)')

    # Homing: tcmotor HOMF/HOMR command fields
    # homed and home_mode are inherited from TwinCATAxis (PLC :bHomed / :eHomeMode).
    # HOMF sets eHomeMode=LOW_LIMIT + pulses bHomeCmd; HOMR sets HIGH_LIMIT.
    # Only use HOMF/HOMR when home_mode matches, otherwise use bHomeCmd directly.
    home_cmd_fwd = Cpt(EpicsSignal, '.HOMF', kind='normal',
                       doc='Home via low limit switch (tcmotor.HOMF)')
    home_cmd_rev = Cpt(EpicsSignal, '.HOMR', kind='normal',
                       doc='Home via high limit switch (tcmotor.HOMR)')

    set_metadata(stop_signal, dict(variety='command-proc', value=1))
    set_metadata(done, dict(variety='bitmask', bits=1))
    set_metadata(motor_is_moving, dict(variety='bitmask', bits=1))
    set_metadata(high_limit_switch, dict(variety='bitmask', bits=1))
    set_metadata(low_limit_switch, dict(variety='bitmask', bits=1))
    set_metadata(msta, dict(variety='bitmask', bits=16))
    set_metadata(home_cmd_fwd, dict(variety='command-proc', value=1))
    set_metadata(home_cmd_rev, dict(variety='command-proc', value=1))

    @property
    @raise_if_disconnected
    def is_homed(self) -> bool:
        """
        Whether the axis is at its home position.

        Fixes the legacy ``homed`` property which referenced a nonexistent
        ``motor_is_homed`` component. Here it reads the ``homed`` signal
        (``bHomed``) directly.
        """
        return bool(self.homed.get())

    @raise_if_disconnected
    def reset(self, *, success=False):
        """
        Pulse the reset signal.

        Fixes the legacy ``reset`` which called ``self.reset.put`` (the bound
        method) instead of the ``reset_signal`` component.
        """
        self.reset_signal.put(1, wait=False)

    @raise_if_disconnected
    def home(self, wait: bool = True, **kwargs):
        """
        Adapted from BeckhoffAxis.home for the motor-record layout.

        Uses the tcmotor ``HOMF``/``HOMR`` command fields when ``home_mode``
        matches ``LOW_LIMIT``/``HIGH_LIMIT`` respectively, otherwise falls
        back to pulsing ``bHomeCmd`` directly via ``plc.cmd_home``.
        """
        self._run_subs(sub_type=self._SUB_REQ_DONE, success=False)
        self._reset_sub(self._SUB_REQ_DONE)

        status = MoveStatus(self, self.plc.home_pos.get(),
                            timeout=None, settle_time=self._settle_time)

        mode = self.home_mode.get(as_string=True)
        if mode == 'LOW_LIMIT':
            self.home_cmd_fwd.put(1)
        elif mode == 'HIGH_LIMIT':
            self.home_cmd_rev.put(1)
        else:
            # Other modes: pulse bHomeCmd directly
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
