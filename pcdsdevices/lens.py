"""
Basic Beryllium Lens XFLS
"""
# flake8: noqa
from ophyd.device import Component as Cpt, FormattedComponent as FCpt, Device
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             pseudo_position_argument, real_position_argument)

from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .mv_interface import setup_preset_paths

class XFLS(InOutRecordPositioner):
    """
    XRay Focusing Lens (Be)

    This is the simple version where the lens positions are named by number.
    """
    __doc__ += basic_positioner_init

    states_list = ['LENS1', 'LENS2', 'LENS3', 'OUT']
    in_states = ['LENS1', 'LENS2', 'LENS3']
    _lens_transmission = 0.8

    def __init__(self, prefix, *, name, **kwargs):
        # Set a default transmission, but allow easy subclass overrides
        for state in self.in_states:
            self._transmission[state] = self._lens_transmission
        super().__init__(prefix, name=name, **kwargs)


# Change into PseudoPositioner when it's time to add the calculations
class LensStack(Device):
    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')

    def __init__(self, x_prefix, y_prefix, z_prefix, *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        super().__init__(x_prefix, *args, **kwargs)

    def allign_move(self,z_pos=None):
        """
        Uses the positions from allign function to move the LensStack
        to an alligned position at the given z_pos.
        This is automatically called at the end of allign,
        but can also be called independantly to bypass the allignment itself.
        """
        setup_preset_paths(hutch='presets',exp='presets')
        pos = [self.x.presets.positions.entry.pos,
               self.y.presets.positions.entry.pos,
               self.z.presets.positions.entry.pos,
               self.x.presets.positions.exit.pos,
               self.y.presets.positions.exit.pos,
               self.z.presets.positions.exit.pos]
        self.x.move(((pos[0]-pos[3])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[0])
        self.y.move(((pos[1]-pos[4])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[1])
        self.z.move(z_pos)

    def allign(self,z_position=None):
        """
        Generates equations for alligning the beam based on user input.

        This program uses two points, one made on the lower limit
        and the other made on the upper limit, after the user uses tweak function 
        to put the beam into alignment, and uses those two points
        to make two equations to determine a y- and x-position
        for any z-value the user wants that will keep the beam focused.
        The beam line will be saved in a file in the presets folder,
        and can be reused with allign_move
        """
        setup_preset_paths(hutch='presets',exp='presets')
        self.z.move(self.z.limits[0])
        self.x.tweak(self.y)
        pos = [self.x.position,self.y.position,self.z.position]
        self.z.move(self.z.limits[1])
        print()
        self.x.tweak(self.y)
        pos.extend([self.x.position,self.y.position,self.z.position])
        self.x.presets.add_hutch(value=pos[0],name="entry")
        self.x.presets.add_hutch(value=pos[3],name="exit")
        self.y.presets.add_hutch(value=pos[1],name="entry")
        self.y.presets.add_hutch(value=pos[4],name="exit")
        self.z.presets.add_hutch(value=pos[2],name="entry")
        self.z.presets.add_hutch(value=pos[5],name="exit")
        allign_move(z_position)
