import copy
import enum
import logging
import typing
import warnings

import numpy as np
import ophyd
import ophyd.pseudopos
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.positioner import PositionerBase
from ophyd.pseudopos import (PseudoSingle, pseudo_position_argument,
                             real_position_argument)
from ophyd.signal import EpicsSignal
from scipy.constants import speed_of_light

from .device import InterfaceComponent as ICpt
from .device import InterfaceDevice
from .interface import FltMvInterface
from .signal import NotepadLinkedSignal
from .sim import FastMotor
from .utils import convert_unit, get_status_float, get_status_value

logger = logging.getLogger(__name__)


class PseudoSingleInterface(FltMvInterface, PseudoSingle):
    """PseudoSingle with FltMvInterface mixed in."""
    notepad_setpoint = Cpt(
        NotepadLinkedSignal, ':OphydSetpoint',
        notepad_metadata={'record': 'ao', 'default_value': 0.0},
    )

    notepad_readback = Cpt(
        NotepadLinkedSignal, ':OphydReadback',
        notepad_metadata={'record': 'ai', 'default_value': 0.0},
    )

    def __init__(self, prefix='', parent=None, verbose_name=None, **kwargs):
        if not prefix:
            # PseudoSingle generally does not get a prefix. Fix that here,
            # or 'notepad_setpoint' and 'notepad_readback' will have no
            # prefix.
            attr_name = kwargs['attr_name']
            prefix = f'{parent.prefix}:{attr_name}'

        super().__init__(prefix=prefix, parent=parent, **kwargs)
        self._verbose_name = verbose_name

    @property
    def calculated_dial_pos(self):
        """
        Calculate the dial position of the real motor dial position.
        """
        dial_pos = []
        try:
            for real_pos in self.parent.real_positioners:
                dial_pos.append(real_pos.dial_position.get())
            if dial_pos:
                calc_dial = self.parent.inverse(
                    self.parent.RealPosition(*dial_pos))
            # try to get the correct pseudo position base on the name
            return f'{calc_dial[calc_dial._fields.index(self.attr_name)]:.3e}'
        # some motors might not have dial_position
        except Exception:
            return None

    def format_status_info(self, status_info):
        """
        Override status info handler to render the virtual motor.

        Display virtual motor status info in the ipython terminal.

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
        units = get_status_value(status_info, 'units')
        if not units:
            units = get_status_value(status_info, 'notepad_readback', 'units')
        position = get_status_float(
            status_info, 'position', precision=3, format='e')
        # if a dial_pos is not present we can assume that the dial position is
        # the same as the normal position
        dial_pos = self.calculated_dial_pos or position

        low, high = self.limits
        name = self.prefix
        if self._verbose_name:
            name = f'{self._verbose_name} {self.prefix}'

        return f"""\
