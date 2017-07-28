 #!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Offset Mirror Classes

This script contains all the classes relating to the offset mirrors used in the
FEE and XRT. Each offset mirror contains a stepper motor and piezo motor to
control the pitch, two pairs of motors to control the gantry and then a coupling
motor control the coupling between the gantry motor pairs.

Classes implemented here are as follows:

OMMotor
    Motor class that will represent all the individual motors on the offset
    mirror system. The pitch stepper and all the gantry motors are interfaced
    with using this class.

Piezo
    Motor class to represent the piezo stepper motor. Unless the motor is set
    to be in 'manual' mode this class should never be usable.

OffsetMirror
    High level device that includes all the relevant components of the offset
    mirror. This includes a pitch, piezo, primary gantry x, and primary gantry
    y motors. This is the class that should be used to control the offset
    mirrors.
"""

############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np
from ophyd import PositionerBase
from ophyd.utils import (DisconnectedError, LimitError)
from ophyd.utils.epics_pvs import (raise_if_disconnected, AlarmSeverity)
from ophyd.status import wait as status_wait
from ophyd.signal import Signal

##########
# Module #
##########
from .device import Device
from .signal import (EpicsSignal, EpicsSignalRO)
from .component import (FormattedComponent, Component)

logger = logging.getLogger(__name__)


class OMMotor(Device, PositionerBase):
    """
    Base class for each motor in the LCLS offset mirror system.

    Components
    ----------
    user_readback : EpicsSignalRO, ":RBV"
        Readback for current motor position

    user_setpoint : EpicsSignal, ":VAL"
        Setpoint signal for motor position

    velocity : EpicsSignal, ":VELO"
        Velocity signal for the motor

    motor_is_moving : EpicsSignalRO, ":MOVN"
        Readback for bit that indicates if the motor is currenly moving

    motor_done_move : EpicsSignalRO, ":DMOV"
        Readback for bit that indicates the motor has completed the desired
        motion

    high_limit_switch : EpicsSignalRO, ":HLS"
        Readback for high limit switch bit

    low_limit_switch : EpicsSignalRO, ":LLS"
        Readback for low limit switch bit

    interlock : EpicsSignalRO, ":INTERLOCK"
        Readback indicating if safe torque off (STO) is enabled

    enabled : EpicsSignalRO, ":ENABLED"
        Readback for stepper motor enabled bit

    motor_stop : Signal
        Not implemented in the PLC/EPICS but included as an empty signal to
        appease the Bluesky interface

    Parameters
    ---------- 
    prefix : str
        The EPICS base pv to use

    read_attrs : sequence of attribute names, optional
        The signals to be read during data acquisition (i.e., in read() and
        describe() calls)

    configuration_attrs : sequence of attribute names, optional
        The signals to be returned when asked for the motor configuration (i.e.
        in read_configuration(), and describe_configuration() calls)

    name : str, optional
        The name of the motor

    parent : instance or None, optional
        The instance of the parent device, if applicable

    settle_time : float, optional
        The amount of time to wait after moves to report status completion

    tolerance : float, optional
        Tolerance used to judge if the motor has reached its final position
    """
    # position
    user_readback = Component(EpicsSignalRO, ':RBV', auto_monitor=True)
    user_setpoint = Component(EpicsSignal, ':VAL', limits=True)

    # limits
    upper_ctrl_limit = Component(EpicsSignal, ':VAL.DRVH')
    lower_ctrl_limit = Component(EpicsSignal, ':VAL.DRVL')

    # configuration
    velocity = Component(EpicsSignal, ':VELO')

    # motor status
    motor_is_moving = Component(EpicsSignalRO, ':MOVN')
    motor_done_move = Component(EpicsSignalRO, ':DMOV', auto_monitor=True)
    high_limit_switch = Component(EpicsSignal, ':HLS')
    low_limit_switch = Component(EpicsSignal, ':LLS')

    # status
    interlock = Component(EpicsSignalRO, ':INTERLOCK')
    enabled = Component(EpicsSignalRO, ':ENABLED')

    # appease bluesky since there is no stop pv for these motors
    motor_stop = Component(Signal, value=0)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, settle_time=0, tolerance=0.01,
                 use_limits=True, **kwargs):

        if read_attrs is None:
            read_attrs = ['user_readback']
        if configuration_attrs is None:
            configuration_attrs = ['velocity', 'interlock', 'enabled']

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs, name=name, 
                         parent=parent, settle_time=settle_time, **kwargs)
        
        # Make the default alias for the user_readback the name of the
        # motor itself.
        self.user_readback.name = self.name
        self.tolerance = tolerance
        self.use_limits = use_limits

        # Set up subscriptions
        self.motor_done_move.subscribe(self._move_changed)
        self.user_readback.subscribe(self._pos_changed)

    @property
    @raise_if_disconnected
    def precision(self):
        """
        The precision of the readback PV, as reported by EPICS.

        Returns
        -------
        precision : int
        """
        return self.user_readback.precision

    @property
    @raise_if_disconnected
    def moving(self):
        """
        Whether or not the motor is moving.

        Returns
        -------
        moving : bool
        """
        return bool(self.motor_is_moving.get(use_monitor=False))

    @raise_if_disconnected
    def move(self, position, wait=True, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position : float
            Position to move to

        wait : bool, optional
            Wait for the status object to complete the move before returning

        moved_cb : callable, optional
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        Returns
        -------
        status : MoveStatus
            Status object of the move

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`

        ValueError
            On invalid positions

        RuntimeError
            If motion fails other than timing out
        """
        logger.debug("Moving {} to {}".format(self.name, position))
        # Check if the move is valid
        self._check_value(position)
    
        # Begin the move process
        self._started_moving = False
        # Begin the move process
        status = super().move(position, **kwargs)
        self.user_setpoint.put(position, wait=False)

        # If we are within the tolerance we have completed the move
        if abs(self.position - position) < self.tolerance:
            status._finished(success=True)

        # Wait for the status object to register the move as complete
        if wait:
            logger.info("Waiting for {} to finish move ..."
                        "".format(self.name))
            status_wait(status)

        return status

    def _check_value(self, position):
        """
        Checks to make sure the inputted value is both valid and within the
        soft limits of the motor.

        Parameters
        ----------
        position : float
            Position to check for validity

        Raises
        ------
        ValueError
            If position is None, NaN or Inf

        LimitError
            If the position is outside the soft limits
        """
        # Check for invalid positions
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))
        if not self.use_limits:
            return

        # If the limits are the same value or lower limit is > upper limit, pass
        if self.low_limit >= self.high_limit:
            return

        # Check if it is within the soft limits
        if not (self.low_limit <= position <= self.high_limit):
            err_str = "Requested value {0} outside of range: [{1}, {2}]".format(
                position, self.low_limit, self.high_limit)
            logger.warn(err_str)
            raise LimitError(err_str)
        
    @raise_if_disconnected
    def mv(self, position, wait=True, **kwargs):
        """
        Alias for the move() method.

        Returns
        -------
        status : MoveStatus
            Status object of the move
        """
        return self.move(position, wait=wait, **kwargs)

    @property
    @raise_if_disconnected
    def position(self):
        """
        The current position of the motor in its engineering units.

        Returns
        -------
        position : float
        """
        return self.user_readback.value

    @raise_if_disconnected
    def set_current_position(self, pos):
        """
        Configure the motor user position to the given value.

        Parameters
        ----------
        pos : float
        """
        self.user_setpoint.put(pos, wait=False)

    def check_value(self, pos):
        """
        Check that the position is within the soft limits.

        Raises
        ------
        ValueError
            On invalid positions, or outside the limits
        """
        self.user_setpoint.check_value(pos)

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        """
        Callback from EPICS, indicating a change in position.
        """
        self._set_position(value)

    def _move_changed(self, timestamp=None, value=None, sub_type=None,
                      **kwargs):
        """
        Callback from EPICS, indicating that movement status has changed.
        """
        
        was_moving = self._moving
        self._moving = (value != 1)
        started = False
        if not self._started_moving:
            started = self._started_moving = (not was_moving and self._moving)

        if started:
            self._run_subs(sub_type=self.SUB_START, timestamp=timestamp,
                           value=value, **kwargs)

        if was_moving and not self._moving:
            success = True
            # Check if we are moving towards the low limit switch
            #if self.low_limit_switch.get() == 1:
            #    success = False
            #if self.high_limit_switch.get() == 1:
            #    success = False

            # Some issues with severity, ctrl timeouts, etc.
            #severity = self.user_readback.alarm_severity

            #if severity != AlarmSeverity.NO_ALARM:
            #    status = self.user_readback.alarm_status
            #    logger.error('Motion failed: %s is in an alarm state '
            #                 'status=%s severity=%s',
            #                 self.name, status, severity)
            #    success = False
            self._done_moving(success=success, timestamp=timestamp, value=value)

    @property
    def report(self):
        """
        Returns a dictionary containing current report values of the motor.

        Returns
        -------
        rep : dict
        """
        try:
            rep = super().report
        except DisconnectedError:
            rep = {'position': 'disconnected'}
        rep['pv'] = self.user_readback.pvname
        return rep    

    @property
    def high_limit(self):
        """
        Returns the upper limit fot the user setpoint.

        Returns 
        -------
        high_limit : float
        """
        return self.upper_ctrl_limit.value

    @high_limit.setter
    def high_limit(self, value):
        """
        Sets the high limit for user setpoint.
        """
        self.upper_ctrl_limit.put(value)

    @property
    def low_limit(self):
        """
        Returns the lower limit fot the user setpoint.

        Returns 
        -------
        low_limit : float
        """
        return self.lower_ctrl_limit.value

    @low_limit.setter
    def low_limit(self, value):
        """
        Sets the high limit for user setpoint.
        """
        self.lower_ctrl_limit.put(value)

    @property
    def limits(self):
        """
        Returns the limits of the motor.

        Returns 
        -------
        limits : tuple
        """
        return (self.low_limit, self.high_limit)

    @limits.setter
    def limits(self, value):
        """
        Sets the limits for user setpoint.
        """
        self.low_limit = value[0]
        self.high_limit = value[1]


