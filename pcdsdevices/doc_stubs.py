basic_positioner_init = """

    Parameters
    ----------
    prefix: ``str``
        The EPICS PV prefix for this motor.

    name: ``str``, required keyword
        An identifying name for this motor.

    settle_time: ``float``, optional
        The amount of extra time to wait before interpreting a move as done

    timeout ``float``, optional
        The amount of time to wait before automatically marking a long
        in-progress move as failed.

"""

insert_remove = """

        Parameters
        ----------
        moved_cb: ``callable``, optional
            Call this callback when movement is finished. This callback must
            accept one keyword argument, ``obj``, which will be set to this
            instance.

        timeout: ``float``, optional
            Maximum time to wait for the motion.

        wait: ``bool``, optional
            If ``True``, do not continue until the move is complete.

        Returns
        -------
        moved_status: ``Status``
            ``Status`` that will be marked as done when the motion is complete.

"""

PIM_base = """
    Profile intensity monitor

    Parameters
    ----------
    prefix : str
        The EPICS base of the motor

    name : str
        A name to refer to the device

    prefix_det : str
        The EPICS base PV of the detector

    prefix_zoom : str
        The EPICS base PV of the zoom motor
    """

IonPump_base = """
    Ion Pump

    Parameters
    ----------
    prefix : ``str``
        Ion Pump PV

    name : ``str``
        Alias for the ion pump
    """

GaugeSet_base = """
    Class for a Gauge Set

    Parameters
    ----------
    prefix : ``str``
        Gauge base PV (up to GCC/GPI)

    name : ``str``
        Alias for the gauge set

    index : ``str`` or ``int``
        Index for gauge (e.g. '02' or 3)
    """
