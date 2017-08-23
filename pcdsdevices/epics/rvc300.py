#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classes pertaining to the RVC300 gas valve regulation controllers
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
import numpy as np
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import raise_if_disconnected

##########
# Module #
##########
from .device import Device
from .component import Component
from .signal import (EpicsSignal, EpicsSignalRO)

logger = logging.getLogger(__name__)


class RVC300(Device):
    """
    Base RVC300 Class
    """
    # Configuration
    measurements = Component(EpicsSignal, ":UpdateHighRate.SCAN")
    configvars = Component(EpicsSignal, ":UpdateAll.SCAN")

    # Pressure Readback
    pressure = Component(EpicsSignalRO, ":GetActualValueRaw", auto_monitor=True)

    # System Control
    operating_mode = Component(EpicsSignal, ":GetOperatingMode",
                               write_pv=":SetOperatingMode")
    pressure_setpoint = Component(EpicsSignal, ":GetPressSetpointRaw",
                                  write_pv=":SetPressSetpointRaw")
    flow_setpoint = Component(EpicsSignal, ":GetFlowSetpoint",
                                  write_pv=":SetFlowSetpoint")
    close_valve = Component(EpicsSignal, ":CloseValve.PROC")

    # Valve Information
    valve_type = Component(EpicsSignalRO, ":GetValveType")
    valve_version = Component(EpicsSignalRO, ":GetValveVersion")
    valve_temperature = Component(EpicsSignalRO, ":GetEvr116Temp")
    valve_position = Component(EpicsSignalRO, ":GetEvr116Pos",
                               auto_monitor=True)
    valve_status = Component(EpicsSignalRO, ":GetEvr116Status")
    
    # PID
    controller_type = Component(EpicsSignal, ":SetControllerType")
    pcomp = Component(EpicsSignalRO, ":GetPComp")
    manipvar = Component(EpicsSignalRO, ":GetManipVar")
    icomp = Component(EpicsSignalRO, ":GetIComp")
    dcomp = Component(EpicsSignalRO, ":GetDComp")
    p_gain = Component(EpicsSignal, ":GetPGain")
    reset_time = Component(EpicsSignal, ":GetResetTime")
    derivative_time = Component(EpicsSignal, ":GetDerivativeTime")

    def __init__(self, prefix, *, read_attrs=None, configuration_attrs=None,
                 name=None, parent=None, valid_modes=None, **kwargs):
        if read_attrs is None:
            read_attrs = ["pressure", "operating_mode", "pressure_setpoint",
                          "flow_setpoint"]
        if configuration_attrs is None:
            configuration_attrs = ["pressure", "operating_mode",
                                   "pressure_setpoint", "flow_setpoint"]

        if valid_modes is None:
            self.valid_modes = ["WAIT", "PRESS", "FLOW"]
        
        super().__init__(prefix, read_attrs=read_attrs, parent=parent, 
                         configuration_attrs=configuration_attrs, name=name,
                         **kwargs)

    @raise_if_disconnected
    def move(self, value, mode=None, wait=True, **kwargs):
        """
        Changes the current setpoint of the controller to the inputted value.

        If the controller is currently in 'PRESS' mode, then the inputted value
        will be passed to the 'pressure_setpoint' component. If the controller
        is currently in "FLOW" mode, then the inputted value will be passed to
        the 'flow_setpoint' component. If the current mode is "WAIT" a warining
        is raised, and neither setpoints are changed.

        Parameters
        ----------
        value : int or float
            Value to change the set point to.

        mode : str or None, optional
        	If not None, move() changes the setpoint for the mode inputted.

        wait : bool, optional
            Wait for the status object to complete the move before returning.

        Returns
        -------
        status : MoveStatus
            Status object of the move.

        Raises
        ------
        ValueError
            On invalid setpoints or modes.

        RuntimeError
            If motion fails other than timing out.
        """
        # Begin the move process
        set_mode = mode or self.mode        
        self.check_values(value, mode=set_mode)

        # Pressure Mode
        if set_mode.upper() == "PRESS":
            logger.debug("Changing {0} pressure setpoint to {1}".format(
                self.name, value))
            status = self.pressure_setpoint.set(value)

        # Flow Mode
        elif set_mode.upper() == "FLOW":
            logger.debug("Changing {0} flow setpoint to {1}".format(
                self.name, value))
            status = self.flow_setpoint.set(value)

        # Wait Mode
        else:
            msg = "Cannot change setpoint for {0} - currently in 'WAIT' " \
                  "mode.".format(self.name)
            logger.warning(msg)
            return

        # Wait for the status object to register the move as complete
        if wait:
            logger.info("Waiting for {0} to reach setpoint...".format(
                self.name))
            status_wait(status)
        
        return status

    def mv(self, value, **kwargs):
        """
        Alias for the move() method.
        
        Returns
        -------
        status : MoveStatus
            Status object of the move.
        """
        return self.move(value, **kwargs)

    def set(self, value, **kwargs):
        """
        Alias for the move() method.
        
        Returns
        -------
        status : MoveStatus
            Status object of the move.
        """
        return self.move(value, **kwargs)

    @property
    def position(self, mode=None, **kwargs):
        """
        Returns the current pressure in the chamber.

        Returns
        -------
        pressure : float
        	Current pressure in the chamber.
        """
        return self.pressure.value

    def setpoint(self, mode=None, **kwargs):
        """
        Returns the setpoint of the current mode.

        If mode is not none, then it the setpoint for that mode is returned. If
        the current mode is 'WAIT' then a warning is raised.

        Returns
        -------
        setpoint : float
        	The setpoint of the current mode.

        Raises
        ------
        ValueError
        	If the inputted mode is invalid.
        """
        pos_mode = mode or self.mode
        check_mode(pos_mode)

        if pos_mode.upper() == "PRESS":
            return self.pressure_setpoint.value
        elif pos_mode.upper() == "FLOW":
            return self.flow_setpoint.value
        else:
            msg = "Mode is 'WAIT'. To get a position input a mode, to " \
                  "position, or change the operating mode."
            logger.warning(msg)
            return

    def check_mode(self, mode):
        """
        Checks to see if the inputted mode is one of the valid modes.

        Raises
        ------
        ValueError
        	If the inputted mode is not a valid mode.
        """
        if not isinstance(mode, str) or mode.upper() not in self.valid_modes:
            err = "Invlid mode '{0}' inputted. Must be in of '{1}'.".format(
                mode, self.valid_modes)
            logger.error(err)
            raise ValueError(err)

    def check_values(self, val, mode=None):
        """
        Checks to see if the inputted value is a valid setpoint. It will
        optionally check the inputted mode if it is not None.

        Raises
        ------
        ValueError
        	If the inputted value is invalid or the mode is not a valid mode.
        """
        # Handle non-numbers, nan, inf and bools
        if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val) \
           or val is True or val is False:
            err = "Invlid setpoint inputted '{0}'. Must be a number.".format(
                val)
            logger.error(err)
            raise ValueError(err)

        # Handle numbers less than 0
        elif val < 0:
            err = "Invlid setpoint inputted '{0}'. Value must be positive." \
                  "".format(val)
            logger.error(err)
            raise ValueError(err)
        
        # Check the mode
        if mode is not None:
            self.check_mode(mode)

    def close(self, **kwargs):
        """
        Closes the valve.
        """
        self.close_valve.put(1, **kwargs)

    def start_pid(self, **kwargs):
        """
        Sets the operating mode to PRESS.
        """
        self.mode = "PRESS"

    @property
    @raise_if_disconnected
    def p(self):
        """
        Pressure readback for the rvc300.

        Returns
        -------
        pressure : float
        	Current sensed pressure in the chamber.
        """
        return self.pressure.value        

    @property
    @raise_if_disconnected
    def mode(self):
        """
        Current operating mode of the controller.

        Returns
        -------
        mode : str
        	Current operating mode of the controller.
        """
        return self.operating_mode.value

    @mode.setter
    @raise_if_disconnected
    def mode(self, val):
        """
        Sets the current operating mode of the contoller.

        Raises
        ------
        ValueError
        	When the requested operating mode is not a valid mode.
        """
        # Handle bad inputs
        self.check_mode(val)
        self.operating_mode.put(val.upper())

    @property
    @raise_if_disconnected
    def kp(self):
        """
        Gain paramter for the PID.

        Returns
        -------
        kp : float
        	The current gain setting.
        """
        return self.p_gain.value

    @kp.setter
    @raise_if_disconnected
    def kp(self, val):
        """
        Sets the gain paramter.

        Raises
        ------
        ValueError
        	When the inputted gain is invalid.
        """
        # Handle bad inputs
        if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
            err = "Invlid kp inputted '{0}', must be a number.".format(val)
            logger.error(err)
            raise ValueError(err)
        
        self.p_gain.put(val)

    @property
    @raise_if_disconnected
    def tn(self):
        """
        Reset time paramter for the PID.

        Returns
        -------
        tn : float
        	The current reset time.
        """
        return self.reset_time.value

    @tn.setter
    @raise_if_disconnected
    def tn(self, val):
        """
        Sets the reset time paramter.

        Raises
        ------
        ValueError
        	When the inputted reset time is invalid.
        """
        # Handle bad inputs
        if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
            err = "Invlid tn inputted '{0}', must be a number.".format(val)
            logger.error(err)
            raise ValueError(err)
        
        self.reset_time.put(val)

    @property
    @raise_if_disconnected
    def tv(self):
        """
        Derivative time paramter for the PID.

        Returns
        -------
        tv : float
        	The current derivative time.
        """
        return self.derivative_time.value

    @tv.setter
    @raise_if_disconnected
    def tv(self, val):
        """
        Sets the derivative time paramter.

        Raises
        ------
        ValueError
        	When the inputted derivative time is invalid.
        """
        # Handle bad inputs
        if not isinstance(val, (int, float)) or np.isnan(val) or np.isinf(val):
            err = "Invlid tv inputted '{0}', must be a number.".format(val)
            logger.error(err)
            raise ValueError(err)
        
        self.derivative_time.put(val)
        