class Piezo(Device, PositionerBase):
    """
    Class to handle the piezo motor on the mirror pitch mechanism.

    Note: If the motor is set to 'PID' mode then none of the PVs will be
    controllable.

    Components
    ----------
    user_readback : EpicsSignalRO, ":VRBV"
        Readback for current motor position

    user_setpoint : EpicsSignal, ":VSET"
        Setpoint signal for motor position
    
    high_limit : EpicsSignalRO, ":VMAX"
        High limit of piezo voltage

    low_limit : EpicsSignalRO, ":VMIN"
        Low limit of piezo voltage

    enable : EpicsSignalRO, ":Enable"
        Readback for if the piezo is enabled

    motor_stop : Signal
        Not implemented in the PLC/EPICS but included as an empty signal to
        appease the Bluesky interface

    Parameters
    ---------- 
    prefix : str
        The EPICS base pv to use

    read_attrs : sequence of attribute names, optional
        The signals to be read during data acquisition (i.e., in read() and
        describe() calls)

    configuration_attrs : sequence of attribute names, optional
        The signals to be returned when asked for the motor configuration (i.e.
        in read_configuration(), and describe_configuration() calls)

    name : str, optional
        The name of the piezo

    parent : instance or None, optional
        The instance of the parent device, if applicable    
    """    
    # position
    user_readback = Component(EpicsSignalRO, ':VRBV')
    user_setpoint = Component(EpicsSignal, ':VSET', limits=True)

    # configuration
    high_limit = Component(EpicsSignal, ':VMAX')
    low_limit = Component(EpicsSignal, ':VMIN')

    # status
    enable = Component(EpicsSignalRO, ':Enable')

    # Stop
    motor_stop = Component(Signal, value=0)
    
    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['user_readback', 'user_setpoint', 'enable']

        if configuration_attrs is None:
            configuration_attrs = ['high_limit', 'low_limit', 'enable']

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)

    @property
    @raise_if_disconnected
    def precision(self):
        """
        The precision of the readback PV, as reported by EPICS.

        Returns
        -------
        precision : int        
        """
        return self.user_readback.precision

    @property
    @raise_if_disconnected
    def limits(self):
        """
        Returns the minimum and maximum voltage of the piezo.

        Returns
        -------
        limits : tuple
            Tuple of (low_limit, high_limit)
        """
        return (self.low_limit.value, self.high_limit.value)

    @raise_if_disconnected
    def move(self, position, wait=True, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Note: This will only work if the motor is in 'manual' mode.

        Parameters
        ----------
        position : float
            Position to move to

        wait : bool, optional
            Wait for the status object to complete the move before returning

        moved_cb : callable, optional
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        Returns
        -------
        status : MoveStatus
            Status object of the move

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`

        ValueError
            On invalid positions

        RuntimeError
            If motion fails other than timing out
        """
        self._started_moving = False

        status = super().move(position, **kwargs)
        self.user_setpoint.put(position, wait=False)

        # Wait for status
        if wait:
            status_wait(status)

        return status

    @raise_if_disconnected
    def mv(self, position, wait=True, **kwargs):
        """
        Alias for the move() method.

        Returns
        -------
        status : MoveStatus
            Status object of the move
        """
        return self.move(position, wait=wait, **kwargs)

    @property
    @raise_if_disconnected
    def position(self):
        """
        The current position of the motor in its engineering units.
        
        Returns
        -------
        position : float
        """
        return self.user_readback.value

    @raise_if_disconnected
    def set_current_position(self, pos):
        """
        Configure the motor user position to the given value.
        
        Parameters
        ----------
        pos
           Position to set.
        """
        self.set_use_switch.put(1, wait=True)
        self.user_setpoint.put(pos, wait=True)
        self.set_use_switch.put(0, wait=True)

    def check_value(self, pos):
        """
        Check that the position is within the soft limits.

        Raises
        ------
        ValueError
            On invalid positions, or outside the limits
        """
        # Check it is a valid position
        if np.isnan(pos) or np.isinf(pos):
            raise ValueError("Invalid position inputted.")
        # Check it is within the limits
        if pos < self.low_limit or pos > self.high_limit:
            raise ValueError("Position outside voltage limits.")

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        """
        Callback from EPICS, indicating a change in position.
        """
        self._set_position(value)

    @property
    def report(self):
        """
        Returns a dictionary containing current report values of the motor.

        Returns
        -------
        rep : dict
        """        
        try:
            rep = super().report
        except DisconnectedError:
            # TODO there might be more in this that gets lost
            rep = {'position': 'disconnected'}
        rep['pv'] = self.user_readback.pvname
        return rep
    

class OffsetMirror(Device):
    """
    X-Ray offset mirror class for each individual mirror system used in the FEE
    and XRT. Controls for the pitch, and primary gantry x and y motors are
    included.

    When controlling the pitch motor, if the piezo is set to 'PID' mode, then
    the pitch mechanism is setup to first move the stepper as close to the
    desired position, then the piezo will kick in to constantly try and correct
    any positional changes. When in this mode the piezo cannot be controlled
    via EPICS, and must first be switched to 'manual' mode.

    Note: Interfaces to the coupling motor and both secondary gantry motors are
    not provided.

    Components
    ----------
    pitch : OMMotor
        Stepper motor of the pitch mechanism

    piezo : Piezo
        Piezo motor of the pitch mechanism

    gan_x_p : OMMotor
        Primary X gantry motor

    gan_y_p : OMMotor
        Primary Y gantry motor

    motor_stop : Signal
        Not implemented in the PLC/EPICS but included as an empty signal to
        appease the Bluesky interface

    Parameters
    ---------- 
    prefix : str
        The EPICS base PV of the pitch motor

    prefix_xy : str
        The EPICS base PV of the gantry x and y gantry motors

    read_attrs : sequence of attribute names, optional
        The signals to be read during data acquisition (i.e., in read() and
        describe() calls)

    configuration_attrs : sequence of attribute names, optional
        The signals to be returned when asked for the motor configuration (i.e.
        in read_configuration(), and describe_configuration() calls)

    name : str, optional
        The name of the offset mirror

    parent : instance or None, optional
        The instance of the parent device, if applicable

    settle_time : float, optional
        The amount of time to wait after the pitch motor moves to report status
        completion

    tolerance : float, optional
        Tolerance used to judge if the pitch motor has reached its final 
        position
    """    
    # Pitch Motor
    pitch = FormattedComponent(OMMotor, "{self._prefix}")
    # Piezo Motor
    piezo = FormattedComponent(Piezo, "PIEZO:{self._area}:{self._mirror}")    
    # Gantry motors
    gan_x_p = FormattedComponent(OMMotor, "{self._prefix_xy}:X:P")
    gan_y_p = FormattedComponent(OMMotor, "{self._prefix_xy}:Y:P")

    # This is not implemented in the PLC. Included to appease bluesky
    motor_stop = Component(Signal, value=0)
    
    # Currently structured to pass the ioc argument down to the pitch motor
    def __init__(self, prefix, prefix_xy, *, name=None, read_attrs=None, 
                 parent=None, configuration_attrs=None, settle_time=0, 
                 tolerance=0.01, **kwargs):

        self._prefix = prefix
        self._prefix_xy = prefix_xy
        self._area = prefix.split(":")[1]
        self._mirror = prefix.split(":")[2]
        
        if read_attrs is None:
            read_attrs = ['pitch', 'gan_x_p', 'gan_y_p']

        if configuration_attrs is None:
            configuration_attrs = []

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
        self.settle_time = settle_time
        self.tolerance = tolerance

    def move(self, position, wait=True, **kwargs):
        """
        Move the pitch motor to the inputted position, optionally waiting for
        the move to complete.

        Parameters
        ----------
        position : float
            Position to move to

        wait : bool, optional
            Wait for the status object to complete the move before returning

        moved_cb : callable, optional
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        Returns
        -------
        status : MoveStatus
            Status object of the move

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`

        ValueError
            On invalid positions

        RuntimeError
            If motion fails other than timing out
        """        
        return self.pitch.move(position, wait=wait, **kwargs)

    @raise_if_disconnected
    def mv(self, position, wait=True, **kwargs):
        """
        Move the pitch motor to the inputted position. Alias for the move() 
        method.

        Returns
        -------
        status : MoveStatus
            Status object of the move
        """
        return self.move(position, wait=wait, **kwargs)

    def set(self, position, wait=True, **kwargs):
        """
        Set the pitch motoro to the inputted position. Alias for the move() 
        method.

        Returns
        -------
        status : MoveStatus
            Status object of the move        
        """
        return self.move(position, wait=wait, **kwargs)
    
    @property
    @raise_if_disconnected
    def position(self):
        """
        Readback the current pitch position. Alias for the pitch.position
        property.

        Returns
        -------
        position : float
        """
        return self.pitch.user_readback.value        

    @property
    @raise_if_disconnected
    def alpha(self):
        """
        Pitch motor readback position. Alias for the position property.

        Returns
        -------
        alpha : float        
        """
        return self.position

    @alpha.setter
    def alpha(self, position, wait=True, **kwargs):
        """
        Setter for alpha. Alias for the move() method.

        Returns
        -------
        status : MoveStatus
            Status object of the move        
        """
        return self.move(position, wait=wait, **kwargs)

    @property
    @raise_if_disconnected
    def x(self):
        """
        Primary gantry X readback position. Alias for the gan_x_p.position 
        property.

        Returns
        -------
        position : float
        """
        return self.gan_x_p.position

    @x.setter
    def x(self, position, **kwargs):
        """
        Setter for the primary gantry X motor. Alias for the gan_x_p.move() 
        method.

        Returns
        -------
        status : MoveStatus
            Status object of the move        
        """
        return self.gan_x_p.move(position, **kwargs)

    @property
    @raise_if_disconnected
    def y(self):
        """
        Primary gantry Y readback position. Alias for the gan_y_p.position 
        property.

        Returns
        -------
        position : float
        """
        return self.gan_y_p.position

    @y.setter
    def y(self, position, **kwargs):
        """
        Setter for the primary gantry Y motor. Alias for the gan_y_p.move() 
        method.

        Returns
        -------
        status : MoveStatus
            Status object of the move        
        """
        return self.gan_y_p.move(position, **kwargs)

    @property
    def settle_time(self):
        """
        Returns the settle time of the pitch motor.

        Returns
        -------
        settle_time : float
        """
        return self.pitch.settle_time

    @settle_time.setter
    def settle_time(self, settle_time):
        """
        Setter for the pitch settle time.
        """
        self.pitch.settle_time = settle_time

    @property
    def tolerance(self):
        """
        Returns the tolerance of the pitch motor.

        Returns
        -------
        settle_time : float
        """
        return self.pitch.tolerance

    @tolerance.setter
    def tolerance(self, tolerance):
        """
        Setter for the tolerance of the pitch motor
        """
        self.pitch.tolerance = tolerance

    @property
    def high_limit(self):
        """
        Returns the upper limit fot the pitch motor.

        Returns 
        -------
        high_limit : float
        """
        return self.pitch.high_limit

    @high_limit.setter
    def high_limit(self, value):
        """
        Sets the high limit for pitch motor.

        Returns 
        -------
        status : StatusObject
        """
        self.pitch.high_limit = value

    @property
    def low_limit(self):
        """
        Returns the lower limit fot the pitch motor.

        Returns 
        -------
        low_limit : float
        """
        return self.pitch.low_limit

    @low_limit.setter
    def low_limit(self, value):
        """
        Sets the high limit for pitch motor.

        Returns 
        -------
        status : StatusObject
        """
        self.pitch.low_limit = value

    @property
    def limits(self):
        """
        Returns the EPICS limits of the user_setpoint pv.

        Returns
        -------
        limits : tuple
        """
        return self.pitch.limits

    @limits.setter
    def limits(self, value):
        """
        Sets the limits of the user_setpoint pv
        """
        self.pitch.limits = value
