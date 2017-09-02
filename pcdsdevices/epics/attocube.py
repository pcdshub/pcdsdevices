#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Attocube devices
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


class EccBase(Device):
    """
    ECC Motor Class
    """
    # position
    user_readback = Component(EpicsSignalRO, ":POSITION")
    user_setpoint = Component(EpicsSignal, ":CMD:TARGET")

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
        # Make sure the motor is enabled
        if not self.enabled:
            err = "Motor must be enabled before moving."
            logger.error(err)
            raise MotorDisabled(err)

        logger.debug("Moving {} to {}".format(self.name, position))
        # Check if the move is valid
        self._check_value(position)

        # Begin the move process
        status = self.user_setpoint.put(position, wait=False)

        # Wait for the status object to register the move as complete
        if wait:
            logger.info("Waiting for {} to finish move ..."
                        "".format(self.name))
            status_wait(status)

        return status

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
        """
        # Check for invalid positions
        if position is None or np.isnan(position) or np.isinf(position):
            raise ValueError("Invalid value inputted: '{0}'".format(position))

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
