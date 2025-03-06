"""
Module for LCLS's special motor records.
"""
import functools
import logging
import shutil
import subprocess
import time
from enum import Enum
from typing import Callable, ClassVar, Optional

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.epics_motor import EpicsMotor
from ophyd.ophydobj import Kind
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import DeviceStatus, MoveStatus, SubscriptionStatus
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError
from ophyd.utils.epics_pvs import raise_if_disconnected
from pcdsutils.ext_scripts import get_hutch_name
from prettytable import PrettyTable

from pcdsdevices.pv_positioner import (PVPositionerComparator,
                                       PVPositionerIsClose)

from .device import UpdateComponent as UpCpt
from .doc_stubs import basic_positioner_init
from .eps import EPS
from .interface import FltMvInterface
from .pseudopos import OffsetMotorBase, delay_class_factory
from .registry import device_registry
from .signal import EpicsSignalEditMD, EpicsSignalROEditMD, PytmcSignal
from .utils import get_status_float, get_status_value
from .variety import set_metadata

logger = logging.getLogger(__name__)


class MstaEnum(Enum):
    """
    Enum for the EPICS motor record .MSTA field bits.
    """
    # Note: the motor record docs start bit numbering at 1, but the MSTA bits
    # start at 0.
    direction = 0       # last raw move direction (0: negative, 1: positive)
    done = 1            # motion is complete
    plus_ls = 2         # plus limit switch is hit
    home_ls = 3         # state of the home limit switch
    # Bit 4 is un-used
    # closed-loop positioning enabled, called "position" in the docs
    closed_loop = 5
    slip_stall = 6      # slip stall is detected
    home = 7            # at the home position
    enc_present = 8     # encoder is present. Called "present" in the docs.
    problem = 9         # driver stopped polling, or there's a hardware problem
    moving = 10         # the motor has a non-zero velocity (it's moving)
    gain_support = 11   # the motor supports closed loop control
    comm_error = 12     # controller communication error
    minus_ls = 13       # minus limit switch is hit
    homed = 14          # the motor has been homed


class NewportMstaEnum(Enum):
    """
    Enum for the LCLS Newport XPS8 EPICS motor record .MSTA field bits.
    """
    # Note: the motor record docs start bit numbering at 1, but the MSTA bits
    # start at 0.
    direction = 0       # last raw move direction (0: negative, 1: positive)
    done = 1            # motion is complete
    plus_ls = 2         # plus limit switch is hit
    home_ls = 3         # state of the home limit switch
    slip = 4            # continue of slip stall
    # closed-loop positioning enabled, called "position" in the docs
    closed_loop = 5
    slip_stall = 6      # slip stall is detected
    home = 7            # at the home position
    enc_present = 8     # encoder is present. Called "present" in the docs.
    problem = 9         # driver stopped polling, or there's a hardware problem
    moving = 10         # the motor has a non-zero velocity (it's moving)
    gain_support = 11   # the motor supports closed loop control
    comm_error = 12     # controller communication error
    minus_ls = 13       # minus limit switch is hit
    homed = 14          # the motor has been homed
    powerup = 15        # the motor has been homed
    mchb = 16           # MCode heart-beat
    stall = 17          # stall detected
    # 6 un-used bits for byte alignment
    errno = 24          # error number


class ImsMstaEnum(Enum):
    """
    Enum for the LCLS IMS EPICS motor record .MSTA field bits.
    """
    # Note: the motor record docs start bit numbering at 1, but the MSTA bits
    # start at 0.
    direction = 0       # last raw move direction (0: negative, 1: positive)
    done = 1            # motion is complete
    plus_ls = 2         # plus limit switch is hit
    home_ls = 3         # state of the home limit switch
    slip = 4            # continue of slip stall detect
    # closed-loop positioning enabled, called "position" in the docs
    closed_loop = 5
    slip_stall = 6      # slip stall is detected
    home = 7            # at the home position
    enc_enable = 8      # encoder is enabled ("EE")
    problem = 9         # driver stopped polling, or there's a hardware problem
    moving = 10         # the motor has a non-zero velocity (it's moving)
    gain_support = 11   # the motor supports closed loop control
    comm_error = 12     # controller communication error
    minus_ls = 13       # minus limit switch is hit
    homed = 14          # the motor has been homed
    errno = 15          # error number (7 bits)
    stall = 22          # stall detected
    trip_enabled = 23   # trip enabled
    powerup = 24        # power cycled
    ne = 25             # numeric enable
    by0 = 26            # MCode not running (BY = 0)
    # 4 un-used bits for byte alignment
    not_init = 31          # initializaton not finished


