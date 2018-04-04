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