Virtual Motor {name}
Current position (user, dial): {position}, {dial_pos} [{units}]
User limits (low, high): {low}, {high} [{units}]
Preset position: {self.presets.state()}
"""


def _as_float(self):
    """Pseudo Position scalar value -> float"""
    return float(self[0])


class PseudoPositioner(ophyd.pseudopos.PseudoPositioner):
    """
    This is a PCDS-specific PseudoPositioner subclass which has a few notable
    changes/additions:

    * Adds support for NotepadLinkedSignal.
    * Makes scalar ``RealPosition`` and ``PseudoPosition`` easily convert
      to floating point values.
    * Adds a set_current_position helper method

    """ + ophyd.pseudopos.PseudoPositioner.__doc__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.RealPosition._fields) == 1:
            self.RealPosition.__float__ = _as_float

        if len(self.PseudoPosition._fields) == 1:
            self.PseudoPosition.__float__ = _as_float

    def _update_notepad_ioc(self, position, attr):
        """
        Update the notepad IOC with a fully-specified ``PseudoPos``.

        Parameters
        ----------
        position : PseudoPos
            The position.

        attr : str
            The signal attribute name, such as ``notepad_setpoint``.
        """
        for positioner, value in zip(self._pseudo, position):
            try:
                signal = getattr(positioner, attr, None)
                if signal is None:
                    continue
                if signal.connected and signal.write_access:
                    if signal.get(use_monitor=True) != value:
                        if isinstance(signal, ophyd.signal.EpicsSignalBase):
                            signal.put(value, wait=False)
                        else:
                            signal.put(value)
            except Exception as ex:
                self.log.debug('Failed to update notepad %s to position %s',
                               attr, value, exc_info=ex)

    @pseudo_position_argument
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        '''
        Move to a specified position, optionally waiting for motion to
        complete.

        Parameters
        ----------
        position
            Pseudo position to move to.

        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.

        Returns
        -------
        status : MoveStatus

        Raises
        ------
        TimeoutError
            When motion takes longer than `timeout`.

        ValueError
            On invalid positions.

        RuntimeError
            If motion fails other than timing out.
        '''
        status = super().move(position, wait=wait, timeout=timeout,
                              moved_cb=moved_cb)
        self._update_notepad_ioc(position, 'notepad_setpoint')
        return status

    def _update_position(self):
        """Update the pseudo position based on that of the real positioners."""
        position = super()._update_position()
        self._update_notepad_ioc(position, 'notepad_readback')
        return position

    def set_current_position(self, position):
        """
        Adjust all offsets so that the pseudo position matches the input.

        This will raise an AttributeError if any of the real motors is missing
        a ``set_current_position`` method.

        Parameters
        ----------
        position : PseudoPos
            The position
        """
        real_pos = self.forward(position)
        for motor, pos in zip(self._real, real_pos):
            motor.set_current_position(pos)


class SyncAxesBase(FltMvInterface, PseudoPositioner):
    """
    Synchronized Axes.

    This class is deprecated. Use `SyncAxis` instead.

    This will move all axes in a coordinated way, retaining offsets.

    This can be configured to report its position as the min, max, mean, or any
    custom function acting on a list of positions. Min is the default.

    You should subclass this by adding real motors as components. The class
    will pick them up and include them correctly into the coordinated move.

    An example:

    .. code-block:: python

       class Parallel(SyncAxesBase):
           left = Cpt(EpicsMotor, ':01')
           right = Cpt(EpicsMotor, ':02')

    Like all `~ophyd.pseudopos.PseudoPositioner` classes, any subclass of
    `~ophyd.positioner.PositionerBase` will be included in the synchronized
    move.
    """

    pseudo = Cpt(PseudoSingleInterface)

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'SyncAxesBase is deprecated and will be removed in a future '
            'release. Please switch to SyncAxis.',
            DeprecationWarning)
        if self.__class__ is SyncAxesBase:
            raise TypeError(('SyncAxesBase must be subclassed with '
                             'the axes to synchronize included as '
                             'components'))
        super().__init__(*args, **kwargs)
        self._offsets = None

    def calc_combined(self, real_position):
        """
        Calculate the combined pseudo position.

        By default, this is just the position of our first axis.

        Parameters
        ----------
        real_position : ~typing.NamedTuple
            The positions of each of the real motors, accessible by name.

        Returns
        -------
        pseudo_position : float
            The combined position of the axes.
        """

        return real_position[0]

    def save_offsets(self):
        """
        Save the current offsets for the synchronized assembly.

        If not done earlier, this will be automatically run before it is first
        needed (generally, right before the first move).
        """

        pos = self.real_position
        combo = float(self.calc_combined(pos))
        offsets = {fld: float(getattr(pos, fld)) - combo
                   for fld in pos._fields}
        self._offsets = offsets
        logger.debug('Offsets %s cached', offsets)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """Composite axes move to the combined axis position plus an offset."""
        if self._offsets is None:
            self.save_offsets()
        real_pos = {}
        for axis, offset in self._offsets.items():
            real_pos[axis] = float(pseudo_pos.pseudo) + offset
        return self.RealPosition(**real_pos)

    @real_position_argument
    def inverse(self, real_pos):
        """Combined axis readback is the mean of the composite axes."""
        return self.PseudoPosition(pseudo=float(self.calc_combined(real_pos)))


class SyncAxisOffsetMode(enum.IntEnum):
    # Define a static offset and do not change it
    STATIC_FIXED = 0
    # Automatically pick a static offset based on initial positions
    AUTO_FIXED = 1


class SyncAxis(FltMvInterface, PseudoPositioner):
    """
    Pseudomotor class for moving motors with linear relationships.

    This will move all axes in a configurable coordinated way. It handles all
    cases where the motor coordination can be described by a simple scale and
    offset (multiply by a number, then add a number).

    The calculation for moves is simply:
    pos = sync * scale + offset

    Where sync is the pseudomotor's position and every real motor can have
    a unique scale and offset.

    The default settings will simply move all included real motors
    to the same value when the sync motor is moved. That is to say, a scale of
    1 and an offset of 0.

    You should subclass this by adding real motors as components. The class
    will pick them up and include them correctly into the coordinated move.

    An example:

    .. code-block:: python

       class Parallel(SyncAxis):
           left = Cpt(EpicsMotor, ':01')
           right = Cpt(EpicsMotor, ':02')

    Like all `~ophyd.pseudopos.PseudoPositioner` classes, any subclass of
    `~ophyd.positioner.PositionerBase` will be included in the synchronized
    move.

    See the following attributes for a dive into the settings and internals:

    Attributes
    ----------
    offset_mode : SyncAxisOffsetMode (enum)
        Selection of how and when offsets are interpreted. The default is
        ``STATIC_FIXED``, which means "define static offsets at class creation
        and never change them." Also available is ``AUTO_FIXED``, which means
        "define offsets based on the current motor positions at the first move
        and do not change them during this session."

    offsets : dict {str: float} or None
        Specification of which offset to use for each motor. The mapping should
        be from attribute name to offset value. Any omitted motor will have an
        offset of ``default_offset``.

    default_offset : float
        Any motor omitted from ``offsets`` will have this number assigned to
        them and its offset. The default value is 0.

    scales : dict {str: float} or None
        Specification of which scale to use for each motor. The mapping should
        be from attribute name to scale value. Any omitted motor will have a
        scale of ``default_scale``.

    default_scale : float
        Any motor omitted from ``scales`` will have this number assigned to
        them and its scale. The default value is 1.

    warn_inconsistent : bool
        If `True` (the default), warn the user if the real motors are not in a
        consistent position. An inconsistent position, or desync, can occur if
        a motor in the `SyncAxis` group has been moved manually.

    warn_deadband : float
        How far out of sync our motors can be before we consider ourselves to
        be in an inconsistent, or desync state. Defaults to 0.001.

    fix_sync_keep_still : str or None
        Which motor to keep still when we recover the position using the
        `fix_sync` method. We will assume one motor (this motor) is in the
        correct position and move all the other motors to their correct
        positions. If omitted, the first motor will be considered the guiding
        motor that we do not move.

    sync_limits : tuple or None
        Limits to apply to the sync axis. Set these if you don't think your
        real motor limits are sufficient to protect your application.
        e.g. sync_limits = (-100, 100) will bind the `SyncAxis` to move between
        -100 and 100.
    """
    sync = Cpt(PseudoSingleInterface, kind='omitted')

    tab_whitelist = ['fix_sync']

    # Enum that defines how and when offsets are interpreted
    offset_mode = SyncAxisOffsetMode.STATIC_FIXED
    # dict {str: float} that defines what offset to apply to each motor
    offsets = None
    # float that defines what offset to use for motors missing from offsets
    default_offset = 0
    # dict {str: float} that defines what scale to apply to each motor
    scales = None
    # float that defines what scale to use for motors missing from scales
    default_scale = 1
    # bool that defines if we should warn about inconsistent axes
    warn_inconsistent = True
    # float that defines how much of a deviation to warn on
    warn_deadband = 0.001
    # bool that defines which motor to keep still when calling fix_sync
    # if omitted, we'll keep the first real motor still
    fix_sync_keep_still = None
    # tuple of two floats that defines if we should add limits to the sync axis
    sync_limits = None

    def __init__(self, *args, **kwargs):
        self._check_settings()
        self._has_setup = False
        self._real_attrs = [attr for attr, _ in self._get_real_positioners()]
        self.scales = self._fill_info_dict(
            self.scales, self.default_scale, 'scales')
        super().__init__(*args, **kwargs)
        if self.sync_limits is not None:
            self.sync._limits = tuple(self.sync_limits)

    def _check_settings(self):
        """Mostly just a typo check."""
        if self.__class__ is SyncAxis:
            raise TypeError(
                'SyncAxis must be subclassed with '
                'the axes to synchronize included as '
                'components'
                )
        try:
            self.offset_mode = SyncAxisOffsetMode(self.offset_mode)
        except ValueError:
            try:
                self.offset_mode = SyncAxisOffsetMode[self.offset_mode]
            except KeyError:
                raise ValueError(
                    f'Invalid offset_mode: {self.offset_mode}'
                    ) from None
        self._check_info_dict(self.offsets, 'offsets')
        self._check_info_dict(self.scales, 'scales')
        if (self.fix_sync_keep_still is not None
                and self.fix_sync_keep_still not in self.component_names):
            raise ValueError(
                f'Invalid fix_sync_keep_still == {self.fix_sync_keep_still}. '
                'Must match a motor.'
                )

    def _check_info_dict(self, setting, info_kind):
        """Helper function to check that all keys in the dict are Cpts"""
        if setting is not None:
            for attr, _ in setting.items():
                if attr not in self.component_names:
                    raise ValueError(
                        f'Invalid key {attr} in {info_kind}. '
                        'Must match a motor.'
                        )

    def _fill_info_dict(self, setting, default, info_kind):
        """Helper function to fill default values into the dict"""
        if setting is None:
            setting = {}
        elif isinstance(setting, dict):
            setting = copy.copy(setting)
        else:
            raise ValueError(
                f'Invalid {info_kind}: {setting}, must be dict or None')
        for attr in self._real_attrs:
            setting.setdefault(attr, default)
        return setting

    def _setup_offsets(self):
        if not self._has_setup:
            if self.offset_mode == SyncAxisOffsetMode.STATIC_FIXED:
                self._handle_static_fixed()
            elif self.offset_mode == SyncAxisOffsetMode.AUTO_FIXED:
                self._handle_auto_fixed()
            else:
                raise ValueError(f'Invalid offset_mode: {self.offset_mode}')
            self._has_setup = True

    def _handle_static_fixed(self):
        self.offsets = self._fill_info_dict(
            self.offsets, self.default_offset, 'offsets')

    def _handle_auto_fixed(self):
        pos = self.real_position
        first_pos = pos[0]
        self.offsets = {
            fld: float(getattr(pos, fld)) - first_pos for fld in pos._fields}

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate where to move each real motor when the sync moves.

        The calculation is:
        1. Multiply by scale
        2. Add the offset

        Offsets are defined in the class definition.
        """
        self._setup_offsets()
        real_pos = {}
        for attr in self._real_attrs:
            real_pos[attr] = self.forward_single(attr, pseudo_pos.sync)
        return self.RealPosition(**real_pos)

    def forward_single(self, attr, pos):
        """
        Run the forward calculation for a single real motor from the sync pos.

        This gives us the real motor setpoint value for one axis.
        """
        return pos * self.scales[attr] + self.offsets[attr]

    @real_position_argument
    def inverse(self, real_pos):
        """
        Calculate where the sync motor is based on the first real motor.

        The calculation is:
        1. Subtract the offset
        2. Divide by the scale
        """
        self._setup_offsets()
        attr = real_pos._fields[0]
        pos = real_pos[0]
        calc = self.inverse_single(attr, pos)
        return self.PseudoPosition(sync=calc)

    def inverse_single(self, attr, pos):
        """
        Run the inverse calculation on a single real motor value.

        This gives us the sync readback position.
        """
        if isinstance(pos, tuple):
            # Psuedo position tuple, assume first value is correct
            # This happens if we are synchronizing pseudo motors
            pos = pos[0]
        return (pos - self.offsets[attr]) / self.scales[attr]

    def is_synced(self, real_pos=None):
        """
        Check all motor positions for consistency.

        This gets called in status_info if warn_inconsistent is True.
        If the motors are desyncronized greater than the warn_deadband,
        this will return ``False``. Otherwise it will return ``True``.
        """
        if real_pos is None:
            real_pos = self.real_position
        pseudo_calcs = []
        for attr, pos in real_pos._asdict().items():
            calc = self.inverse_single(attr, pos)
            pseudo_calcs.append(calc)
        pick_answer = pseudo_calcs[0]
        for calc in pseudo_calcs:
            if not np.isclose(pick_answer, calc,
                              atol=self.warn_deadband, rtol=0):
                return False
        return True

    def consistency_warning(self):
        """
        Return the consistency warning text
        """
        return (
            f'{self.name} is in an inconsistent state. Call '
            'set_current_position or fix_sync to resolve.'
            )

    def fix_sync(self, confirm=True, wait=True, timeout=10):
        """
        Method to re-synchronize the axes via motion.

        This will move every motor except the one defined by the
        fix_sync_keep_still attribute, which will be used to define the
        correct position.
        """
        anchor = self.fix_sync_keep_still or self._real_attrs[0]

        # Calculate the sync position using anchor
        anchor_pos = getattr(self.real_position, anchor)
        sync_pos = self.inverse_single(anchor, anchor_pos)

        # Calculate the goal positions for every motor
        goal = self.forward(self.PseudoPosition(sync=sync_pos))
        logger.info('Planning to perform the following moves:')
        moves = {}

        for attr, pos in goal._asdict().items():
            if attr == anchor:
                logger.info(f'Keep {attr} at {anchor_pos}')
            else:
                logger.info(f'Move {attr} to {pos}')
                moves[attr] = pos

        if not confirm:
            logger.info('Automatically doing moves because confirm=False')
            do_moves = True
        else:
            do_moves = input('Confirm? (y/n): ').lower().startswith('y')

        if do_moves:
            statuses = []
            for attr, pos in moves.items():
                motor = getattr(self, attr)
                statuses.append(motor.move(pos))
            if wait:
                for status in statuses:
                    status.wait(timeout=timeout)

    def format_status_info(self, status_info):
        """
        Special SyncAxis handling to show all the real motors.
        """
        lines = []
        if self.warn_inconsistent and not status_info['is_synced']:
            lines.append(self.consistency_warning())
        big_name = status_info['name']
        lines.append(f'SyncAxis: {big_name}')
        for attr in self._real_attrs:
            info = status_info[attr]
            name = get_status_value(info, 'name')
            name = name.replace(big_name + '_', '')
            pos = get_status_float(info, 'position', format='g')
            units = get_status_value(info, 'units')
            lines.append(f'{name} position: {pos} [{units}]')
        sync_pos = get_status_float(status_info, 'position', format='g')
        lines.append(f'Sync position: {sync_pos}')
        limits = status_info['limits']
        lines.append(f'Sync limits (low, high): {limits}')
        return '\n'.join(lines)

    def status_info(self):
        """
        Add the limits and sync information
        """
        info = super().status_info()
        info['limits'] = self.sync.limits
        if self.warn_inconsistent:
            try:
                info['is_synced'] = self.is_synced()
            except Exception:
                info['is_synced'] = False
                err = 'Error checking for sync axis consistency.'
                logger.debug(err, exc_info=True)
                logger.error(err)
        return info


