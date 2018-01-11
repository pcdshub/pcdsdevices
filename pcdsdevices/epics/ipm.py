from ophyd.status import wait as status_wait
from ophyd import Component

from ..state import StateRecordPositioner
from .inout import Diode


class IPM(StateRecordPositioner):
    """
    Standard intensity position monitor motion.
    """
    states_list = ['T1', 'T2', 'T3', 'T4', 'OUT']
    diode = Component(Diode, ":DIODE")

    transmission = 0.8  # Completely making up this number :)

    def target_in(self, target):
        """
        Move the target to one of the target positions

        Parameters
        ----------
        target, int
            Number of which target to move in. Must be one of 1, 2, 3, 4.
        """
        target = int(target)
        self.state.put(target)

    @property
    def inserted(self):
        """
        Report if the IPIMB is not OUT"
        """
        return self.position != "OUT"

    @property
    def removed(self):
        """
        Report if the IPM is inserted
        """
        return self.position == "OUT"

    def remove(self, *args, wait=False, **kwargs):
        """
        Remove the IPM by going to the `OUT` position

        Parameters
        ----------
        wait : bool, optional
            Wait for the status object to complete the move before returning

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        settle_time: float, optional
            Delay after the set() has completed to indicate completion to the
            caller

        Returns
        -------
        status : MoveStatus
            Status object of the move

        Notes
        -----
        Instantiated for `lightpath` compatability
        """
        # Set to out
        status = self.set("OUT", **kwargs)
        # Wait on status
        if wait:
            status_wait(status)
        return status

    def diode_in(self):
        """
        Move the diode to the in position.
        """
        self.diode.set("IN")

    def diode_out(self):
        """
        Move the diode to the out position.
        """
        self.diode.set("OUT")
