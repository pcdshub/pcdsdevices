"""
Basic Beryllium Lens XFLS
"""
import time
import numpy as np
import yaml
import os.path
import shutil

from shutil import copyfile
from datetime import date

from ophyd.device import Component as Cpt, FormattedComponent as FCpt
from ophyd.pseudopos import (PseudoPositioner, PseudoSingle,
                             pseudo_position_argument, real_position_argument)

from periodictable import xsf

from .attenuator import Attenuator
from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .mv_interface import tweak_base
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

    def __init__(self, prefix, *, name, **kwargs):
        # Set a default transmission, but allow easy subclass overrides
        for state in self.in_states:
            self._transmission[state] = self._lens_transmission
        super().__init__(prefix, name=name, **kwargs)


class LensStackBase(PseudoPositioner):
    """
    Class for Be lens macros and safe operations.
    """
    lensRadii2D = [50e-6, 100e-6, 200e-6, 300e-6, 500e-6, 1000e-6, 1500e-6]

    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')

    calib_z = Cpt(PseudoSingle)

    def __init__(self, x_prefix, y_prefix, z_prefix, lensset=None,
                 _zoffset=None, zdir=None, E=None, attObj=None, lclsObj=None,
                 monoObj=None, beamsizeUnfocused=500e-6, *args, **kwargs):
        self.x_prefix = x_prefix
        self.y_prefix = y_prefix
        self.z_prefix = z_prefix
        self._zdir = zdir
        self._zoffset = _zoffset
        self.beamsizeUnfocused = beamsizeUnfocused

        self._E = E
        self._attObj = attObj
        self._lclsObj = lclsObj
        self._monoObj = monoObj
        self.lensset = lensset

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

    def align(self, z_position=None):
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
        self.z.move(self.z.limits[0])
        self.tweak()
        pos = [self.x.position, self.y.position, self.z.position]
        self.z.move(self.z.limits[1])
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

    def getDelta(self,E, material="Be", density=None):
        delta = 1-np.real(xsf.index_of_refraction(material, density=density,
                          energy=E))
        return delta

    def set_E(self, energy):
        self._E = energy

    def _moveBeamsize(self, size, safe=True, lensset=None):
        """
        Change the beamsize at the sample location.
        """
        if None in (self._zoffset, self._zdir, self.beamsizeUnfocused):
            print("Cannot move beamsize. At least one of",
                  "zoffset, zdir, beamsizeUnfocused not defined at init.")
        else:
            dist = self.calcDistanceForSize(size, lensset,
                        self._E, fwhm_unfocused=self.beamsizeUnfocused)[0]
            self._moveZ((dist - self._zoffset) * self._zdir * 1000,
                            safe=safe)

    def _whereBeamsize(self, lensset):
        """
        Return the beamsize at the sample location.
        """
        if None in (self._zoffset, self._zdir, self.beamsizeUnfocused):
            print("Cannot check beamsize. At least one of", \
                  "zoffset, zdir, beamsizeUnfocused was not defined at init.")
        else:
            dist_m = self.z.wm() /1000 * self._zdir + self._zoffset
            return self.calcBeamFWHM(self._E, lensset, distance=dist_m, material="Be",
                                density=None, fwhm_unfocused=self.beamsizeUnfocused)


    def calcFocalLength(self, E, lensset, material="Be", density=None):
        # lens_set = (n1,radius1,n2,radius2,...)
        num = []
        rad = []
        ftot_inverse = 0 
        for i in range(len(lensset)//2):
            num = lensset[2*i]
            rad = lensset[2*i+1]
            if rad is not None:
                rad = float(rad)
                num = float(num)
                ftot_inverse += num/self.calcFocalLengthForSingleLens(E, rad, material, density)
        return 1./ftot_inverse

    def calcFocalLengthForSingleLens(self, E, radius,
                                     material="Be", density=None):
        delta = self.getDelta(E, material, density)
        f = (radius/2)/delta
        return f

    def calcDistanceForSize(self, sizeFWHM, lensset, E=None,
                            fwhm_unfocused=None):
        size = sizeFWHM*2./2.35
        f = self.calcFocalLength(E, lensset, 'Be', None)
        lam = 12.398/E*1e-10
        # the w parameter used in the usual formula is 2*sigma
        w_unfocused = fwhm_unfocused*2/2.35
        # assuming gaussian beam divergence = w_unfocused/f we can obtain
        waist = lam/np.pi*f/w_unfocused
        rayleigh_range = np.pi*waist**2/lam
        distance = ((np.sqrt((size/waist)**2-1)*np.asarray([-1., 1.])
                        * rayleigh_range) + f)
        return distance

    def _moveZ(self, pos, safe=True):
        """
        Moves z to pos and x and y to their calibrated offset positions.
        If safe is True, we call ._makeSafe().
        """
        if safe:
            is_safe = self._makeSafe()
            if not safe or is_safe:
                if calib_z is None:
                    self.z.move(pos)
                else:
                    calib_z = self.align()
                    dz = pos - calib_z["z_ref"]
                    self.z.move(pos)
                    self.x.move(calib_z["x_ref"] + calib_z["dx"] * dz)
                    self.y.move(calib_z["y_ref"] + calib_z["dy"] * dz)
        else:
            print("crl moveZ ABORTED!")

    def calcBeamFWHM(self, E, lensset, distance=None, material="Be", density=None,
                     fwhm_unfocused=None,printsummary=True):
        f = self.calcFocalLength(E, lensset, material, density)
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


    def _makeSafe(self):
        """
        Move the thickest attenuator in to prevent damage
        due to wayward focused x-rays.
        Return True if the attenuator was moved in.
        """
        if self._attObj is None:
            print("WARNING: Cannot do safe crl moveZ,\
                       no attenuator object provided.")
            return False
        filt, thk = self._attObj.filters[0], 0
        for f in self._attObj.filters:
            t = f.thickness.get()
            if t > thk:
                filt, thk = f, t
        if not filt.inserted:
            filt.insert()
            time.sleep(0.01)
           # filt.wait
        if filt.inserted:
            print("REMINDER: Beam stop attenuator moved in!")
            safe = True
        else:
            print("WARNING: Beam stop attenuator did not move in!")
            safe = False
        return safe


class LensStack(LensStackBase):
    def __init__(self, *args, *, path, **kwargs):
        self.path = path + '.yaml'
        lensset = self.ReadLens()
        super().__init__(*args, lensset=lensset, **kwargs)

    def ReadLens(self):
        with open(self.path, 'r') as f:
            read_data = yaml.load(f)
            # [float(i) for i in read_data]
        return read_data

    def CreateLens(self, lensset):
        # [float(i) for i in lensset]
        shutil.copyfile(self.path, self.path + str(date.today()))
        with open(name, "w") as f:
            yaml.dump(self.path, f)


class SimLensStackBase(LensStackBase):
    """
    Test version of the lens stack for testing the Be lens class.
    """
    x = Cpt(FastMotor, limits=(-10, 10))
    y = Cpt(FastMotor, limits=(-10, 10))
    z = Cpt(FastMotor, limits=(-100, 100))


class SimLensStack(SimLensStackBase, LensStack):
    pass
