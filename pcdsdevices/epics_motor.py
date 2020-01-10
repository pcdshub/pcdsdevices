"""
Module for LCLS's special motor records.
"""
import logging
import shutil
import os
from ophyd.device import Component as Cpt
from ophyd.epics_motor import EpicsMotor
from ophyd.signal import Signal, EpicsSignal, EpicsSignalRO
from ophyd.status import DeviceStatus, SubscriptionStatus, wait as status_wait
from ophyd.utils import LimitError

from .doc_stubs import basic_positioner_init
from .interface import FltMvInterface
from .pseudopos import DelayBase


logger = logging.getLogger(__name__)


class EpicsMotorInterface(FltMvInterface, EpicsMotor):
    """
    The standard EpicsMotor class, but with our interface attached.

    This includes some PCDS preferences, but not any IOC differences.

    Notes
    -----
    The full list of preferences implemented here are:

        1. Use the FltMvInterface mixin class for some name aliases and
        bells-and-whistles level functions
        2. Instead of using the limit fields on the setpoint PV, the EPICS
        motor class has the ``LLM`` and ``HLM`` soft limit fields for
        convenient usage. Unfortunately, pyepics does not update its internal
        cache of the limits after the first get attempt. We therefore disregard
        the internal limits of the PV and use the soft limit records
        exclusively.
        3. The disable puts field ``.DISP`` is added, along with ``enable`` and
        ``disable`` convenience methods. When ``.DISP`` is 1, puts to the motor
        record will be ignored, effectively disabling the interface.
        4. The description field keeps track of the motors scientific use along
           the beamline.
    """
    # Reimplemented because pyepics does not recognize when the limits have
    # been changed without a re-connection of the PV. Instead we trust the soft
    # limits records
    user_setpoint = Cpt(EpicsSignal, ".VAL", limits=False, kind='normal')
    # Additional soft limit configurations
    low_soft_limit = Cpt(EpicsSignal, ".LLM", kind='omitted')
    high_soft_limit = Cpt(EpicsSignal, ".HLM", kind='omitted')
    # Enable/Disable puts
    disabled = Cpt(EpicsSignal, ".DISP", kind='omitted')
    # Description is valuable
    description = Cpt(EpicsSignal, '.DESC', kind='normal')

    tab_whitelist = ["set_current_position", "home", "velocity",
                     "enable", "disable"]

    @property
    def low_limit(self):
        """
        The lower soft limit for the motor.
        """
        return self.low_soft_limit.value

    @low_limit.setter
    def low_limit(self, value):
        self.low_soft_limit.put(value)

    @property
    def high_limit(self):
        """
        The higher soft limit for the motor.
        """
        return self.high_soft_limit.value

    @high_limit.setter
    def high_limit(self, value):
        self.high_soft_limit.put(value)

    @property
    def limits(self):
        """
        The soft limits of the motor.
        """
        return (self.low_limit, self.high_limit)

    @limits.setter
    def limits(self, limits):
        self.low_limit = limits[0]
        self.high_limit = limits[1]

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
            - Check if the motor is disabled (``.DISP`` field)

        Raises
        ------
        `MotorDisabledError`
            If the motor is passed any motion command when disabled
        ``LimitError(ValueError)``
            When the provided value is outside the range of the low
            and high limits
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
        if self.disabled.value == 1:
            raise MotorDisabledError("Motor is not enabled. Motion requests "
                                     "ignored")


