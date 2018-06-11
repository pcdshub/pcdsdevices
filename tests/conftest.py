from ophyd.areadetector.base import EpicsSignalWithRBV
from ophyd.sim import FakeEpicsSignal, fake_device_cache


class HotfixFakeEpicsSignal(FakeEpicsSignal):
    """
    Extensions of FakeEpicsPV for ophyd=1.2.0 that should be submitted as a PR
    """
    def __init__(self, read_pv, write_pv=None, *, string=False, **kwargs):
        self.as_string = string
        self._enum_strs = None
        super().__init__(read_pv, write_pv=write_pv, string=string, **kwargs)
        self._limits = None

    def get(self, *, as_string=None, connection_timeout=1.0, **kwargs):
        """
        Implement getting as enum strings
        """
        if as_string is None:
            as_string = self.as_string

        value = super().get()

        if as_string:
            if self.enum_strs is not None and isinstance(value, int):
                return self.enum_strs[value]
            elif value is not None:
                return str(value)
        return value

    def put(self, value, *args, **kwargs):
        """
        Implement putting as enum strings
        """
        if self.enum_strs is not None and value in self.enum_strs:
            value = self.enum_strs.index(value)
        super().put(value, *args, **kwargs)

    @property
    def enum_strs(self):
        """
        Simulated enum strings.

        Use sim_set_enum_strs during setup to set the enum strs.
        """
        return self._enum_strs

    def sim_set_enum_strs(self, enums):
        """
        Set the enum_strs for a fake devices

        Parameters
        ----------
        enums: list or tuple of str
            The enums will be accessed by array index, e.g. the first item in
            enums will be 0, the next will be 1, etc.
        """
        self._enum_strs = enums

    def check_value(self, value):
        """
        Implement some of the checks from epicsSignal
        """
        super().check_value(value)
        if value is None:
            raise ValueError('Cannot write None to epics PVs')


fake_device_cache[EpicsSignalWithRBV] = HotfixFakeEpicsSignal
