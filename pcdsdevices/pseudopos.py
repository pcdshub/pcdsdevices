import logging

from ophyd.device import Component as Cpt, FormattedComponent as FCpt
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             real_position_argument, pseudo_position_argument)
from scipy.constants import speed_of_light

from .sim import FastMotor
from .utils import convert_unit
from .interface import FltMvInterface

logger = logging.getLogger(__name__)


class SyncAxesBase(PseudoPositioner, FltMvInterface):
    """
    Synchronized Axes.

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

    Like all ``PseudoPositioner`` classes, any subclass of ``PositionerBase``
    will be included in the synchronized move.
    """
    pseudo = Cpt(PseudoSingle)

    def __init__(self, *args, **kwargs):
        if self.__class__ is SyncAxesBase:
            raise TypeError(('SyncAxesBase must be subclassed with '
                             'the axes to synchronize included as '
                             'components'))
        super().__init__(*args, **kwargs)
        self._offsets = {}

    def calc_combined(self, real_position):
        """
        Calculate the combined pseudo position.

        By default, this is just the position of our first axis.

        Parameters
        ----------
        real_position: `namedtuple`
            The positions of each of the real motors, accessible by name

        Returns
        -------
        pseudo_position: ``float``
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
        combo = self.calc_combined(pos)
        offsets = {fld: getattr(pos, fld) - combo for fld in pos._fields}
        self._offsets = offsets
        logger.debug('Offsets %s cached', offsets)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Composite axes move to the combined axis position plus an offset
        """
        if not self._offsets:
            self.save_offsets()
        real_pos = {}
        for axis, offset in self._offsets.items():
            real_pos[axis] = pseudo_pos.pseudo + offset
        return self.RealPosition(**real_pos)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Combined axis readback is the mean of the composite axes
        """
        return self.PseudoPosition(pseudo=self.calc_combined(real_pos))


class DelayBase(PseudoPositioner, FltMvInterface):
    """
    Laser delay stage to rescale a physical axis to a time axis.

    The optical laser travels along the motor's axis and bounces off a number
    of mirrors, then continues to the destination. In this way, the path length
    of the laser changes, which introduces a variable delay. This delay is a
    simple multiplier based on the speed of light.

    Attributes
    ----------
    delay: ``PseudoSingle``
        The fake axis. It has configurable units and number of bounces.

    motor: ``PositionerBase``
        The real axis. This can be a number of things based on the inheriting
        class, but it must have a valid ``egu`` so we know how to convert to
        the time axis.

    Parameters
    ----------
    prefix: ``str``
        The EPICS prefix of the real motor

    name: ``str``, required keyword
        A name to assign to this delay stage.

    egu: ``str``, optional
        The units to use for the delay axis. The default is seconds. Any
        time unit is acceptable.

    n_bounces: ``int``, optional
        The number of times the laser bounces on the delay stage, e.g. the
        number of mirrors that this stage moves. The default is 2, a delay
        branch that bounces the laser back along the axis it enters.
    """
    delay = FCpt(PseudoSingle, egu='{self.egu}', add_prefix=['egu'])
    motor = None

    def __init__(self, *args, egu='s', n_bounces=2, **kwargs):
        if self.__class__ is DelayBase:
            raise TypeError(('DelayBase must be subclassed with '
                             'a "motor" component, the real motor to move.'))
        self.n_bounces = n_bounces
        super().__init__(*args, egu=egu, **kwargs)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Convert delay unit to motor unit
        """
        seconds = convert_unit(pseudo_pos.delay, self.delay.egu, 'seconds')
        meters = seconds * speed_of_light / self.n_bounces
        motor_value = convert_unit(meters, 'meters', self.motor.egu)
        return self.RealPosition(motor=motor_value)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Convert motor unit to delay unit
        """
        meters = convert_unit(real_pos.motor, self.motor.egu, 'meters')
        seconds = meters / speed_of_light * self.n_bounces
        delay_value = convert_unit(seconds, 'seconds', self.delay.egu)
        return self.PseudoPosition(delay=delay_value)


class SimDelayStage(DelayBase):
    motor = Cpt(FastMotor, init_pos=0, egu='mm')


class PseudoSingleInterface(PseudoSingle, FltMvInterface):
    """
    PseudoSingle with FltMvInterface mixed in
    """
    pass
