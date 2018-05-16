import numpy as np
from ophyd.device import Component as Cpt
from ophyd.pseudopos import PseudoPositioner, PseudoSingle


class SyncAxesBase(PseudoPositioner):
    """
    Synchronized Axes.

    This will move all axes to the same position at the same time. And report
    its position as the average value of all axes.

    Attributes
    ----------
    axes: ``list of str``
        Names of the components that correspond to the real axes.
    """
    pseudo = Cpt(PseudoSingle)

    def forward(self, pseudo_pos):
        """
        Composite axes all move to the combined axis position
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        return self.RealPosition(**{axis: pseudo_pos.pseudo
                                    for axis in self.axes})

    def inverse(self, real_pos):
        """
        Combined axis readback is the mean of the composite axes
        """
        real_pos = self.RealPosition(*real_pos)
        return self.PseudoPosition(pseudo=np.mean(real_pos))

    @property
    def position(self):
        return super().position.pseudo


def SyncAxes(*args, **kwargs):
    """
    Create and instantiate a `SyncAxesBase` subclass with the desired
    components.
    """
    if 'axes' in kwargs:
        raise ValueError(('axes is a reserved name for SyncAxes and cannot be '
                          'a component name or a kwarg'))
    cpt = {}
    kwd = {}

    for key, value in kwargs.items():
        if isinstance(value, Cpt):
            cpt[key] = value
        else:
            kwd[key] = value
    cpt['axes'] = list(cpt.keys())

    cls = type('SyncAxes', (SyncAxesBase,), cpt)
    return cls(*args, **kwd)
