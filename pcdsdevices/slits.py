"""
Module to define `Slits` classes.

The SLAC EPICS motor record contains an extra set of records to abstract four
axes into a Slits object. This allows an operator to manipulate the center and
width in two dimensions of a small aperture. The classes below allow both
individual parameters of the aperture and the Slit as a whole to be controlled
and scanned. The `Slits` class instantiates four sub-devices: `~Slits.xwidth`,
`~Slits.xcenter`, `~Slits.ycenter`, `~Slits.ywidth`. These are each represented
by a `SlitPositioner`. The main `Slits` class assumes that most of
the manipulation will be done on the size of the aperture not the position,
however, if control of the center is desired the ``center`` sub-devices can be
used.
"""
import logging
from collections import OrderedDict

from ophyd import Component as Cpt
from ophyd import Device
from ophyd import DynamicDeviceComponent as DDCpt
from ophyd import EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt
from ophyd.epics_motor import EpicsMotor
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import SignalRO
from ophyd.status import wait as status_wait

from .interface import BaseInterface, FltMvInterface, MvInterface
from .sensors import RTD

logger = logging.getLogger(__name__)


class SlitPositioner(PVPositioner, FltMvInterface):
    """
    Abstraction of a Slit axis.

    Each adjustable parameter of the slit (center, width) can be modeled as a
    motor in itself, even though each controls two different actual motors in
    reality, this gives a convienent interface for adjusting the aperture size
    and location with out backwards calculating motor positions.

    Parameters
    ----------
    prefix : str
        The prefix location of the slits, e.g. 'MFX:DG2'.

    name : str
        Alias for the axis.

    slit_type : {'XWIDTH', 'YWIDTH', 'XCENTER', 'YCENTER'}
        The aspect of the slit position you would like to control with this
        specific motor.

    limits : tuple, optional
        Limits on the motion of the positioner. By default, the limits on the
        setpoint PV are used if `None` is given.

    See Also
    --------
    `ophyd.PVPositioner`
        SlitPositioner inherits directly from `~ophyd.PVPositioner`.
    """

    readback = FCpt(EpicsSignalRO, '{self.prefix}:ACTUAL_{self._dirlong}',
                    auto_monitor=True, kind='hinted')
    setpoint = FCpt(EpicsSignal, '{self.prefix}:{self._dirshort}_REQ',
                    auto_monitor=True, kind='normal')
    done = Cpt(EpicsSignalRO, ':DMOV', auto_monitor=True, kind='omitted')

    def __init__(self, prefix, *, slit_type="", name=None,
                 limits=None, **kwargs):
        # Private PV names to deal with complex naming schema
        self._dirlong = slit_type
        self._dirshort = slit_type[:4]
        # Initalize PVPositioner
        super().__init__(prefix, limits=limits, name=name, **kwargs)

    @property
    def egu(self):
        """Engineering Units."""
        return self._egu or self.readback._read_pv.units

    def _setup_move(self, position):
        # This is subclassed because we need `wait` to be set to `False` unlike
        # the default PVPositioner method. `wait` set to `True` will not return
        # until the move has completed
        logger.debug('%s.setpoint = %s', self.name, position)
        self.setpoint.put(position, wait=False)


