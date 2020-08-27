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


class PVPositionerDone(FltMvInterface, PVPositioner):
    """
    PV Positioner with no readback that reports done immediately.

    Optionally, this PV positioner can be configured to skip small moves,
    e.g. moves that are smaller than the atol value.

    Parameters
    ----------
    prefix: str
        PV prefix for the request setpoint. This should always be a hutch name.

    name: str, required keyword
        Name to use for this device in log messages, data streams, etc.

    skip_small_moves: bool, optional
        Defaults to False. If True, ignores move requests that are smaller
        than the atol factor.
        This can be very useful for synchronized energy scans where the ACR
        side of the process can be very slow, but does not necessarily need to
        happen at every step. Rather than design complicated scan patterns, we
        can skip the small moves here and move the monochromater and beam
        request devices in parallel.

    atol: int, optional
        Absolute tolerance that determines when the move is done and when to
        skip moves using the skip_small_moves parameter.
    """

    atol = 0

    setpoint = None

    done = Cpt(InternalSignal, value=0)
    done_value = 1

    def __init__(self, prefix, *, name, skip_small_moves=False, **kwargs):
        self.skip_small_moves = skip_small_moves
        super().__init__(prefix, name=name, **kwargs)

    def _setup_move(self, position):
        """Skip the move part of the move if below the tolerance."""
        if self.skip_small_moves and abs(position-self.position) < self.atol:
            self.log.debug('Skipping small move of %s', self.name)
            self._toggle_done()
        else:
            self.log.debug('Doing pv positioner move of %s', self.name)
            super()._setup_move(position)
            self._toggle_done()

    def _toggle_done(self):
        self.done.put(0, force=True)
        self.done.put(1, force=True)
