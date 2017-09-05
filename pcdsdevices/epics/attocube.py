#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attocube devices
"""
############
# Standard #
############
import logging
import os

###############
# Third Party #
###############
import numpy as np
from ophyd import PositionerBase
from ophyd.utils import LimitError
from ophyd.status import wait as status_wait

##########
# Module #
##########
from .device import Device
from .component import Component
from .epicsmotor import EpicsMotor
from .signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)


class EccController(Device):
    """
    ECC Controller
    """
    _firm_day = Component(EpicsSignalRO, ":CALC:FIRMDAY")
    _firm_month = Component(EpicsSignalRO, ":CALC:FIRMMONTH")
    _firm_year = Component(EpicsSignalRO, ":CALC:FIRMYEAR")
    _flash = Component(EpicsSignal, ":RDB:FLASH", write_pv=":CMD:FLASH")
    
    @property 
    def firmware(self):
        """
        Returns the firmware in the same date format as the EDM screen.
        """
        return "{0}/{1}/{2}".format(
            self._firm_day.value, self._firm_month.value, self._firm_year.value)
    
    @property
    def flash(self):
        """
        Saves the current configuration of the controller.
        """
        return self._flash.set(1)


class EccBase(Device, PositionerBase):
    """
    ECC Motor Class
    """
    # position
    user_readback = Component(EpicsSignalRO, ":POSITION", auto_monitor=True)
    user_setpoint = Component(EpicsSignal, ":CMD:TARGET")

    # limits
    upper_ctrl_limit = Component(EpicsSignal, ':CMD:TARGET.HOPR')
    lower_ctrl_limit = Component(EpicsSignal, ':CMD:TARGET.LOPR')

    # configuration
    motor_egu = Component(EpicsSignalRO, ":UNIT")
    motor_amplitude = Component(EpicsSignal, ":CMD:AMPL")
    motor_dc = Component(EpicsSignal, ":CMD:DC")
    motor_frequency = Component(EpicsSignal, ":CMD:FREQ")

    # motor status
    motor_connected = Component(EpicsSignalRO, ":ST_CONNECTED")
    motor_enabled = Component(EpicsSignalRO, ":ST_ENABLED")
    motor_referenced = Component(EpicsSignalRO, ":ST_REFVAL")
    motor_error = Component(EpicsSignalRO, ":ST_ERROR")
    motor_is_moving = Component(EpicsSignalRO, ":RD_MOVING")
    motor_done_move = Component(EpicsSignalRO, ":RD_INRANGE")
    high_limit_switch = Component(EpicsSignal, ":ST_EOT_FWD")
    low_limit_switch = Component(EpicsSignal, ":ST_EOT_BWD")

    # commands
    motor_stop = Component(EpicsSignal, ":CMD:STOP")
    motor_reset = Component(EpicsSignal, ":CMD:RESET.PROC")
    motor_enable = Component(EpicsSignal, ":CMD:EOT")

    def __init__(self, prefix, desc=None, *args, **kwargs):
        self.desc=desc
        super().__init__(prefix, *args, **kwargs)
        if desc is None:
            self.desc = self.name

    @property
    def position(self):
        """
        Returns the current position of the motor.

        Returns
        -------
        position : float
            Current position of the motor.
        """
        return self.user_readback.value

    @property
    def egu(self):
        """
        The engineering units (EGU) for a position

        Returns
        -------
        Units : str
            Engineering units for the position.
        """
        return self.motor_egu.get()

    def enable(self):
        """
        Enables the motor power.

        Returns
        -------
        Status
            The status object for setting the power signal.
        """
        return self.motor_enable.set(1)

    def disable(self):
        """
        Disables the motor power.

        Returns
        -------
        Status
            The status object for setting the power signal.
        """
        return self.motor_enable.set(0)

    @property
    def enabled(self):
        """
        Returns if the motor is curently enabled.

        Returns
        -------
        enabled : bool
            True if the motor is powered, False if not.
        """
        return bool(self.motor_enable.value)

    @property
    def connected(self):
        """
        Returns if the motor is curently connected.

        Returns
        -------
        connected : bool
            True if the motor is connected, False if not.
        """
        return bool(self.motor_connected.value)

    @property
    def referenced(self):
        """
        Returns if the motor is curently referenced.

        Returns
        -------
        referenced : bool
            True if the motor is referenced, False if not.
        """
        return bool(self.motor_referenced.value)
    
    @property
    def error(self):
        """
        Returns the current error with the motor.
        
        Returns
        -------
        error : bool
            Error enumeration.
        """
        return bool(self.motor_error.value)

    def reset(self):
        """
        Sets the current position to be the zero position of the motor.

        Returns
        -------
        status : StatusObject        
            Status object for the set.
        """
        self.motor_reset.set(1)
    
    
    def move(self, position, *args, **kwargs):
        """
        Move to a specified position.

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
            Status object for the move.
        
        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        
        ValueError
            On invalid positions
        
        RuntimeError
            If motion fails other than timing out
        """
        try:
            # Make sure the motor is enabled
            if not self.enabled:
                err = "Motor must be enabled before moving."
                logger.error(err)
                raise MotorDisabled(err)

            logger.debug("Moving {} to {}".format(self.name, position))
            # Check if the move is valid
            self._check_value(position)

            # Begin the move process
            status = self.user_setpoint.set(position)
            return status

        except KeyboardInterrupt:
            self.stop()

    def _check_value(self, position):
        """
        Checks to make sure the inputted value is valid.

        Parameters
        ----------
        position : float
            Position to check for validity

        Raises
        ------
        ValueError
            If position is None, NaN or Inf
        LimitError
            If the position is outside the soft limits.
        """
        # Check for invalid positions
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))

        # Check if it is within the soft limits
        if not (self.low_limit <= position <= self.high_limit):
            err_str = "Requested value {0} outside of range: [{1}, {2}]"
            logger.warn(err_str.format(position, self.low_limit,
                                       self.high_limit))
            raise LimitError(err_str)

    def stop(self, *, success=False):
        """
        Stops the motor.

        Returns
        -------
        Status : StatusObject
            Status of the set.
        """
        status = self.motor_stop.set(1, wait=False)
        super().stop(success=success)
        return status
        
    def move_rel(self, rel_position, *args, **kwargs):
        """
        Move relative to the current position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        rel_position
            Relative position to move to

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
            Status object for the move.
        
        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`
        
        ValueError
            On invalid positions
        
        RuntimeError
            If motion fails other than timing out        
        """
        return self.move(rel_position + self.position, *args, **kwargs)

    def mv(self, position, *args, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete. Alias for move().

        Returns
        -------
        status : MoveStatus        
            Status object for the move.
        """
        return self.move(position, *args, **kwargs)

    def mvr(self, rel_position, *args, **kwargs):
        """
        Move relative to the current position, optionally waiting for motion to
        complete. Alias for move_rel().

        Returns
        -------
        status : MoveStatus        
            Status object for the move.
        """
        return self.move_rel(rel_position, *args, **kwargs)

    def wm(self):
        """
        Returns the current position of the motor.

        Returns
        -------
        position : float
            Current readback position of the motor.
        """
        return self.position    
    
    def expert_screen(self):
        """
        Launches the expert screen for the motor.
        """
        pv_spl = self.prefix.split(":")
        act = [s for s in pv_spl[::-1] if s.startswith("ACT")][0]
        p = ":".join(pv_spl[:pv_spl.index(act)])
        axis = act[3:]
        os.system("/reg/neh/operator/xcsopr/bin/snd/expert_screen.sh {0} {1}"
                  "".format(p, axis))

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

    def status(self, status="", offset=0, print_status=True, newline=False):
        """
        Returns the status of the device.
        
        Parameters
        ----------
        status : str, optional
            The string to append the status to.
            
        offset : int, optional
            Amount to offset each line of the status.

        print_status : bool, optional
            Determines whether the string is printed or returned.

        newline : bool, optional
            Adds a new line to the end of the string.

        Returns
        -------
        status : str
            Status string.
        """
        status += "{0}{1}\n".format(" "*offset, self.desc)
        status += "{0}PV: {1:>25}\n".format(" "*(offset+2), self.prefix)
        status += "{0}Enabled: {1:>20}\n".format(" "*(offset+2), 
                                                 str(self.enabled))
        status += "{0}Faulted: {1:>20}\n".format(" "*(offset+2), 
                                                 str(self.error))
        status += "{0}Position: {1:>19}\n".format(" "*(offset+2), 
                                                  np.round(self.wm(), 6))
        status += "{0}Limits: {1:>21}\n".format(
            " "*(offset+2), str((int(self.low_limit), int(self.high_limit))))
        if newline:
            status += "\n"
        if print_status is True:
            print(status)
        else:
            return status

    def __repr__(self):
        """
        Returns the status of the motor. Alias for status().

        Returns
        -------
        status : str
            Status string.
        """
        return self.status(print_status=False)


class TranslationEcc(EccBase):
    """
    Class for the translation ecc motor
    """
    pass


class GoniometerEcc(EccBase):
    """
    Class for the goniometer ecc motor
    """
    pass


class DiodeEcc(EccBase):
    """
    Class for the diode insertion ecc motor
    """
    pass


# Exceptions

class AttocubeException(Exception):
    """
    Base attocube motor exceptions.
    """
    pass


class MotorDisabled(AttocubeException):
    """
    Exception raised when an action requiring the motor be enabled is requested.
    """
    pass
