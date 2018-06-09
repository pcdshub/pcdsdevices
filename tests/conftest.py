import time
import inspect

from ophyd.sim import FakeEpicsSignal


class HotfixFakeEpicsSignal(FakeEpicsSignal):
    """
    Extensions of FakeEpicsPV for ophyd=1.2.0 that should be submitted as a PR
    """
    def __init__(self, read_pv, write_pv=None, *, string=False, **kwargs):
        self.as_string = string
        super().__init__(read_pv, write_pv=write_pv, string=string, **kwargs)
        self._enum_strs = None

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

        Use sim_enum_strs during setup to set the enum strs.
        """
        return self._enum_strs

    def sim_enum_strs(self, enums):
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


def get_classes_in_module(module, subcls=None):
    classes = []
    all_classes = inspect.getmembers(module)
    for _, cls in all_classes:
        try:
            if cls.__module__ == module.__name__:
                if subcls is not None:
                    try:
                        if not issubclass(cls, subcls):
                            continue
                    except TypeError:
                        continue
                classes.append(cls)
        except AttributeError:
            pass
    return classes


def connect_rw_pvs(epics_signal):
    """
    Modify an epics signal using fake epics pvs such that writing to the
    write_pv changes the read_pv
    """
    def make_put(original_put, read_pv):
        def put(*args, **kwargs):
            original_put(*args, **kwargs)
            read_pv.put(*args, **kwargs)
        return put
    write_pv = epics_signal._write_pv
    read_pv = epics_signal._read_pv
    write_pv.put = make_put(write_pv.put, read_pv)


def func_wait_true(func, timeout=1, step=0.1):
    """
    For things that don't happen immediately but don't have a good way to wait
    for them. Does a simple timeout loop, returning after timeout or when
    func() is True.
    """
    while not func() and timeout > 0:
        timeout -= step
        time.sleep(step)


def attr_wait_true(obj, attr, timeout=1, step=0.1):
    func_wait_true(lambda: getattr(obj, attr), timeout=timeout, step=step)


def attr_wait_false(obj, attr, timeout=1, step=0.1):
    func_wait_true(lambda: not getattr(obj, attr), timeout=timeout, step=step)


def attr_wait_value(obj, attr, value, delta=0.01, timeout=1, step=0.1):
    func_wait_true(lambda: abs(getattr(obj, attr) - value) < delta,
                   timeout=timeout, step=step)
