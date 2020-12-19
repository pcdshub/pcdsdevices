"""
Module for common target stage stack configurations.
"""
import logging
import numpy as np

from ophyd.device import Device
from ophyd import Component as Cpt
from ophyd import FormattedComponent as FCpt
import matplotlib.pyplot as plt
from itertools import chain
import json
import jsonschema
import yaml

from pcdsdevices.epics_motor import _GetMotorClass, Newport
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
        Save four preset coordinate points.

        These are the coordinates from the four corners of the
        wanted/defined grid. The points for these coordinates shuld be taken
        from the middle of the four targets that are encasing the grid.

        The user will be asked to define the coordinates using the `tweak`
        method.

        Examples
        --------
        # Press q when ready to save the coordinates
        >>> xy.set_presets()
        Setting coordinates for (0, 0) top left corner:

        0.0000, : 0.0000, scale: 0.1

        Setting coordinates for (0, M) top right corner:

        10.0000, : 0.0000, scale: 0.1

        Setting coordinates for (N, M) bottom right corner:

        10.0000, : -10.0000, scale: 0.1

        Setting coordinates for (N, 0) bottom left corner:

        -0.0000, : -10.0000, scale: 0.1
        """
        if not hasattr(self.y, 'presets') or not hasattr(self.y, 'presets'):
            raise AttributeError('No folder setup for motor presets. '
                                 'Please add a location to save the positions '
                                 'to, using setup_preset_paths from '
                                 'pcdsdevices.interface to save the position.')

        print('\nSetting coordinates for (0, 0) top left corner: \n')
        self.tweak()
        pos = [self.x.position, self.y.position]
        print('\nSetting coordinates for (0, M) top right corner: \n')
        self.tweak()
        pos.extend([self.x.position, self.y.position])
        print('\nSetting coordinates for (N, M) bottom right corner: \n')
        self.tweak()
        pos.extend([self.x.position, self.y.position])
        print('\nSetting coordinates for (N, 0) bottom left corner: \n')
        self.tweak()
        pos.extend([self.x.position, self.y.position])
        # create presets
        # corner (0, 0)
        self.x.presets.add_hutch(value=pos[0], name="x_top_left")
        self.y.presets.add_hutch(value=pos[1], name="y_top_left")
        # corner (0, M)
        self.x.presets.add_hutch(value=pos[2], name="x_top_right")
        self.y.presets.add_hutch(value=pos[3], name="y_top_right")
        # corner (M, N)
        self.x.presets.add_hutch(value=pos[4], name="x_bottom_right")
        self.y.presets.add_hutch(value=pos[5], name="y_bottom_right")
        # corner (N, 0)
        self.x.presets.add_hutch(value=pos[6], name="x_bottom_left")
        self.y.presets.add_hutch(value=pos[7], name="y_bottom_left")

    def get_presets(self):
        """
        Get the saved presets if any.

        Examples
        --------
        >>> xy.get_presets()
        ((0, 0),
        (9.99999999999998, 0),
        (9.99999999999998, -9.99999999999998),
        (-6.38378239159465e-16, -9.99999999999998))

        Returns
        -------
        coord : tuple
            Four coordinate positions.
            (top_left, top_right, bottom_right, bottom_left)
        """
        try:
            # corner (0, 0)
            top_left = (self.x.presets.positions.x_top_left.pos,
                        self.y.presets.positions.y_top_left.pos)
            # corner (0, M)
            top_right = (self.x.presets.positions.x_top_right.pos,
                         self.y.presets.positions.y_top_right.pos)
            # corner (M, N)
            bottom_right = (self.x.presets.positions.x_bottom_right.pos,
                            self.y.presets.positions.y_bottom_right.pos)
            # corner (N, 0)
            bottom_left = (self.x.presets.positions.x_bottom_left.pos,
                           self.y.presets.positions.y_bottom_left.pos)
            return top_left, top_right, bottom_right, bottom_left
        except Exception:
            logger.warning('Could not get presets, try to set_presets.')


class XYGridStage(XYTargetGrid):
    """
    Class that helps support multiple samples on a mount for an XY Grid setup.

    We could have multiple samples mounted in a setup. This class helps
    figuring out the samples' patterns and maps points accordingly, and saves
    those records in a file.

    Parameters
    ----------
    name
    x_prefix : str
        Epics PV prefix for x motor.
    y_prefix : str
        Epics PV prefix for y motor.
    x_spacing : float
        Spacing between targets of the sample on the x axis in mm.
    y_spacing : float
        Spacing between targets of the sample on y the axis in mm.
    path : str
        Path to an `yaml` file where to save the grid patterns for
        different samples.
    """
    # # XPP:USR:PRT:MMN:06
    # x = FCpt(Newport, '{self._x_prefix}', doc='X axis', name='x_axis')
    # # XPP:USR:PRT:MMN:07
    # y = FCpt(Newport, '{self._y_prefix}', doc='Y axis', name='y_axis')

    # grid = FCpt(XYTargetGrid, x='{self._x_prefix}', y='{self._y_prefix}',
    #             name='{self._name}', x_spacing='{self._x_spacing}',
    #             y_scaping='{self._y_spacing}')

    sample_schema = json.loads("""
    {
        "type": "object",
        "properties": {
            "x_points": {"type": "array", "items": {"type": "number"}},
            "y_points": {"type": "array", "items": {"type": "number"}}
        },
        "required": ["x_points", "y_points"],
        "additionalProperties": false
    }
    """)

    def __init__(self, name, x_prefix, y_prefix, x_spacing, y_spacing, path):
        self._x_prefix = x_prefix
        self._y_prefix = y_prefix
        self._x_spacing = x_spacing
        self._y_spacing = y_spacing
        self._name = name
        self._path = path
        # TODO: assert here for a valid path, also valid yaml file
        super().__init__(name=name, x=x_prefix, y=y_prefix,
                         x_spacing=x_spacing, y_spacing=y_spacing)

    def mapped_samples(self, path=None):
        """
        Get all the available sample grids names that are currently saved.

        Returns
        -------
        samples : list
            List of string of all the sample names available.
        """
        with open(path) as sample_file:
            try:
                data = yaml.safe_load(sample_file)
            except yaml.YAMLError as err:
                logger.error('Error when loading the samples yaml file: %s',
                             err)
        return list(data.keys())

    def get_grid(self, sample_name, path=None):
        """
        Get the mapped grid of a sample.

        Parameters
        ----------
        sample_name : str
            The sample name that we want the grid for. To see current
            avaialble samples call `mapped_grids`
        path : str, optional
            Path to the `.yml` file. Defaults to the path defined when
            creating this object.

        Returns
        -------
        grid : tuple
            List of all the mapped points on the grid for the sample.
            `(x_points, y_points)`
        """
        path = path or self._path
        data = None
        with open(path) as sample_file:
            try:
                data = yaml.safe_load(sample_file)
            except yaml.YAMLError as err:
                logger.error('Error when loading the samples yaml file: %s',
                             err)
        if data is None:
            logger.warning('The file is empy, not sample grid yet. '
                           'Please use `save_presets` to insert grids '
                           'in the file.')
        try:
            return data[sample_name]['x_points'], data[sample_name]['y_points']
        except KeyError:
            logger.error('The sample %s might not have x and y points devined '
                         'in the file.', sample_name)

    def save_grid(self, sample_name, x_points, y_points, path=None):
        """
        Save a grid of mapped points for a sample.

        Parameters
        ----------
        sample_name : int
            A name to identify the sample grid, should be snake_case style.
        x_points : list
            List of all the mapped x points on the grid.
        y_points : list
            List of all the mapped y points on the grid.
        path : str, optional
            Path to the `.yml` file. Defaults to the path defined when
            creating this object.

        Examples
        --------
        >>> x_points = [1, 2, 3, 4, 5]
        >>> y_points = [1, 2, 3, 4, 5]
        >>> save_grid('sample_1', x_points, y_points)
        """
        path = path or self._path
        data = {sample_name: {"x_points": x_points, "y_points": y_points}}
        # validate the data
        try:
            temp_data = json.loads(json.dumps(data[sample_name]))
            jsonschema.validate(temp_data, self.sample_schema)
        except jsonschema.exceptions.ValidationError as err:
            logger.warning('Invalid input: %s', err)
        # override the existing sample grids or append other grids
        with open(path) as sample_file:
            yaml_dict = yaml.safe_load(sample_file) or {}
            yaml_dict.update(data)
        with open(path, 'w') as sample_file:
            yaml.safe_dump(yaml_dict, sample_file)

    def map_points(self, snake_like=True, show_grid=False):
        """
        Map all the sample positions in 2-d coordinates.

        Parameters
        ----------
        snake_like : bool
            Indicates if the points should be mapped in a snake-like pattern.
        show_grid : bool
            Indicates if the grid of mapped points should be displayed.

        Returns
        -------
        coord : list
            List of all coordinate points for samples on the grid.
        """
        bottom_left, top_left, top_right = self.get_presets()
        if all([bottom_left, top_left, top_right]) is None:
            msg = 'Could not get presets, make sure you set presets'
            logger.error(msg)
            raise ValueError(msg)

        # leaving these guys here for reference only for now
        # # distance from bottom_left to top_left
        # height = np.sqrt(np.power((top_left[0] - bottom_left[0]), 2)
        #                  + np.power((top_left[1] - bottom_left[1]), 2))
        # # distance from top_left to top_right
        # width = np.sqrt(np.power((top_right[0] - top_left[0]), 2)
        #                 + np.power((top_right[1] - top_left[1]), 2))

        x_grid_points = np.arange(top_left[0], top_right[0], self.x_spacing)
        y_grid_points = np.arange(bottom_left[1], top_left[1], self.y_spacing)

        # The meshgrid function returns
        # two 2-dimensional arrays
        xx, yy = np.meshgrid(x_grid_points, y_grid_points,
                             sparse=False, indexing='xy')

        if show_grid:
            plt.plot(xx, yy, marker='.', color='k', linestyle='none')
            plt.show()

        # flat out the arrays of points
        if not snake_like:
            flat_xx = list(chain.from_iterable(xx))
            flat_yy = list(chain.from_iterable(yy))
            return flat_xx, flat_yy

        xx = self.snake_grid_list(xx)
        yy = self.snake_grid_list(yy)
        return xx, yy

    def map_skewed(self, height=2500, width=2500, snake_like=True,
                   show_grid=False):
        """
        Temporary function - just for practice ... will be eventually removed
        """
        bottom_left, top_left, top_right = self.get_presets()
        if all([bottom_left, top_left, top_right]) is None:
            msg = 'Could not get presets, make sure you set presets'
            logger.error(msg)
            raise ValueError(msg)

        # get the original meshgrid
        # starting at 0, 0 top left corner, find the other 2 points if known
        # distance
        start_x, start_y = top_left[0], top_left[1]
        original_bl = [start_x, start_y - height]
        original_tr = [start_x + width, start_y]

        x_grid_points = np.arange(top_left[0], original_tr[0], self.x_spacing)
        y_grid_points = np.arange(original_bl[1], top_left[1], self.y_spacing)

        # The meshgrid function returns
        # two 2-dimensional arrays
        xx, yy = np.meshgrid(x_grid_points, y_grid_points,
                             sparse=False, indexing='xy')
        original_shape = xx.shape

        # this is a silly way to determine the points....
        # just for practice..
        # skewd when:
        # if buttom_left[0] != to_left[0]
        # if top_right[y] != top_left[1]
        # how much is skewed:
        x_skewed = bottom_left[0] - top_left[0]
        y_skewed = top_right[1] - top_left[1]
        pts = None
        if not np.isclose(x_skewed, 0) or not np.isclose(y_skewed, 0):
            # needs to be adjusted for skewd
            sk = x_skewed / height
            sky = y_skewed / width
            print(f'x_skewed: {x_skewed}')
            print(f'y_skewed: {y_skewed}')
            affine = np.array([[1, sky], [-sk, 1]])
            # affine = np.array([[1, 0], [-sk, 1]])
            # x values are skewed
            # pts = np.einsum('ij, jk->ik', affine,
            # y values are skewed
            pts = np.einsum('ij, ik->jk', affine,
                            np.array([xx.flatten(), yy.flatten()]))
        xx = pts[0, :]
        yy = pts[1, :]
        # reshape these guys xx, yy into original shape
        xx = xx.reshape(original_shape)
        yy = yy.reshape(original_shape)

        if show_grid:
            plt.plot(xx, yy, marker='.', color='k', linestyle='none')
            plt.show()

        # flat out the arrays of points
        if not snake_like:
            flat_xx = list(chain.from_iterable(xx))
            flat_yy = list(chain.from_iterable(yy))
            return flat_xx, flat_yy

        xx = self.snake_grid_list(xx)
        yy = self.snake_grid_list(yy)
        return xx, yy

    def snake_grid_list(self, points):
        """
        Flatten out a meshgrid.

        Flatten them into lists with snake_like pattern coordinate points.
        [[1, 2], [3, 4]] => [1, 2, 4, 3]

        Parameters
        ----------
        points : array
            Array containing the grid points for an axis.

        Returns
        -------
        flat_points : list
            List of all the grid points folowing a snake-like pattern.
        """
        temp_points = []
        for i in range(points.shape[0]):
            if i % 2 == 0:
                temp_points.append(points[i])
            else:
                t = points[i]
                tt = t[::-1]
                temp_points.append(tt)
        flat_points = list(chain.from_iterable(temp_points))
        return flat_points
