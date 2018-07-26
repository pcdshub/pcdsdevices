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
from .mv_interface import setup_preset_paths,tweak_base

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

class LensStack(PseudoPositioner):
    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')
    
    calib_z = Cpt(PseudoSingle)

    def __init__(self, x_prefix, y_prefix, z_prefix, *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        super().__init__(x_prefix, *args, **kwargs)

    def tweak(self):
        """
        Calls the tweak function from mv_interface
        with the x and y motors.
        """
        tweak_base(self.x,self.y)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        z_pos = pseudo_pos.calib_z
        setup_preset_paths(hutch='presets',exp='presets')
        pos = [self.x.presets.positions.entry.pos,
               self.y.presets.positions.entry.pos,
               self.z.presets.positions.entry.pos,
               self.x.presets.positions.exit.pos,
               self.y.presets.positions.exit.pos,
               self.z.presets.positions.exit.pos]
        x_pos = ((pos[0]-pos[3])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[0]
        y_pos = ((pos[1]-pos[4])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[1]
        return self.RealPosition(x = x_pos, y = y_pos, z = z_pos)

    @real_position_argument
    def inverse(self, real_pos):
        return self.PseudoPosition(calib_z = self.z.position)

    def align(self,z_position=None):
        """
        Generates equations for aligning the beam based on user input.

        This program uses two points, one made on the lower limit
        and the other made on the upper limit, after the user uses tweak function 
        to put the beam into alignment, and uses those two points
        to make two equations to determine a y- and x-position
        for any z-value the user wants that will keep the beam focused.
        The beam line will be saved in a file in the presets folder,
        and can be used with the pseudo positioner on the z axis.
        """
        setup_preset_paths(hutch='presets',exp='presets')
        self.z.move(self.z.limits[0])
        self.tweak()
        pos = [self.x.position,self.y.position,self.z.position]
        self.z.move(self.z.limits[1])
        print()
        self.tweak()
        pos.extend([self.x.position,self.y.position,self.z.position])
        self.x.presets.add_hutch(value=pos[0],name="entry")
        self.x.presets.add_hutch(value=pos[3],name="exit")
        self.y.presets.add_hutch(value=pos[1],name="entry")
        self.y.presets.add_hutch(value=pos[4],name="exit")
        self.z.presets.add_hutch(value=pos[2],name="entry")
        self.z.presets.add_hutch(value=pos[5],name="exit")
        self.calib_z.move(z_position)
