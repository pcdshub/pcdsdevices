#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import logging
from enum import Enum

###############
# Third Party #
###############
from ophyd import EpicsMotor
from ophyd.utils import LimitError

##########
# Module #
##########
from .device import Device
from .component import Component
from .signal import EpicsSignal

logger = logging.getLogger(__name__)


class DirectionEnum(Enum): 
    positive = 0
    pos = 0
    negative = 1
    neg = 1

class EpicsMotor(EpicsMotor, Device):
    """
    Epics motor for PCDS.
    """
    low_soft_limit = Component(EpicsSignal, ".LLM")
    high_soft_limit = Component(EpicsSignal, ".HLM")
    offset_val = Component(EpicsSignal, ".OFF")
    direction_enum = Component(EpicsSignal, ".DIR")

    @property
    def low_limit(self):
        """
        Returns the lower soft limit for the motor.

        Returns
        -------
        low_limit : float
            The lower soft limit of the motor.
        """
        return self.low_soft_limit.value 
    
    @low_limit.setter
    def low_limit(self, value):
        """
        Sets the low limit for the motor.

        Returns
        -------
        status : StatusObject
            Status object of the set.
        """
        return self.low_soft_limit.set(value)

    @property
    def high_limit(self):
        """
        Returns the higher soft limit for the motor.

        Returns
        -------
        high_limit : float
            The higher soft limit of the motor.
        """
        return self.high_soft_limit.value     

    @high_limit.setter
    def high_limit(self, value):
        """
        Sets the high limit for the motor.

        Returns
        -------
        status : StatusObject
            Status object of the set.
        """
        return self.high_soft_limit.set(value)

    @property
    def limits(self):
        """
        Returns the soft limits of the motor.

        Returns
        -------
        limits : tuple
            Soft limits of the motor.
        """
        return (self.low_limit, self.high_limit)
    
    @limits.setter
    def limits(self, limits):
        """
        Sets the limits for the motor.
        
        Parameters
        ----------
        limits : tuple
            Desired low and high limits.
        """
        self.low_limit = limits[0]
        self.high_limit = limits[1]

    def set_limits(self, llm, hlm):
        """
        Sets the limits of the motor. Alias for limits = (llm, hlm).
        
        Parameters
        ----------
        llm : float
            Desired low limit.
            
        hlm : float
            Desired low limit.
        """        
        self.limits = (llm, hlm)

    def check_value(self, value):
        """
        Check if the value is within the soft limits of the motor.

        Raises
        ------
        ValueError
        """
        # Check for control limits on the user_setpoint pv
        super().check_value(value)

        if value is None:
            raise ValueError('Cannot write None to epics PVs')

        low_limit, high_limit = self.limits
        
        if not (low_limit <= value <= high_limit):
            raise LimitError("Value {} outside of range: [{}, {}]"
                             .format(value, low_limit, high_limit))

    @property
    def direction(self):
        """
        Returns the current direction of the motor.
        """
        return DirectionEnum(self.direction_enum.value).name

    @direction.setter
    def direction(self, val):
        """
        Sets the direction of the motor

        Parameters
        ----------
        val : int, str
            The desired direction as an enum or string.
        """
        if isinstance(val, int):
            self.direction_enum.put(DirectionEnum(val).value)
        else:
            self.direction_enum.put(DirectionEnum[val.lower()].value)

    @property
    def offset(self):
        """
        Returns the current offset of the motor.
        
        Returns
        -------
        offset : float
            Current user off set of the motor.
        """
        return self.offset_val.value

    @offset.setter
    def offset(self, val):
        """
        Sets the offset of the motor.

        Parameters
        ----------
        val : float
            The desired offset.
        """
        self.offset_val.put(val)

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

 
