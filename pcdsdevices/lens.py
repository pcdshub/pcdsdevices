"""
Module for Beryllium Lens positioners.
"""
import shutil
import time
from collections import defaultdict
from datetime import date

import numpy as np
import yaml
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             pseudo_position_argument, real_position_argument)
from periodictable import xsf

from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import CombinedInOutRecordPositioner, InOutRecordPositioner
from .interface import tweak_base
from .sim import FastMotor

LENS_RADII = [50e-6, 100e-6, 200e-6, 300e-6, 500e-6, 1000e-6, 1500e-6]


class XFLS(InOutRecordPositioner):
    """
    X-ray Focusing (Be) Lens Stack.

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


class Prefocus(CombinedInOutRecordPositioner):
    """
    PreFocussing Lens Stack (PFLS).

    Positions stack to one of three states or 'OUT' using a combined state
    record controlling an X and a Y motor.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the lens stack.

    name : str
        A name to refer to the device.
    """

    # Clear the default in/out state list. List will be populated during
    # init to grab appropriate state names for each target.
    states_list = []
    # In should be everything except state 0 (Unknown) and state 1 (Out)
    _in_if_not_out = True

    def __init__(self, prefix, *, name, **kwargs):
        # Set default transmission
        # Done this way because states are still unknown at this point
        # Assume that having any target in gives transmission 0.8
        self._transmission = defaultdict(lambda state: 0.8
                                         if state in self.in_states
                                         else (1 if state in self.out_states
                                               else 0))
        super().__init__(prefix, name=name, **kwargs)


class LensStackBase(PseudoPositioner):
    """Class for Be lens macros and safe operations."""
    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')

    calib_z = Cpt(PseudoSingle)
    beam_size = Cpt(PseudoSingle)

    tab_whitelist = ['tweak', 'align']
    tab_component_names = True

    def __init__(self, x_prefix, y_prefix, z_prefix, lens_set=None,
                 z_offset=None, z_dir=None, E=None, att_obj=None,
                 lcls_obj=None, mono_obj=None, beamsize_unfocused=500e-6,
                 *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        self.z_dir = z_dir
        self.z_offset = z_offset
        self.beamsize_unfocused = beamsize_unfocused

        self._E = E
        self._att_obj = att_obj
        self._lcls_obj = lcls_obj
        self._mono_obj = mono_obj
        if lens_set is not None:
            lens_set = list(lens_set)
        self.lens_set = lens_set

        super().__init__(x_prefix, *args, **kwargs)

    def calc_distance_for_size(self, sizeFWHM, lens_set, E=None,
                               fwhm_unfocused=None):
        size = sizeFWHM*2./2.35
        f = self.calc_focal_length(E, lens_set, 'Be', None)
        lam = 12.398/E*1e-10
        # the w parameter used in the usual formula is 2*sigma
        w_unfocused = fwhm_unfocused*2/2.35
        # assuming gaussian beam divergence = w_unfocused/f we can obtain
        waist = lam/np.pi*f/w_unfocused
        rayleigh_range = np.pi*waist**2/lam
        distance = ((np.sqrt((size/waist)**2-1)*np.asarray([-1., 1.])
                     * rayleigh_range) + f)
        return distance

    def tweak(self):
        """
        Calls the tweak function from mv_interface.

        Use left and right arrow keys for the x motor and up and down for
        the y motor.
        Shift and left or right changes the step size.
        Press q to quit.
        """

        tweak_base(self.x, self.y)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        if not np.isclose(pseudo_pos.beam_size, self.beam_size.position):
            beam_size = pseudo_pos.beam_size
            dist = self.calc_distance_for_size(beam_size, self.lens_set,
                                               self._E,
                                               self.beamsize_unfocused)[0]
            z_pos = (dist - self.z_offset) * self.z_dir * 1000
        else:
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
            return self.RealPosition(x=self.x.position, y=self.y.position,
                                     z=z_pos)

    @real_position_argument
    def inverse(self, real_pos):
        dist_m = real_pos.z / 1000 * self.z_dir + self.z_offset
        print('dist_m', dist_m)
        beamsize = self.calc_beam_fwhm(self._E, self.lens_set, distance=dist_m,
                                       material="Be", density=None,
                                       fwhm_unfocused=self.beamsize_unfocused)
        return self.PseudoPosition(calib_z=real_pos.z, beam_size=beamsize)

    def align(self, z_position=None, edge_offset=20):
        """
        Generates equations for aligning the beam based on user input.

        This program uses two points, one made on the lower limit
        and the other made on the upper limit, after the user uses the tweak
        function to put the beam into alignment, and uses those two points
        to make two equations to determine a y- and x-position
        for any z-value the user wants that will keep the beam focused.
        The beam line will be saved in a file in the presets folder,
        and can be used with the pseudo positioner on the z-axis.
        If called with an integer, automatically moves the z-motor.
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

    @pseudo_position_argument
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        if self._make_safe() is True:
            return super().move(position, wait=wait, timeout=timeout,
                                moved_cb=moved_cb)

    def get_delta(self, E, material="Be", density=None):
        delta = 1-np.real(xsf.index_of_refraction(material, density=density,
                          energy=E))
        return delta

    def calc_focal_length(self, E, lens_set, material="Be", density=None):
        # lens_set = (n1,radius1,n2,radius2,...)
        num = []
        rad = []
        ftot_inverse = 0
        for i in range(len(lens_set)//2):
            num = lens_set[2*i]
            rad = lens_set[2*i+1]
            if rad is not None:
                rad = float(rad)
                num = float(num)
                fln = self.calc_focal_length_for_single_lens(E, rad,
                                                             material,
                                                             density)
                ftot_inverse += num/fln
        return 1./ftot_inverse

    def calc_focal_length_for_single_lens(self, E, radius,
                                          material="Be", density=None):
        delta = self.get_delta(E, material, density)
        f = (radius/2)/delta
        return f

    def calc_beam_fwhm(self, E, lens_set, distance=None, material="Be",
                       density=None, fwhm_unfocused=None, printsummary=True):
        f = self.calc_focal_length(E, lens_set, material, density)
        lam = 1.2398/E*1e-9
        # the w parameter used in the usual formula is 2*sigma
        w_unfocused = fwhm_unfocused*2/2.35
        # assuming gaussian beam divergence = w_unfocused/f we can obtain
        waist = lam/np.pi*f/w_unfocused
        rayleigh_range = np.pi*waist**2/lam
        size = waist*np.sqrt(1.+(distance-f)**2./rayleigh_range**2)
        if printsummary:
            print("FWHM at lens   : %.3e" % (fwhm_unfocused))
            print("waist          : %.3e" % (waist))
            print("waist FWHM     : %.3e" % (waist*2.35/2.))
            print("rayleigh_range : %.3e" % (rayleigh_range))
            print("focal length   : %.3e" % (f))
            print("size           : %.3e" % (size))
            print("size FWHM      : %.3e" % (size*2.35/2.))
        return size*2.35/2

    def _make_safe(self):
        """
        Move the thickest attenuator in to prevent damage due to wayward
        focused x-rays. Return `True` if the attenuator was moved in.
        """
        if self._att_obj is None:
            print("WARNING: Cannot do safe crl moveZ,\
                       no attenuator object provided.")
            return False
        filt, thk = self._att_obj.filters[0], 0
        for f in self._att_obj.filters:
            t = f.thickness.get()
            if t > thk:
                filt, thk = f, t
        if not filt.inserted:
            filt.insert()
            time.sleep(0.01)
        if filt.inserted:
            print("REMINDER: Beam stop attenuator moved in!")
            safe = True
        else:
            print("WARNING: Beam stop attenuator did not move in!")
            safe = False
        return safe


class LensStack(LensStackBase):
    def __init__(self, *args, path, **kwargs):
        self.path = path
        lens_set = self.read_lens()
        super().__init__(*args, lens_set=lens_set, **kwargs)

    def read_lens(self):
        with open(self.path, 'r') as f:
            read_data = yaml.safe_load(f)
        return read_data

    def create_lens(self, lens_set, make_backup=True):
        # Make a backup with today's date
        if make_backup:
            shutil.copyfile(self.path, self.backup_path)
        with open(self.path, "w") as f:
            yaml.dump(self.lens_set, f)

    @property
    def backup_path(self):
        return self.path + str(date.today()) + '.bak'


class SimLensStackBase(LensStackBase):
    """Test version of the lens stack for testing the Be lens class."""
    x = Cpt(FastMotor, limits=(-10, 10))
    y = Cpt(FastMotor, limits=(-10, 10))
    z = Cpt(FastMotor, limits=(-100, 100))


class SimLensStack(SimLensStackBase, LensStack):
    pass
