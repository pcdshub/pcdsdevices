#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Aerotech devices
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

##########
# Module #
##########
from .epicsmotor import EpicsMotor
from .component import Component
from .signal import (EpicsSignal, EpicsSignalRO, FakeSignal)

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
    # Remove when these have been figured out
    low_limit_switch = Component(FakeSignal)
    high_limit_switch = Component(FakeSignal)
    direction_of_travel = Component(FakeSignal)

    power = Component(EpicsSignal, ".CNEN")
    retries = Component(EpicsSignalRO, ".RCNT")
    retries_max = Component(EpicsSignal, ".RTRY")
    retries_deadband = Component(EpicsSignal, ".RDBD")
    axis_fault = Component(EpicsSignalRO, ":AXIS_FAULT")
    axis_status = Component(EpicsSignalRO, ":AXIS_STATUS")
    clear_error = Component(EpicsSignal, ":CLEAR")
    config = Component(EpicsSignal, ":CONFIG")
    zero_all_proc = Component(EpicsSignal, ".ZERO_P.PROC")
    home_forward = Component(EpicsSignal, ".HOMF")
    home_reverse = Component(EpicsSignal, ".HOMR")

    def __init__(self, prefix, desc=None, *args, **kwargs):
        self.desc=desc
        super().__init__(prefix, *args, **kwargs)
        self.configuration_attrs.append("power")
        if desc is None:
            self.desc = self.name

    def homf(self):
        """
        Home the motor forward.
        
        Returns
        -------
        Status : StatusObject
            Status of the set.
        """
        return self.home_forward.set(1)

    def homr(self):
        """
        Home the motor in reverse.
        
        Returns
        -------
        Status : StatusObject
            Status of the set.
        """
        return self.home_reverse.set(1)

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
        try:
            if not self.enabled:
                err = "Motor must be enabled before moving."
                logger.error(err)
                raise MotorDisabled(err)
            return super().move(position, *args, **kwargs)
        except KeyboardInterrupt:
            self.stop()

    def set_position(self, position_des):
        """
        Sets the current position to be the inputted position by changing the 
        offset.
        
        Parameters
        ----------
        position_des : float
            The desired current position.
        """
        logger.info("Previous position: {0}, offset: {1}".format(
            self.position, self.offset))
        self.offset += position_des - self.position
        logger.info("New position: {0}, offset: {1}".format(
            self.position, self.offset))

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
        return self.config.set(1)

    @property
    def faulted(self):
        """
        Returns the current fault with the motor.
        
        Returns
        -------
        faulted
            Fault enumeration.
        """
        return bool(self.axis_fault.value)
    
    def zero_all(self):
        """
        Sets the current position to be the zero position of the motor.

        Returns
        -------
        status : StatusObject        
            Status object for the set.
        """
        self.zero_all_proc.set(1)

    def expert_screen(self):
        """
        Launches the expert screen for the motor.
        """
        os.system("/reg/neh/operator/xcsopr/bin/snd/expert_screen.sh {0}"
                  "".format(self.prefix))
        
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
                                                 str(self.faulted))
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
