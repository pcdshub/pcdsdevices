"""

This module contains a generic class to handle a simple n-axis device
"""

from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


MAX_AXIS = 20 # seems reasonable for now, but can be increased if needed


class N_axis(BaseInterface, Device):
    def __init__(self, prefix, name, **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.axis = []
        for ii in range(1,MAX_AXIS+1):
            try:
                self.axis.append(getattr(self, 'm{}'.format(ii)))
            except AttributeError:
                break
        return
    

def _make_axs_classes(max_axis, name):
    """Generate all possible subclasses for n_axis=1..max_axis"""
    axs_classes = {}
    for i in range(1, max_axis+1):
        axs = {}
        for n in range(1, i+1):
            comp = Cpt(BeckhoffAxis, ':MMS:{:02d}'.format(n), kind='normal')
            axs['m{}'.format(n)] = comp
        
        cls_name = '{}{}'.format(name, i)
        cls = type(cls_name, (N_axis,), axs)
        cls.num_axis = i
        axs_classes[i] = cls
    return axs_classes

_axs_classes = _make_axs_classes(MAX_AXIS, 'n_axis_')


def get_n_axis_device(prefix, n_axis, *args, name, **kwargs):
    cls = _axs_classes[n_axis]
    return cls(prefix, name=name, **kwargs)




