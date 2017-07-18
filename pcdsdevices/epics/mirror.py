#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes relating to the offset mirrors used in the FEE and XRT.
"""
############
# Standard #
############
import time
import logging
from enum import Enum
from epics.pv import fmt_time

###############
# Third Party #
###############
from ophyd import PositionerBase
from ophyd.utils import DisconnectedError
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
    motor_stop = Component(Signal)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, settle_time=1, tolerance=0.01, 
                 **kwargs):
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
    def limits(self):
        """
        Returns the EPICS limits of the user_setpoint pv.

        Returns
        -------
        limits : tuple
        """
        return self.user_setpoint.limits

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
        self._started_moving = False
        # Begin the move process
        status = super().move(position, **kwargs)
        self.user_setpoint.put(position, wait=False)

        # If we are within the tolerance we have completed the move
        if abs(self.position - position) < self.tolerance:
            status._finished(success=True)

        # Wait for the status object to register the move as complete
        try:
            if wait:
                status_wait(status)
        except KeyboardInterrupt:
            self.stop()
            raise

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
        pos : float
        """
        self.user_setpoint.put(pos, wait=False)

    def check_value(self, pos):
        """
        Check that the position is within the soft limits.

        Raises
        ------
        LimitError
            When the inputted position is outside the motor limits

        ValueError
            On invalid positions        
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
        

class OffsetMirror(Device):
    """
    X-Ray offset mirror class for each individual mirror system used in the FEE
    and XRT. Controls for the pitch, and primary gantry x and y motors are
    included. 

    Note: Interfaces to the piezo motor, coupling motor, and both secondary
    gantry motors are not provided.

    Components
    ----------
    pitch : OMMotor
        Pitch motor (Both stepper and piezo)

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
    # Gantry motors
    gan_x_p = FormattedComponent(OMMotor, "{self._prefix_xy}:X:P")
    gan_y_p = FormattedComponent(OMMotor, "{self._prefix_xy}:Y:P")

    # This is not implemented in the PLC. Included to appease bluesky
    motor_stop = Component(Signal)
    
    # Currently structured to pass the ioc argument down to the pitch motor
    def __init__(self, prefix, prefix_xy, *, name=None, read_attrs=None, 
                 parent=None, configuration_attrs=None, settle_time=1, 
                 tolerance=0.01, **kwargs):
        self._prefix = prefix
        self._prefix_xy = prefix_xy

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
        Move to the inputted position in pitch. Alias for pitch.move()

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
        return self.pitch.move(position, wait=wait**kwargs)

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

    def set(self, position, wait=True**kwargs):
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
