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

from lightpath import LightpathState
from ophyd import Component as Cpt
from ophyd import DynamicDeviceComponent as DDCpt
from ophyd import EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt
from ophyd.ophydobj import OphydObject
from ophyd.pv_positioner import PVPositioner
from ophyd.signal import Signal, SignalRO
from ophyd.status import Status
from ophyd.status import wait as status_wait

from .areadetector.detectors import PCDSAreaDetectorTyphosTrigger
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis, BeckhoffAxisNoOffset
from .interface import (BaseInterface, FltMvInterface, LightpathInOutCptMixin,
                        LightpathMixin, MvInterface)
from .pmps import TwinCATStatePMPS
from .sensors import RTD, TwinCATTempSensor
from .signal import NotImplementedSignal, PytmcSignal
from .sim import FastMotor
from .utils import get_status_float, get_status_value, schedule_task
from .variety import set_metadata

logger = logging.getLogger(__name__)


class SlitsBase(MvInterface, GroupDevice, LightpathMixin):
    """
    Base class for slit motion interfacing.
    """
    # QIcon for UX
    _icon = 'fa.th-large'

    # Mark as parent class for lightpath interface
    _lightpath_mixin = True
    lightpath_cpts = ['xwidth.user_readback', 'ywidth.user_readback']

    # Tab settings
    tab_whitelist = ['open', 'close', 'block', 'hg', 'ho', 'vg', 'vo']

    # Just to hold a value
    nominal_aperture = Cpt(Signal, kind='normal')

    # Placeholders for each component to override
    # These are expected to be positioners
    xwidth = Cpt(SignalRO)
    ywidth = Cpt(SignalRO)
    xcenter = Cpt(SignalRO)
    ycenter = Cpt(SignalRO)

    # The gap opens/closes when we move the slits device
    stage_group = [xwidth, ywidth]

    def __init__(self, *args, nominal_aperture=5.0, **kwargs):
        self._has_subscribed = False
        super().__init__(*args, **kwargs)
        self.nominal_aperture.put(nominal_aperture)
        self.hg = self.xwidth
        self.vg = self.ywidth
        self.ho = self.xcenter
        self.vo = self.ycenter
        self._pre_stage_gap: tuple[float, float] = None

        self._inserted = False
        self._removed = False

    def format_status_info(self, status_info):
        """
        Override status info handler to render the slits.

        Display slits status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        # happi metadata
        try:
            md = self.root.md
        except AttributeError:
            name = f'Slit: {self.prefix}'
        else:
            beamline = get_status_value(md, 'beamline')
            stand = get_status_value(md, 'stand')
            if stand is not None:
                name = f'{beamline} Slit {self.name} on {stand}'
            else:
                name = f'{beamline} Slit {self.name}'

        x_width = get_status_float(status_info, 'xwidth', 'position',
                                   include_plus_sign=True)
        y_width = get_status_float(status_info, 'ywidth', 'position',
                                   include_plus_sign=True)
        x_center = get_status_float(status_info, 'xcenter', 'position',
                                    include_plus_sign=True)
        y_center = get_status_float(status_info, 'ycenter', 'position',
                                    include_plus_sign=True)
        w_units = get_status_value(status_info, 'ywidth', 'setpoint', 'units')
        c_units = get_status_value(status_info, 'ycenter', 'setpoint', 'units')

        return f"""\
{name}
(hg, vg): ({x_width}, {y_width}) [{w_units}]
(ho, vo): ({x_center}, {y_center}) [{c_units}]
"""

    def move(self, width, height=None, *, wait=False, moved_cb=None,
             timeout=None):
        """
        Set the dimensions of the width/height of the slits gap.

        Parameters
        ---------
        size : float or tuple of float
            Target size for slits in both x and y axis. If a square gap is
            desired, a single value can be entered. Otherwise, the width and
            height can both be entered, either as separate arguments or as a
            tuple.

        wait : bool, optional
            If `True`, block until move is completed. Defaults to `False`.

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

        # Check for missing size
        if width is None and height is None:
            raise TypeError("move() missing 1 required positional "
                            "argument: 'width'")
        elif width is None:
            width = height
        # Check for rectangular setpoint
        elif isinstance(width, tuple):
            (width, height) = width
        elif height is None:
            height = width
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

    def __call__(self, width=None, height=None):
        """
        If arguments are provided, attempt a move. Otherwise, query position.
        """
        if width is None and height is None:
            return self.wm()
        else:
            return self.move(width=width, height=height)

    @property
    def current_aperture(self) -> tuple[float, float]:
        """
        Current size of the aperture. Returns a tuple in the form
        ``(width, height)``.
        """
        return (self.xwidth.position, self.ywidth.position)

    @property
    def position(self) -> tuple[float, float]:
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
        Status
            `~ophyd.Status` object based on move completion.

        See Also
        --------
        :meth:`Slits.move`
        """

        # Use nominal_aperture by default
        size = size or self.nominal_aperture
        if size > min(self.current_aperture):
            return self.move(size, wait=wait, timeout=timeout, **kwargs)
        else:
            status = Status()
            status.set_finished()
            return status

    def set(self, size):
        """Alias for the move method, here for ``bluesky`` compatibilty."""
        return self.move(size, wait=False)

    def stage(self) -> list[OphydObject]:
        """
        Store the initial values of the aperture position before scanning.
        """
        self._pre_stage_gap = self.position
        return super().stage()

    def unstage(self) -> list[OphydObject]:
        """
        Restore the initial values of the aperture position.
        """
        if self._pre_stage_gap is not None:
            self.move(
                self._pre_stage_gap[0],
                self._pre_stage_gap[1],
                wait=True
                )
        self._pre_stage_gap = None
        return super().unstage()

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

    def calc_lightpath_state(
        self,
        xwidth: float,
        ywidth: float
    ) -> LightpathState:
        widths = [xwidth, ywidth]
        self._inserted = (min(widths) < self.nominal_aperture.get())
        self._removed = not self._inserted
        self._transmission = 1.0 if self._inserted else 0.0

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: self._transmission}
        )

    @property
    def inserted(self):
        return self._inserted

    @property
    def removed(self):
        return self._removed


class BadSlitPositionerBase(FltMvInterface, PVPositioner):
    """Base class for slit positioner with awful PV names."""

    readback = FCpt(EpicsSignalRO, '{prefix}:ACTUAL_{_dirlong}',
                    auto_monitor=True, kind='normal')
    setpoint = FCpt(EpicsSignal, '{prefix}:{_dirshort}_REQ',
                    auto_monitor=True, kind='normal')

    def __init__(self, prefix, *, slit_type="", limits=None, **kwargs):
        # Private PV names to deal with complex naming schema
        self._dirlong = slit_type
        self._dirshort = slit_type[:4]
        # Initalize PVPositioner
        super().__init__(prefix, limits=limits, **kwargs)


class LusiSlitPositioner(BadSlitPositionerBase):
    """
    Abstraction of a Slit axis from LCLS-I

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

    done = Cpt(EpicsSignalRO, ':DMOV', auto_monitor=True, kind='omitted')

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


