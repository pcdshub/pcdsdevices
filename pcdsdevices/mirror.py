"""
Offset Mirror Classes

This module contains all the classes relating to the offset mirrors used in the
FEE and XRT. Each offset mirror contains a stepper motor and piezo motor to
control the pitch, and two pairs of motors to control the horizontal and
vertical gantries.
"""
import logging

import numpy as np
from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as Cpt,
                   PVPositioner, FormattedComponent as FCpt)

from .doc_stubs import basic_positioner_init
from .inout import InOutRecordPositioner
from .interface import FltMvInterface, BaseInterface

logger = logging.getLogger(__name__)


class OMMotor(FltMvInterface, PVPositioner):
    """
    Base class for each motor in the LCLS offset mirror system.
    """
    __doc__ += basic_positioner_init

    # position
    readback = Cpt(EpicsSignalRO, ':RBV', auto_monitor=True, kind='hinted')
    setpoint = Cpt(EpicsSignal, ':VAL', limits=True, kind='normal')
    done = Cpt(EpicsSignalRO, ':DMOV', auto_monitor=True, kind='omitted')
    motor_egu = Cpt(EpicsSignal, ':RBV.EGU', kind='omitted')

    # status
    interlock = Cpt(EpicsSignalRO, ':INTERLOCK', kind='omitted')
    enabled = Cpt(EpicsSignalRO, ':ENABLED', kind='omitted')
    # limit switches
    low_limit_switch = Cpt(EpicsSignalRO, ":LLS", kind='omitted')
    high_limit_switch = Cpt(EpicsSignalRO, ":HLS", kind='omitted')

    @property
    def egu(self):
        """
        Engineering units of the readback PV, as reported by EPICS.

        Returns
        -------
        egu: ``str``
        """
        return self.motor_egu.get()

    def check_value(self, position):
        """
        Checks to make sure the inputted value is both valid and within the
        soft limits of the motor.

        Parameters
        ----------
        position: ``float``
            Position to check for validity

        Raises
        ------
        ``ValueError``
            If position is ``None``, ``NaN`` or ``Inf``

        ``LimitError``
            If the position is outside the soft limits
        """
        # Check that we do not have a NaN or an Inf as those will
        # will make the PLC very unhappy ...
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))
        # Use the built-in PVPositioner check_value
        super().check_value(position)


class Pitch(OMMotor):
    """
    HOMS Pitch Mechanism

    The axis is actually a piezo actuator and a stepper motor in series, and
    this is reflected in the PV naming
    """
    __doc__ += basic_positioner_init

    piezo_volts = FCpt(EpicsSignalRO, "{self._piezo}:VRBV", kind='normal')
    stop_signal = FCpt(EpicsSignal, "{self._piezo}:STOP", kind='omitted')
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
    """
    # Readbacks for gantry information
    gantry_difference = FCpt(EpicsSignalRO, "{self.gantry_prefix}:GDIF",
                             kind='normal')
    decoupled = FCpt(EpicsSignalRO, "{self.gantry_prefix}:DECOUPLE",
                     kind='config')
    # Readbacks for the secondary motor
    follower_readback = FCpt(EpicsSignalRO, "{self.follow_prefix}:RBV",
                             kind='normal')
    follower_low_limit_switch = FCpt(EpicsSignalRO, "{self.follow_prefix}:LLS",
                                     kind='omitted')
    follower_high_limit_switch = FCpt(EpicsSignalRO,
                                      "{self.follow_prefix}:HLS",
                                      kind='omitted')

    def __init__(self, prefix, *, gantry_prefix=None, **kwargs):
        self.gantry_prefix = gantry_prefix or 'GANTRY:' + prefix
        self.follow_prefix = prefix + ':S'
        super().__init__(prefix + ':P', **kwargs)

    def check_value(self, pos):
        """
        Add additional check for the gantry coupling

        This is not a safety measure, but instead just here largely
        for bookkeeping and to give the operator further feedback on why the
        requested move is not completed.
        """
        # Check that the gantry is not decoupled
        if self.decoupled.get():
            raise PermissionError("The gantry is not currently coupled")
        # Allow OMMotor to check the value
        super().check_value(pos)


class OffsetMirror(Device, BaseInterface):
    """
    X-Ray offset mirror class.

    This is for each individual mirror system used in the FEE
    and XRT. Controls for the pitch, and primary gantry x and y motors are
    included.

    When controlling the pitch motor, if the piezo is set to 'PID' mode, then
    the pitch mechanism is setup to first move the stepper as close to the
    desired position, then the piezo will kick in to constantly try and correct
    any positional changes.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the pitch motor

    prefix_xy : str
        The EPICS base PV of the gantry x and y gantry motors

    xgantry_prefix : str
        The name of the horizontal gantry if not identical to the prefix

    name : str
        The name of the offset mirror
    """
    # Pitch Motor
    pitch = FCpt(Pitch, "MIRR:{self.prefix}", kind='hinted')
    # Gantry motors
    xgantry = FCpt(Gantry, "{self._prefix_xy}:X",
                   gantry_prefix="{self._xgantry}",
                   add_prefix=['suffix', 'gantry_prefix'],
                   kind='normal')
    ygantry = FCpt(Gantry, "{self._prefix_xy}:Y",
                   gantry_prefix='GANTRY:{self.prefix}:Y',
                   add_prefix=['suffix', 'gantry_prefix'],
                   kind='config')
    # Transmission for Lightpath Interface
    transmission = 1.0
    # QIcon for UX
    _icon = 'fa.minus-square'
    # Subscription types
    SUB_STATE = 'state'

    tab_whitelist = ['pitch', 'xgantry', 'ygantry']

    def __init__(self, prefix, *, prefix_xy=None,
                 xgantry_prefix=None, **kwargs):
        # Handle prefix mangling
        self._prefix_xy = prefix_xy or prefix
        self._xgantry = xgantry_prefix or 'GANTRY:' + prefix + ':X'
        super().__init__(prefix, **kwargs)

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
    Retractable `OffsetMirror`

    Both XRT M1H and XRT M2H can be completely removed from the beam depending
    on the beam destination. In this case, the X gantry can be controlled via
    the standard PCDS states record. This class has all the functionality of
    `OffsetMirror` with the addition of the records that control the
    overall state.

    Parameters
    ----------
    in_lines: ``list``, optional
        List of beamlines that are delivered beam when the mirror is in

    out_lines: ``list``, optional
        List of beamlines thate are delivered beam when the mirror is out
    """
    # Reverse state order as PointingMirror is non-standard
    states_list = ['OUT', 'IN']

    def __init__(self, prefix, *, out_lines=None, in_lines=None, **kwargs):
        # Branching pattern
        self.in_lines = in_lines or list()
        self.out_lines = out_lines or list()
        super().__init__(prefix, **kwargs)

    @property
    def destination(self):
        """
        Current list of destinations the mirror currently supports
        """
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
        """
        return self.in_lines + self.out_lines

    def check_value(self, pos):
        """
        Check that our gantry is coupled before state moves
        """
        # Check the X gantry
        if self.xgantry.decoupled.get():
            raise PermissionError("Can not move the horizontal gantry is "
                                  "uncoupled")
        # Allow StatePositioner to check the state
        return super().check_value(pos)
