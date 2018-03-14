"""
Module for defining bell-and-whistles movement features
"""
from bluesky.utils import ProgressBar
from ophyd.status import wait as status_wait


class MvInterface:
    """
    Interface layer to attach to a positioner for motion shortcuts.

    Defines common shortcuts that the beamline scientists like for moving
    things on the command line. There is no need for these in a scripting
    environnment, but this is a safe space for implementing move features that
    would otherwise be disruptive to running scans and writing higher-level
    applications.
    """
    def mv(self, position, timeout=None, wait=False):
        """
        Absolute move to a position.

        Parameters
        ----------
        position
            Desired end position

        timeout: ``float``, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.

        wait: ``bool``, optional
            If ``True``, wait for motion completion before returning.
            Defaults to ``False``.
        """
        self.move(position, timeout=timeout, wait=wait)

    def wm(self):
        """
        Get the mover's positon (where motor)

        Returns
        -------
        position
            Current position
        """
        return self.position

    def __call__(self, position=None, timeout=None, wait=False):
        """
        Calling the object will either move the object or get the current
        position, depending on if the position argument is given. See the
        docstrings for `mv` and `wm`.
        """
        if position is None:
            return self.wm()
        else:
            self.mv(position, timeout=timeout, wait=wait)


class FltMvInterface(MvInterface):
    """
    Extension of MvInterface for when the position is a float.

    This lets us do more with the interface, such as relative moves.
    """
    def mvr(self, delta, timeout=None, wait=False):
        """
        Relative move from this position.

        Parameters
        ----------
        delta: float
            Desired change in position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.

        wait: bool, optional
            If True, wait for motion completion before returning. Defaults to
            False.
        """
        self.mv(delta + self.wm(), timeout=timeout, wait=wait)

    def umv(self, position, timeout=None):
        """
        Move to a position, wait, and update with a progress bar.

        Parameters
        ----------
        position: float
            Desired end position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.
        """
        status = self.move(position, timeout=timeout, wait=False)
        ProgressBar([status])
        try:
            status_wait(status)
        except KeyboardInterrupt:
            self.stop()

    def umvr(self, delta, timeout=None):
        """
        Relative move from this position, wait, and update with a progress bar.

        Parameters
        ----------
        delta: float
            Desired change in position

        timeout: number, optional
            If provided, the mover will throw an error if motion takes longer
            than timeout to complete. If omitted, the mover's default timeout
            will be use.
        """
        self.umv(delta + self.wm(), timeout=timeout)
