basic_positioner_init = """

    Parameters
    ----------
    prefix : str
        The EPICS PV prefix for this motor.

    name : str
        An identifying name for this motor.

    settle_time : float, optional
        The amount of extra time to wait before interpreting a move as done.

    timeout : float, optional
        The amount of time to wait before automatically marking a long
        in-progress move as failed.

"""

insert_remove = """

        Parameters
        ----------
        moved_cb : callable, optional
            Call this callback when movement is finished. This callback must
            accept one keyword argument, ``obj``, which will be set to this
            instance.

        timeout : float, optional
            Maximum time to wait for the motion.

        wait : bool, optional
            If `True`, do not continue until the move is complete.

        Returns
        -------
        moved_status : :class:`~ophyd.status.Status`
            Status that will be marked as done when the motion is complete.

"""

IonPump_base = """
    Ion Pump.

    Parameters
    ----------
    prefix : str
        EPICS base PV for the ion pump.

    name : str
        Name to refer to the ion pump.
    """

GaugeSet_base = """
    Class for a Gauge Set.

    Parameters
    ----------
    prefix : str
        Gauge base PV (up to GCC/GPI).

    name : str
        Alias for the gauge set.

    index : str or int
        Index for gauge (e.g. '02' or 3).
    """

IPM_base = """
    Standard intensity position monitor.

    This is an `InOutRecordPositioner` that moves
    the target position to any of the four set positions, or out. Valid states
    are (1, 2, 3, 4, 5) or the equivalent
    (TARGET1, TARGET2, TARGET3, TARGET4, OUT).
    IPMs each also have a diode, which is implemented as the diode attribute of
    this class. This can easily be controlled using ``ipm.diode.insert()`` or
    ``ipm.diode.remove()``.
    """
