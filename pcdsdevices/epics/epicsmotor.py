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
    llm = Component(EpicsSignal, ".LLM")
    hlm = Component(EpicsSignal, ".HLM")
    offset_val = Component(EpicsSignal, ".OFF")
    direction_enum = Component(EpicsSignal, ".DIR")
    zero_all_proc = Component(EpicsSignal, ".ZERO_P.PROC")

    @EpicsMotor.low_limit.setter
    def low_limit(self, value):
        """
        Sets the low limit for the motor.

        Returns
        -------
        status : StatusObject
            Status object of the set.
        """
        return self.llm.set(value)

    @EpicsMotor.high_limit.setter
    def low_limit(self, value):
        """
        Sets the low limit for the motor.

        Returns
        -------
        status : StatusObject
            Status object of the set.
        """
        return self.hlm.set(value)

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

    def zero_all(self):
        """
        Sets the current position to be the zero position of the motor.

        Returns
        -------
        status : StatusObject        
            Status object for the set.
        """
        self.zero_all_proc.set(1)