class EpicsMotorInterface(FltMvInterface, EpicsMotor):
    """
    The standard EpicsMotor class, but with our interface attached.

    This includes some PCDS preferences, but not any IOC differences.

    Notes
    -----
    The full list of preferences implemented here are:

        1. Use the FltMvInterface mixin class for some name aliases and
           bells-and-whistles level functions.
        2. Instead of using the limit fields on the setpoint PV, the EPICS
           motor class has the 'LLM' and 'HLM' soft limit fields for
           convenient usage. Unfortunately, pyepics does not update its
           internal cache of the limits after the first get attempt. We
           therefore disregard the internal limits of the PV and use the soft
           limit records exclusively.
        3. The disable puts field '.DISP' is added, along with :meth:`enable`
           and :meth:`disable` convenience methods. When '.DISP' is 1, puts to
           the motor record will be ignored, effectively disabling the
           interface.
        4. The description field keeps track of the motors scientific use along
           the beamline.
        5. The post-move error logs only appear after a move in that session,
           not after a move in another user's session. This is achieved by
           keeping track of whether or not a move was caused by this session
           and filtering self.log appropriately.
    """
    # Allow metadata overrides by replacing the signal classes
    user_readback = UpCpt(cls=EpicsSignalROEditMD)
    user_setpoint = UpCpt(cls=EpicsSignalEditMD)
    # Re-implement cpts for subscription ease
    high_limit_travel = UpCpt()
    low_limit_travel = UpCpt()

    # Enable/Disable puts
    disabled = Cpt(EpicsSignal, ".DISP", kind='omitted')
    set_metadata(disabled, dict(variety='bitmask',
                                bits=1))
    # Description is valuable
    description = Cpt(EpicsSignal, '.DESC', kind='normal')
    # Current Dial position
    dial_position = Cpt(EpicsSignalRO, '.DRBV', kind='normal')

    tab_whitelist = ["set_current_position", "home", "velocity",
                     "check_limit_switches", "get_low_limit",
                     "set_low_limit", "get_high_limit", "set_high_limit",
                     "velocity_base", "velocity_max"]

    set_metadata(EpicsMotor.home_forward, dict(variety='command-proc',
                                               tags={"confirm"},
                                               value=1))
    EpicsMotor.home_forward.kind = Kind.normal
    set_metadata(EpicsMotor.home_reverse, dict(variety='command-proc',
                                               tags={"confirm"},
                                               value=1))
    EpicsMotor.home_reverse.kind = Kind.normal
    set_metadata(EpicsMotor.low_limit_switch, dict(variety='bitmask', bits=1))
    EpicsMotor.low_limit_switch.kind = Kind.normal
    set_metadata(EpicsMotor.high_limit_switch, dict(variety='bitmask', bits=1))
    EpicsMotor.high_limit_switch.kind = Kind.normal
    set_metadata(EpicsMotor.motor_done_move, dict(variety='bitmask', bits=1))
    EpicsMotor.motor_done_move.kind = Kind.omitted
    set_metadata(EpicsMotor.motor_is_moving, dict(variety='bitmask', bits=1))
    EpicsMotor.motor_is_moving.kind = Kind.normal
    set_metadata(EpicsMotor.motor_stop, dict(variety='command-proc', value=1))
    EpicsMotor.motor_stop.kind = Kind.normal
    EpicsMotor.high_limit_travel.kind = Kind.config
    EpicsMotor.low_limit_travel.kind = Kind.config
    EpicsMotor.direction_of_travel.kind = Kind.normal

    velocity_base = Cpt(EpicsSignal, '.VBAS', kind='omitted')
    velocity_max = Cpt(EpicsSignal, '.VMAX', kind='config')

    msta_raw = Cpt(EpicsSignalRO, '.MSTA', kind='omitted')

    _alarm_filter_installed: ClassVar[bool] = False
    _moved_in_session: bool
    _egu: str

    def __init__(self, *args, **kwargs):
        self._moved_in_session = False
        self._egu = ''
        super().__init__(*args, **kwargs)
        self._install_motion_error_filter()
        self.motor_egu.subscribe(self._cache_egu)

    @high_limit_travel.sub_value
    def _update_hlt(self, value, **kwargs):
        """
        Update ctrl metadata when the high limit switch position updates.
        """
        self.user_readback._override_metadata(upper_ctrl_limit=value)
        self.user_setpoint._override_metadata(upper_ctrl_limit=value)

    @low_limit_travel.sub_value
    def _update_llt(self, value, **kwargs):
        """
        Update ctrl metadata when the low limit switch position updates.
        """
        self.user_readback._override_metadata(lower_ctrl_limit=value)
        self.user_setpoint._override_metadata(lower_ctrl_limit=value)

    def move(self, position: float, wait: bool = True, **kwargs) -> MoveStatus:
        self._moved_in_session = True
        return super().move(position, wait=wait, **kwargs)

    def format_status_info(self, status_info):
        """
        Override status info handler to render the motor.

        Display motor status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        precision = self.user_readback.metadata['precision'] or 3
        description = get_status_value(status_info, 'description', 'value')
        units = get_status_value(status_info, 'user_setpoint', 'units')
        dial = get_status_float(status_info, 'dial_position', 'value',
                                precision=precision)
        user = get_status_float(status_info, 'position', precision=precision)

        low, high = self.limits
        switch_limits = self.check_limit_switches()

        name = ' '.join(self.prefix.split(':'))
        name = f'{name}: {self.prefix}'
        if description:
            name = f'{description}: {self.prefix}'

        return f"""\
{name}
Current position (user, dial): {user}, {dial} [{units}]
User limits (low, high): {low:.{precision}f}, {high:.{precision}f} [{units}]
Preset position: {self.presets.state()}
Limit Switch: {switch_limits}
"""

    @property
    def limits(self) -> tuple[float, float]:
        """Override the limits attribute"""
        return self._get_epics_limits()

    def _get_epics_limits(self) -> tuple[float, float]:
        limits = self.user_setpoint.limits
        if limits is None or limits == (None, None):
            # Not initialized
            return (0, 0)
        return limits

    @property
    def msta(self):
        """
        Returns the msta fields as a dictionary.
        """
        # the MSTA field is a float for some reason...
        val = int(self.msta_raw.get())
        d = dict()
        for bit in MstaEnum:
            d[bit.name] = (val >> bit.value) & 0x1
        return d

    @property
    def homed(self):
        """
        Get the home status of the motor as reported by the MSTA field.
        """
        msta = self.msta
        return bool(msta[MstaEnum.homed.name])

    @limits.setter
    def limits(self, lims: tuple[float, float]):
        """
        Write to the epics limits on setattr

        Expects a tuple of two elements, the low and high limits to set.
        """
        # Wrong len is probably a bigger mistake
        if len(lims) != 2:
            raise ValueError("Limits should be a tuple of 2 values.")
        # Adjust for moment of dsylexia
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

    def enable(self):
        """
        Enables the motor.

        When disabled, all EPICS puts to the base record will be dropped.
        """

        return self.disabled.put(value=0)

    def disable(self):
        """
        Disables the motor.

        When disabled, all EPICS puts to the base record will be dropped.
        """

        return self.disabled.put(value=1)

    def check_value(self, value):
        """
        Raise an exception if the motor cannot move to value.

        The full list of checks done in this method:

            - Check if the value is within the soft limits of the motor.
            - Check if the motor is disabled ('.DISP' field).

        Raises
        ------
        MotorDisabledError
            If the motor is passed any motion command when disabled.

        ~ophyd.utils.errors.LimitError
            When the provided value is outside the range of the low
            and high limits.
        """

        # First check that the user has returned a valid EPICS value. It will
        # not consult the limits of the PV itself because limits=False
        super().check_value(value)

        # Find the soft limit values from EPICS records and check that this
        # command will be accepted by the motor
        if any(self.limits):
            if not (self.low_limit <= value <= self.high_limit):
                raise LimitError("Value {} outside of range: [{}, {}]"
                                 .format(value, self.low_limit,
                                         self.high_limit))

        # Find the value for the disabled attribute
        if self.disabled.get() == 1:
            raise MotorDisabledError("Motor is not enabled. Motion requests "
                                     "ignored")

    def check_limit_switches(self):
        """
        Check the limits switches.

        Returns
        -------
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

    def get_low_limit(self):
        """Get the low limit."""
        return self.low_limit_travel.get()

    def set_low_limit(self, value):
        """
        Set the low limit.

        Parameters
        ----------
        value : float
            Limit of travel in the negative direction.

        Raises
        ------
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
                             f'high limit: {_current_high_limit}')

        # update EPICS limits
        self.low_limit_travel.put(value)

    def get_high_limit(self):
        """Get high limit."""
        return self.high_limit_travel.get()

    def set_high_limit(self, value):
        """
        Limit of travel in the positive direction.

        Parameters
        ----------
        value : float
            High limit value to be set.

        Raises
        ------
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

    @raise_if_disconnected
    def set_current_position(self, pos):
        '''Configure the motor user position to the given value

        Override ophyd's method temporarily for error handling.

        Parameters
        ----------
        pos : number
           Position to set.
        '''
        self.set_use_switch.put(1, wait=True)
        try:
            self.user_setpoint.put(pos, wait=True, force=True)
        finally:
            self.set_use_switch.put(0, wait=True)

    @property
    def egu(self) -> str:
        """
        Engineering units str if available, otherwise ''

        Use the monitored/cached value rather than checking EPICS.
        """
        return self._egu

    def _cache_egu(self, value: str, **kwargs) -> None:
        """
        Cache the value of EGU for later use in the egu property.
        """
        self._egu = value

    def _instance_error_filter(self, record: logging.LogRecord) -> bool:
        """
        Instance-specific motion error filter.

        This filter will remove log messages that contain the
        keyword "alarm" unless a move was requested in this
        session and is active.

        Returns True if the message should pass, or False if the message
        should be filtered.
        """
        return self._moved_in_session or ' alarm ' not in record.msg

    def _install_motion_error_filter(self) -> None:
        """
        Applies the class _motion_error_filter to self.log
        """
        if not EpicsMotorInterface._alarm_filter_installed:
            EpicsMotorInterface._alarm_filter_installed = True
            self.log.logger.addFilter(EpicsMotorInterfaceAlarmFilter())

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
        """
        Mark that a move have not yet been requested in this session.
        """
        self._moved_in_session = False