class SlitPositioner(LusiSlitPositioner):
    # Should probably deprecate this name
    pass


class LusiSlits(SlitsBase):
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

    # Base class overrides
    xwidth = Cpt(LusiSlitPositioner, '', slit_type='XWIDTH', kind='hinted')
    ywidth = Cpt(LusiSlitPositioner, '', slit_type='YWIDTH', kind='hinted')
    xcenter = Cpt(LusiSlitPositioner, '', slit_type='XCENTER', kind='normal')
    ycenter = Cpt(LusiSlitPositioner, '', slit_type='YCENTER', kind='normal')

    # Local PVs
    blocked = Cpt(EpicsSignalRO, ':BLOCKED', kind='omitted')
    open_cmd = Cpt(EpicsSignal, ':OPEN', kind='omitted')
    close_cmd = Cpt(EpicsSignal, ':CLOSE', kind='omitted')
    block_cmd = Cpt(EpicsSignal, ':BLOCK', kind='omitted')

    lightpath_cpts = ['xwidth.readback', 'ywidth.readback']

    def open(self):
        """Uses the built-in 'OPEN' record to move open the aperture."""
        self.open_cmd.put(1)

    def close(self):
        """Close the slits to have an aperture of 0mm on each side."""
        self.close_cmd.put(1)

    def block(self):
        """Overlap the slits to block the beam."""
        self.block_cmd.put(1)

    def calc_lightpath_state(
        self,
        xwidth_readback: float,
        ywidth_readback: float
    ) -> LightpathState:
        """widths have different names due to different positioner class"""
        return super().calc_lightpath_state(xwidth=xwidth_readback,
                                            ywidth=ywidth_readback)


