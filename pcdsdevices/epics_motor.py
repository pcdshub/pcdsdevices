"""
Module for LCLS's special motor records.
"""
import logging
import os
import shutil

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.epics_motor import EpicsMotor
from ophyd.ophydobj import Kind
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.status import DeviceStatus, MoveStatus, SubscriptionStatus
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError
from ophyd.utils.epics_pvs import raise_if_disconnected, set_and_wait

from pcdsdevices.pv_positioner import PVPositionerComparator

from .doc_stubs import basic_positioner_init
from .interface import FltMvInterface
from .pseudopos import OffsetMotorBase, delay_class_factory
from .signal import EpicsSignalEditMD, EpicsSignalROEditMD, PytmcSignal
from .utils import get_status_value
from .variety import set_metadata

logger = logging.getLogger(__name__)


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
    """
    # Enable/Disable puts
    disabled = Cpt(EpicsSignal, ".DISP", kind='omitted')
    set_metadata(disabled, dict(variety='command-enum'))
    # Description is valuable
    description = Cpt(EpicsSignal, '.DESC', kind='normal')
    # Current Dial position
    dial_position = Cpt(EpicsSignalRO, '.DRBV', kind='normal')

    tab_whitelist = ["set_current_position", "home", "velocity", "enable",
                     "disable", "check_limit_switches", "get_low_limit",
                     "set_low_limit", "get_high_limit", "set_high_limit"]

    set_metadata(EpicsMotor.home_forward, dict(variety='command-proc',
                                               value=1))
    EpicsMotor.home_forward.kind = Kind.normal
    set_metadata(EpicsMotor.home_reverse, dict(variety='command-proc',
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
        description = get_status_value(status_info, 'description', 'value')
        units = get_status_value(status_info, 'user_setpoint', 'units')
        dial = get_status_value(status_info, 'dial_position', 'value')
        user = get_status_value(status_info, 'position')

        low, high = self.limits
        switch_limits = self.check_limit_switches()

        name = ' '.join(self.prefix.split(':'))
        name = f'{name}: {self.prefix}'
        if description:
            name = f'{description}: {self.prefix}'

        return f"""\
{name}
Current position (user, dial): {user}, {dial} [{units}]
User limits (low, high): {low}, {high} [{units}]
Preset position: {self.presets.state()}
Limit Switch: {switch_limits}
"""

    @property
    def limits(self):
        """Override the limits attribute"""
        return self._get_epics_limits()

    def _get_epics_limits(self):
        limits = self.user_setpoint.limits
        if limits is None or limits == (None, None):
            # Not initialized
            return (0, 0)
        return limits

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

    tab_whitelist = ["spg_stop", "spg_pause", "spg_go"]

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
        os.system(executable + ' ' + arg)

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
        set_and_wait(self.user_setpoint, pos, timeout=1)
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
    velocity_base = Cpt(EpicsSignal, '.VBAS', kind='omitted')
    velocity_max = Cpt(EpicsSignal, '.VMAX', kind='config')

    tab_whitelist = ['auto_setup', 'reinitialize', 'clear_.*']

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

    def reinitialize(self, wait=False):
        """
        Reinitialize the IMS motor.

        Parameters
        ----------
        wait : bool
            Wait for the motor to be fully intialized.

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
        st = SubscriptionStatus(self.error_severity,
                                initialize_complete,
                                settle_time=0.5)
        # Wait on status if requested
        if wait:
            status_wait(st)
        return st

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

    # Override from EpicsMotor to change class for MD update
    user_readback = Cpt(EpicsSignalROEditMD, '.RBV', kind='hinted',
                        auto_monitor=True)
    user_setpoint = Cpt(EpicsSignalEditMD, '.VAL', limits=True,
                        auto_monitor=True)

    # Override from EpicsMotor to disable
    offset_freeze_switch = Cpt(Signal, kind='omitted')

    # Override from EpicsMotor to add subscription
    motor_egu = Cpt(EpicsSignal, '.EGU', kind='config',
                    auto_monitor=True)

    # Override from EpicsMotor to add subscription
    high_limit_travel = Cpt(EpicsSignal, '.HLM', kind='omitted',
                            auto_monitor=True)
    low_limit_travel = Cpt(EpicsSignal, '.LLM', kind='omitted',
                           auto_monitor=True)

    # Override from EpicsMotor to disable
    home_forward = Cpt(Signal, kind='omitted')
    home_reverse = Cpt(Signal, kind='omitted')

    # Add new signal for subscription
    motor_prec = Cpt(EpicsSignalRO, '.PREC', kind='omitted',
                     auto_monitor=True)

    def home(self, *args, **kwargs):
        # This function should eventually be used. There is a way to home
        # Newport motors to a reference mark
        raise NotImplementedError("Homing is not yet implemented for Newport "
                                  "motors")

    # This needs to be re-done if you override user_readback
    @user_readback.sub_value
    def _pos_changed(self, *args, **kwargs):
        super()._pos_changed(*args, **kwargs)

    @motor_egu.sub_value
    def _update_units(self, value, **kwargs):
        self.user_readback._override_metadata(units=value)
        self.user_setpoint._override_metadata(units=value)

    @high_limit_travel.sub_value
    def _update_hlt(self, value, **kwargs):
        self.user_readback._override_metadata(upper_ctrl_limit=value)
        self.user_setpoint._override_metadata(upper_ctrl_limit=value)

    @low_limit_travel.sub_value
    def _update_llt(self, value, **kwargs):
        self.user_readback._override_metadata(lower_ctrl_limit=value)
        self.user_setpoint._override_metadata(lower_ctrl_limit=value)

    @motor_prec.sub_value
    def _update_prec(self, value, **kwargs):
        self.user_readback._override_metadata(precision=value)
        self.user_setpoint._override_metadata(precision=value)


