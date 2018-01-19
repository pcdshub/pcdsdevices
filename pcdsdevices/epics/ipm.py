from ophyd import Component

from ..inout import InOutRecordPositioner


class IPM(InOutRecordPositioner):
    """
    Standard intensity position monitor motion.
    """
    states_list = ['T1', 'T2', 'T3', 'T4', 'OUT']
    diode = Component(InOutRecordPositioner, ":DIODE")

    in_states = ['T1', 'T2', 'T3', 'T4']
    _transmission = {'T' + str(n): 0.8 for n in range(1, 5)}

    def target_in(self, target, moved_cb=None, timeout=None, wait=False):
        """
        Move the target to one of the target positions

        Parameters
        ----------
        target, int
            Number of which target to move in. Must be one of 1, 2, 3, 4.
        """
        target = int(target)
        self.move(target, moved_cb=moved_cb, timeout=timeout, wait=wait)

    def diode_in(self, moved_cb=None, timeout=None, wait=False):
        """
        Move the diode to the in position.
        """
        self.diode.insert(moved_cb=moved_cb, timeout=timeout, wait=wait)

    def diode_out(self, moved_cb=None, timeout=None, wait=False):
        """
        Move the diode to the out position.
        """
        self.diode.remove(moved_cb=moved_cb, timeout=timeout, wait=wait)
