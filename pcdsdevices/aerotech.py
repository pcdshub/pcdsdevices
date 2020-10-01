"""
Aerotech devices.
"""
import logging

import numpy as np
from ophyd import Component as Cpt
from ophyd.signal import EpicsSignal, EpicsSignalRO, Signal
from ophyd.utils import LimitError

from .epics_motor import EpicsMotorInterface, MotorDisabledError
from .utils import stop_on_keyboardinterrupt

logger = logging.getLogger(__name__)


class AerotechMotorError(Exception):
    """
    Exception raised when an action requiring the motor not have an error is
    requested.
    """
    pass


class AerotechMotorFaulted(AerotechMotorError):
    """
    Exception raised when an action requiring the motor not be faulted is
    requested.
    """
    pass


class AerotechMotorStopped(AerotechMotorError):
    """
    Exception raised when an action requiring the motor to not be stopped is
    requested.
    """
    pass


class AerotechMotor(EpicsMotorInterface):
    """
    Aerotech motor class.

    Attributes
    ----------
    power : EpicsSignal
        Enables or disables power to the axis.

    retries : EpicsSignalRO
        Number of retries attempted.

    retries_max : EpicsSignal
        Maximum number of retries.

    retries_deadband : EpicsSignal
        Tolerance of each retry.

    axis_fault : EpicsSignalRO
        Fault readback for the motor.

    axis_status : EpicsSignalRO
        Status readback for the motor.

    clear_error : EpicsSignal
        Clear error signal.

    config : EpicsSignal
        Signal to reconfig the motor.
    """
    # TODO: Remove when these have been figured out
    low_limit_switch = Cpt(Signal)
    high_limit_switch = Cpt(Signal)

    power = Cpt(EpicsSignal, ".CNEN")
    retries = Cpt(EpicsSignalRO, ".RCNT")
    retries_max = Cpt(EpicsSignal, ".RTRY")
    retries_deadband = Cpt(EpicsSignal, ".RDBD")
    axis_status = Cpt(EpicsSignalRO, ":AXIS_STATUS")
    axis_fault = Cpt(EpicsSignalRO, ":AXIS_FAULT")
    clear_error = Cpt(EpicsSignal, ":CLEAR")
    config = Cpt(EpicsSignal, ":CONFIG")
    zero_all_proc = Cpt(EpicsSignal, ":ZERO_P.PROC")
    home_forward = Cpt(EpicsSignal, ".HOMF")
    home_reverse = Cpt(EpicsSignal, ".HOMR")
    dial = Cpt(EpicsSignalRO, ".DRBV")
    state_component = Cpt(EpicsSignal, ".SPMG")

    def __init__(self, prefix, *args, name=None, **kwargs):
        super().__init__(prefix, *args, name=name, **kwargs)
        self.motor_done_move.unsubscribe(self._move_changed)
        self.user_readback.unsubscribe(self._pos_changed)
        self.configuration_attrs.append("power")
        self._state_list = ["Stop", "Pause", "Move", "Go"]

    def _status_print(self, status, msg=None, ret_status=False, print_set=True,
                      timeout=None, wait=True, reraise=False):
        """
        Internal method that optionally returns the status object and
        optionally prints a message about the set. If a message is passed but
        print_set is False then the message is logged at the debug level.

        Parameters
        ----------
        status : StatusObject or list
            The inputted status object.

        msg : str or None, optional
            Message to print if print_set is True.

        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        wait : bool, optional
            Wait for the status to complete.

        reraise : bool, optional
            Raise the RuntimeError in the except.

        Returns
        -------
        Status
            Inputted status object.
        """
        try:
            # Wait for the status to complete
            if wait:
                status.wait(timeout)

            # Notify the user
            if msg is not None:
                if print_set:
                    logger.info(msg)
                else:
                    logger.debug(msg)
            if ret_status:
                return status

        # The operation failed for some reason
        except RuntimeError:
            error = "Operation completed, but reported an error."
            logger.error(error)
            if reraise:
                raise

    @stop_on_keyboardinterrupt
    def homf(self, ret_status=False, print_set=True, check_status=True):
        """
        Home the motor forward.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        check_status : bool, optional
            Check if the motors are in a valid state to move.

        Returns
        -------
        Status : StatusObject
            Status of the set.
        """
        # Check the motor status
        if check_status:
            self.check_status()
        status = self.home_forward.set(1, timeout=self.set_timeout)
        return self._status_print(status, f"Homing '{self.name}' forward.",
                                  print_set=print_set, ret_status=ret_status)

    @stop_on_keyboardinterrupt
    def homr(self, ret_status=False, print_set=True, check_status=True):
        """
        Home the motor in reverse.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        check_status : bool, optional
            Check if the motors are in a valid state to move.

        Returns
        -------
        Status : StatusObject
            Status of the set.
        """
        # Check the motor status
        if check_status:
            self.check_status()
        status = self.home_reverse.set(1, timeout=self.set_timeout)
        return self._status_print(
            status, f"Homing '{self.name}' in reverse.",
            print_set=print_set, ret_status=ret_status)

    def move(self, position, *args, wait=False, check_status=True,
             timeout=None, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Position to move to.

        wait : bool, optional
            Wait for the motor to complete the motion.

        check_status : bool, optional
            Check if the motors are in a valid state to move.

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
        # Check the motor status
        if check_status:
            self.check_status(position)
        logger.debug(f"Moving {self.name} to {position}")
        return super().move(position, wait=wait, timeout=timeout, *args,
                            **kwargs)

    def mv(self, position, *args, wait=True, print_move=True, **kwargs):
        """
        Move to a specified position, optionally waiting for motion to
        complete. mv() is different from move() by catching all the common
        exceptions that this motor can raise and just raises a logger
        warning. Therefore if building higher level functionality, do not
        use this method and use move() instead otherwise none of these
        exceptions will propagate to it.

        Parameters
        ----------
        position
            Position to move to.

        wait : bool, optional
            Wait for the motor to complete the motion.

        check_status : bool, optional
            Check if the motors are in a valid state to move.

        print_move : bool, optional
            Print a short statement about the move.

        Exceptions Caught
        -----------------
        LimitError
            Error raised when the inputted position is beyond the soft limits.

        MotorDisabledError
            Error raised if the motor is disabled and move is requested.

        MotorFaulted
            Error raised if the motor is disabled and the move is requested.

        MotorStopped
            Error raised if the motor is stopped and the move is requested.

        Returns
        -------
        status : MoveStatus
            Status object for the move.
        """
        try:
            status = self.move(position, *args, wait=wait, **kwargs)

            # Notify the user that a motor has completed or the command is sent
            if print_move:
                if wait:
                    logger.info("Move completed for '%s'.", self.name)
                else:
                    logger.info("Move command sent to '%s'", self.name)
            return status

        # Catch all the common motor exceptions
        except LimitError:
            logger.warning("Requested move '%s' is outside the soft limits "
                           "%s for motor %s", position, self.limits, self.name)
        except MotorDisabledError:
            logger.warning("Cannot move - motor %s is currently disabled. Try "
                           "running 'motor.enable()'.", self.name)
        except AerotechMotorFaulted:
            logger.warning("Cannot move - motor %s is currently faulted. Try "
                           "running 'motor.clear()'.", self.name)
        except AerotechMotorStopped:
            logger.warning("Cannot move - motor %s is currently stopped. Try "
                           "running 'motor.state=\"Go\"'.", self.name)

    def check_status(self, position=None):
        """
        Checks the status of the motor to make sure it is ready to move. Checks
        the current position of the motor, and if a position is provided it
        also checks that position.

        Parameters
        ----------
        position : float, optional
            Position to check for validity.

        Raises
        ------
        MotorDisabledError
            If the motor is disabled.

        MotorFaulted
            If the motor is faulted.

        MotorStopped
            If the motor is stopped.
        """
        if not self.enabled:
            err = f"Motor '{self.name}' is currently disabled"
            logger.error(err)
            raise MotorDisabledError(err)

        if self.faulted:
            err = f"Motor '{self.name}' is currently faulted."
            logger.error(err)
            raise AerotechMotorFaulted(err)

        if self.state == "Stop":
            err = f"Motor '{self.name}' is currently stopped."
            logger.error(err)
            raise AerotechMotorStopped(err)

        # Check if the current position is valid
        self.check_value(self.position)
        # Check if the move position is valid
        if position:
            self.check_value(position)

    def set_position(self, position_des, print_set=True):
        """
        Sets the current position to be the inputted position by changing the
        offset.

        Parameters
        ----------
        position_des : float
            The desired current position.
        """
        # Print to console or just to the log
        if print_set:
            log_level = logger.info
        else:
            log_level = logger.debug

        log_level("'%s' previous position: %s, offset: %s", self.position,
                  self.offset)
        self.offset += position_des - self.position
        log_level("'%s' New position: %s, offset: %s", self.position,
                  self.offset)

    def enable(self, ret_status=False, print_set=True):
        """
        Enables the motor power.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the power signal.
        """
        status = self.power.set(1, timeout=self.set_timeout)
        return self._status_print(status, f"Enabled motor '{self.name}'.",
                                  print_set=print_set, ret_status=ret_status)

    def disable(self, ret_status=False, print_set=True):
        """
        Disables the motor power.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the power signal.
        """
        status = self.power.set(0, timeout=self.set_timeout)
        return self._status_print(status, f"Disabled motor '{self.name}'.",
                                  print_set=print_set, ret_status=ret_status)

    @property
    def enabled(self):
        """
        Returns if the motor is curently enabled.

        Returns
        -------
        enabled : bool
            True if the motor is powered, False if not.
        """
        return bool(self.power.get())

    def clear(self, ret_status=False, print_set=True):
        """
        Clears the motor error.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the clear_error signal.
        """
        status = self.clear_error.set(1, timeout=self.set_timeout)
        return self._status_print(status, f"Cleared motor '{self.name}'.",
                                  print_set=print_set, ret_status=ret_status)

    def reconfig(self, ret_status=False, print_set=True):
        """
        Re-configures the motor.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the config signal.
        """
        status = self.config.set(1, timeout=self.set_timeout)
        return self._status_print(status, f"Reconfigured motor '{self.name}'.",
                                  print_set=print_set, ret_status=ret_status)

    @property
    def faulted(self):
        """
        Returns the current fault with the motor.

        Returns
        -------
        faulted
            Fault enumeration.
        """
        if self.axis_fault.connected:
            return bool(self.axis_fault.get())

    def zero_all(self, ret_status=False, print_set=True):
        """
        Sets the current position to be the zero position of the motor.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        status : StatusObject
            Status object for the set.
        """
        status = self.zero_all_proc.set(1, timeout=self.set_timeout)
        return self._status_print(status, f"Zeroed motor '{self.name}'.",
                                  print_set=print_set, ret_status=ret_status)

    @property
    def state(self):
        """
        Returns the state of the motor. State can be one of the following:
            'Stop', 'Pause', 'Move', 'Go'

        Returns
        -------
        state : str
            The current state of the motor
        """
        return self._state_list[self.state_component.get()]

    @state.setter
    def state(self, val, ret_status=False, print_set=True):
        """
        Sets the state of the motor. Inputted state can be one of the following
        states or the index of the desired state:
            'Stop', 'Pause', 'Move', 'Go'
        Alias for set_state((val, False, True)

        Parameters
        ----------
        val : int or str

        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the state signal.
        """
        try:
            return self.set_state(val, ret_status, print_set)
        except ValueError:
            logger.info("State must be one of the following: %s",
                        self._state_list)

    def set_state(self, state, ret_status=True, print_set=False):
        """
        Sets the state of the motor. Inputted state can be one of the following
        states or the index of the desired state:
            'Stop', 'Pause', 'Move', 'Go'

        Parameters
        ----------
        val : int or str

        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for setting the state signal.
        """
        # Make sure it is in title case if it's a string
        val = state
        if isinstance(state, str):
            val = state.title()

        # Make sure it is a valid state or enum
        if val not in self._state_list + list(range(len(self._state_list))):
            error = f"Invalid state inputted: '{val}'."
            logger.error(error)
            raise ValueError(error)

        # Lets enforce it's a string or value
        status = self.state_component.set(val, timeout=self.set_timeout)

        return self._status_print(
            status, f"Changed state of '{self.name} to '{val}'.",
            print_set=print_set, ret_status=ret_status)

    def ready_motor(self, ret_status=False, print_set=True):
        """
        Sets the motor to the ready state by clearing any errors, enabling it,
        and setting the state to be 'Go'.

        Parameters
        ----------
        ret_status : bool, optional
            Return the status object of the set.

        print_set : bool, optional
            Print a short statement about the set.

        Returns
        -------
        Status
            The status object for all the sets.
        """
        status = [self.clear(ret_status=True, print_set=False)]
        status.append(self.enable(ret_status=True, print_set=False))
        status.append(self.set_state("Go", ret_status=True, print_set=False))
        return self._status_print(
            status, f"Motor '{self.name}' is now ready to move.",
            print_set=print_set, ret_status=ret_status
        )

    # def expert_screen(self, print_msg=True):
    #     """
    #     Launches the expert screen for the motor.
    #
    #     Parameters
    #     ----------
    #     print_msg : bool, optional
    #         Prints that the screen is being launched.
    #     """
    #     path = absolute_submodule_path(
    #         "hxrsnd/screens/motor_expert_screens.sh")
    #     if print_msg:
    #         logger.info("Launching expert screen.")
    #     os.system(f"{path} {self.prefix} aerotech &")

    def status(self, status="", offset=0, print_status=True, newline=False,
               short=False):
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
        prefix = ' ' * offset
        indent = ' ' * (offset + 2)
        if short:
            dial = self.dial.get()
            status += (
                f"\n{prefix}"
                f"{self.name:<16}|"
                f"{self.position:^16.3f}|"
                f"{dial:^16.3f}"
            )
        else:
            position = np.round(self.wm(), 6)
            dial = np.round(self.dial.get(), 6)
            limits = (int(self.low_limit), int(self.high_limit))
            status += f"""
                {prefix}{self.name}
                {indent}PV: {self.prefix:>25}
                {indent}Enabled: {self.enabled:>20}
                {indent}Faulted: {self.faulted:>20}
                {indent}State: {self.state:>22}
                {indent}Position: {position:>19}
                {indent}Dial: {dial:>23}
                {indent}Limits: {str(limits):>21}"""

        if newline:
            status += "\n"

        if print_status:
            logger.info(status)
        else:
            return status
