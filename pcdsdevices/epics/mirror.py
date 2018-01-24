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
                   PVPositioner, FormattedComponent as FC)

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
    # limit switches
    low_limit_switch = C(EpicsSignalRO, ":LLS")
    high_limit_switch = C(EpicsSignalRO, ":HLS")

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


class Gantry(OMMotor):
    """
    Gantry Axis

    The horizontal and vertical motion of the OffsetMirror are controlled by
    two coupled stepper motors. Instructions are sent to both by simply
    requesting a move on the primary so they are represented here as a single
    motor with additional diagnostics and interlock

    Parameters
    ----------
    prefix : str
        Base prefix for both stepper motors i.e XRT:M1H. Do not include the "P"
        or "S" to indicate primary or secondary steppers

    gantry_prefix : str, optional
        Prefix for the shared gantry diagnostics if it is different than the
        stepper motor prefix

    kwargs:
        All passed to OMMotor
    """
    # Readbacks for gantry information
    gantry_difference = FC(EpicsSignalRO, "{self.gantry_prefix}:GDIF")
    decoupled = FC(EpicsSignalRO, "{self.gantry_prefix}:DECOUPLE")
    # Readbacks for the secondary motor
    follower_readback = FC(EpicsSignalRO, "{self.follow_prefix}:RBV")
    follower_low_limit_switch = FC(EpicsSignalRO, "{self.follow_prefix}:LLS")
    follower_high_limit_switch = FC(EpicsSignalRO, "{self.follow_prefix}:HLS")

    _default_read_attrs = ['readback', 'setpoint', 'gantry_difference']

    def __init__(self, prefix, *, gantry_prefix=None, **kwargs):
        self.gantry_prefix = gantry_prefix or 'GANTRY:' + prefix
        self.follow_prefix = prefix + ':S'
        super().__init__(prefix + ':P', **kwargs)

    def move(self, position, **kwargs):
        """
        Move the gantry to a specific position

        Calls OMMotor.move but first checks that the gantry is coupled before
        proceeding. This is not a safety measure, but instead just here largely
        for bookkeeping and to give the operator further feedback on why the
        requested move is not completed.

        Parameters
        ----------
        position: float
            Requested position

        kwargs:
            Passed to OMMotor.move
        """
        # Check that the gantry is not decoupled
        if not self.decoupled.get():
            raise PermissionError("The gantry is not currently coupled")
        return super().move(position, **kwargs)


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

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the pitch motor

    prefix_xy : str
        The EPICS base PV of the gantry x and y gantry motors

    xgantry_prefix : str
        The name of the horizontal gantry if not identical to the prefix

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
    """
    # Pitch Motor
    pitch = FC(Pitch, "MIRR:{self.prefix}")
    # Gantry motors
    xgantry = FC(Gantry, "{self._prefix_xy}:X",
                 gantry_prefix="{self._xgantry}",
                 add_prefix=['suffix', 'gantry_prefix'])
    ygantry = FC(Gantry, "{self._prefix_xy}:Y")
    # Transmission for Lightpath Interface
    transmission = 1.0
    SUB_STATE = 'sub_state_changed'

    _default_read_attrs = ['pitch', 'xgantry.readback',
                           'xgantry.gantry_difference']

    _default_configuration_attrs = ['ygantry.setpoint']

    def __init__(self, prefix, *, prefix_xy=None, xgantry_prefix=None,
                 nominal_position=None, **kwargs):
        # Handle prefix mangling
        self._prefix_xy = prefix_xy or prefix
        self._xgantry = xgantry_prefix or 'GANTRY:' + prefix + ':X'
        super().__init__(prefix, **kwargs)
        self.pitch.nominal_position = nominal_position

    @property
    def nominal_position(self):
        """
        The nominal angle that the OffsetMirror is considered aligned
        """
        return self.pitch.nominal_position

    @nominal_position.setter
    def nominal_position(self, pos):
        if pos is not None:
            pos = float(pos)
        self.pitch.nominal_position = pos

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


class PointingMirror(InOutRecordPositioner, OffsetMirror):
    """
    Parameters
    ----------
    mps_prefix : str, optional
        Base prefix for the MPS bit of the mirror

    in_lines : list, optional
        List of beamlines that are delivered beam when the mirror is in

    out_lines : list, optional
        List of beamlines thate are delivered beam when the mirror is out
    """
    # MPS Information
    mps = FC(MPS, '{self._mps_prefix}', veto=False)
    # Define default read and configuration attributes
    _default_read_attrs = ['pitch', 'xgantry.readback',
                           'xgantry.gantry_difference']
    _default_configuration_attrs = ['ygantry.setpoint', 'state']

    def __init__(self, *args, mps_prefix=None,
                 out_lines=None, in_lines=None,
                 **kwargs):
        self._has_subscribed = False
        # Store MPS information
        self._mps_prefix = mps_prefix
        # Branching pattern
        self.in_lines = in_lines
        self.out_lines = out_lines
        super().__init__(*args, **kwargs)

    @property
    def destination(self):
        """
        Current destination of the beamlines, return an empty list if the state
        is unknown. If :attr:`.branches` only returns a single possible
        beamline, that is returned. Otherwise, the `state` PV is used
        """
        # A single possible destination
        if len(self.branches) == 1:
            return self.branches
        # Inserted
        if self.inserted and not self.removed:
            return self.in_lines
        # Removed
        elif self.removed and not self.inserted:
            return self.out_lines
        # Unknown
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

    def set(self, *args, **kwargs):
        """
        Check that our gantry is coupled before state moves
        """
        # Check the X gantry
        if self.xgantry.decoupled.get():
            raise PermissionError("Can not move the gantry is uncoupled")
        # Follow through with the super().set
        super().set(*args, **kwargs)
