"""
Module for common target stage stack configurations.
"""
import logging
import numpy as np
from datetime import datetime

from ophyd.device import Device
import matplotlib.pyplot as plt
from itertools import chain
import json
import jsonschema
import yaml

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
            top_left = (round(self.x.presets.positions.x_top_left.pos, 3),
                        round(self.y.presets.positions.y_top_left.pos, 3))
            # corner (0, M)
            top_right = (round(self.x.presets.positions.x_top_right.pos, 3),
                         round(self.y.presets.positions.y_top_right.pos, 3))
            # corner (M, N)
            bottom_right = (
                round(self.x.presets.positions.x_bottom_right.pos, 3),
                round(self.y.presets.positions.y_bottom_right.pos, 3))
            # corner (N, 0)
            bottom_left = (
                round(self.x.presets.positions.x_bottom_left.pos, 3),
                round(self.y.presets.positions.y_bottom_left.pos, 3))
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
    x_motor : str or motor object
        Epics PV prefix for x motor, or a motor object.
    y_motor : str or motor object
        Epics PV prefix for y motor, or a motor object.
    m_points : int
        Number of targets in x direction, used to determine the coordinate
        points, where for e.g.: `(0, m_points)` would represent the top right
        corner of the desired sample grid.
    n_points : int
        Number of targets in y direction, used to determine the coordinate
        points, where for e.g.: `(n_points, 0)` would represent the bottom
        left corner of the desired sample grid.
    path : str
        Path to an `yaml` file where to save the grid patterns for
        different samples.
    """
    # TODO: i don't really need this
    sample_schema = json.loads("""
    {
        "type": "object",
        "properties": {
            "time_created": {"type": "string"},
            "top_left": {"type": "array", "items": {"type": "number"}},
            "top_rigt": {"type": "array", "items": {"type": "number"}},
            "bottom_right": {"type": "array", "items": {"type": "number"}},
            "bottom_left": {"type": "array", "items": {"type": "number"}},
            "M": {"type": "number"},
            "N": {"type": "number"},
            "coefficients": {"type": "array"}
        },
        "required": ["time_created", "top_left", "top_right", "bottom_right",
        "bottom_left", "coefficients"],
        "additionalProperties": true
    }
    """)

    def __init__(self, name, x_motor, y_motor, m_points, n_points, path):
        self._path = path
        self._m_points = m_points
        self._n_points = n_points
        # TODO: assert here for a valid path, also valid yaml file
        # assert os.path.exists(path)
        # TODO: i don't need y and x spacing, because it is asserting as flaot
        # in GridAxis - it will make me add them here
        super().__init__(name=name, x=x_motor, y=y_motor,
                         x_spacing=0.0, y_spacing=0.0)
        self._coefficients = []

    @property
    def m_n_points(self):
        """
        Get the current m and n points.

        The m and n points represents the number of grid points on the current
        grid in the x and y direction respectively.

        Returns
        -------
        m_points, n_points : tuple
            The number of grid points on the x and y axis.
            E.g.: `10, 5` -> 10 by 5 grid.
        """
        return self._m_points, self._n_points

    @m_n_points.setter
    def m_n_points(self, m_n_values):
        """
        Set m and n points.

        Set the m value representing the number of grid points in x direction,
        and n value representing the number of grid points in the y direction.

        Parameters
        ----------
        m_n_values : tuple
            The number of grid points on the x and y axis respecively.

        Examples
        --------
        >>> xy_grid.m_n_points = 10, 10
        """
        try:
            self._m_points, self._n_points = m_n_values
        except ValueError:
            logger.error("Please pass an iterable with two items for m points"
                         " and n points respectively.")

    @property
    def coefficients(self):
        """
        Get the current coefficients if any.

        These coefficients are calculated from the projective transformation.
        Knowing the coefficients, and x an y value can be determined.

        Returns
        -------
        coefficients : list
            Array of 8 projective transformation coefficients.
        """
        return self._coefficients

    @coefficients.setter
    def coefficients(self, coefficients):
        """
        Set the current coefficients.

        These coefficients are calculated from the projective transformation.
        Knowing the coefficients, and x an y value can be determined.

        Parameters
        ----------
        coefficients : array
            Array of 8 projective transformation coefficients.
        """
        self._coefficients = coefficients

    def mapped_samples(self, path=None):
        """
        Get all the available sample grids names that are currently saved.

        Returns
        -------
        samples : list
            List of strings of all the sample names available.
        """
        path = path or self._path
        with open(path) as sample_file:
            try:
                data = yaml.safe_load(sample_file)
                if not data:
                    logger.info('The file is empty, no samples saved yet.')
                    return
                return list(data.keys())
            except yaml.YAMLError as err:
                logger.error('Error when loading the samples yaml file: %s',
                             err)

    def get_sample(self, sample_name, path=None):
        """
        Get the information for a saved sample.

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
        data : dictionary
            Dictionary of all the information for a saved sample.

        Examples
        --------
        >>> get_sample('sample1')
        {'time_created': '2021-01-06 11:43:40.701095',
        'top_left': [0, 0],
        'top_right': [4.0, -1.0],
        'bottom_right': [4.4, -3.5],
        'bottom_left': [1.0, -3.0],
        'M': 10,
        'N': 10,
        'coefficients': [1.1686746987951824,
        -0.3855421686746996,
        -9.730859023513261e-15,
        -0.29216867469879476,
        1.1566265060240974,
        6.281563288265657e-16,
        0.042168674698794054,
        -0.05220883534136586]}
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
            logger.warning('The file is empty, not sample grid yet. '
                           'Please use `save_presets` to insert grids '
                           'in the file.')
        try:
            return data[sample_name]
        except Exception:
            logger.error('The sample %s might not have x and y points devined '
                         'in the file.', sample_name)

    def save_grid(self, sample_name, path=None):
        """
        Save a grid of mapped points for a sample.

        Parameters
        ----------
        sample_name : int
            A name to identify the sample grid, should be snake_case style.
        path : str, optional
            Path to the `.yml` file. Defaults to the path defined when
            creating this object.

        Examples
        --------
        >>> save_grid('sample_1')
        """
        path = path or self._path
        now = str(datetime.now())
        top_left, top_right, bottom_right, bottom_left = (), (), (), ()
        if self.get_presets():
            top_left, top_right, bottom_right, bottom_left = self.get_presets()
        m_points, n_points = self.m_n_points
        coefficients = self.coefficients
        data = {sample_name: {"time_created": now,
                              "top_left": top_left,
                              "top_right": top_right,
                              "bottom_right": bottom_right,
                              "bottom_left": bottom_left,
                              "M": m_points,
                              "N": n_points,
                              "coefficients": coefficients}}
        # validate the data
        # TODO: don't need this anymore, so maybe remove it,
        # but it won't hurt to have it anyway
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
            yaml.safe_dump(yaml_dict, sample_file,
                           sort_keys=False, default_flow_style=False)

    def remove_all_samples(self, path=None):
        """
        Empty the samples file.

        All the grid samples will be deleted.

        Parameters
        ----------
        path : string, optional
            Path of .yml file with samples.
        """
        path = path or self._path
        with open(path, 'w') as sample_file:
            yaml.safe_dump(None, sample_file)

    def map_points(self, snake_like=True, show_grid=False):
        """
        Map all the sample positions in 2-d coordinates.

        Parameters
        ----------
        snake_like : bool, optional
            Indicates if the points should be mapped in a snake-like pattern.
            Defaults to `True`.
        show_grid : bool, optional
            Indicates if the grid of mapped points should be displayed.
            Defaults to `False`
        shear : bool, optional
            Indicates if shear transformation should be applied.
            Defaults to `True`.
        Returns
        -------
        xx, yy : tuple
            xx and yy list of all coordinate points for samples on the grid.
        """
        top_left, top_right, bottom_right, bottom_left = self.get_presets()
        if all([top_left, top_right, bottom_right, bottom_left]) is None:
            raise ValueError('Could not get presets, make sure you set presets'
                             ' first using the `set_presets` method.')

        # distance from bottom_left to top_left
        height = np.sqrt(np.power((top_left[0] - bottom_left[0]), 2)
                         + np.power((top_left[1] - bottom_left[1]), 2))
        # distance from top_left to top_right
        width = np.sqrt(np.power((top_right[0] - top_left[0]), 2)
                        + np.power((top_right[1] - top_left[1]), 2))
        start_x, start_y = top_left[0], top_left[1]
        perfect_bl = [start_x, start_y + height]
        perfect_tr = [start_x + width, start_y]

        m_points, n_points = self.m_n_points

        x_grid_points = np.linspace(
            top_left[0], perfect_tr[0], num=m_points)
        y_grid_points = np.linspace(
            top_left[1], perfect_bl[1], num=n_points)

        # leaving this here for now, it was working fine but might not work in
        #  all cases
        # x_grid_points = np.linspace(
        #     top_left[0], top_right[0], num=m_points)
        # y_grid_points = np.linspace(
        #     top_left[1], bottom_left[1], num=n_points)

        # The meshgrid function returns two 2-dimensional arrays
        xx_origin, yy_origin = np.meshgrid(x_grid_points, y_grid_points)

        # apply projective transformation
        coeffs = self.projective_transform(
            top_left=top_left, top_right=top_right,
            bottom_right=bottom_right, bottom_left=bottom_left)
        coeffs = list(coeffs)
        xx, yy = self.get_xy_coordinate(xx_origin, yy_origin, coeffs)
        # if projective:
        #     xx, yy = self.projective_transform(xx=xx_origin, yy=yy_origin,
        #                                        top_left=top_left,
        #                                        top_right=top_right,
        #                                        bottom_right=bottom_right,
        #                                        bottom_left=bottom_left)
        # return the original xx and yy if no transformations applied
        # if not projective:
        #     xx, yy = xx_origin, yy_origin

        if show_grid:
            plt.plot(xx, yy, marker='.', color='k', linestyle='none')
            plt.show()

        # flat out the arrays of points
        if not snake_like:
            flat_xx = list(chain.from_iterable(xx.tolist()))
            flat_yy = list(chain.from_iterable(yy.tolist()))
            return flat_xx, flat_yy

        xx = self.snake_grid_list(xx)
        yy = self.snake_grid_list(yy)
        return xx, yy

    def find_perfect_coordiantes(self, top_left, top_right, bottom_right,
                                 bottom_left):
        """
        Find a rectangule given 4 points for a quarilateral.

        Based on 4 coordinates ABCD find the distance A->B and distance
        B->C and add those distances to the starting coordinates to find
        the top_right corner and bottom_left corner respectively.
        Add perfect top_right coordinats to the perfect bottom_left
        coordinates to get the bottom_right corner coordinates.
        """
        # a, b, c, d = top_left, top_right, bottom_right, bottom_left
        # area1 = ((a[0] * (b[1] - c[1]) + b[0] *
        #          (c[1] - a[1]) + c[0] * (a[1] - b[1])) / 2)

        # area2 = ((a[0] * (d[1] - c[1]) + d[0] *
        #           (c[1] - a[1]) + c[0] * (a[1] - d[1])) / 2)
        # area = abs(area1) + abs(area2)
        # distance from bottom_left to top_left
        height = np.sqrt(np.power((top_left[0] - bottom_left[0]), 2)
                         + np.power((top_left[1] - bottom_left[1]), 2))
        # distance from top_left to top_right
        width = np.sqrt(np.power((top_right[0] - top_left[0]), 2)
                        + np.power((top_right[1] - top_left[1]), 2))
        start_x, start_y = top_left[0], top_left[1]
        perfect_bl = [start_x, start_y + height]
        perfect_tr = [start_x + width, start_y]
        # find the 4th perfect coordinate
        perfect_br = [perfect_tr[0] + perfect_bl[0],
                      perfect_tr[1] + perfect_bl[1]]

        perfect_plane = [(top_left[0], top_left[1]),
                         (perfect_tr[0], perfect_tr[1]),
                         (perfect_br[0], perfect_br[1]),
                         (perfect_bl[0], perfect_bl[1])]
        return perfect_plane

    # TODO: this probably belongs somewhere else as well as the snake like grid
    def projective_transform(self, top_left, top_right, bottom_right,
                             bottom_left):
        """
        Find the projective transformation of the sample grid.

        Parameters
        ----------
        top_left : tuple
            (x, y) coordinates of the top left corner
        top_right : tuple
            (x, y) coordinates of the top right corner
        bottom_right : tuple
            (x, y) coordinates of the bottom right corner
        bottom_left : tuple
            (x, y) coordinates of the bottom left corner

        Returns
        -------
        coeff : list
            List of 8 projective transformation coefficients. They are used to
            find x and y.
        """
        # TODO i don't know how to find the true coordinate values of this
        # perfect plane - not sure if this will work fine...
        perfect_plane = self.find_perfect_coordiantes(top_left, top_right,
                                                      bottom_right,
                                                      bottom_left)

        new_plane = [(top_left[0], top_left[1]),
                     (top_right[0], top_right[1]),
                     (bottom_right[0], bottom_right[1]),
                     (bottom_left[0], bottom_left[1])]

        grid = []
        for p1, p2 in zip(perfect_plane, new_plane):
            grid.append([
                p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
            grid.append([
                0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

        grid_matrix = np.matrix(grid, dtype=np.float64)

        new_plane_matrix = np.array(new_plane).reshape(8)
        coefficients = (np.dot(np.linalg.inv(np.transpose(grid_matrix)
                        * grid_matrix) * np.transpose(grid_matrix),
                        new_plane_matrix))
        coeffs = np.array(coefficients).reshape(8)
        self._coefficients = coeffs.tolist()
        return coeffs

        # a, b, c = coeff[0], coeff[1], coeff[2]
        # d, e, f = coeff[3], coeff[4], coeff[5]
        # g, h = coeff[6], coeff[7]

        # def x_formula(x, y):
        #     # x = (ax + by + c) / (gx + hy + 1)
        #     new_x = (a*x + b*y + c) / (g*x + h*y + 1)
        #     return np.round(new_x, decimals=4)

        # def y_formula(x, y):
        #     # y = (dx + ey + f) / (gx + hy + 1)
        #     new_y = (d*x + e*y + f) / (g*x + h*y + 1)
        #     return np.round(new_y, decimals=4)

        # new_xx = np.array([x_formula(xx[i], yy[i])
        #                    for i in range(xx.shape[0])])
        # new_yy = np.array([y_formula(xx[i], yy[i])
        #                    for i in range(xx.shape[0])])
        # return new_xx, new_yy

    def get_xy_coordinate(self, xx, yy, coefficients=None):
        """
        TODO: some type of function that will return x, y values from a grid,
        given the coefficients and the coordinates.

        TODO: make it work with one single pair of elements?

        Parameters
        ----------
        xx : list
        yy : list
        """
        # The homography transformation coefficients
        coeffs = coefficients or self.coefficients

        def x_formula(x, y):
            # x = (ax + by + c) / (gx + hy + 1)
            new_x = ((coeffs[0] * x + coeffs[1] * y
                     + coeffs[2]) / (coeffs[6] * x + coeffs[7] * y + 1))
            return new_x

        def y_formula(x, y):
            # y = (dx + ey + f) / (gx + hy + 1)
            new_y = ((coeffs[3] * x + coeffs[4] * y
                     + coeffs[5]) / (coeffs[6] * x + coeffs[7] * y + 1))
            return new_y

        new_xx = np.array([x_formula(xx[i], yy[i])
                           for i in range(xx.shape[0])])
        new_yy = np.array([y_formula(xx[i], yy[i])
                           for i in range(yy.shape[0])])
        return new_xx, new_yy

    def mesh_interpolation(self, top_left, top_right, bottom_right,
                           bottom_left):
        """
        Mapping functions for an arbitrary quadrilateral.

        Reference: https://www.particleincell.com/2012/quad-interpolation/

        Parameters
        ----------
        top_left : tuple
            (x, y) coordinates of the top left corner
        top_right : tuple
            (x, y) coordinates of the top right corner
        bottom_right : tuple
            (x, y) coordinates of the bottom right corner
        bottom_left : tuple
            (x, y) coordinates of the bottom left corner

        Returns
        -------
        a_coeffs, b_coeffs : tuple
            List of tuples with the alpha and beta coefficients for projective
            transformation. They are used to find x and y.
        """
        # describes the entire point space enclosed by the quadrilateral
        unit_grid = np.array([[1, 0, 0, 0],
                              [1, 1, 0, 0],
                              [1, 1, 1, 1],
                              [1, 0, 1, 0]])
        # x value coordinates for current grid (4 corners)
        px = np.array([top_left[0],
                       top_right[0],
                       bottom_right[0],
                       bottom_left[0]])
        # y value coordinates for current grid (4 corners)
        py = np.array([top_left[1],
                       top_right[1],
                       bottom_right[1],
                       bottom_left[1]])

        a_coeffs = np.linalg.inv(unit_grid).dot(np.transpose(px))
        b_coeffs = np.linalg.inv(unit_grid).dot(np.transpose(py))

        return a_coeffs.flatten(), b_coeffs.flatten()

    def convert_physical_to_logical(self, a_coeffs, b_coeffs, x, y):
        """
        Convert the physical coordinates to logical coordinates.

        Parameters
        ----------
        a_coeffs : array
            Perspective transformation coefficients for alpha.
        b_coeffs : array
            Perspective transformation coefficients for beta.
        x : float
            The x coordinate value.
        y : float
            The y coordinate value.
        """
        # aa = a(4)*b(3) - a(3)*b(4)
        aa = a_coeffs[3] * b_coeffs[2] - a_coeffs[2] * b_coeffs[3]
        # bb = a(4)*b(1) - a(1)*b(4) + a(2)*b(3) - a(3)*b(2) + x*b(4) - y*a(4)
        bb = (a_coeffs[3] * b_coeffs[0] - a_coeffs[0] * b_coeffs[3]
              + a_coeffs[1] * b_coeffs[2] - a_coeffs[2]
              * b_coeffs[1] + x * b_coeffs[3] - y * a_coeffs[3])
        # cc = a(2)*b(1) - a(1)*b(2) + x*b(2) - y*a(2)
        cc = (a_coeffs[1]*b_coeffs[0] - b_coeffs[0]
              * b_coeffs[1] + x * b_coeffs[1] - y * b_coeffs[1])

        # compute m_points (-b+sqrt(b ^ 2-4ac))/(2a)
        det = np.sqrt((bb * bb) - (4 * aa * cc))
        if(aa.all() == 0.0):
            m_points = -cc / bb
        else:
            m_points = (-bb + det) / (2 * aa)
        # compute l_points
        l_points = ((x - a_coeffs[0] - a_coeffs[2] * m_points) /
                    (a_coeffs[1] + a_coeffs[3] * m_points))
        return m_points.tolist(), l_points.tolist()

    def convert_to_physical(self, a_coeffs, b_coeffs, l_point, m_point):
        """
        Convert to physical coordinates from logical coordinates.

        Parameters
        ----------
        a_coeffs : array
            Perspective transformation coefficients for alpha.
        b_coeffs : array
            Perspective transformation coefficients for beta.
        l_points : float
            Logical point in the x direction.
        m_point : float
            Logical point in the y direction.

        Returns
        -------
        x, y : tuple
            The x and y physical values on the specified grid.
        """
        # x = a(1) + a(2)*l + a(3)*m + a(4)*l*m
        x = (a_coeffs[0] + a_coeffs[1] * l_point + a_coeffs[2]
             * m_point + a_coeffs[3] * l_point * m_point)
        # y = b(1) + b(2)*l + b(3)*m + b(4)*l*m
        # y = (b_coeffs[0] + b_coeffs[1] * l_point +
        #      b_coeffs[2] * m_point + b_coeffs[3] * l_point * m_point)
        a = a_coeffs
        b = b_coeffs
        m = m_point
        y = ((1) / (a[1] + a[3] * m) * (-a[0] * b[1] - a[0] * b[3] * m + a[1]
                                        * b[0] + a[1] * b[2] * m - a[2] * b[1]
                                        * m - (a[2] * b[3]) * m * m + a[3]
                                        * b[0] * m + a[3] * b[2] * (m * m)
                                        + b[1] * x + b[3] * m))
        return x, y

    def snake_grid_list(self, points):
        """
        TODO: maybe find something in bluesky to do this based on m/n
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
        # convert the numpy.float64 to normal float to be able to easily
        # save them in the yaml file
        flat_points = [float(v) for v in flat_points]
        return flat_points
