from enum import Enum

from ..state import StatePositioner


class InOutPositioner(StatePositioner):
    _states_enum = Enum('InOutState', 'IN OUT')

    @property
    def inserted(self):
        return self.position == 'IN'

    @property
    def removed(self):
        return self.position == 'OUT'

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        return self.move('OUT', moved_cb=finished_cb, timeout=timeout,
                         wait=wait, **kwargs)


class Diode(InOutPositioner):
    pass


class Reflaser(InOutPositioner):
    """
    Mirror that is inserted into the beam to point a reference laser along the
    beam path.
    """
    pass


class TTReflaser(Reflaser):
    """
    Motor stack that includes both a timetool and a reflaser.
    """
    _states_enum = Enum('TTStates', 'TT REFL OUT')

    @property
    def inserted(self):
        return self.state.position in ('TT', 'REFL')