class EpicsMotorInterfaceAlarmFilter(logging.Filter):
    """
    Log filter dispatcher for the EpicsMotorInterface alarm filters.

    Finds the EpicsMotorInterface object associated with a ophyd.objects log
    message and gives it a chance to filter the log message out.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        """Find the motor in the device registry and run its filter."""
        try:
            name = record.ophyd_object_name
        except AttributeError:
            # Fails if not the ophyd.objects logger -> ignore
            return True
        try:
            obj = device_registry[name]
        except KeyError:
            # Fails if the device was destroyed - can we even get here?
            return True
        try:
            filt = obj._instance_error_filter
        except AttributeError:
            # Fails if the device is not an EpicsMotorInterface -> ignore
            return True
        return filt(record)


class PCDSMotorBase(EpicsMotorInterface):
    """
    EpicsMotor for PCDS.

    This incapsulates all motor record implementations standard for PCDS,
    including but not exclusive to Pico, Piezo, IMS and Newport motors. While
    these types of motors may have additional records and configuration
    requirements, this class is meant to handle the shared records between
    them.

    Notes
    -----
    The purpose of this class is to account for the differences between the
    community Motor Record and the PCDS Motor Record. The points that matter
    for this class are:

        1. The 'TDIR' field does not exist on the PCDS implementation. This
        indicates what direction the motor has travelled last. To account for
        this difference, we use the :meth:`._pos_changed` callback to keep
        track of which direction we believe the motor to be travelling
        and store this in a simple :class:`~ophyd.signal.Signal`.
        2. The 'SPG' field implements the three states used in the LCLS
        motor record.  This is a reduced version of the standard EPICS
        'SPMG' field.  Setting to 'STOP', 'PAUSE' and 'GO'  will respectively
        stop motor movement, pause a move in progress, or resume a paused move.
        3. In some cases, puts to the setpoint PV cannot be waited on. In fact
        this seems to brick the whole python session, requiring a slightly
        modified set_current_position method.
    """

    # Disable missing field that our EPICS motor record lacks
    # This attribute is tracked by the _pos_changed callback
    direction_of_travel = Cpt(Signal, kind='omitted')
    # This attribute changes if the motor is stopped and unable to move 'Stop',
    # paused and ready to resume on Go 'Paused', and to resume a move 'Go'.
    motor_spg = Cpt(EpicsSignal, '.SPG', kind='omitted')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs[self.motor_spg] = 2

    def spg_stop(self):
        """
        Stops the motor.

        After which the motor must be set back to 'go' via :meth:`.spg_go` in
        order to move again.
        """

        return self.motor_spg.put(value='Stop')

    def spg_pause(self):
        """
        Pauses a move.

        Move will resume if :meth:`.go` is called.
        """

        return self.motor_spg.put(value='Pause')

    def spg_go(self):
        """Resumes paused movement."""
        return self.motor_spg.put(value='Go')

    def check_value(self, value):
        """
        Raise an exception if the motor cannot move to value.

        The full list of checks done in this method:

            - Check if the value is within the soft limits of the motor.
            - Check if the motor is disabled ('.DISP' field).
            - Check if the spg field is on "pause" or "stop".

        Raises
        ------
        MotorDisabledError
            If the motor is passed any motion command when disabled, or if
            the '.SPG' field is not set to 'Go'.

        ~ophyd.utils.errors.LimitError
            When the provided value is outside the range of the low
            and high limits.
        """

        super().check_value(value)

        if self.motor_spg.get() in [0, 'Stop']:
            raise MotorDisabledError("Motor is stopped.  Motion requests "
                                     "ignored until motor is set to 'Go'")

        if self.motor_spg.get() in [1, 'Pause']:
            raise MotorDisabledError("Motor is paused.  If a move is set, "
                                     "motion will resume when motor is set "
                                     "to 'Go'")

    def _pos_changed(self, timestamp=None, old_value=None,
                     value=None, **kwargs):
        # Store the internal travelling direction of the motor to account for
        # the fact that our EPICS motor does not have TDIR field
        try:
            comparison = int(value > old_value)
            self.direction_of_travel.put(comparison)
        except TypeError:
            # We have some sort of null/None/default value
            logger.debug('Could not compare value=%s > old_value=%s',
                         value, old_value)
        # Pass information to PositionerBase
        super()._pos_changed(timestamp=timestamp, old_value=old_value,
                             value=value, **kwargs)

    def screen(self):
        """
        Opens Epics motor expert screen e.g. for reseting motor after stalling.
        """
        executable = 'motor-expert-screen'
        if shutil.which(executable) is None:
            logger.error('%s is not on path, we cannot start the screen',
                         executable)
            return
        arg = self.prefix

        logger.info(f'Opening {executable} for {self.name}...')
        subprocess.run([executable, arg],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

    @raise_if_disconnected
    def set_current_position(self, pos):
        """
        Change the offset such that pos is the current position.

        This is a re-implementation of the ophyd set_current_position, which
        does not work on some legacy PCDS motors because they do not use the
        standard motor record. This non-standard record does not respond
        correctly to wait=True on the VAL field while SET/USE is set to SET.
        """
        self.set_use_switch.put(1, wait=True)
        try:
            # Force to ignore limits
            self.user_setpoint.put(pos, force=True)
            # Instead of waiting on the put (broken), manually check
            for _ in range(3):
                if np.isclose(self.user_setpoint.get(), pos):
                    break
                time.sleep(0.1)
        finally:
            self.set_use_switch.put(0, wait=True)


class IMS(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record for IMS motors.

    This is a subclass of :class:`PCDSMotorBase`.
    """

    __doc__ += basic_positioner_init
    # Bit masks to clear errors and flags
    _bit_flags = {'powerup': {'clear': 36,
                              'readback': 24},
                  'stall': {'clear': 40,
                            'readback': 22},
                  'error': {'clear': 48,
                            'readback': 15,
                            'mask': 0x7f}}
    # Custom IMS bit fields
    reinit_command = Cpt(EpicsSignal, '.RINI', kind='omitted')
    bit_status = Cpt(EpicsSignalRO, '.MSTA', kind='omitted')
    seq_seln = Cpt(EpicsSignal, ':SEQ_SELN', kind='omitted')
    error_severity = Cpt(EpicsSignal, '.SEVR', kind='omitted')
    part_number = Cpt(EpicsSignalRO, '.PN', kind='omitted')

    # IMS velocity has limits
    velocity = Cpt(EpicsSignal, '.VELO', limits=True, kind='config')

    tab_whitelist = [
        'reinitialize',
        'acceleration',
        'clear_.*',
        'configure',
        'get_configuration',
        'get_configuration_values',
        'get_current_values',
        'find_configuration',
        'diff_configuration'
    ]

    # The singleton parameter manager object.
    _pm = None
    # If we fail to create _pm, set bool to only try once
    _pm_init_error = False

    def stage(self):
        """
        Stage the IMS motor.

        This clears all present flags on the motor and reinitializes the motor
        if we don't register a valid part number.
        """

        # Check the part number to avoid crashing the IOC
        if not self.part_number.get() or self.error_severity.get() == 3:
            self.reinitialize(wait=True)
        # Clear any pre-existing flags
        self.clear_all_flags()
        return super().stage()

    def auto_setup(self):
        """
        Automated setup of the IMS motor.

        If necessarry this command will:

            * Reinitialize the motor.
            * Clear powerup, stall and error flags.
        """

        # Reinitialize if necessary
        if not self.part_number.get() or self.error_severity.get() == 3:
            self.reinitialize(wait=True)
        # Clear all flags
        self.clear_all_flags()

    def reinitialize(self, wait: bool = False,
                     timeout: float = 10.0) -> SubscriptionStatus:
        """
        Reinitialize the IMS motor.

        Parameters
        ----------
        wait : bool, optional
            Wait for the motor to be fully intialized.

        timeout : float, optional
            If the re-initialization takes too long, raise an error.

        Returns
        -------
        :class:`~ophyd.status.SubscriptionStatus`
            Status object reporting the initialization state of the motor.
        """
        logger.info('Reinitializing motor')
        # Issue command
        self.reinit_command.put(1)

        # Check error
        def initialize_complete(value=None, **kwargs):
            return value != 3

        # Generate a status
        st = SubscriptionStatus(
            self.error_severity,
            initialize_complete,
            timeout=timeout,
            settle_time=0.5,
        )
        # Wait on status if requested
        if wait:
            status_wait(st)
        return st

    @property
    def msta(self):
        """
        Returns the msta fields as a dictionary.
        """
        # the MSTA field is a float for some reason...
        val = int(self.msta_raw.get())
        d = dict()
        for bit in ImsMstaEnum:
            if bit.name == 'errno':
                d[bit.name] = (val >> bit.value) & 0x7F  # 7 bit error number
            else:
                d[bit.name] = (val >> bit.value) & 0x1
        return d

    def clear_all_flags(self):
        """Clear all the flags from the IMS motor."""
        # Clear all flags
        for func in (self.clear_powerup, self.clear_stall, self.clear_error):
            func(wait=True)

    def clear_powerup(self, wait=False, timeout=10):
        """Clear powerup flag."""
        return self._clear_flag('powerup', wait=wait, timeout=timeout)

    def clear_stall(self, wait=False, timeout=5):
        """Clear stall flag."""
        return self._clear_flag('stall', wait=wait, timeout=timeout)

    def clear_error(self, wait=False, timeout=10):
        """Clear error flag."""
        return self._clear_flag('error', wait=wait, timeout=timeout)

    def _clear_flag(self, flag, wait=False, timeout=10):
        """Clear flag whose information is in :attr:`._bit_flags`"""
        # Gather our flag information
        flag_info = self._bit_flags[flag]
        bit = flag_info['readback']
        mask = flag_info.get('mask', 1)

        # Create a callback function to check for bit
        def flag_is_cleared(value=None, **kwargs):
            return not bool((int(value) >> bit) & mask)

        # Check that we need to actually set the flag
        if flag_is_cleared(value=self.bit_status.get()):
            logger.debug("%s flag is not currently active", flag)
            st = DeviceStatus(self)
            st.set_finished()
            return st

        # Issue our command
        logger.info('Clearing %s flag ...', flag)
        self.seq_seln.put(flag_info['clear'])
        # Generate a status
        st = SubscriptionStatus(self.bit_status, flag_is_cleared)
        if wait:
            status_wait(st, timeout=timeout)
        return st

    @property
    def md(self):
        if self._md is None:
            raise AttributeError('Device does not have an attached md, '
                                 'and was likely not initialized from happi')
        return self._md

    @md.setter
    def md(self, new_md):
        """ initialize attributes when md is set """
        self._md = new_md
        self._extra = self._md.extraneous
        self._id = self._extra.get('_id')
        self._pvbase = self._extra.get('pvbase')
        self._stageidentity = self._extra.get('stageidentity')
        if self._stageidentity is None:
            logger.warning(f"Stage Identity has not been set for this object: {self._id}. Configure manually.")
            return
        elif self._stageidentity == "NEW":
            logger.warning(f"This is a new stage, parameter manager configuration does not exist yet. Please manually configure {self._id}")
            return
        else:
            try:
                IMS._setup_and_check_pmgr()
                self._pm.set_config(self._pvbase, self._stageidentity)
            except Exception:
                return

    def configure(self, cfgname=None):
        """
        Use the parameter manager to configure the motor.

        cfgname : str | None
            The name of the configuration to apply.  If None, use the
            configuration saved in the database.

        Returns nothing.
        """
        self._setup_and_check_pmgr()
        self._pm.apply_config(self.prefix, cfgname)

    def get_configuration(self):
        """
        Find the current configuration of the motor in the parameter manager.

        Returns the current configuration name as a string or throws an
        exception.
        """
        self._setup_and_check_pmgr()
        return self._pm.get_config(self.prefix)

    def get_configuration_values(self, cfgname=None):
        """
        Return the current configuration parameters of the motor
        in the parameter manager

        Parameters
        ----------
        cfgname : str
               The name of the configuration

        Returns
        -------
        A dictionary mapping field names to the configured values
        """
        self._setup_and_check_pmgr()
        if not cfgname:
            cfgname = self.get_configuration()
        return self._pm.get_config_values(cfgname)

    def get_current_values(self, pv=None):
        """
        Returns the current parameters for a given pv.

        Parameters
        ----------
        pv : str
          Default is None

        Returns
        -------
        cdict : dict
            A dictionary mapping field names (str) to values.
        """

        pv = self.prefix
        self._setup_and_check_pmgr()

        self._pm.update_db()
        o = self._pm._search(self._pm.pm.objs, 'rec_base', pv)
        return self._pm.pm.getActualConfig(o['id'])

    @staticmethod
    def find_configuration(pattern, case_insensitive=True, display=30):
        """
        Find parameter manager configurations that match the pattern.

        pattern : str
            The substring to match.  "." matches any character, and "*"
            matches any string.  These maybe quoted using "\".

        case_insensitive : boolean
            True if the match should be case insensitive, False if it
            should be case sensitive.

        display : int | None
            The maximum number of configurations to display.  If None,
            don't display any, but return a list of all matches.

        Returns a list of strings if display is None, and nothing otherwise.
        """
        IMS._setup_and_check_pmgr()
        matches = IMS._pm.match_config(pattern, ci=case_insensitive, parent='USR')
        if display is None:
            return matches
        if len(matches) >= display:
            print("'%s' matches %d configurations." % (pattern, len(matches)))
            print("Use a more restrictive pattern or "
                  "larger value for display (%d)." % display)
        else:
            print("Matches for '%s':" % pattern)
            for m in matches:
                print("    %s" % m)

    def diff_configuration(self, cfgname=None):
        """
        Find the differences between the actual motor settings and the
        current parameter manager configuration.

        Parameters
        ----------
        cfgname : str
            The name of the configuration to compare the settings to.  If
            this is None, use the current configuration.

        Returns
        -------
        diff : PrettyTable
            A table with headers "Parameter", "Actual", and "Configuration",
            showing the differences between the live values and the configured
            values.

        Raises an exception if the comparison fails for any reason.
        """
        IMS._setup_and_check_pmgr()

        d = self._pm.diff_config(self.prefix, cfgname)
        table = PrettyTable()
        table.field_names = ["Parameter", "Actual", "Configuration"]
        for key, value in d.items():
            actual = value[0]
            configuration = value[1]
            table.add_row([key, actual, configuration])
        return table

    @staticmethod
    def setup_pmgr():
        try:
            from pmgr import pmgrAPI
        except ImportError:
            logger.error('Failed to import pmgr!')
            logger.debug('', exc_info=True)
            IMS._pm_init_error = True
        try:
            hutch = get_hutch_name()
        except Exception:
            logger.error('Could not determine hutch for pmgr!')
            logger.debug('', exc_info=True)
            IMS._pm_init_error = True
            return
        try:
            IMS._pm = pmgrAPI.pmgrAPI("ims_motor", hutch)
        except Exception:
            logger.error('Failed to create IMS pmgr object!')
            logger.debug('', exc_info=True)
            IMS._pm_init_error = True
            return

    @staticmethod
    def _setup_pmgr_if_needed():
        if IMS._pm is None and not IMS._pm_init_error:
            IMS.setup_pmgr()

    @staticmethod
    def check_pmgr():
        if IMS._pm is None:
            raise RuntimeError('pmgr has not been set up yet, call setup_pmgr')
        if IMS._pm_init_error:
            raise RuntimeError('pmgr not available, initialized with an error')

    @staticmethod
    def _setup_and_check_pmgr():
        IMS._setup_pmgr_if_needed()
        IMS.check_pmgr()


