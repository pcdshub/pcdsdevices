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

    
class Piezo(Device, PositionerBase):
    """
    Piezo driver object used for fine pitch adjustments.
    """
    # position
    user_readback = Component(EpicsSignalRO, ':VRBV')
    user_setpoint = Component(EpicsSignal, ':VSET', limits=True)

    # configuration
    high_limit = Component(EpicsSignal, ':VMAX')
    low_limit = Component(EpicsSignal, ':VMIN')

    # status
    enable = Component(EpicsSignalRO, ':Enable')
    stop = Component(EpicsSignalRO, ':STOP')

    motor_stop = Component(Signal)

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
        """
        return self.user_readback.precision

    @property
    @raise_if_disconnected
    def limits(self):
        """
        Returns the EPICS limits of the user_setpoint pv.
        """
        return self.user_setpoint.limits

    @raise_if_disconnected
    def stop(self, *, success=False):
        """
        Stops the motor.
        """
        self.motor_stop.put(1, wait=False)
        super().stop(success=success)

    @raise_if_disconnected
    def move(self, position, wait=True, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.
        Returns
        -------
        status : MoveStatus
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

        try:
            if wait:
                status_wait(status)
        except KeyboardInterrupt:
            self.stop()
            raise

        return status

    @raise_if_disconnected
    def mv(self, position, wait=True, **kwargs):
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
        """
        if pos < self.low_limit or pos > self.high_limit:
            raise ValueError

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        """
        Callback from EPICS, indicating a change in position.
        """
        self._set_position(value)

    @property
    def report(self):
        try:
            rep = super().report
        except DisconnectedError:
            # TODO there might be more in this that gets lost
            rep = {'position': 'disconnected'}
        rep['pv'] = self.user_readback.pvname
        return rep    

    
class CouplingMotor(Device):
    """
    Device that manages the coupling between gantry motors.
    """
    gan_diff = Component(EpicsSignalRO, ':GDIF')
    gan_tol = Component(EpicsSignal, ':GTOL', limits=True)
    enabled = Component(EpicsSignal, ':ENABLED')
    decouple = Component(EpicsSignal, ':DECOUPLE')
    high_limit_switch = Component(EpicsSignal, ':HLS')
    low_limit_switch = Component(EpicsSignal, ':LLS')
    fault = Component(EpicsSignalRO, ':FAULT')

    def __init__(self, prefix, *, name=None, read_attrs=None, parent=None, 
                 configuration_attrs=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['gan_diff', 'decouple']
            
        if configuration_attrs is None:
            configuration_attrs = ['gan_dif', 'gan_tol', 'enabled', 
                                   'decouple', 'fault', 'high_limit_switch', 
                                   'low_limit_switch']

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
        

class OffsetMirror(Device):
    """
    X-Ray offset mirror class to represent the various mirrors we use in the FEE
    and XRT to steer the beam.
    """
    # Gantry motors
    gan_x_p = FormattedComponent(OMMotor, "{self._xy_prefix}:X:P")
    gan_x_s = FormattedComponent(OMMotor, "{self._xy_prefix}:X:S")
    gan_y_p = FormattedComponent(OMMotor, "{self._xy_prefix}:Y:P")
    gan_y_s = FormattedComponent(OMMotor, "{self._xy_prefix}:Y:S")

    # Piezo motor
    piezo = FormattedComponent(Piezo, "PIEZO:{self._area}:{self._mirror}")
    
    # # Coupling motor
    coupling = FormattedComponent(CouplingMotor, "{self._gan_x}")
    
    # Pitch Motor
    pitch = FormattedComponent(OMMotor, "{self._prefix}")

    # This is not implemented in the PLC. Included to appease bluesky
    motor_stop = Component(Signal)
    
    # Currently structured to pass the ioc argument down to the pitch motor
    def __init__(self, prefix, xy_prefix, gantry_x_prefix, *, name=None,
                 read_attrs=None, parent=None, configuration_attrs=None,
                 settle_time=1, tolerance=0.01, **kwargs):
        self._prefix = prefix
        self._area = prefix.split(":")[1]
        self._mirror = prefix.split(":")[2]
        self._xy_prefix = xy_prefix
        self._gan_x = gantry_x_prefix

        if read_attrs is None:
            read_attrs = ['pitch', 'gan_x_p', 'gan_x_s']

        if configuration_attrs is None:
            configuration_attrs = []

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, **kwargs)
        self.settle_time = settle_time
        self.tolerance = tolerance

    def move(self, position, **kwargs):
        """
        Move to the inputted position in pitch.
        """        
        return self.pitch.move(position, **kwargs)

    @raise_if_disconnected
    def mv(self, position, wait=True, **kwargs):
        return self.move(position, wait=wait, **kwargs)

    def set(self, position, **kwargs):
        """
        Alias for move.
        """
        return self.move(position, **kwargs)
    
    @property
    @raise_if_disconnected
    def position(self):
        """
        Readback the current pitch position.
        """
        return self.pitch.user_readback.value        

    @property
    @raise_if_disconnected
    def alpha(self):
        """
        Mirror pitch readback. Does the same thing as self.position.
        """
        return self.position

    @alpha.setter
    def alpha(self, position, **kwargs):
        """
        Mirror pitch setter. Does the same thing as self.move.
        """
        return self.move(position, **kwargs)

    @property
    @raise_if_disconnected
    def x(self):
        """
        Mirror x position readback.
        """
        return self.gan_x_p.user_readback.value

    @x.setter
    def x(self, position, **kwargs):
        """
        Mirror x position setter.
        """
        return self.gan_x_p.move(position, **kwargs)

    @property
    @raise_if_disconnected
    def decoupled(self):
        """
        Checks to see if the gantry x motors are coupled.
        """
        return bool(self.coupling.decouple.value)

    @property
    @raise_if_disconnected
    def fault(self):
        """
        Checks if the coupling motor is faulted.
        """
        return bool(self.coupling.fault.value)

    @property
    @raise_if_disconnected
    def gdif(self):
        """
        Returns the gantry difference of the x gantry motors.
        """
        return self.coupling.gan_diff.value

    @property
    def settle_time(self):
        """
        Returns the settle time of the pitch motor.
        """
        return self.pitch.settle_time

    @settle_time.setter
    def settle_time(self, settle_time):
        """
        Sets the settle time of the pitch motor.
        """
        self.pitch.settle_time = settle_time

    @property
    def tolerance(self):
        """
        Returns the tolerance of the pitch motor.
        """
        return self.pitch.tolerance

    @tolerance.setter
    def tolerance(self, tolerance):
        """
        Sets the tolerance of the pitch motor.
        """
        self.pitch.tolerance = tolerance
