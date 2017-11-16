#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Offset Mirror Classes

This script contains all the classes relating to the offset mirrors used in the
FEE and XRT. Each offset mirror contains a stepper motor and piezo motor to
control the pitch, two pairs of motors to control the gantry and then a
coupling motor control the coupling between the gantry motor pairs.

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
from ophyd.utils.epics_pvs import raise_if_disconnected
from ophyd.status import wait as status_wait
from ophyd.signal import Signal

##########
# Module #
##########
from .device import Device
from .signal import (EpicsSignal, EpicsSignalRO)
from .component import (FormattedComponent, Component)
from .mps import MPS
from .state import InOutStates
from ..interface import BranchingInterface

logger = logging.getLogger(__name__)


class OMMotor(Device, PositionerBase):
    """
    Base class for each motor in the LCLS offset mirror system.

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

    nominal_position : float, optional
        The position believed to be aligned to the beam. This can either be the
        previously aligned position, or the position given by the alignment
        team

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

    # misc
    motor_egu = Component(EpicsSignalRO, ':RBV.EGU')

    # appease bluesky since there is no stop pv for these motors
    motor_stop = Component(Signal, value=0)

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, settle_time=0, tolerance=0.01,
                 use_limits=True, nominal_position=None, **kwargs):

        self.nominal_position = nominal_position
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
    def egu(self):
        """
        Engineering units of the readback PV, as reported by EPICS.

        Returns
        -------
        egu: str
        """
        return self.motor_egu.get()

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
    def move(self, position, wait=False, **kwargs):
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

        # Make sure limits are logical
        if self.low_limit >= self.high_limit:
            return

        # Check if it is within the soft limits
        if not (self.low_limit <= position <= self.high_limit):
            err_str = "Requested value {0} outside of range: [{1}, {2}]"
            logger.warn(err_str.format(position, self.low_limit,
                                       self.high_limit))
            raise LimitError(err_str)

    @raise_if_disconnected
    def mv(self, position, wait=False, **kwargs):
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
            self._done_moving(success=success, timestamp=timestamp,
                              value=value)

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
    def move(self, position, wait=False, **kwargs):
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
    def mv(self, position, wait=False, **kwargs):
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


class OffsetMirror(Device, PositionerBase):
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
    pitch = FormattedComponent(OMMotor, "{self.prefix}")
    # Gantry motors
    gan_x_p = FormattedComponent(OMMotor, "{self._prefix_xy}:X:P")
    gan_y_p = FormattedComponent(OMMotor, "{self._prefix_xy}:Y:P")
    # This is not implemented in the PLC. Included to appease bluesky
    motor_stop = Component(Signal, value=0)
    #Transmission for Lightpath Interface
    transmission= 1.0
    SUB_STATE = 'sub_state_changed'

    def __init__(self, prefix, prefix_xy, *, name=None, read_attrs=None,
                 parent=None, configuration_attrs=None, settle_time=0,
                 tolerance=0.5, timeout=None, nominal_position=None,
                 **kwargs):
        self._prefix_xy = prefix_xy
        self._area = prefix.split(":")[1]
        self._mirror = prefix.split(":")[2]

        if read_attrs is None:
            read_attrs = ['pitch', 'gan_x_p', 'gan_y_p']

        if configuration_attrs is None:
            configuration_attrs = []

        super().__init__(prefix, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         name=name, parent=parent, timeout=timeout,
                         settle_time=settle_time,
                         **kwargs)
        self.settle_time = settle_time
        self.tolerance = tolerance
        self.timeout = timeout
        self.nominal_position = nominal_position

    def move(self, position, wait=False, **kwargs):
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

    mv = move

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
        return self.pitch.position

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

    @property
    def timeout(self):
        return self.pitch.timeout

    @timeout.setter
    def timeout(self, tmo):
        if tmo is not None:
            tmo = float(tmo)
        self.pitch.timeout = tmo
        self.gan_x_p.timeout = tmo
        self.gan_y_p.timeout = tmo

    @property
    def nominal_position(self):
        return self.pitch.nominal_position

    @nominal_position.setter
    def nominal_position(self, pos):
        if pos is not None:
            pos = float(pos)
        self.pitch.nominal_position = pos

    @property
    def egu(self):
        return 'um'

    @property
    def inserted(self):
        """
        Treat OffsetMirror as always inserted
        """
        return True

    @property
    def removed(self):
        """
        Treat OffsetMirror as always inserted
        """
        return False


class PointingMirror(OffsetMirror, metaclass=BranchingInterface):
    """
    mps_prefix : str, optional
        Base prefix for the MPS bit of the mirror

    state_prefix : str, optional
        Base prefix for the state record that has the In/Out state of the
        mirror

    in_lines : list, optional
        List of beamlines that are delivered beam when the mirror is in

    out_lines : list, optional
        List of beamlines thate are delivered beam when the mirror is out
    """
    #MPS Information
    mps = FormattedComponent(MPS, '{self._mps_prefix}', veto=True)
    #State Information
    state = FormattedComponent(InOutStates, '{self._state_prefix}')
    #Coupling for horizontal gantry
    x_gantry_decoupled = FormattedComponent(EpicsSignalRO,
                                            "GANTRY:{self._prefix_xy}:X:DECOUPLE")

    def __init__(self, *args, mps_prefix=None, state_prefix=None, out_lines=None,
                 in_lines=None, **kwargs):
        self._has_subscribed = False
        #Store MPS information
        self._mps_prefix = mps_prefix
        #Store State information
        self._state_prefix = state_prefix
        #Branching pattern
        self.in_lines = in_lines
        self.out_lines = out_lines
        super().__init__(*args, **kwargs)

    @property
    def inserted(self):
        """
        Whether PointingMirror is inserted
        """
        return self.state.value == 'IN'

    @property
    def removed(self):
        """
        Whether PointingMirror is removed
        """
        return self.state.value == 'OUT'

    def remove(self, wait=False, timeout=None): 
        """
        Remove the PointingMirror from the beamline

        If the horizontal gantry is not coupled, the request will raise a
        `RuntimeError`
        """
        if self.coupled:
            return self.state.move("OUT", wait=wait, timeout=timeout)
        else:
            raise RuntimeError("Gantry is not coupled, can not move")

    def insert(self, wait=False, timeout=None):
        """
        Insert the pointing mirror into the beamline

        If the horizontal gantry is not coupled, the request will raise a
        `RuntimeError`
        """
        if self.coupled:
            return self.state.move("IN", wait=wait, timeout=timeout)
        else:
            raise RuntimeError("Gantry is not coupled, can not move")
 
    @property
    def destination(self):
        """
        Current destination of the beamlines, return an empty list if the state
        is unknown. If :attr:`.branches` only returns a single possible
        beamline, that is returned. Otherwise, the `state` PV is used
        """
        #A single possible destination
        if len(self.branches) == 1:
            return self.branches
        #Inserted
        if self.inserted and not self.removed:
            return self.in_lines
        #Removed
        elif self.removed and not self.inserted:
            return self.out_lines
        #Unknown
        else:
            return []

    @property
    def branches(self):
        """
        Return all possible beamlines for mirror destinations

        If the `in_lines` and `out_lines` are not set, it is assumed that this
        steering mirror does not redirect beam to another beamline and the
        beamline of the mirror is used
        """
        if self.in_lines and self.out_lines:
            return self.in_lines + self.out_lines
        else:
            return [self.db.beamline]

    @property
    def coupled(self):
        """
        Whether the horizontal gantry is coupled
        """
        return not bool(self.x_gantry_decoupled.get())

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes of the mirror

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        if not self._has_subscribed:
            #Subscribe to changes in state
            self.state.subscribe(self._on_state_change, run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _on_state_change(self, **kwargs):
        """
        Callback run on state change
        """
        kwargs.pop('sub_type', None)
        kwargs.pop('obj', None)
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)