class DelayBase(FltMvInterface, PseudoPositioner):
    """
    Laser delay stage to rescale a physical axis to a time axis.

    The optical laser travels along the motor's axis and bounces off a number
    of mirrors, then continues to the destination. In this way, the path length
    of the laser changes, which introduces a variable delay. This delay is a
    simple multiplier based on the speed of light.

    Attributes
    ----------
    delay : ~ophyd.pseudopos.PseudoSingle
        The fake axis. It has configurable units and number of bounces.

    motor : ~ophyd.positioner.PositionerBase
        The real axis. This can be a number of things based on the inheriting
        class, but it must have a valid ``egu`` so we know how to convert to
        the time axis.

    user_offset : ~ophyd.signal.Signal
        An optional offset for the delay.  This must be in the same units as
        `delay`.

    Parameters
    ----------
    prefix : str
        The EPICS prefix of the real motor.

    name : str
        A name to assign to this delay stage.

    egu : str, optional
        The units to use for the delay axis. The default is seconds. Any
        time unit is acceptable.

    n_bounces : int, optional
        The number of times the laser bounces on the delay stage, e.g. the
        number of mirrors that this stage moves. The default is 2, a delay
        branch that bounces the laser back along the axis it enters.

    invert : bool, optional
        If True, increasing the real motor will decrease the delay.
        If False (default), increasing the real motor will increase the delay.
    """

    delay = FCpt(PseudoSingleInterface, egu='{self.egu}', add_prefix=['egu'])
    user_offset = Cpt(NotepadLinkedSignal, ':OphydOffset',
                      notepad_metadata={'record': 'ao', 'default_value': 0.0})
    motor = None

    def __init__(self, *args, egu='s', n_bounces=2, invert=False, **kwargs):
        if self.__class__ is DelayBase:
            raise TypeError(('DelayBase must be subclassed with '
                             'a "motor" component, the real motor to move.'))
        self.n_bounces = n_bounces
        if invert:
            self.n_bounces *= -1
        super().__init__(*args, egu=egu, **kwargs)

    @pseudo_position_argument   # TODO: upstream this fix
    def check_value(self, value):
        return super().check_value(value)

    @user_offset.sub_value
    def _offset_changed(self, value, **kwargs):
        """
        The user offset was changed.  Update the readback value, if possible.
        """
        if not hasattr(self, 'real_position'):
            # A race condition on instantiation can cause this subscription to
            # fire prior to the real position being available.  The position
            # will update based on this offset when available.
            return

        try:
            self._update_position()
        except ophyd.utils.DisconnectedError:
            ...

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """Convert delay unit to motor unit."""
        seconds = convert_unit(pseudo_pos.delay - self.user_offset.get(),
                               self.delay.egu, 'seconds')
        meters = seconds * speed_of_light / self.n_bounces
        motor_value = convert_unit(meters, 'meters', self.motor.egu)
        return self.RealPosition(motor=motor_value)

    @real_position_argument
    def inverse(self, real_pos):
        """Convert motor unit to delay unit."""
        meters = convert_unit(real_pos.motor, self.motor.egu, 'meters')
        seconds = meters / speed_of_light * self.n_bounces
        delay_value = convert_unit(seconds, 'seconds', self.delay.egu)
        return self.PseudoPosition(delay=delay_value + self.user_offset.get())

    def set_current_position(self, position):
        '''
        Calculate and configure the user_offset value, indicating the provided
        ``position`` as the new current position.

        Parameters
        ----------
        position
            The new current position.
        '''
        self.user_offset.put(0.0)
        new_offset = position - self.position[0]
        self.user_offset.put(new_offset)

    def format_status_info(self, status_info):
        """
        Use the renderer from the subdevice
        """
        return self.delay.format_status_info(status_info['delay'])


