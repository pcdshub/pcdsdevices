import logging

from ophyd.utils import LimitError
from ophyd import EpicsMotor, Component, EpicsSignal, Signal


logger = logging.getLogger(__name__)


class EpicsMotor(EpicsMotor):
    """
    Epics motor for PCDS.
    """
    # Additional soft limit configurations
    low_soft_limit = Component(EpicsSignal, ".LLM")
    high_soft_limit = Component(EpicsSignal, ".HLM")
    # Disable missing field that our EPICS motor record lacks
    # This attribute is tracked by the _pos_changed callback
    direction_of_travel = Component(Signal)

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

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        # Store the internal travelling direction of the motor to account for
        # the fact that our EPICS motor does not have DIR field
        if None not in (value, self.position):
            self.direction_of_travel.put(int(value > self.position))
        # Pass information to PositionerBase
        super()._pos_changed(timestamp=timestamp, value=value, **kwargs)

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
