import logging

from ophyd.device import Component as Cpt
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             real_position_argument, pseudo_position_argument)

logger = logging.getLogger(__name__)


class SyncAxesBase(PseudoPositioner):
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
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        real_pos = {}
        for axis, offset in self._offsets.items():
            real_pos[axis] = pseudo_pos.pseudo + offset
        return self.RealPosition(**real_pos)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Combined axis readback is the mean of the composite axes
        """
        real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(pseudo=self.calc_combined(real_pos))