DelayNewport = delay_class_factory(Newport)


class OffsetMotor(OffsetMotorBase):
    motor = FCpt(IMS, '{self._motor_prefix}')


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


class BeckhoffAxisPLC(Device):
    """Error handling for the Beckhoff Axis PLC code."""
    status = Cpt(PytmcSignal, 'sErrorMessage', io='i', kind='normal',
                 string=True, doc='PLC error or warning')
    err_code = Cpt(PytmcSignal, 'nErrorId', io='i', kind='normal',
                   doc='Current NC error code')
    cmd_err_reset = Cpt(PytmcSignal, 'bReset', io='o', kind='normal',
                        doc='Command to reset an active error')
    cmd_home = Cpt(PytmcSignal, 'bHomeCmd', io='o', kind='normal',
                   doc='Start TwinCAT homing routine.')
    home_pos = Cpt(PytmcSignal, 'fHomePosition', io='io', kind='config',
                   doc='Numeric position of home.')

    set_metadata(err_code, dict(variety='scalar', display_format='hex'))
    set_metadata(cmd_err_reset, dict(variety='command', value=1))
    set_metadata(cmd_home, dict(variety='command-proc', value=1))


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
              doc='PLC error handling.')
    motor_spmg = Cpt(EpicsSignal, '.SPMG', kind='config',
                     doc='Stop, Pause, Move, Go')

    # Clear the normal homing PVs that don't really work here
    home_forward = None
    home_reverse = None

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


class MotorDisabledError(Exception):
    """Error that indicates that we are not allowed to move."""
    pass


class SmarActOpenLoop(Device):
    """
    Class containing the open loop PVs used to control an un-encoded SmarAct
    stage.

    Can be used for sub-classing, or creating a simple  device without the
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


class SmarActTipTilt(Device):
    """
    Class for bundling two SmarActOpenLoop axes arranged in a tip-tilt mirro
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

    # These PVs will probably not be needed for most encoded motors, but can be
    # useful
    open_loop = Cpt(SmarActOpenLoop, '', kind='omitted')


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
                   ('MMB', BeckhoffAxis),
                   ('PIC', PCDSMotorBase),
                   ('MCS', SmarAct))
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
    | MMB           | :class:`.BeckhoffAxis`  |
    +---------------+-------------------------+
    | PIC           | :class:`.PCDSMotorBase` |
    +---------------+-------------------------+
    | MCS           | :class:`.SmarAct`       |
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
