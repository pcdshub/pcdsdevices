import copy
import logging

from ophyd.device import (Device, Component as Cpt,
                          DynamicDeviceComponent as DDCpt)
from ophyd.signal import Signal, EpicsSignal, EpicsSignalRO
from ophyd.utils import ReadOnlyError, LimitError

logger = logging.getLogger(__name__)


def make_fake_class(cls):
    """
    Inspect cls and construct a fake class that has the same structure.

    This works by replacing EpicsSignal with FakeEpicsSignal and EpicsSignalRO
    with FakeEpicsSignalRO. The fake class will be a subclass of the real
    class.

    This assumes that EPICS connections are done entirely in EpicsSignal and
    EpicsSignalRO subcomponents. If this is not true, this will fail silently
    until the test.

    Parameters
    ----------
    cls: `ophyd.Device`

    Returns
    -------
    fake_class: `ophyd.Device`
    """
    # Cache to avoid repeating work.
    # EpicsSignal and EpicsSignalRO begin in the cache.
    if cls not in fake_class_cache:
        if not issubclass(cls, Device):
            # Ignore non-devices and non-epics-signals
            logger.debug('Ignore cls=%s, bases are %s', cls, cls.__bases__)
            fake_class_cache[cls] = cls
            return cls
        fake_dict = {}
        # Update all the components recursively
        for cpt_name in cls.component_names:
            cpt = getattr(cls, cpt_name)
            fake_cpt = copy.copy(cpt)
            if isinstance(cpt, Cpt):
                fake_cpt.cls = make_fake_class(cpt.cls)
                logger.debug('switch cpt_name=%s to cls=%s',
                             cpt_name, fake_cpt.cls)
            # DDCpt stores the classes in a different place
            elif isinstance(cpt, DDCpt):
                fake_defn = {}
                for ddcpt_name, ddcpt_tuple in cpt.defn.items():
                    subcls = make_fake_class(ddcpt_tuple[0])
                    fake_defn[ddcpt_name] = [subcls] + list(ddcpt_tuple[1:])
                fake_cpt.defn = fake_defn
            else:
                raise RuntimeError(("{} is not a component or a dynamic "
                                    "device component. I don't know how you "
                                    "found this error, should be impossible "
                                    "to reach it.".format(cpt)))
            fake_dict[cpt_name] = fake_cpt
        fake_class = type('Fake{}'.format(cls.__name__), (cls,), fake_dict)
        fake_class_cache[cls] = fake_class
        logger.debug('fake_class_cache[%s] = %s', cls, fake_class)
    return fake_class_cache[cls]


class FakeEpicsSignal(Signal):
    """
    Fake version of EpicsSignal that's really just a signal.

    We can emulate EPICS features here. Currently we just emulate the put
    limits because it was involved in a kwarg.
    """
    def __init__(self, read_pv, write_pv=None, *, pv_kw=None,
                 put_complete=False, string=False, limits=False,
                 auto_monitor=False, name=None, **kwargs):
        """
        Mimic EpicsSignal signature
        """
        super().__init__(name=name, **kwargs)
        self._use_limits = limits
        self._sim_getter = None
        self._sim_putter = None

    def sim_set_getter(self, getter):
        """
        Set a method to call instead of get
        """
        self._sim_getter = getter

    def sim_set_putter(self, putter):
        """
        Set a method to call instead of put
        """
        self._sim_putter = putter

    def get(self, *args, **kwargs):
        if self._sim_getter:
            return self._sim_getter(*args, **kwargs)
        return super().get(*args, **kwargs)

    def put(self, *args, **kwargs):
        if self._sim_putter is not None:
            return self._sim_putter(*args, **kwargs)
        return super().put(*args, **kwargs)

    def sim_put(self, *args, **kwargs):
        """
        Update the read-only signal's value.

        Implement here instead of FakeEpicsSignalRO so you can call it with
        every fake signal.
        """
        return Signal.put(self, *args, **kwargs)

    @property
    def limits(self):
        return self._limits

    def sim_limits(self, limits):
        """
        Set the fake signal's limits.
        """
        self._limits = limits

    def check_value(self, value):
        """
        Check fake limits before putting
        """
        super().check_value(value)
        if self._use_limits and not self.limits[0] < value < self.limits[1]:
            raise LimitError('value={} limits={}'.format(value, self.limits))


class FakeEpicsSignalRO(FakeEpicsSignal):
    """
    Read-only FakeEpicsSignal
    """
    def put(self, *args, **kwargs):
        raise ReadOnlyError()

    def set(self, *args, **kwargs):
        raise ReadOnlyError()


fake_class_cache = {EpicsSignal: FakeEpicsSignal,
                    EpicsSignalRO: FakeEpicsSignalRO}
