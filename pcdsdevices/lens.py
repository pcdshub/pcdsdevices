"""
Basic Beryllium Lens XFLS
"""
from ophyd.device import Component as Cpt, FormattedComponent as FCpt
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             pseudo_position_argument, real_position_argument)

from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .interface import tweak_base
from .sim import FastMotor


class XFLS(InOutRecordPositioner):
    """
    XRay Focusing Lens (Be)

    This is the simple version where the lens positions are named by number.
    """
    __doc__ += basic_positioner_init

    states_list = ['LENS1', 'LENS2', 'LENS3', 'OUT']
    in_states = ['LENS1', 'LENS2', 'LENS3']
    _lens_transmission = 0.8

    # QIcon for UX
    _icon = 'fa.ellipsis-v'

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

    tab_whitelist = ['tweak', 'align']
    tab_component_names = True

    def __init__(self, x_prefix, y_prefix, z_prefix, *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        super().__init__(x_prefix, *args, **kwargs)

    def tweak(self):
        """
        Calls the tweak function from mv_interface.
        Use left and right arrow keys for the x motor
        and up and down for the y motor.
        Shift and left or right changes the step size.
        Press q to quit.
        """
        tweak_base(self.x, self.y)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        z_pos = pseudo_pos.calib_z
        try:
            pos = [self.x.presets.positions.align_position_one.pos,
                   self.y.presets.positions.align_position_one.pos,
                   self.z.presets.positions.align_position_one.pos,
                   self.x.presets.positions.align_position_two.pos,
                   self.y.presets.positions.align_position_two.pos,
                   self.z.presets.positions.align_position_two.pos]
            x_pos = ((pos[0]-pos[3])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[0]
            y_pos = ((pos[1]-pos[4])/(pos[2]-pos[5]))*(z_pos-pos[2])+pos[1]
            return self.RealPosition(x=x_pos, y=y_pos, z=z_pos)
        except AttributeError:
            self.log.debug('', exc_info=True)
            self.log.error("Please setup the pseudo motor for use by using "
                           "the align() method.  If you have already done "
                           "that, check if the preset pathways have been "
                           "setup.")

    @real_position_argument
    def inverse(self, real_pos):
        return self.PseudoPosition(calib_z=self.z.position)

    def align(self, z_position=None, edge_offset=20):
        """
        Generates equations for aligning the beam based on user input.

        This program uses two points, one made on the lower limit
        and the other made on the upper limit, after the user uses the tweak
        function to put the beam into alignment, and uses those two points
        to make two equations to determine a y- and x-position
        for any z-value the user wants that will keep the beam focused.
        The beam line will be saved in a file in the presets folder,
        and can be used with the pseudo positioner on the z axis.
        If called with an integer, automatically moves the z motor.
        """
        self.z.move(self.z.limits[0] + edge_offset)
        self.tweak()
        pos = [self.x.position, self.y.position, self.z.position]
        self.z.move(self.z.limits[1] - edge_offset)
        print()
        self.tweak()
        pos.extend([self.x.position, self.y.position, self.z.position])
        try:
            self.x.presets.add_hutch(value=pos[0], name="align_position_one")
            self.x.presets.add_hutch(value=pos[3], name="align_position_two")
            self.y.presets.add_hutch(value=pos[1], name="align_position_one")
            self.y.presets.add_hutch(value=pos[4], name="align_position_two")
            self.z.presets.add_hutch(value=pos[2], name="align_position_one")
            self.z.presets.add_hutch(value=pos[5], name="align_position_two")
        except AttributeError:
            self.log.debug('', exc_info=True)
            self.log.error("No folder setup for motor presets. "
                           "Please add a location to save the positions to "
                           "using setup_preset_paths from mv_interface to "
                           "keep the position files.")
            return
        if z_position is not None:
            self.calib_z.move(z_position)


class SimLensStack(LensStack):
    """
    Test version of the lens stack for testing the Be lens class.
    """
    x = Cpt(FastMotor, limits=(-10, 10))
    y = Cpt(FastMotor, limits=(-10, 10))
    z = Cpt(FastMotor, limits=(-100, 100))
