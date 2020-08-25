import numpy as np
from ophyd.device import Component as Cpt
from ophyd.pv_positioner import PVPositioner

from .interface import FltMvInterface
from .signal import InternalSignal


class PVPositionerComparator(FltMvInterface, PVPositioner):
    """
    PV Positioner with a software done signal.

    The done state is set by a comparison function defined in the class body.
    The comparison function takes two arguments, readback and setpoint,
    returning True if we are close enough to be considered done or False if we
    are too far away.
    """

    # Override setpoint, readback in subclass
    setpoint = None
    readback = None

    done = Cpt(InternalSignal, value=0)
    done_value = 1

    # Optionally override limits to a 2-element tuple in subclass
    limits = None

    def __init__(self, prefix, *, name, **kwargs):
        self._last_readback = None
        self._last_setpoint = None
        super().__init__(prefix, name=name, **kwargs)
        if None in (self.setpoint, self.readback):
            raise NotImplementedError('PVPositionerComparator requires both '
                                      'a setpoint and a readback signal to '
                                      'compare!')

    def done_comparator(self, readback, setpoint):
        """Override done_comparator in subclass."""
        raise NotImplementedError('Must implement a done comparator!')

    def __init_subclass__(cls, **kwargs):
        """Set up callbacks in subclass."""
        super().__init_subclass__(**kwargs)
        if None not in (cls.setpoint, cls.readback):
            cls.setpoint.sub_value(cls._update_setpoint)
            cls.readback.sub_value(cls._update_readback)

    def _update_setpoint(self, *args, value, **kwargs):
        """Callback to cache the setpoint and update done state."""
        self._last_setpoint = value
        # Always set done to False when a move is requested
        # This means we always get a rising edge when finished moving
        # Even if the move distance is under our done moving tolerance
        self.done.put(0, force=True)
        self._update_done()

    def _update_readback(self, *args, value, **kwargs):
        """Callback to cache the readback and update done state."""
        self._last_readback = value
        self._update_done()

    def _update_done(self):
        """Update our status to done if we pass the comparator."""
        if None not in (self._last_readback, self._last_setpoint):
            is_done = self.done_comparator(self._last_readback,
                                           self._last_setpoint)
            self.done.put(int(is_done), force=True)


class PVPositionerIsClose(PVPositionerComparator):
    """
    PV Positioner that updates done state based on np.isclose.

    The arguments atol and rtol can be set as class attributes or passed as
    initialization arguments.
    """

    atol = None
    rtol = None

    def __init__(self, prefix, *, name, atol=None, rtol=None, **kwargs):
        if atol is not None:
            self.atol = atol
        if rtol is not None:
            self.rtol = rtol
        super().__init__(prefix, name=name, **kwargs)

    def done_comparator(self, readback, setpoint):
        kwargs = {}
        if self.atol is not None:
            kwargs['atol'] = self.atol
        if self.rtol is not None:
            kwargs['rtol'] = self.rtol
        return np.isclose(readback, setpoint, **kwargs)