class Slits(LusiSlits):
    # Should Probably Deprecate this name
    pass


class BeckhoffSlitPositioner(BadSlitPositionerBase):
    """
    Abstraction of a Slit axis from LCLS-II.

    This class needs a BeckhoffSlits parent to function properly.
    """

    readback = FCpt(PytmcSignal, BadSlitPositionerBase.readback.suffix,
                    io='i', auto_monitor=True, kind='normal')
    setpoint = FCpt(PytmcSignal, BadSlitPositionerBase.setpoint.suffix,
                    io='io', auto_monitor=True, kind='normal')
    done = Cpt(Signal, kind='omitted')
    actuate = Cpt(Signal, kind='omitted')

    @actuate.sub_value
    def _execute_move(self, *args, value, **kwargs):
        if value == 1:
            self.parent.exec_queue.put(1)

    @done.sub_value
    def _reset_actuate(self, *args, value, old_value, **kwargs):
        if value == 1 and old_value == 0:
            self.actuate.put(0)


class BeckhoffSlits(SlitsBase):
    # Base class overrides
    xwidth = Cpt(BeckhoffSlitPositioner, '', slit_type='XWIDTH', kind='hinted')
    ywidth = Cpt(BeckhoffSlitPositioner, '', slit_type='YWIDTH', kind='hinted')
    xcenter = Cpt(BeckhoffSlitPositioner, '', slit_type='XCENTER',
                  kind='normal')
    ycenter = Cpt(BeckhoffSlitPositioner, '', slit_type='YCENTER',
                  kind='normal')

    # Slit state commands
    exec_queue = Cpt(Signal, kind='omitted')
    exec_move = Cpt(PytmcSignal, ':GO', io='io', kind='omitted')

    # Slit calculated move dmov
    done_all = Cpt(Signal, kind='omitted')
    done_top = Cpt(PytmcSignal, ':TOP:DMOV', io='i', kind='omitted')
    done_bottom = Cpt(PytmcSignal, ':BOTTOM:DMOV', io='i', kind='omitted')
    done_north = Cpt(PytmcSignal, ':NORTH:DMOV', io='i', kind='omitted')
    done_south = Cpt(PytmcSignal, ':SOUTH:DMOV', io='i', kind='omitted')

    # Raw motors
    top = Cpt(BeckhoffAxisNoOffset, ':MMS:TOP', kind='normal')
    bottom = Cpt(BeckhoffAxisNoOffset, ':MMS:BOTTOM', kind='normal')
    north = Cpt(BeckhoffAxisNoOffset, ':MMS:NORTH', kind='normal')
    south = Cpt(BeckhoffAxisNoOffset, ':MMS:SOUTH', kind='normal')

    lightpath_cpts = ['xwidth.readback', 'ywidth.readback']

    def __init__(self, prefix, *, name, **kwargs):
        self._started_move = False
        self._top_done = False
        self._bottom_done = False
        self._north_done = False
        self._south_done = False
        super().__init__(prefix, name=name, nominal_aperture=3, **kwargs)

    @exec_queue.sub_value
    def _exec_handler(self, *args, value, old_value, **kwargs):
        """Wait just a moment to queue up move requests."""
        if value == 1 and old_value == 0:
            self._started_move = True
            schedule_task(self.exec_move.put, args=(1,), delay=0.2)

    @done_all.sub_value
    def _reset_exec_move(self, *args, value, old_value, **kwargs):
        """When we're done moving, reset the exec_move signal."""
        if self._started_move and value == 1 and old_value == 0:
            self._started_move = False
            self.exec_queue.put(0)
            self.exec_move.put(0)

    @done_all.sub_value
    def _dmov_fanout(self, *args, value, **kwargs):
        """When we're done moving, tell our pv positioners."""
        self.xwidth.done.put(value)
        self.ywidth.done.put(value)
        self.xcenter.done.put(value)
        self.ycenter.done.put(value)

    @done_top.sub_value
    def _update_top_done(self, value, *args, **kwargs):
        """Update axis done flag, and then the group done if applicable"""
        self._top_done = value
        self._update_dmov()

    @done_bottom.sub_value
    def _update_bottom_done(self, value, *args, **kwargs):
        """Update axis done flag, and then the group done if applicable"""
        self._bottom_done = value
        self._update_dmov()

    @done_north.sub_value
    def _update_north_done(self, value, *args, **kwargs):
        """Update axis done flag, and then the group done if applicable"""
        self._north_done = value
        self._update_dmov()

    @done_south.sub_value
    def _update_south_done(self, value, *args, **kwargs):
        """Update axis done flag, and then the group done if applicable"""
        self._south_done = value
        self._update_dmov()

    def _update_dmov(self, *args, **kwargs):
        """
        Call this inside a callback to update the done_all signal.

        Each direction's done moving signal should update its
        individual done moving boolean in a callback and then call
        this method to update the aggregate done_all signal.
        """
        done = all((self._top_done,
                    self._bottom_done,
                    self._north_done,
                    self._south_done))
        if done != self.done_all.get():
            self.done_all.put(done)

    def calc_lightpath_state(
        self,
        xwidth_readback: float,
        ywidth_readback: float
    ) -> LightpathState:
        """widths have different names due to different positioner class"""
        return super().calc_lightpath_state(xwidth=xwidth_readback,
                                            ywidth=ywidth_readback)