delay_classes = {}


def delay_class_factory(motor_class):
    """
    Create a subclass of DelayBase that controls a motor of class motor_class.

    Used in delay_instace_factory (DelayMotor), may be useful for one-line
    declarations inside ophyd Devices.
    """
    try:
        cls = delay_classes[motor_class]
    except KeyError:
        cls = type(
            'Delay' + motor_class.__name__,
            (DelayBase,),
            {'motor': Cpt(motor_class, '')}
        )
        delay_classes[motor_class] = cls
    return cls


def delay_instance_factory(
        prefix, motor_class, egu='s', n_bounces=2, invert=False, **kwargs
        ):
    cls = delay_class_factory(motor_class)
    return cls(prefix, egu=egu, n_bounces=n_bounces, invert=invert, **kwargs)


delay_instance_factory.__doc__ = DelayBase.__doc__


class DelayMotor(InterfaceDevice, DelayBase):
    """
    Generic time delay-stage with variable units and number of bounces.

    The optical laser travels along the motor's axis and bounces off a number
    of mirrors, then continues to the destination. In this way, the path length
    of the laser changes, which introduces a variable delay. This delay is a
    simple multiplier based on the speed of light.

    Parameters
    ----------
    motor : `PositionerBase`
        An instantiated motor to transform into a DelayMotor. Will be included
        as a subcomponent in this device. This motor must have a valid
        engineering unit assigned to it in length units.

    name : str, optional
        A name to refer to this `DelayMotor` by. If omitted, will default to
        the motor's name with _delay_motor appended to the end.

    egu : str, optional
        The units to use for the delay axis. The default is seconds. Any
        time unit is acceptable.

    n_bounces : int, optional
        The number of times the laser bounces on the delay stage, e.g. the
        number of mirrors that this stage moves. The default is 2, a delay
        branch that bounces the laser back along the axis it enters.

    invert : bool, optional
        If True, increasing the real motor will decrease the delay.
        If False (default), increasing the real motor will increase the delay.
    """
    motor = ICpt(PositionerBase)

    def __init__(
            self, motor, name=None, egu='s', n_bounces=2, invert=False,
            **kwargs,
            ):
        if name is None:
            name = motor.name + '_delay_motor'
        super().__init__(
            motor.prefix, name=name,
            egu=egu, n_bounces=n_bounces, invert=invert,
            motor=motor, **kwargs,
            )


