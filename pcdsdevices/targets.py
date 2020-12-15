"""
Module for common target stage stack configurations.
"""
import logging
import numpy as np

from ophyd.device import Device
import matplotlib.pyplot as plt
from itertools import chain

from pcdsdevices.epics_motor import _GetMotorClass
from .interface import tweak_base

logger = logging.getLogger(__name__)


def StageStack(mdict, name):
    """
    Conveniencefunction for generating a stage stack device. Intended for
    bundling various motors into a single object. The function takes a
    dictionary of PVs and/or previously instantiated motor objects and bundles
    them together. If given a PV, The factory function attempts to determine
    the appropriate motor class from the given base PV; if this fails then it
    will attempt to create an EpicsMotor. Axes are given the same name as they
    are assigned in the provided dictionary. See examples below.

    Parameters
    ----------
    mdict : dictionary
        Dictionary of motor objects and or base PVs.

    name : str
        Name for the stack. Used to make a class name. No whitespace.

    Examples
    --------
    # Make a classic XYZ stack with two PVs and one motor object
    d = {'x': 'TST:MMS:01', 'y': 'TST:MMS:02', 'z': z_motor}
    xyz = StageStack(d, 'my_xyz')
    """
    cpts = {}
    for mname, mitem in mdict.items():
        # Check if this is a PV or motor object
        if issubclass(type(mitem), Device):  # Motor object
            cpts[mname] = mitem
        elif isinstance(mitem, (str)):  # PV
            mcls = _GetMotorClass(mitem)
            cpt = mcls(prefix=mitem, name=mname)
            cpts[mname] = cpt
        else:  # Something is wrong
            logger.warning("Unrecognized input {}. "
                           "Skipping axis {}.".format(mitem, mname))
    cls_name = name + '_StageStack'
    cls = type(cls_name, (object,), cpts)

    dev = cls()

    return dev


# Internal class
class GridAxis():
    """
    Class for axes that move in regularly spaced intervals.
    """
    def __init__(self, stage, spacing):
        assert isinstance(spacing, float), "Specify a float target spacing"
        self.stage = stage
        self.spacing = spacing

    def advance(self, nspaces, direction, wait=False):
        """
        Move the grid axis in the specified direction by (n_spacings * spacing)
        """
        assert direction in [1, -1], "Direction must be 1 or -1"
        assert nspaces >= 1, "n_targets must be >= 1"

        curr_pos = self.stage.wm()
        next_pos = curr_pos + direction*(nspaces*self.spacing)
        self.stage.mv(next_pos, wait=wait)