def _rtd_fields(cls, attr_base, range_, **kwargs):
    padding = max(range_)//10 + 2
    defn = OrderedDict()
    for i in range_:
        attr = '{attr}{i}'.format(attr=attr_base, i=i)
        suffix = ':RTD:{i}'.format(i=str(i).zfill(padding))
        defn[attr] = (cls, suffix, kwargs)
    return defn


class PowerSlits(BeckhoffSlits):
    """
    'SL*:POWER'.

    Power slits variant of slits. The XTES design.

    Parameters
    ----------
    prefix : str
        The PV base of the device.
    """

    rtds = DDCpt(_rtd_fields(RTD, 'rtd', range(1, 9)))
    fsw = Cpt(NotImplementedSignal, ':FSW', kind='normal')


class ExitSlitTarget(TwinCATStatePMPS):
    """
    Controls the exit slits target state.
    Defines the state count as 3 (OUT and 2 targets) to limit the number of
    config PVs we connect to.
    """
    config = UpCpt(state_count=3)


class ExitSlits(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.video-camera'

    target = Cpt(ExitSlitTarget, ':YAG:STATE', kind='hinted',
                 doc='Control of the YAG  stack via saved positions.')
    yag_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:YAG', kind='normal',
                    doc='Direct control of the Yag Stack motor.')
    pitch_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:PITCH', kind='normal',
                      doc='Direct control of the slits assembly pitch  motor.')
    vert_motor = Cpt(
        BeckhoffAxisNoOffset, ':MMS:VERT', kind='normal',
        doc='Direct control of the slits assembly vertical motor.'
    )
    roll_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:ROLL', kind='normal',
                     doc='Direct control of the slits assembly roll motor.')
    gap_motor = Cpt(BeckhoffAxisNoOffset, ':MMS:GAP', kind='normal',
                    doc='Direct control of the slits gap  motor.')
    detector = Cpt(PCDSAreaDetectorTyphosTrigger, ':CAM:', kind='normal',
                   doc='Area detector settings and readbacks.')
    cam_power = Cpt(PytmcSignal, ':CAM:PWR', io='io', kind='config',
                    doc='Camera power supply controls.')
    fan_power = Cpt(PytmcSignal, ':FAN:PWR', io='io', kind='config',
                    doc='Fan power supply controls.')
    led_power = Cpt(PytmcSignal, ':LED:PWR', io='io', kind='config',
                    doc='LED power supply controls.')
    led = Cpt(PytmcSignal, ':CAM:CIL:PCT', io='io', kind='config',
              doc='Percent of light from the dimmable illuminatior.')
    set_metadata(led, dict(variety='scalar-range',
                           range={'value': (0, 100),
                                  'source': 'value'}
                           ))
    yag_thermocouple = Cpt(TwinCATTempSensor, ':RTD:YAG', kind='normal',
                           doc='Thermocouple on the YAG holder.')
    upper_crystal_thermocouple = Cpt(
        TwinCATTempSensor, ':RTD:CRYSTAL_TOP', kind='normal',
        doc='Thermocouple on the TOP CRYSTAL.'
    )
    lower_crystal_thermocouple = Cpt(
        TwinCATTempSensor, ':RTD:CRYSTAL_BOTTOM', kind='normal',
        doc='Thermocouple on the BOTTOM CRYSTAL.'
    )
    heatsync_thermocouple = Cpt(
        TwinCATTempSensor, ':RTD:HeatSync', kind='normal',
        doc='Thermocouple on the Heat Sync.'
    )
    set_metadata(cam_power, dict(variety='command-enum'))

    @property
    def y_states(self):
        """Alias old name. Will deprecate."""
        return self.target


