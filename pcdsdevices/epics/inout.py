from ..state import StateRecordPositioner


class InOutPositioner(StateRecordPositioner):
    states_list = ['IN', 'OUT']

    @property
    def inserted(self):
        return self.position == 'IN'

    @property
    def removed(self):
        return self.position == 'OUT'

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        return self.move('OUT', moved_cb=finished_cb, timeout=timeout,
                         wait=wait, **kwargs)


class TTReflaser(InOutPositioner):
    """
    Motor stack that includes both a timetool and a reflaser.
    """
    states_list = ['TT', 'REFL', 'OUT']

    @property
    def inserted(self):
        return self.state.position in ('TT', 'REFL')
