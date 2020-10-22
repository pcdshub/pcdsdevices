"""
Module for Beryllium Lens positioners.
"""
import time
from collections import defaultdict
from datetime import date
import logging
import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt
from pcdscalc import be_lens_calcs as calcs

from .doc_stubs import basic_positioner_init
from .epics_motor import IMS
from .inout import CombinedInOutRecordPositioner, InOutRecordPositioner
from .interface import BaseInterface, tweak_base
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .sim import FastMotor

logger = logging.getLogger(__name__)

# Set of Be lenses with thicknesses.
LENS_RADII = calcs.LENS_RADII


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


class LensStackBase(BaseInterface, PseudoPositioner):
    """
    Class for Be lens macros and safe operations.

    x, y, z: real motors that move the position of the lens set
    calib_z, beam_size pseudo motors

    An ophyd PseudoPositioner relates one or more pseudo (virtual) axes to one
    or more real (physical) axes via forward and inverse calculations.

    The purpose of this class is using the motor that moves the z stage of
    BeLensStack so that we can scan the focal size. What needs to be done is
    move the x motor and then the combination motor that when the z motor moves
    we also move the x and y to compensate for the stage not beign perfect.

    What do we usually do:
    For each lens pack that is in, tweak x and y until the fixture on YAG
    screen is as pretty as it can be - save this position.
    Move the z motor on one extreem to the furthest upstream position, and
    then figure out the optimal x and y for each lens pack.
    Move the motor to the other side, the most downstream side and do the same
    thing. Save the x and y here as well.

    So this focus motor, moves three motors in combination. The z is used for
    the main calculations records, to get a focal spot size, and x
    and y are moved based on the tweak that was done at the beginning.

    In general, it saves an x, y, z at the ends of motion, the idea being that
    the beam is a line that is not colinear with any one axis, so we draw a
    line in 3D space to follow the center of the beam.

    The scientist workflow is basically the same as before: you call one
    function (align) with low beam to find the centers of the lenses, then you
    have two pseudo motors (calib_z, beam_size) that magically put the lens in
    the right spot.

    Notes
    -----
    Use `pcdscalc.be_lens_cals.configure_defaults` function to set some default
    parameters used in some calculations for different hutches.
    Use `pcdscalc.set_lens_set_to_file` to set the lens sets file
    """
    x = FCpt(IMS, '{self.x_prefix}')
    y = FCpt(IMS, '{self.y_prefix}')
    z = FCpt(IMS, '{self.z_prefix}')

    calib_z = Cpt(PseudoSingleInterface)
    beam_size = Cpt(PseudoSingleInterface)

    tab_whitelist = ['tweak', 'align', 'calib_z', 'beam_size', 'create_lens',
                     'read_lens']
    tab_component_names = True

    # TODO: do we want these guys to be None? it seems like if they
    # are None calculations fail - at least z_offset and z_dir should
    # probably not be None
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

    def tweak(self):
        """
        Call the tweak function from `pcdsdevice.interface`.

        Use the Left arrow to move x motor left.
        Use the Right arrow to move x motor right.
        Use the Down arrow to move y motor down.
        Use the Up arrow to move y motor up.
        Use Shift & Up arrow to scale*2.
        Use Shift & Down arrow to scale/2.
        Press q to quit.
        """
        tweak_base(self.x, self.y)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Run a forward(pseudo -> real) calculation.

        Calculate a RealPosition from a given PseudoPosition.
        `calc_distance_for_size` calculates distance for beam size (fwhm size)

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            Pseudo position to move to.

        Returns
        -------
            RealPosition

        Raises
        ------
        AttributeError
            If pseudo motor is not setup for use.
        """
        if not np.isclose(pseudo_pos.beam_size, self.beam_size.position):
            beam_size = pseudo_pos.beam_size
            dist = calcs.calc_distance_for_size(beam_size, self.lens_set,
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
                           "the align() method. If you have already done that,"
                           " check if the preset pathways have been setup.")
            return self.RealPosition(x=self.x.position, y=self.y.position,
                                     z=z_pos)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Run an inverse (real -> pseudo) calculation.

        `calc_beam_fwhm` returns fwhm (Full width at half maximum) size for
        certain lenses configuration and energy at a given distance.

        Parameters
        ----------
        real_pos : RealPosition

        Returns
        -------
            PseudoPosition
        """
        dist_m = real_pos.z / 1000 * self.z_dir + self.z_offset
        logger.info('dist_m %s', dist_m)
        beamsize = calcs.calc_beam_fwhm(self._E, self.lens_set,
                                        distance=dist_m,
                                        material="Be", density=None,
                                        fwhm_unfocused=self.beamsize_unfocused)
        return self.PseudoPosition(calib_z=real_pos.z, beam_size=beamsize)

    def align(self, z_position=None, edge_offset=20):
        """
        Generate equations for aligning the beam based on user input.

        This program uses two points, one made on the lower limit
        and the other made on the upper limit, after the user uses the tweak
        function to put the beam into alignment, and uses those two points
        to make two equations to determine a y- and x-position
        for any z-value the user wants that will keep the beam focused.
        The beam line will be saved in a file in the presets folder,
        and can be used with the pseudo positioner on the z-axis.
        If called with an integer, automatically moves the z-motor.

        Parameters
        ----------
        z_position : number, optional
        edge_offset : number, optional

        Notes
        ----
        Macro for calibration. Steps:

        1. Make safe

        2. Save z pos

        3. Move z, x to previous reference position

        4. Move y to preset corresponding to lenssetNo,
           or don't move it if left as None

        5. call .align() to align x and y with beam

        6. save reference position

        7. move z by dz, call .align() to align x and y with beam

        8. save trajectory as dx and dy

        9. return to original z pos, but aligned with the beam
        """

        self.z.move(self.z.limits[0] + edge_offset)
        self.tweak()
        pos = [self.x.position, self.y.position, self.z.position]
        self.z.move(self.z.limits[1] - edge_offset)
        print()
        self.tweak()
        pos.extend([self.x.position, self.y.position, self.z.position])
        try:
            # create presets
            self.x.presets.add_hutch(value=pos[0], name="align_position_one")
            self.x.presets.add_hutch(value=pos[3], name="align_position_two")
            self.y.presets.add_hutch(value=pos[1], name="align_position_one")
            self.y.presets.add_hutch(value=pos[4], name="align_position_two")
            self.z.presets.add_hutch(value=pos[2], name="align_position_one")
            self.z.presets.add_hutch(value=pos[5], name="align_position_two")
        except AttributeError:
            self.log.debug('', exc_info=True)
            self.log.error('No folder setup for motor presets. '
                           'Please add a location to save the positions to '
                           'using setup_preset_paths from '
                           'pcdsdevices.interface to keep the position files.')
            return
        if z_position is not None:
            self.calib_z.move(z_position)

    @pseudo_position_argument
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        """
        Move to a specified position, optionally waiting for motion to
        complete.

        Moves z to pos and x and y to their calibrated offset positions.
        If safe is True, then `._make_safe()` gets called
        TODO: should i have a `safe` attribute here like the old code?

        Parameters
        ----------
        position
            Pseudo position to move to.
        wait : bool, optional
            Defaults to True
        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used.
        moved_cb : callable
            Call this callback when movement has finished. This callback must
            accept one keyword argument: 'obj' which will be set to this
            positioner instance.
        """
        if self._make_safe() is True:
            return super().move(position, wait=wait, timeout=timeout,
                                moved_cb=moved_cb)
        else:
            logger.warning('Aborting moving for safety.')
            return

    def _make_safe(self):
        """
        Move the thickest attenuator in to prevent damage due to wayward
        focused x-rays.

        Returns
        -------
        safe : bool
            Return `True` if the attenuator was moved in.
        """
        if self._att_obj is None:
            logger.warning('Cannot do safe moveZ, no attenuator'
                           ' object provided.')
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
            logger.info('Beam stop attenuator moved in!')
            safe = True
        else:
            logger.warning('Beam stop attenuator did not move in!')
            safe = False
        return safe