class XYTargetGrid():
    """
    Class methods for managing a target grid oriented normal to the beam, with
    regular X-Y spacing between targets.

    Parameters
    ----------
    x : Ophyd motor object
        X stage (LUSI coords.) to be using in the stack

    y : Ophyd motor object
        Y stage (LUSI coords.) to be using in the stack

    x_init : float
        The initial position for the x motor. Defines the x-position of target
        'zero'.

    x_spacing : float
        The nominal spacing between targets in the x-direction.

    x_comp : float (optional)
        A parameter to account for skew in target position due to non-ideal
        mounting. This skew is assumed to be identical between targets.

    y_init : float
        The initial position for the y motor. Defines the y-position of target
        'zero'.

    y_spacing : float
        The nominal spacing between targets in the y-direction.

    y_comp : float (optional)
        A parameter to account for skew in target position due to non-ideal
        mounting. This skew is assumed to be identical between targets.

    Examples
    --------
    # Make a target stack with targets spaced in a 1.0mm square grid, starting
    # at motor positions (0.0, 0.0), with no skew.

    xygrid = XYTargetGrid(x=x_motor, y=y_motor, x_init=0.0, y_init=0.0,
                          x_spacing=1.0, y_spacing=1.0)

    # Make a target stack as above, but with some skew in x and y.

    xygrid = XYTargetGrid(x=x_motor, y=y_motor, x_init=0.0, y_init=0.0,
                          x_spacing=1.0, y_spacing=1.0, x_comp=0.05,
                          y_comp=0.01)
    """

    def __init__(self, name, x=None, y=None, x_init=None, x_spacing=None,
                 x_comp=0.0, y_init=None, y_spacing=None, y_comp=0.0):

        self.x_init = x_init
        self.x_spacing = x_spacing
        self.x_comp = x_comp

        self.y_init = y_init
        self.y_spacing = y_spacing
        self.y_comp = y_comp

        d = {'x': x, 'y': y}
        self._stack = StageStack(d, name)

        self.x = self._stack.x
        self._xgrid = GridAxis(self.x, self.x_spacing)
        self.y = self._stack.y
        self._ygrid = GridAxis(self.y, self.y_spacing)

        # Treat compensation axes like additional grid axes
        if self.x_comp:
            self._x_comp_axis = GridAxis(self.x, self.x_comp)

        if self.y_comp:
            self._y_comp_axis = GridAxis(self.y, self.y_comp)

    def wm(self):
        """
        Return current position of X and Y axes as a dictionary, i.e.
        {x: <x_position>, y: <y_position>}.
        """
        return {'x': self.x.wm(), 'y': self.y.wm()}

    def reset(self, wait=False):
        """
        Return to the defined initial position (x_init, y_init). Should be
        called during experiment setup prior to using other class methods to
        initialize the position.

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.
        """
        self.x.mv(self.x_init, wait=wait)
        self.y.mv(self.y_init, wait=wait)

    def next(self, nspaces=1, wait=False):
        """
        Move forward (in X) by specified integer number of targets.

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.

        nspaces : int (default = 1)
            Number of spaces to move "forward" on x-axis.
        """
        self._xgrid.advance(nspaces, 1, wait=wait)
        if self.y_comp:
            self._y_comp_axis.advance(nspaces, 1, wait=wait)

    def back(self, nspaces=1, wait=False):
        """
        Move backward (in X) by specified integer number of targets.

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.

        nspaces : int (default = 1)
            Number of spaces to move "backward" on x-axis.
        """
        self._xgrid.advance(nspaces, -1, wait=wait)
        if self.y_comp:
            self._y_comp_axis.advance(nspaces, -1, wait=wait)

    def up(self, nspaces=1, wait=False):
        """
        Move to higher target position by specified integer number of targets
        (stage moves down).

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.

        nspaces : int (default = 1)
            Number of spaces to move "up" on y-axis.
        """
        self._ygrid.advance(nspaces, 1, wait=wait)
        if self.x_comp:
            self._x_comp_axis.advance(nspaces, 1, wait=wait)

    def down(self, nspaces=1, wait=False):
        """
        Move to lower target position by specified integer number of targets
        (stage moves up).

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.

        nspaces : int (default = 1)
            Number of spaces to move "down" on y-axis.
        """
        self._ygrid.advance(nspaces, -1, wait=wait)
        if self.x_comp:
            self._x_comp_axis.advance(nspaces, -1, wait=wait)

    def move(self, nxspaces, nyspaces, wait=False):
        """
        Move to a specific target position given by (xspaces, yspaces)
        from the defined initial position. Includes compensation if defined.

        Parameters:
        -----------
        wait : bool (default = False)
            Flag to wait for movement to complete before returning.

        nxspaces : int (default = 1)
            Number of spaces to move on x-axis.

        nyspaces : int (default = 1)
            Number of spaces to move on y-axis.
        """
        xpos = self.x_init + self.x_spacing*nxspaces + self.x_comp*nyspaces
        ypos = self.y_init + self.y_spacing*nyspaces + self.y_comp*nxspaces

        self.x.mv(xpos, wait=wait)
        self.y.mv(ypos, wait=wait)

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

    def set_presets(self):
        """
        Save three preset coordinate points.
        """
        if not (self.y.presets.has_presets and self.x.presets.has_presets):
            raise AttributeError('No folder setup for motor presets. '
                                 'Please add a location to save the positions '
                                 'to, using setup_preset_paths from '
                                 'pcdsdevices.interface to save the position.')

        print('Setting coordinates for (N, 0) bottom left corner')
        self.tweak()
        pos = [self.x.position, self.y.position]
        print('Setting coordinates for (0, 0) top left corner')
        self.tweak()
        pos.extend([self.x.position, self.y.position])
        print('Setting coordinates for (0, M) top right corner')
        self.tweak()
        pos.extend([self.x.position, self.y.position])
        # create presets
        self.x.presets.add_hutch(value=pos[0], name="x_bottom_left")
        self.x.presets.add_hutch(value=pos[2], name="x_top_left")
        self.x.presets.add_hutch(value=pos[4], name="x_top_right")
        self.y.presets.add_hutch(value=pos[1], name="y_bottom_left")
        self.y.presets.add_hutch(value=pos[3], name="y_top_left")
        self.y.presets.add_hutch(value=pos[5], name="y_top_right")

    def get_presets(self):
        """
        Get the saved presets if any.

        Returns
        -------
        pos : tuple
            Three coordinate positions - bottom_left, top_left, top_right
        """
        try:
            pos = [self.x.presets.positions.x_bottom_left.pos,
                   self.y.presets.positions.y_bottom_left.pos,
                   self.x.presets.positions.x_top_left.pos,
                   self.y.presets.positions.y_top_left.pos,
                   self.x.presets.positions.x_top_right.pos,
                   self.y.presets.positions.y_top_right.pos]
            bottom_left = (pos[0], pos[1])
            top_left = (pos[2], pos[3])
            top_right = (pos[4], pos[5])
            return bottom_left, top_left, top_right
        except Exception:
            logger.warning('Could not get presets, try to set_presets.')

    def map_points(self, snake_like=True):
        """
        Map all the sample positions in 2-d coordinates.

        Parameters
        ----------
        snake_like : bool
            Indicates if the points should be mapped in a snake-like pattern.

        Returns
        -------
        coord : list
            List of all coordinate points for samples on the grid.
        """
        bottom_left, top_left, top_right = self.get_presets()
        if all([bottom_left, top_left, top_right]) is None:
            logger.warning('Could not get presets, make sure you set presets')
            return
        # distance from bottom_left to top_left
        height = np.sqrt(np.power((top_left[0] - bottom_left[0]), 2)
                         + np.power((top_left[1] - bottom_left[1]), 2))
        # distance from top_left to top_right
        width = np.sqrt(np.power((top_right[0] - top_left[0]), 2)
                        + np.power((top_right[1] - top_left[1]), 2))

        # the very first coordinate is the most top-left sample on the grid
        current_x = top_left[0]
        current_y = top_left[1]
        # we need to get all the places where the samples will be on both axes
        x_grid_points = [current_x]
        y_grid_points = [current_y]

        # starting at the top left corner of the grid
        # find all the samples locations on the x axes
        while current_x < width - self.x_spacing:
            current_x = current_x + self.x_spacing
            x_grid_points.append(current_x)

        # starting at the top left corner of the grid
        # find all the samples locations on the y axes
        while current_y < height + self.y_spacing:
            current_y = current_y + self.y_spacing
            y_grid_points.append(current_y)

        # The meshgrid function returns
        # two 2-dimensional arrays
        xx, yy = np.meshgrid(x_grid_points, y_grid_points,
                             sparse=False, indexing='xy')

        plt.plot(xx, yy, marker='.', color='k', linestyle='none')
        plt.show()

        # flat out the arrays of points
        if not snake_like:
            flat_xx = list(chain.from_iterable(xx))
            flat_yy = list(chain.from_iterable(yy))
            return flat_xx, flat_yy
        # make paris of (x, y) coordinates
        # coord = list(zip(flat_xx, flat_yy))
        return self.get_snake_grid_list(xx, yy)

    def get_snake_grid_list(self, xx, yy):
        """
        Flatten out the x and y meshgrids.

        Flatten them into lists with snake_like pattern coordinate points.

        Parameters
        ----------
        xx : array
            Array containing the grid points for x.
        yy : array
            Array containing the grid points for y.

        Returns
        -------
        xx, yy : tuple
            Lists of all the x and y grid points folowing a snake-like pattern.
        """
        temp_x = []
        temp_y = []
        for i in range(xx.shape[0]):
            if i % 2 == 0:
                temp_x.append(xx[i])
            else:
                t = xx[i]
                tt = t[::-1]
                temp_x.append(tt)
        for i in range(yy.shape[0]):
            if i % 2 == 0:
                temp_y.append(yy[i])
            else:
                t = yy[i]
                tt = t[::-1]
                temp_y.append(tt)
        xx = list(chain.from_iterable(temp_x))
        yy = list(chain.from_iterable(temp_y))
        return xx, yy