class Newport(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record for Newport motors.

    This is a subclass of :class:`PCDSMotorBase` that:
    - Overwrites missing signals for Newports
    - Disables the :meth:`home` method broken for Newports
    - Does special metadata handling because this is broken for Newports
    """

    __doc__ += basic_positioner_init
    # Overrides are in roughly the same order as from EpicsMotor

    # Override from EpicsMotor to disable
    offset_freeze_switch = Cpt(Signal, kind='omitted')

    # Override from EpicsMotor to add subscription
    motor_egu = UpCpt()

    # Override from EpicsMotor to disable
    home_forward = Cpt(Signal, kind='omitted')
    home_reverse = Cpt(Signal, kind='omitted')

    # Add new signal for subscription
    motor_prec = Cpt(EpicsSignalRO, '.PREC', kind='omitted',
                     auto_monitor=True)

    velocity_max = Cpt(EpicsSignalRO, '.SVEL', kind='config')
    velocity_base = Cpt(Signal, kind='omitted')

    def home(self, *args, **kwargs):
        # This function should eventually be used. There is a way to home
        # Newport motors to a reference mark
        raise NotImplementedError("Homing is not yet implemented for Newport "
                                  "motors")

    @property
    def msta(self):
        """
        Returns the msta fields as a dictionary.
        """
        # the MSTA field is a float for some reason...
        val = int(self.msta_raw.get())
        d = dict()
        for bit in NewportMstaEnum:
            if bit.name == 'errno':
                d[bit.name] = (val >> bit.value) & 0xFF  # 8 bit error number
            else:
                d[bit.name] = (val >> bit.value) & 0x1
        return d

    @motor_egu.sub_value
    def _update_units(self, value, **kwargs):
        """
        Update ctrl metadata when the units update.
        """
        self.user_readback._override_metadata(units=value)
        self.user_setpoint._override_metadata(units=value)

    @motor_prec.sub_value
    def _update_prec(self, value, **kwargs):
        """
        Update ctrl metadata when the precision updates.
        """
        self.user_readback._override_metadata(precision=value)
        self.user_setpoint._override_metadata(precision=value)


DelayNewport = delay_class_factory(Newport)


class OffsetMotor(OffsetMotorBase):
    motor = FCpt(IMS, '{self._motor_prefix}')


class OffsetIMSWithPreset(OffsetMotorBase):
    """
    Offset IMS with an additiona Offset _SET PV.

    This motor puts to an additional PV (_SET) during `set_current_postion`.
    """
    motor = FCpt(IMS, '{self._motor_prefix}')
    offset_set_pv = FCpt(EpicsSignal, '{self._prefix}_SET', kind='normal')

    # override the set_current_position
    def set_current_position(self, position):
        '''
        Override this method defined in OffsetMotorBase to allow setting the
        new current position to the _SET pv as well.

        Calculate and configure the user_offset value, indicating the provided
        ``position`` as the new current position.

        Parameters
        ----------
        position : number
            The new current position.
        '''
        self.user_offset.put(0.0)
        new_offset = position - self.position[0]
        self.offset_set_pv.put(new_offset)
        self.user_offset.put(new_offset)


class PMC100(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record PMC100 motors.

    This is a subclass of :class:`PCDSMotorBase` that overwrites missing
    signals and disables the :meth:`.home` method, because it will not work the
    same way for Newport motors.
    """

    __doc__ += basic_positioner_init

    home_forward = Cpt(Signal, kind='omitted')
    home_reverse = Cpt(Signal, kind='omitted')

    def home(self, *args, **kwargs):
        raise NotImplementedError("PMC100 motors have no homing procedure")


class MMC100(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record for MMC100 controlled motors.

    This is a subclass of :class:`PCDSMotorBase` that:
    - Overwrites missing freeze offset signal for Newports
    - Changes the homing PVs to those used for moving to limits on MMC100s
    """

    __doc__ += basic_positioner_init
    # Overrides are in roughly the same order as from EpicsMotor

    offset_freeze_switch = Cpt(Signal, kind='omitted')

    home_forward = Cpt(EpicsSignal, '.MLP', kind='omitted')
    home_reverse = Cpt(EpicsSignal, '.MLN', kind='omitted')

    velocity_base = Cpt(Signal, kind='omitted')


class BeckhoffAxisPLC(Device):
    """
    Error handling, debug, and aux functions for the Beckhoff Axis PLC code.
    """
    status = Cpt(PytmcSignal, 'sErrorMessage', io='i', kind='normal',
                 string=True, doc='PLC error or warning')
    err_bool = Cpt(PytmcSignal, 'bError', io='i', kind='normal',
                   doc='True if there is some sort of error.')
    err_code = Cpt(PytmcSignal, 'nErrorId', io='i', kind='normal',
                   doc='Current NC error code')
    cmd_err_reset = Cpt(PytmcSignal, 'bReset', io='io', kind='normal',
                        doc='Command to reset an active error')
    enc_count = Cpt(PytmcSignal, 'nEncoderCount', io='i', kind='normal',
                    doc='Raw encoder count for this motor.')
    posdiff = Cpt(PytmcSignal, 'fPosDiff', io='i', kind='normal',
                  doc='Difference between trajectory setpoint and readback.')
    hardware_enable = Cpt(PytmcSignal, 'bHardwareEnable', io='i', kind='normal',
                          doc='TRUE if motor has its hardware enable.')
    cmd_home = Cpt(PytmcSignal, 'bHomeCmd', io='o', kind='normal',
                   doc='Start TwinCAT homing routine.')
    home_pos = Cpt(PytmcSignal, 'fHomePosition', io='io', kind='config',
                   doc='Numeric position of home.')
    user_enable = Cpt(PytmcSignal, 'bUserEnable', io='io', kind='config',
                      doc='Power enable/disable')

    set_metadata(err_code, dict(variety='scalar', display_format='hex'))
    set_metadata(cmd_err_reset, dict(variety='command', value=1))
    set_metadata(cmd_home, dict(variety='command-proc',
                                value=1,
                                tags={"confirm"}))


class BeckhoffAxisPLCEPS(BeckhoffAxisPLC):
    """
    Extended BeckhoffAxisPLC with relevant EPS fields.

    This is to be used in BeckhoffAxisEPS for cases when the motor
    has EPS considerations. Otherwise, these fields are not active
    in PLC logic and are distracting or confusing.
    """
    eps_forward = Cpt(EPS, "stEPSF:", doc="EPS forward enables.")
    eps_backward = Cpt(EPS, "stEPSB:", doc="EPS backward enables.")
    eps_power = Cpt(EPS, "stEPSP:", doc="EPS power enables.")


class BeckhoffAxis(EpicsMotorInterface):
    """
    Beckhoff Axis motor record as implemented by ESS and extended by us.

    This class adds a convenience :meth:`.clear_error` method, and makes
    sure to call it on stage.

    It also exposes the PLC debug PVs.
    """

    __doc__ += basic_positioner_init
    tab_whitelist = ['clear_error']

    plc = Cpt(BeckhoffAxisPLC, ':PLC:', kind='normal',
              doc='PLC error handling and aux functions.')
    motor_spmg = Cpt(EpicsSignal, '.SPMG', kind='config',
                     doc='Stop, Pause, Move, Go')

    # Clear the normal homing PVs that don't really work here
    home_forward = None
    home_reverse = None

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
        be set to the Beckhoff error message if there is one.
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
        Special end of move handling to set the status for BeckhoffAxis.

        If the BeckhoffAxis has an error message, include it and mark failure.
        Otherwise, set success.

        Parameters
        ----------
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
        Stage the Beckhoff axis.

        This simply clears any errors. Stage is called at the start of most
        :mod:`bluesky` plans.
        """

        self.clear_error()
        return super().stage()

    @raise_if_disconnected
    def home(self, direction=None, wait=True, **kwargs):
        """
        Perform the configured homing function.

        This is set on the controller. Unlike other kinds of axes, only
        the single pre-programmed homing routine can be used, so the
        ``direction`` argument has no effect.
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

    def check_value(self, pos: float) -> None:
        """
        Check that the motor can reach the position.

        Inherits limits and related checks from parent classes.
        Adds one additional check: the velocity must be nonzero
        for a move to succeed. Otherwise, the move fails silently.

        Beckhoff EPICS motors at LCLS that have never been initialized
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


class BeckhoffAxisEPS(BeckhoffAxis):
    """
    A beckhoff axis where the EPS indicators are relevant.

    This is to be used for cases when the motor has EPS considerations.
    Otherwise, these fields are not active in PLC logic and are distracting
    or confusing.
    """
    plc = Cpt(BeckhoffAxisPLCEPS, ':PLC:', kind='normal',
              doc='PLC error handling, aux functions, and EPS.')


class BeckhoffAxisEPSCustom(BeckhoffAxis):
    """
    A beckhoff axis where custom EPS Logic has been implemented in
    a PLC and needs a custom screen to display EPS information

    EPS screens are found in
    /cds/group/pcds/epics-dev/screens/pydm/eps_screens/${beamline}/${name}

    """
    pass


class BeckhoffAxisPLC_Pre140(BeckhoffAxisPLC):
    """
    Disable some newly introduced signals.
    """
    posdiff = None
    cmd_home = None
    home_pos = None
    user_enable = None


class BeckhoffAxis_Pre140(BeckhoffAxis):
    """
    Beckhoff Axis compatible with PLCs running older software.

    This version targets the versions of lcls-twincat-motion
    prior to v1.4.0, which is when the homing routines were
    introduced.
    """
    plc = Cpt(BeckhoffAxisPLC_Pre140, ':PLC:', kind='normal',
              doc='PLC error handling and aux functions.')

    def home(self, *args, **kwargs):
        """
        Override ``home`` with a clear error message.
        """
        raise NotImplementedError("This axis does not support homing.")


OldBeckhoffAxis = BeckhoffAxis_Pre140


class BeckhoffAxisNoOffset(BeckhoffAxis):
    """
    A BeckhoffAxis with various fields read-only.

    This is to prevent a user from messing themselves up by changing things
    like user offset and user direction. This is desirable for static beamline
    configurations.

    Rather than removing these entirely, keep them readable in case it is
    useful to know their values.
    """
    user_offset = UpCpt(cls=EpicsSignalRO)
    user_offset_dir = UpCpt(cls=EpicsSignalRO)
    offset_freeze_switch = UpCpt(cls=EpicsSignalRO)
    set_use_switch = UpCpt(cls=EpicsSignalRO)


class MotorDisabledError(Exception):
    """Error that indicates that we are not allowed to move."""
    pass


class SmarActOpenLoop(Device):
    """
    Class containing the open loop PVs used to control an un-encoded SmarAct
    stage.

    Can be used for sub-classing, or creating a simple device without the
    motor record PVs.
    """

    # Voltage for sawtooth ramp
    step_voltage = Cpt(EpicsSignal, ':STEP_VOLTAGE', kind='omitted',
                       doc='Voltage for sawtooth (0-100V)')
    # Frequency of steps
    step_freq = Cpt(EpicsSignal, ':STEP_FREQ', kind='config',
                    doc='Sawtooth drive frequency')
    # Number of steps per step forward, backward command
    jog_step_size = Cpt(EpicsSignal, ':STEP_COUNT', kind='normal',
                        doc='Number of steps per FWD/BWD command')
    # Jog forward
    jog_fwd = Cpt(EpicsSignal, ':STEP_FORWARD', kind='normal',
                  doc='Jog the stage forward')
    set_metadata(jog_fwd, dict(variety='command-proc', value=1))
    # Jog backward
    jog_rev = Cpt(EpicsSignal, ':STEP_REVERSE', kind='normal',
                  doc='Jog the stage backward')
    set_metadata(jog_rev, dict(variety='command-proc', value=1))
    # Total number of steps counted
    total_step_count = Cpt(EpicsSignalRO, ':TOTAL_STEP_COUNT', kind='normal',
                           doc='Current open loop step count')
    # Reset steps ("home")
    step_clear_cmd = Cpt(EpicsSignal, ':CLEAR_COUNT', kind='config',
                         doc='Clear the current step count')
    set_metadata(step_clear_cmd, dict(variety='command-proc', value=1))
    # Scan move
    scan_move = Cpt(EpicsSignal, ':SCAN_POS', write_pv=':SCAN_MOVE',
                    kind='config',
                    doc='Set current piezo voltage (in 16 bit ADC steps)')
    # Diagnostic read only PVs
    channel_temp = Cpt(EpicsSignalRO, ':CHANTEMP', kind='normal',
                       doc="Temperature at the channel's amplifier")
    module_temp = Cpt(EpicsSignalRO, ':MODTEMP', kind='normal',
                      doc='Temperature of the MCS2 Module in the rack')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Long name shenanigans
        self.step_voltage.long_name = 'Step Voltage'
        self.step_freq.long_name = 'Step Frequency'
        self.jog_step_size.long_name = 'Jog Step Size'
        self.jog_fwd.long_name = 'Jog Forward'
        self.jog_rev.long_name = 'Jog Backward'
        self.total_step_count.long_name = 'Total Step Count'
        self.step_clear_cmd.long_name = 'Clear Step Count'
        self.scan_move.long_name = 'Scan Voltage'
        self.channel_temp.long_name = 'Channel Temp. (°C)'
        self.module_temp.long_name = 'Module Temp. (°C)'


class SmarActTipTilt(Device):
    """
    Class for bundling two SmarActOpenLoop axes arranged in a tip-tilt mirror
    positioning configuration into a single device.

    Parameters:
    -----------
    prefix : str <optional, default=''>
        The base PV of the stages. Can be omitted, but then tip_pv and
        tilt_pv must specify the full stage PV.

    tip_pv : str
        The PV suffix of the "tip" axis to add to the device prefix. Any PV
        separator (e.g. ':') must be included.

    tilt_pv : str
        The PV suffix of the "tilt" axis to add to the device prefix. Any PV
        separator (e.g. ':') must be included.

    Examples
    --------
    # Tip Tilt stage with same base PV
    tt = SmarActTipTilt(prefix='LAS:MCS2:01', tip_pv=':M1', tilt_pv=':M2')

    # Tip Tilt stage with different base PV (separate controller, etc.)
    tt2 = SmarActTipTilt(tip_pv='LAS:MCS2:01:M1', tilt_pv='LAS:MCS2:02:M1')
    """

    tip = FCpt(SmarActOpenLoop, '{prefix}{self._tip_pv}', kind='normal')
    tilt = FCpt(SmarActOpenLoop, '{prefix}{self._tilt_pv}', kind='normal')

    def __init__(self, prefix='', *, tip_pv, tilt_pv, **kwargs):
        self._tip_pv = tip_pv
        self._tilt_pv = tilt_pv
        super().__init__(prefix, **kwargs)


class SmarActOpenLoopPositioner(PVPositionerComparator):
    """
    Positioner class for SmarAct open loop stages. Intended to be used in
    BlueSky scans. Uses an integer open loop step count as the position.
    """
    setpoint = Cpt(EpicsSignal, ':SET_TOTAL_STEP_COUNT')
    readback = Cpt(EpicsSignalRO, ':TOTAL_STEP_COUNT')
    atol = 1  # step count after move should be exact, but let's be cautious

    egu = 'steps'

    open_loop = Cpt(SmarActOpenLoop, '', kind='normal')

    def done_comparator(self, readback, setpoint):
        return setpoint-self.atol < readback < setpoint+self.atol


class SmarAct(EpicsMotorInterface):
    """
    Class for encoded SmarAct motors controlled via the MCS2 controller.
    """
    # Positioner type - only useful for encoded stages
    pos_type = Cpt(EpicsSignal, ':PTYPE_RBV', write_pv=':PTYPE', kind='config')

    # Calibration - only works for encoded stages
    needs_calib = Cpt(EpicsSignalRO, ':NEED_CALIB', kind='config')

    do_calib = Cpt(EpicsSignal, ':DO_CALIB.PROC', kind='config')
    set_metadata(do_calib, dict(variety='command-proc', value=1))

    # Configuration for settings in NVRAM
    log_scale_offset = Cpt(EpicsSignal, ':LSCO', write_pv=':SET_LSCO',
                           kind='omitted', doc='Logical Scale Offset')
    def_range_min = Cpt(EpicsSignal, ':DRMIN', write_pv=':SET_DRMIN',
                        kind='omitted', doc='Default Range Minimum')
    def_range_max = Cpt(EpicsSignal, ':DRMAX', write_pv=':SET_DRMAX',
                        kind='omitted', doc='Default Range Maximum')
    log_scale_inv = Cpt(EpicsSignal, ':LSCI_RBV', write_pv=':SET_LSCI',
                        kind='omitted', doc='Default Range Minimum')
    dist_code_inv = Cpt(EpicsSignal, ':DCIN_RBV', write_pv=':SET_DCIN',
                        kind='omitted', doc='Distance Code Inversion')

    # Diagnostic read only PVs
    channel_temp = Cpt(EpicsSignalRO, ':CHANTEMP', kind='normal',
                       doc="Temperature at the channel's amplifier")
    module_temp = Cpt(EpicsSignalRO, ':MODTEMP', kind='normal',
                      doc='Temperature of the MCS2 Module in the rack')

    # These PVs will probably not be needed for most encoded motors, but can be
    # useful
    open_loop = Cpt(SmarActOpenLoop, '', kind='omitted')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Long name shenanigans
        # Motor Record long name overrides
        self.velocity.long_name = 'Velocity'
        self.velocity_base.long_name = 'Velocity Min'
        self.velocity_max.long_name = 'Velocity Max'
        self.acceleration.long_name = 'Acceleration'
        self.motor_stop.long_name = 'Stop Motor'
        self.motor_is_moving.long_name = 'Actively Moving'
        self.dial_position.long_name = 'Dial Position'
        self.direction_of_travel.long_name = 'Direction of Travel'
        self.home_forward.long_name = 'Home Forward'
        self.home_reverse.long_name = 'Home Backward'
        self.low_limit_switch.long_name = 'Low Limit Switch'
        self.high_limit_switch.long_name = 'High Limit Switch'
        self.high_limit_travel.long_name = 'High Limit Travel'
        self.low_limit_travel.long_name = 'Low Limit Travel'
        self.user_setpoint.long_name = 'Setpoint'
        self.user_offset.long_name = 'User Offset'
        self.user_offset_dir.long_name = 'User Offset Direction'
        self.motor_egu.long_name = 'EGU'
        self.description.long_name = 'Description'
        # SmarAct specific long names
        self.pos_type.long_name = 'Positioner Type'
        self.needs_calib.long_name = 'Needs Calibration?'
        self.do_calib.long_name = 'Calibrate'
        self.log_scale_offset.long_name = 'Logical Scale Offset'
        self.def_range_min.long_name = 'Default Range Min.'
        self.def_range_max.long_name = 'Default Range Max'
        self.log_scale_inv.long_name = 'Logical Scale Inversion'
        self.dist_code_inv.long_name = 'Distance Code Inversion'
        self.channel_temp.long_name = 'Channel Temp. (°C)'
        self.module_temp.long_name = 'Module Temp. (°C)'


class SmarActEncodedTipTilt(Device):
    """
    Class for bundling two SmarAct encoded axes arranged in a tip-tilt mirror
    positioning configuration into a single device.
    Refer to SmarActTipTilt for more info.
    """
    tip = FCpt(SmarAct, '{prefix}{self._tip_pv}', kind='normal')
    tilt = FCpt(SmarAct, '{prefix}{self._tilt_pv}', kind='normal')

    def __init__(self, prefix='', *, tip_pv, tilt_pv, **kwargs):
        self._tip_pv = tip_pv
        self._tilt_pv = tilt_pv
        super().__init__(prefix, **kwargs)
        print("hello this is a dummy commit")


class SmarActPicoscale(SmarAct):
    """
    Class for encoded SmarAct motors controller via the MCS2 controller
    which use the PicoScale sensor heads for encoded positions.
    Instantiating a device requires inclusion of the ioc_base in order to
    properly access PicoScale properties.

    Example
    -------
    SmarActPicoscale('prefix': 'LAS:MCS2:02:m1', 'name': 'Delay 1',
                     'ioc_base': 'LAS:MCS2:02').
    """
    # configuration settings and readbacks
    pico_present = Cpt(EpicsSignalRO, ':PS_PRESENT', kind='config',
                       doc='PicoScale is on and connected')
    pico_exists = Cpt(EpicsSignalRO, ':HAVE_PS', kind='config',
                      doc='Does this channel have a PicoScale assigned to it?')
    pico_valid = Cpt(EpicsSignalRO, ':PS_DATA_VALID', kind='config',
                     doc='Is the data valid and ready for accurate msmts?')
    pico_sig_qual = Cpt(EpicsSignalRO, ':PS_SIG_QUALITY', kind='config',
                        doc='Quality of interferometer signal. Higher = better')

    # auto and manual adjustment related PVs
    pico_adj_state = FCpt(EpicsSignal, '{self._ioc_base}:PS:CUR_ADJ_STATE',
                          write_pv='{self._ioc_base}:PS:REQ_ADJ_STATE',
                          kind='config', doc='Set to Manual or Auto adjustment '
                          'mode')
    pico_curr_adj_prog = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:CUR_ADJ_PROGRESS',
                              kind='config', doc='Estimate of current adjustment '
                              'progress')
    pico_adj_done = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:ADJ_DONE',
                         kind='config', doc='Is the auto adjustment done?')

    # Validation that Picoscale is working properly
    pico_enable = Cpt(EpicsSignalRO, ':PS_ENABLE_RBV', kind='normal',
                      doc='Is the PicoScale enabled for this channel?')
    pico_stable = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:STABLE', kind='normal',
                       doc='Is system stable and ready for accurate msmts?')

    # Diagnostic information from PS controller
    pico_name = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:LOCATOR',
                     kind='config', doc='Name of the PicoScale')
    pico_wmin = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:WORKING_MIN',
                     kind='config', doc='Working distance minimum')
    pico_wmax = FCpt(EpicsSignalRO, '{self._ioc_base}:PS:WORKING_MAX',
                     kind='config', doc='Working distance maximum')

    def __init__(self, prefix, *, ioc_base, **kwargs):
        self._ioc_base = ioc_base
        super().__init__(prefix, **kwargs)
        self.pico_adj_done.long_name = 'Auto Adjustment Done?'
        self.pico_adj_state.long_name = 'Auto Adjustment State'
        self.pico_curr_adj_prog.long_name = 'Auto Adjustment Progress'
        self.pico_enable.long_name = 'PicoScale Enabled?'
        self.pico_exists.long_name = 'PicoScale Exists?'
        self.pico_name.long_name = 'PicoScale Name'
        self.pico_present.long_name = 'PicoScale Present?'
        self.pico_sig_qual.long_name = 'Signal Quality'
        self.pico_valid.long_name = 'PicoScale Valid?'
        self.pico_stable.long_name = 'PicoScale Stable?'
        self.pico_wmax.long_name = 'Working distance (max)'
        self.pico_wmin.long_name = 'Working distance (min)'


