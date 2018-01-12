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

Pitch
    Class to handle the control of the pitch mechanism

OffsetMirror
    High level device that includes all the relevant components of the offset
    mirror. This includes a pitch, piezo, primary gantry x, and primary gantry
    y motors. This is the class that should be used to control the offset
    mirrors.
"""
import logging

import numpy as np
from ophyd.signal import Signal
from ophyd.utils.epics_pvs import raise_if_disconnected
from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   PVPositioner, PositionerBase, FormattedComponent as FC)

from .mps import MPS
from ..inout import InOutRecordPositioner

logger = logging.getLogger(__name__)


class OMMotor(PVPositioner):
    """
    Base class for each motor in the LCLS offset mirror system.

    Parameters
    ----------
    prefix : str
        The EPICS base pv to use

    name : str, optional
        The name of the motor

    nominal_position : float, optional
        The position believed to be aligned to the beam. This can either be the
        previously aligned position, or the position given by the alignment
        team

    kwargs:
        All keyword arguments are passed onto PVPositioner
    """
    # position
    readback = C(EpicsSignalRO, ':RBV', auto_monitor=True)
    setpoint = C(EpicsSignal, ':VAL', limits=True)
    done = C(EpicsSignalRO, ':DMOV', auto_monitor=True)
    # status
    interlock = C(EpicsSignalRO, ':INTERLOCK')
    enabled = C(EpicsSignalRO, ':ENABLED')

    def __init__(self, prefix, *, nominal_position=None, **kwargs):
        self.nominal_position = nominal_position
        super().__init__(prefix, **kwargs)
        # Make the default alias for the user_readback the name of the
        # motor itself.
        self.readback.name = self.name

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

    def check_value(self, position):
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
        # Check that we do not have a NaN or an Inf as those will
        # will make the PLC very unhappy ...
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))
        # Use the built-in PVPositioner check_value
        super().check_value(position)

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


class Pitch(OMMotor):
    """
    HOMS Pitch Mechanism

    Similar to OMMotor, but with a larger feature set as it is the most
    requested axis of motion. The axis is actually a piezo actuator and a
    stepper motor in series, and this is reflected in the PV naming
    """
    piezo_volts = FC(EpicsSignalRO, "{self._piezo}:VRBV")
    stop_signal = FC(EpicsSignal, "{self._piezo}:STOP")
    # TODO: Limits will be added soon, but not present yet

    def __init__(self, prefix, **kwargs):
        # Predict the prefix of all piezo pvs
        self._piezo = prefix.replace('MIRR', 'PIEZO')
        super().__init__(prefix, **kwargs)


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
    pitch = FC(OMMotor, "{self.prefix}")
    # Gantry motors
    gan_x_p = FC(OMMotor, "{self._prefix_xy}:X:P")
    gan_y_p = FC(OMMotor, "{self._prefix_xy}:Y:P")
    # This is not implemented in the PLC. Included to appease bluesky
    motor_stop = C(Signal, value=0)
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


class PointingMirror(OffsetMirror):
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
    mps = FC(MPS, '{self._mps_prefix}', veto=True)
    #State Information
    state = FC(InOutRecordPositioner, '{self._state_prefix}')
    #Coupling for horizontal gantry
    x_gantry_decoupled = FC(EpicsSignalRO,
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
        return self.state.position == 'IN'

    @property
    def removed(self):
        """
        Whether PointingMirror is removed
        """
        return self.state.position == 'OUT'

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
