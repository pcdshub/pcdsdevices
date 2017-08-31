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

##########
# Module #
##########
from .epicsmotor import EpicsMotor
from .component import Component
from .signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)


class AeroBase(EpicsMotor):
    """
    Base Aerotech motor class.

    Components
    ----------
    power : EpicsSignal, ".CNEN"
    	Enables or disables power to the axis.

    retries : EpicsSignalRO, ".RCNT"
    	Number of retries attempted.

    retries_max : EpicsSignal, ".RTRY"
    	Maximum number of retries.

    retries_deadband : EpicsSignal, ".RDBD"
    	Tolerance of each retry.

    axis_fault : EpicsSignalRO, ":AXIS_FAULT"
    	Fault readback for the motor.

    axis_status : EpicsSignalRO, ":AXIS_STATUS"
    	Status readback for the motor.

    clear_error : EpicsSignal, ":CLEAR"
    	Clear error signal.

    config : EpicsSignal, ":CONFIG"
    	Signal to reconfig the motor.
    """
    power = Component(EpicsSignal, ".CNEN")
    retries = Component(EpicsSignalRO, ".RCNT")
    retries_max = Component(EpicsSignal, ".RTRY")
    retries_deadband = Component(EpicsSignal, ".RDBD")
    axis_fault = Component(EpicsSignalRO, ":AXIS_FAULT")
    axis_status = Component(EpicsSignalRO, ":AXIS_STATUS")
    clear_error = Component(EpicsSignal, ":CLEAR")
    config = Component(EpicsSignal, ":CONFIG")

    def __init__(self, prefix, *args, **kwargs):
        super().__init__(prefix, *args, **kwargs)
        self.configuration_attrs.append("power")

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
        return super().move(position, *args, **kwargs)

    def moverel(rel_position, *args, **kwargs):
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

    def enable(self):
        """
        Enables the motor power.

        Returns
        -------
        Status
        	The status object for setting the power signal.
        """
        return self.power.set(1)

    def disable(self):
        """
        Disables the motor power.

        Returns
        -------
        Status
        	The status object for setting the power signal.
        """
        return self.power.set(0)

    @property
    def enabled(self):
        """
        Returns if the motor is curently enabled.

        Returns
        -------
        enabled : bool
        	True if the motor is powered, False if not.
        """
        return bool(self.power.value)

    def clear(self):
        """
        Clears the motor error.

        Returns
        -------
        Status
        	The status object for setting the clear_error signal.
        """
        return self.clear_error.set(1)

    def reconfig(self):
        """
        Re-configures the motor.

        Returns
        -------
        Status
        	The status object for setting the config signal.
        """
        return self.reconfig.set(1)

    @property
    def fault(self):
        """
        Returns the current fault with the motor.
        
        Returns
        -------
        fault
        	Fault enumeration.
        """
        return self.axis_fault.value

    @property
    def status(self):
        """
        Returns the current status of the motor.
        
        Returns
        -------
        status
        	Status enumeration.
        """
        return self.axis_status.value
    
    
class RotationAero(AeroBase):
    """
    Class for the aerotech rotation stage.
    """
    pass


class LinearAero(AeroBase):
    """
    Class for the aerotech linear stage.
    """
    pass

    
class DiodeAero(AeroBase):
    """
    VT50 Micronix Motor of the diodes
    """
    pass


# Exceptions

class AerotechException(Exception):
    """
    Base aerotech motor exceptions.
    """
    pass


class MotorDisabled(AerotechException):
    """
    Exception raised when an action requiring the motor be enabled is requested.
    """
    pass