class SimLusiSlits(LusiSlits):
    xwidth = Cpt(FastMotor)
    ywidth = Cpt(FastMotor)
    xcenter = Cpt(FastMotor)
    ycenter = Cpt(FastMotor)


class JJSlits(SlitsBase):
    '''
    Beckhoff Controlled AT-C8-HV JJ X-Ray Slits.
    The JJSlits class defines motor components for the specific JJ X-Ray slits
    model AT-C8-HV. This model of JJSlits holds four in-vacuum motors that set
    the position and opening of the aperture in two dimensions. For each
    dimension, one motor defines the aperture opening, and another determines
    the position of the aperture. This class allows an operator to control
    and scan the position 'center' and opening 'width' of the aperture. The
    'JJSlits' class instantiates four sub-devices: 'JJSlits.xwidth',
    'JJSlits.xcenter', 'JJSlits.ywidth', 'JJSlits.ycenter'.
    Beckhoff controlled JJSlits are implemented along the beamline in HXR
    for beam attenuation.

    Parameters
    ---------
    prefix : str
       Base PV for the JJ X-RAY PLC System
    name : str, keyword-only
    '''

    # Motor Components
    xwidth = Cpt(BeckhoffAxis, ':XWIDTH', kind='normal')
    ywidth = Cpt(BeckhoffAxis, ':YWIDTH', kind='normal')
    xcenter = Cpt(BeckhoffAxis, ':XCENTER', kind='normal')
    ycenter = Cpt(BeckhoffAxis, ':YCENTER', kind='normal')