class Slits(Device, MvInterface):
    """
    Beam slits with combined motion for center and width.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the motor.

    name : str, optional
        The name of the offset mirror.

    nominal_aperture : float, optional
        Nominal slit size that will encompass the beam without blocking.

    Notes
    -----
    The slits represent a unique device when forming the lightpath because
    whether the beam is being blocked or not depends on the pointing. In order
    to create an estimate that will warn operators of 'closed' slits, we set a
    `nominal_aperture` for each unique device along the beamline. This is
    value is considered the smallest the slit aperture can become without
    blocking the beamline. Both the `xwidth` and the `ywidth`(height) need to
    exceed this `nominal_aperture` for the slits to be considered removed.
    """

    xwidth = Cpt(SlitPositioner, '', slit_type='XWIDTH', kind='hinted')
    ywidth = Cpt(SlitPositioner, '', slit_type='YWIDTH', kind='hinted')
    nominal_aperture = Cpt(SignalRO, kind='normal')
    xcenter = Cpt(SlitPositioner, '', slit_type='XCENTER', kind='normal')
    ycenter = Cpt(SlitPositioner, '', slit_type='YCENTER', kind='normal')
    blocked = Cpt(EpicsSignalRO, ':BLOCKED', kind='omitted')
    open_cmd = Cpt(EpicsSignal, ':OPEN', kind='omitted')
    close_cmd = Cpt(EpicsSignal, ':CLOSE', kind='omitted')
    block_cmd = Cpt(EpicsSignal, ':BLOCK', kind='omitted')
    # Subscription information
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE
    # QIcon for UX
    _icon = 'fa.th-large'
    tab_whitelist = ['open', 'close', 'block']

    def __init__(self, *args, nominal_aperture=5.0, **kwargs):
        self._has_subscribed = False
        super().__init__(*args, **kwargs)
        # Initialize nominal_aperture behind the scenes
        self.nominal_aperture._readback = nominal_aperture
        # Modify Kind of center readbacks
        self.xcenter.readback.kind = 'normal'
        self.ycenter.readback.kind = 'normal'

    def move(self, size, wait=False, moved_cb=None, timeout=None):
        """
        Set the dimensions of the width/height of the gap to width paramater.

        Parameters
        ---------
        size : float or tuple of float
            Target size for slits in both x and y axis. Either specify as a
            tuple for a rectangular aperture, ``(width, height)``, or set both
            with single floating point value to use a square opening.

        wait : bool
            If `True`, block until move is completed.

        timeout : float, optional
            Maximum time for the motion. If `None` is given, the default value
            of `xwidth` and `ywidth` positioners is used.

        moved_cb : callable, optional
            Function to be run when the operation finishes. This callback
            should not expect any arguments or keywords.

        Returns
        -------
        status : AndStatus
            Logical combination of the request to both horizontal and vertical
            motors.
        """

        # Check for rectangular setpoint
        if isinstance(size, tuple):
            (width, height) = size
        else:
            width, height = size, size
        # Instruct both width and height then combine the output status
        x_stat = self.xwidth.move(width, wait=False, timeout=timeout)
        y_stat = self.ywidth.move(height, wait=False, timeout=timeout)
        status = x_stat & y_stat
        # Add our callback if one was given
        if moved_cb is not None:
            status.add_callback(moved_cb)
        # Wait if instructed to do so. Stop the motors if interrupted
        if wait:
            try:
                status_wait(status)
            except KeyboardInterrupt:
                self.xwidth.stop()
                self.ywidth.stop()
                raise
        return status

    @property
    def inserted(self):
        """Whether the slits are inserted into the beampath."""
        return min(self.current_aperture) < self.nominal_aperture.get()

    @property
    def removed(self):
        """Whether the slits are entirely removed from the beampath."""
        return not self.inserted

    @property
    def current_aperture(self):
        """
        Current size of the aperture. Returns a tuple in the form
        ``(width, height)``.
        """
        return (self.xwidth.position, self.ywidth.position)

    @property
    def position(self):
        return self.current_aperture

    def remove(self, size=None, wait=False, timeout=None, **kwargs):
        """
        Open the slits to unblock the beam.

        Parameters
        ----------
        size : float, optional
            Open the slits to a specific size. Defaults to `.nominal_aperture`.

        wait : bool, optional
            Wait for the status object to complete the move before returning.

        timeout : float, optional
            Maximum time to wait for the motion. If `None`, the default timeout
            for this positioner is used.

        Returns
        -------
        MoveStatus
            `~ophyd.Status` object based on move completion.

        See Also
        --------
        :meth:`Slits.move`
        """

        # Use nominal_aperture by default
        size = size or self.nominal_aperture
        return self.move(size, wait=wait, timeout=timeout, **kwargs)

    def set(self, size):
        """Alias for the move method, here for ``bluesky`` compatibilty."""
        return self.move(size, wait=False)

    def open(self):
        """Uses the built-in 'OPEN' record to move open the aperture."""
        self.open_cmd.put(1)

    def close(self):
        """Close the slits to have an aperture of 0mm on each side."""
        self.close_cmd.put(1)

    def block(self):
        """Overlap the slits to block the beam."""
        self.block_cmd.put(1)

    def stage(self):
        """
        Store the initial values of the aperture position before scanning.
        """
        self._original_vals[self.xwidth.setpoint] = self.xwidth.readback.get()
        self._original_vals[self.ywidth.setpoint] = self.ywidth.readback.get()
        return super().stage()

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes of the slits.

        Parameters
        ----------
        cb : callable
            Callback to be run.

        event_type : str, optional
            Type of event to run callback on.

        run : bool, optional
            Run the callback immediately.
        """

        # Avoid making child subscriptions unless a client cares
        if not self._has_subscribed:
            # Subscribe to changes in aperture
            self.xwidth.readback.subscribe(self._aperture_changed,
                                           run=False)
            self.ywidth.readback.subscribe(self._aperture_changed,
                                           run=False)
            self._has_subscribed = True
        return super().subscribe(cb, event_type=event_type, run=run)

    def _aperture_changed(self, *args, **kwargs):
        """Callback run when slit size is adjusted."""
        # Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        kwargs.pop('obj',      None)
        # Run subscriptions
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)


def _rtd_fields(cls, attr_base, range_, **kwargs):
    padding = max(range_)//10 + 2
    defn = OrderedDict()
    for i in range_:
        attr = '{attr}{i}'.format(attr=attr_base, i=i)
        suffix = ':RTD:{i}'.format(i=str(i).zfill(padding))
        defn[attr] = (cls, suffix, kwargs)
    return defn


class PowerSlits(Device, BaseInterface):
    """
    'SL*:POWER'.

    Power slits variant of slits. The XTES design.

    Parameters
    ----------
    prefix : str
        The PV base of the device.
    """

    top = FCpt(EpicsMotor, '{self.prefix}:MMS:TOP', kind='normal')
    bottom = FCpt(EpicsMotor, '{self.prefix}:MMS:BOTTOM')
    north = FCpt(EpicsMotor, '{self.prefix}:MMS:NORTH')
    south = FCpt(EpicsMotor, '{self.prefix}:MMS:SOUTH')
    rtds = DDCpt(_rtd_fields(RTD, 'rtd', range(1, 9)))
    fsw = Cpt(EpicsSignalRO, ':FSW', kind='normal')