class SimDelayStage(DelayBase):
    motor = Cpt(FastMotor, init_pos=0, egu='mm')


delay_classes[FastMotor] = SimDelayStage


class LookupTablePositioner(PseudoPositioner):
    """
    A pseudo positioner which uses a look-up table to compute positions.

    Currently supports 1 pseudo positioner and 1 "real" positioner, which
    should be columns of a 2D numpy.ndarray ``table``.

    For additional ``__init__`` arguments, see :class:`ophyd.PseudoPositioner`.

    Parameters
    ----------
    prefix : str
        The EPICS prefix of the real motor.

    name : str
        A name to assign to this delay stage.

    table : np.ndarray
        The table of information.

    column_names : list of str
        List of column names, corresponding to the component attribute names.
        That is, if you have a real motor ``mtr = Cpt(EpicsMotor, ...)``,
        ``"mtr"`` should be in the list of column names of the table.
    """

    table: np.ndarray
    column_names: typing.Tuple[str, ...]
    _table_data_by_name: typing.Dict[str, np.ndarray]

    def __init__(self, *args,
                 table: np.ndarray,
                 column_names: typing.List[str],
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.table = table
        self.column_names = tuple(column_names)
        missing = set()
        for positioner in self._real + self._pseudo:
            if positioner.attr_name not in column_names:
                missing.add(positioner.attr_name)

        if missing:
            raise ValueError(f'Positioners {missing} not present in the table')

        if len(column_names) != self.table.shape[-1]:
            raise ValueError(
                'Incorrect number of column names for the given table.'
            )

        # For now, no fancy interpolation options
        if len(table.shape) != 2:
            raise ValueError(f'Unsupported table dimensions: {table.shape}')

        self._table_data_by_name = {
            column_name: self.table[:, idx]
            for idx, column_name in enumerate(column_names)
        }

        for attr, data in self._table_data_by_name.items():
            obj = getattr(self, attr)
            limits = (np.min(data), np.max(data))
            if isinstance(obj, PseudoSingle):
                obj._limits = limits
            elif hasattr(obj, 'limits'):
                try:
                    obj.limits = limits
                except Exception:
                    self.log.exception('Unable to set limits for %s', obj.name)

    @pseudo_position_argument
    def forward(self, pseudo_pos: tuple) -> tuple:
        '''
        Calculate a RealPosition from a given PseudoPosition

        Must be defined on the subclass.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input, a namedtuple.

        Returns
        -------
        real_position : RealPosition
            The real position output, a namedtuple.
        '''
        values = pseudo_pos._asdict()

        pseudo_field, = self.PseudoPosition._fields
        real_field, = self.RealPosition._fields

        real_value = np.interp(
            values[pseudo_field],
            self._table_data_by_name[pseudo_field],
            self._table_data_by_name[real_field]
        )
        return self.RealPosition(**{real_field: real_value})

    @real_position_argument
    def inverse(self, real_pos: tuple) -> tuple:
        '''Calculate a PseudoPosition from a given RealPosition

        Must be defined on the subclass.

        Parameters
        ----------
        real_position : RealPosition
            The real position input

        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output
        '''
        values = real_pos._asdict()
        pseudo_field, = self.PseudoPosition._fields
        real_field, = self.RealPosition._fields

        pseudo_value = np.interp(
            values[real_field],
            self._table_data_by_name[real_field],
            self._table_data_by_name[pseudo_field]
        )
        return self.PseudoPosition(**{pseudo_field: pseudo_value})


class OffsetMotorBase(FltMvInterface, PseudoPositioner):
    """
    Motor with an offset.
    """
    motor = None
    pseudo_motor = Cpt(PseudoSingleInterface, kind='normal')
    user_offset = Cpt(EpicsSignal, '', kind='normal')

    def __init__(self, prefix, motor_prefix, *args, **kwargs):
        if self.__class__ is OffsetMotorBase:
            raise TypeError('OffsetMotorBase must be subclassed with '
                            'a "motor" component, the real motor to move.')
        self._motor_prefix = motor_prefix
        self._prefix = prefix
        super().__init__(prefix, *args, **kwargs)

    @pseudo_position_argument
    def check_value(self, value):
        return super().check_value(value)

    @user_offset.sub_value
    def _offset_changed(self, value, **kwargs):
        """
        The user offset was changed. Update the readback value, if possible.
        """
        if not hasattr(self, 'real_position'):
            # A race condition on instantiation can cause this subscription to
            # fire prior to the real position being available. The position
            # will update based on this offset when available.
            return

        try:
            # Update the internal position based on the real positioner
            self._update_position()
        except ophyd.utils.DisconnectedError:
            ...

    @pseudo_position_argument
    def forward(self, pseudo_pos: tuple) -> tuple:
        """
        Calculate a RealPosition from a given PseudoPosition.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input, a namedtuple.

        Returns
        -------
        real_pos : RealPosition
            The real position output, a namedtuple.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        motor_value = pseudo_pos.pseudo_motor + self.user_offset.get()
        return self.RealPosition(motor=motor_value)

    @real_position_argument
    def inverse(self, real_pos: tuple) -> tuple:
        """
        Calculate a PseudoPosition from a given RealPosition.

        Parameters
        ----------
        real_pos : RealPosition
            The real position input.

        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output.
        """
        real_pos = self.RealPosition(*real_pos)
        offset = real_pos.motor - self.user_offset.get()
        return self.PseudoPosition(pseudo_motor=offset)

    def set_current_position(self, position):
        '''
        Calculate and configure the user_offset value, indicating the provided
        ``position`` as the new current position.

        Parameters
        ----------
        position : number
            The new current position.
        '''
        self.user_offset.put(0.0)
        new_offset = position - self.position[0]
        self.user_offset.put(new_offset)