class LensStack(LensStackBase):
    """
    Class for Be lens.

    Parameters
    ----------
    x_prefix : str
        The EPICS prefix that identifies the x motor.
    y_prefix : str
        The EPICS prefix that identifies the y motor.
    z_prefix : str
        The EPICS prefix that identifies the z motor.
    lens_set : list, optional
        List of lens sets. e.g. [numer1, lensthick1, number2, lensthick2...]
    z_offset : number
        Distance from sample to lens_z=0 in meters.
    z_dir : number
        1 or -1, represents beam direction wrt z direction.
    E: number, optional
        Beam energy
    att_obj : attenuator object, optional
    lcls_obj
        Object that gets PVs from lcls (for energy)
    mono_obj
        Object that gets energy from monochromator
    beamsize_unfocused : float, optional
        Radial size of x-ray beam before focusing.
    path : str
        Path to the file that defines which lenses are being used.

    Examples
    --------

    Provide the path of the be lens set file:

    >>> path = '../path/to/lens_set'

    If no lens sets are added in the file yet, use the
    `be_lens_calcs.set_lens_set_to_file` function to set the lens sets:

    >>> sets_list_of_tuples = [[3, 0.0001, 1, 0.0002],
                               [1, 0.0001, 1, 0.0003, 1, 0.0005],
                               [2, 0.0001, 1, 0.0005]]
    >>> set_lens_set_to_file(sets_list_of_tuples, '../path/to/lens_set.npy')

    Create the LensStack() object by providing the x, y and z `prefixes`, as
    well as all the other paramters:

    >>> be_stack = LensStack(path=path, x_prefix='X:PREF', y_prefix='Y:PREF',
        z_prefix='Z:PREF', z_offset=2, z_dir=0.2, E=8, name='be_stack')

    Now you can use the `be_stack` object to tweak the motors:

    >>> be_stack.tweak()
    sim_x: -0.1000, sim_y: 0.2000, scale: 0.1
    Left: move x motor left
    Right: move x motor right
    Down: move y motor down
    Up: move y motor up
    + or Shift_Up: scale*2
    - or Shift_Down: scale/2
    Press q to quit. Press any other key to display this message.

    You can then call the `align()` function to create presets

    >>> be_stack.align(z_position=0.001)

    You might get a warning: 'No folder setup for motor presets. Please add a
    location to save the positions to using setup_preset_paths from
    pcdsdevices.interface to keep the position files'.

    TODO: to be continues and revised...

    """
    def __init__(self, *args, path, **kwargs):

        self.path = path
        self.lens_pack = self.read_lens()
        lens_set = calcs.get_lens_set(1, self.path)
        # TODO: get a lens set, need a number ?
        # lens_set = calcs.get_lens_set(1, self.path) # self.read_lens()
        # I might just provide the whole lens_pack to the class, then
        # in the calculations i'll be using one set somehow
        super().__init__(*args, lens_set=lens_set, **kwargs)

    def read_lens(self, print_only=False):
        """
        Read the lens sets from file provided in the path.

        Parameters
        ----------
        print_only : bool
            To indicate if printing out the currents sets only. If `False`
            the `self.lens_pack` will be set to get the current file sets.

        Returns
        -------
        sets : list
            Pack of lens sets.
        """
        lens_pack = calcs.get_lens_set(None, self.path, get_all=True)
        if print_only:
            logger.info(lens_pack)
        else:
            self.lens_pack = lens_pack
            return self.lens_pack

    # TODO: i think i'll need this one here
    # def _get_lensset(self):
    #     """
    #     Return the index of the lensset closest to the beam
    #     """
    #     states = self. ypos.statesAll()
    #     self._original_vals[self.state] = self.state.get()
    #     states.remove("OUT")
    #     states.sort()
    #     pos_d = self.ypos.statePosAll()
    #     here = self.y.wm()
    #     deltas = []
    #     for s in states:
    #         deltas.append(abs(pos_d[s] - here))
    #     index = np.argmin(deltas)
    #     p_len = len(self._lensPacks)
    #     if index >= p_len:
    #         return p_len - 1
    #     else:
    #         return index

    def create_lens(self, lens_set, make_backup=True):
        """
        Write lens set to the file provided when creating this object.

        Parameters
        ----------
        lens_set : list
            List with tuples for lens sets
        make_backup : bool, optional
            To indicate if a backup file should be created or not.
            Defaults to `True`.

        Examples
        --------
        >>> sets_list_of_tuples = [[3, 0.0001, 1, 0.0002],
                                   [1, 0.0001, 1, 0.0003, 1, 0.0005],
                                   [2, 0.0001, 1, 0.0005]]
        >>> create_lens(sets_list_of_tuples)

        """
        calcs.set_lens_set_to_file(lens_set, self.path, make_backup)

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