class PI_M824(PVPositionerIsClose):
    """
    class for hexapod PI axis
    """
    setpoint = Cpt(EpicsSignal, '')
    readback = Cpt(EpicsSignal, ':rbv')
    # one micron seems close enough
    atol = 0.001


def _GetMotorClass(basepv):
    """
    Function to determine the appropriate motor class based on the PV.
    """
    # Available motor types
    motor_types = (('MMS', IMS),
                   ('CLZ', IMS),
                   ('CLF', IMS),
                   ('MMN', Newport),
                   ('MZM', PMC100),
                   ('MMC', MMC100),
                   ('MMB', BeckhoffAxis),
                   ('PIC', PCDSMotorBase),
                   ('MCS', SmarAct),
                   ('MCS2', SmarAct),
                   ('HEX', PI_M824))

    # Search for component type in prefix
    for cpt_abbrev, _type in motor_types:
        if f':{cpt_abbrev}:' in basepv:
            logger.debug("Found %r in basepv %r, loading %r",
                         cpt_abbrev, basepv, _type)
            return _type
    # Default to ophyd.EpicsMotor
    logger.warning("Unable to find type of motor based on component. "
                   "Using 'ophyd.EpicsMotor'")
    return EpicsMotor


def Motor(prefix, **kwargs):
    """
    Load a PCDSMotor with the correct class based on prefix.

    The prefix is searched for one of the component keys in the table below. If
    none of these are found, by default an `EpicsMotor` will be used.

    +---------------+-------------------------+
    | Component Key + Python Class            |
    +===============+=========================+
    | MMS           | :class:`.IMS`           |
    +---------------+-------------------------+
    | CLZ           | :class:`.IMS`           |
    +---------------+-------------------------+
    | CLF           | :class:`.IMS`           |
    +---------------+-------------------------+
    | MMN           | :class:`.Newport`       |
    +---------------+-------------------------+
    | MZM           | :class:`.PMC100`        |
    +---------------+-------------------------+
    | MMC           | :class:`.MMC100`        |
    +---------------+-------------------------+
    | MMB           | :class:`.BeckhoffAxis`  |
    +---------------+-------------------------+
    | PIC           | :class:`.PCDSMotorBase` |
    +---------------+-------------------------+
    | MCS           | :class:`.SmarAct`       |
    +---------------+-------------------------+
    | MCS2          | :class:`.SmarAct`       |
    +---------------+-------------------------+
    | HEX           | :class:`.PI_M824`       |
    +---------------+-------------------------+

    Parameters
    ----------
    prefix : str
        Prefix of motor.

    kwargs
        Passed to class constructor.
    """

    # Determine motor class
    cls = _GetMotorClass(prefix)

    return cls(prefix, **kwargs)
