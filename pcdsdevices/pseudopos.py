from ophyd.device import Component as Cpt
from ophyd.pseudopos import PseudoPositioner, PseudoSingle


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


    Parameters
    ----------
    position_mode: ``func``, optional
        The function to apply to the list of current positions to determine
        the combined position. By default, this is the minimum of all axis
        positions.
    """
    pseudo = Cpt(PseudoSingle)

    _default_mode = min

    def __init__(self, *args, position_mode=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._mode = position_mode or self._default_mode
        self._offsets = {}

    def save_offsets(self):
        """
        Save the current offsets for the synchronized assembly.

        If not done earlier, this will be automatically run before it is first
        needed (generally, right before the first move).
        """
        pos = self.real_position
        combo = self._mode(pos)
        offsets = {fld: getattr(pos, fld) - combo for fld in pos._fields}
        for fld in self.RealPosition._fields:
            if fld not in offsets:
                offsets[fld] = self._offsets.get(fld, 0)
        self._offsets = offsets

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

    def inverse(self, real_pos):
        """
        Combined axis readback is the mean of the composite axes
        """
        real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(pseudo=self._mode(real_pos))