class PCDSMotorBase(EpicsMotorInterface):
    """
    EpicsMotor for PCDS

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

        1. The ``TDIR`` field does not exist on the PCDS implementation. This
        indicates what direction the motor has travelled last. To account for
        this difference, we use the `_pos_changed` callback to keep track of
        which direction we believe the motor to be travelling and store this in
        a simple ``ophyd.Signal``
        2. The ``SPG`` field implements the three states used in the LCLS
        motor record.  This is a reduced version of the standard EPICS
        ``SPMG`` field.  Setting to ``STOP``, ``PAUSE`` and ``GO``  will
        respectively stop motor movement, pause a move in progress, or resume
        a paused move.
    """
    # Disable missing field that our EPICS motor record lacks
    # This attribute is tracked by the _pos_changed callback
    direction_of_travel = Cpt(Signal, kind='omitted')
    # This attribute changes if the motor is stopped and unable to move 'Stop',
    # paused and ready to resume on Go 'Paused', and to resume a move 'Go'.
    motor_spg = Cpt(EpicsSignal, ".SPG", kind='omitted')

    tab_whitelist = ["spg_stop", "spg_pause", "spg_go"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs[self.motor_spg] = 2

    def spg_stop(self):
        """
        Stops the motor.

        After which the motor must be set back to 'go' via <motor>.spg_go() in
        order to move again.
        """
        return self.motor_spg.put(value='Stop')

    def spg_pause(self):
        """
        Pauses a move.

        Move will resume if <motor>.go() is called.
        """
        return self.motor_spg.put(value='Pause')

    def spg_go(self):
        """
        Resumes paused movement.
        """
        return self.motor_spg.put(value='Go')

    def check_value(self, value):
        """
        Raise an exception if the motor cannot move to value.

        The full list of checks done in this method:

            - Check if the value is within the soft limits of the motor.
            - Check if the motor is disabled (``.DISP`` field)`
            - Check if the spg field is on "pause" or "stop"

        Raises
        ------
        `MotorDisabledError`
            If the motor is passed any motion command when disabled, or if
            the ``.SPG`` field is not set to ``Go``.
        ``LimitError(ValueError)``
            When the provided value is outside the range of the low
            and high limits
        """
        super().check_value(value)

        if self.motor_spg.value in [0, 'Stop']:
            raise MotorDisabledError("Motor is stopped.  Motion requests "
                                     "ignored until motor is set to 'Go'")

        if self.motor_spg.value in [1, 'Pause']:
            raise MotorDisabledError("Motor is paused.  If a move is set, "
                                     "motion will resume when motor is set "
                                     "to 'Go'")

    def _pos_changed(self, timestamp=None, old_value=None,
                     value=None, **kwargs):
        # Store the internal travelling direction of the motor to account for
        # the fact that our EPICS motor does not have TDIR field
        if None not in (value, old_value):
            self.direction_of_travel.put(int(value > old_value))
        # Pass information to PositionerBase
        super()._pos_changed(timestamp=timestamp, old_value=old_value,
                             value=value, **kwargs)

    def screen(self):
        """
        Opens Epics motor expert screen for resetting motor after e.g. stalling
        """
        executable = 'motor-expert-screen'
        if shutil.which(executable) is None:
            logger.error('%s is not on path, we cannot start the screen',
                         executable)
            return
        arg = self.prefix
        os.system(executable + ' ' + arg)


class IMS(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record for IMS motors.

    This is a subclass of `PCDSMotorBase`
    """
    __doc__ += basic_positioner_init
    # Bit masks to clear errors and flags
    _bit_flags = {'powerup': {'clear': 36,
                              'readback':  24},
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
        Stage the IMS motor

        This clears all present flags on the motor and reinitializes the motor
        if we don't register a valid part number
        """
        # Check the part number to avoid crashing the IOC
        if not self.part_number.get() or self.error_severity.get() == 3:
            self.reinitialize(wait=True)
        # Clear any pre-existing flags
        self.clear_all_flags()
        return super().stage()

    def auto_setup(self):
        """
        Automated setup of the IMS motor

        If necessarry this command will:

            * Reinitialize the motor
            * Clear powerup, stall and error flags
        """
        # Reinitialize if necessary
        if not self.part_number.get() or self.error_severity.get() == 3:
            self.reinitialize(wait=True)
        # Clear all flags
        self.clear_all_flags()

    def reinitialize(self, wait=False):
        """
        Reinitialize the IMS motor

        Parameters
        ----------
        wait : bool
            Wait for the motor to be fully intialized

        Returns
        -------
        SubscriptionStatus:
            Status object reporting the initialization state of the motor
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
        """Clear all the flags from the IMS motor"""
        # Clear all flags
        for func in (self.clear_powerup, self.clear_stall, self.clear_error):
            func(wait=True)

    def clear_powerup(self, wait=False, timeout=10):
        """Clear powerup flag"""
        return self._clear_flag('powerup', wait=wait, timeout=timeout)

    def clear_stall(self, wait=False, timeout=5):
        """Clear stall flag"""
        return self._clear_flag('stall', wait=wait, timeout=timeout)

    def clear_error(self, wait=False, timeout=10):
        """Clear error flag"""
        return self._clear_flag('error', wait=wait, timeout=timeout)

    def _clear_flag(self, flag, wait=False, timeout=10):
        """Clear flag whose information is in ``._bit_flags``"""
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
            return DeviceStatus(self, done=True, success=True)

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
    PCDS implementation of the Motor Record for Newport motors

    This is a subclass of `PCDSMotorBase` that overwrites missings signals and
    disables the ``home`` method, because it will not work the same way for
    Newport motors.
    """
    __doc__ += basic_positioner_init

    offset_freeze_switch = Cpt(Signal, kind='omitted')
    home_forward = Cpt(Signal, kind='omitted')
    home_reverse = Cpt(Signal, kind='omitted')

    def home(self, *args, **kwargs):
        # This function should eventually be used. There is a way to home
        # Newport motors to a reference mark
        raise NotImplementedError("Homing is not yet implemented for Newport "
                                  "motors")


class DelayNewport(DelayBase):
    __doc__ = DelayBase.__doc__
    motor = Cpt(Newport, '')


class PMC100(PCDSMotorBase):
    """
    PCDS implementation of the Motor Record PMC100 motors

    This is a subclass of `PCDSMotorBase` that overwrites missing signals and
    disables the ``home`` method, because it will not work the same way for
    Newport motors.
    """
    __doc__ += basic_positioner_init

    home_forward = Cpt(Signal, kind='omitted')
    home_reverse = Cpt(Signal, kind='omitted')

    def home(self, *args, **kwargs):
        raise NotImplementedError("PMC100 motors have no homing procedure")


class BeckhoffAxis(EpicsMotorInterface):
    """
    Beckhoff Axis motor record as implemented by ESS.

    This class simply adds a convenience `clear_error` method, and makes
    sure to call it on stage.
    """
    __doc__ += basic_positioner_init

    status = Cpt(EpicsSignalRO, '-MsgTxt', kind='normal', string=True)
    cmd_err_reset = Cpt(EpicsSignal, '-ErrRst', kind='omitted')

    tab_whitelist = ['clear_error']

    def clear_error(self):
        """
        Clear any active motion errors on this axis.
        """
        self.cmd_err_reset.put(1)

    def stage(self):
        """
        Stage the Beckhoff axis.

        This simply clears any errors. Stage is called at the start of most
        ``bluesky`` plans.
        """
        self.clear_error()
        return super().stage()


class MotorDisabledError(Exception):
    """
    Error that indicates that we are not allowed to move.
    """
    pass


def Motor(prefix, **kwargs):
    """
    Load a PCDSMotor with the correct class based on prefix

    The prefix is searched for one of the component keys in the table below. If
    none of these are found, by default an ``ophyd.EpicsMotor`` will be used.

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

    Parameters
    ----------
    prefix: str
        Prefix of motor

    kwargs:
        Passed to class constructor
    """
    # Available motor types
    motor_types = (('MMS', IMS),
                   ('CLZ', IMS),
                   ('CLF', IMS),
                   ('MMN', Newport),
                   ('MZM', PMC100),
                   ('MMB', BeckhoffAxis),
                   ('PIC', PCDSMotorBase))
    # Search for component type in prefix
    for cpt_abbrev, _type in motor_types:
        if f':{cpt_abbrev}:' in prefix:
            logger.debug("Found %r in prefix %r, loading %r",
                         cpt_abbrev, prefix, _type)
            return _type(prefix, **kwargs)
    # Default to ophyd.EpicsMotor
    logger.warning("Unable to find type of motor based on component. "
                   "Using 'ophyd.EpicsMotor'")
    return EpicsMotor(prefix, **kwargs)
