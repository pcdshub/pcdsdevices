"""
Module for common target stage stack configurations.
"""
import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.device import create_device_from_components

from pcdsdevices.epics_motor import _GetMotorClass
#from pcdsdevices.epics_motor import (IMS, Newport, PMC100, BeckhoffAxis,
#                                     PCDSMotorBase, SmarAct, EpicsMotor)
#from pcdsdevices.sim import SynMotor

logger = logging.getLogger(__name__)


#def _GetMotorClass(basepv, sim=False):
#    """
#    Function to determine the appropriate motor class based on the PV. 
#    Shamelessly stolen from epics_motor.py, should be re-factored at some
#    point. Added option for generating simulated motors. 
#    """
#    # Available motor types
#    motor_types = (('MMS', IMS),
#                   ('CLZ', IMS),
#                   ('CLF', IMS),
#                   ('MMN', Newport),
#                   ('MZM', PMC100),
#                   ('MMB', BeckhoffAxis),
#                   ('PIC', PCDSMotorBase),
#                   ('MCS', SmarAct))
#    # Search for component type in prefix
#    for cpt_abbrev, _type in motor_types:
#        if f':{cpt_abbrev}:' in basepv:
#            if not sim:
#                logger.debug("Found %r in basepv %r, loading %r",
#                             cpt_abbrev, basepv, _type)
#                return _type
#            else:
#                return SynMotor
#    # Default to ophyd.EpicsMotor
#    if not sim:
#        logger.warning("Unable to find type of motor based on component. "
#                       "Using 'ophyd.EpicsMotor'")
#        return EpicsMotor
#    else:
#        return SynMotor


#def StageStackCls(name, x_pv=None, y_pv=None, z_pv=None, roll_pv=None,
#                  pitch_pv=None, yaw_pv=None, sim=False):
#    """
#    Generate a stage stack class. See StageStack function for more details on
#    class arguments.
#    """
#    pvs = {'x': x_pv, 'y': y_pv, 'z': z_pv, 'roll': roll_pv, 'pitch': pitch_pv,
#           'yaw': yaw_pv}
#    cpts = {}
#    for mname, mprefix in pvs.items():
#        if mprefix:
#            mcls = _GetMotorClass(mprefix, sim=sim)
#            cpt = mcls(prefix=mprefix, name=mname)
#            cpts[mname] = cpt
#    cls_name = name + '_StageStack'
#    cls = type(cls_name, (object,), cpts)
#
#    return cls


#def StageStackCls(name, mdict):
#    """
#    Helper function. Generates a stage stack class from a dictionary of
#    motor base PVs. 
#    """
#    cpts = {}
#    for mname, mprefix in mdict.items():
#        if mprefix:
#            mcls = _GetMotorClass(mprefix, sim=sim)
#            cpt = mcls(prefix=mprefix, name=mname)
#            cpts[mname] = cpt
#    cls_name = name + '_StageStack'
#    cls = type(cls_name, (object,), cpts)
#
#    return cls


#def StageStack(name, x_pv=None, y_pv=None, z_pv=None, roll_pv=None,
#               pitch_pv=None, yaw_pv=None, sim=False, base_class=object):
#    """
#    Factory function for generating a stage stack device. Intended for bundling
#    various motors into a single object. The stack can accommodate up to 6
#    degrees of freedom: x, y, z, roll (rotation in LUSI z), pitch (rotation in
#    LUSI x), and yaw (rotation in LUSI y). The factory function attempts to
#    determine the appropriate motor class from the given base PV; if this fails
#    then it will attempt to create an EpicsMotor. Any axis PVs not specified
#    will result in that degree of freeding being omitted from the device.
#
#    Parameters
#    ----------
#    name : str
#        Name for the stack. Used to make a class name. No whitespace. 
#    x_pv : str
#        Base PV for the x axis.
#    y_pv : str
#        Base PV for the y axis.
#    z_pv : str
#        Base PV for the z axis.
#    roll_pv : str
#        Base PV for the roll axis.
#    pitch_pv : str
#        Base PV for the pitch axis.
#    yaw_pv : str
#        Base PV for the yaw axis.
#
#    Examples
#    --------
#    # Make a classix XYZ stack
#    xyz = StageStack(name='my_xyz', x_pv='TST:MMS:01', y_pv='TST:MMS:02',
#                     z_pv='TST:MMN:01')
#
#    # Make an XYZ stack with a sample goniometer (pitch).
#    xyz_gon = StageStack(name='my_xyzgon', x_pv='TST:MMS:01', y_pv='TST:MMS:02',
#                         z_pv='TST:MMN:01', pitch_pv='TST:MMZ:01')
#
#    # Make an XY stack with a sample rotation stage (yaw).
#    xy_rot = StageStack(name='my_xyrot', x_pv='TST:MMS:01', y_pv='TST:MMS:02',
#                         yaw_pv='TST:MMZ:01')
#    """
#
#    cls = StageStackCls(name, x_pv, y_pv, z_pv, roll_pv, pitch_pv, yaw_pv,
#                        sim=sim)
#    dev = cls()
#
#    return dev


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
        if issubclass(type(mitem), Device): # Motor object
            cpts[mname] = mitem
        elif isinstance(mitem, (str)): # PV
            mcls = _GetMotorClass(mitem)
            cpt = mcls(prefix=mitem, name=mname)
            cpts[mname] = cpt
        else: # Something is wrong
            logger.warning("Unrecognized input {}. "
                           "Skipping axis {}.".format(mitem, mname))
    cls_name = name + '_StageStack'
    cls = type(cls_name, (object,), cpts)

    dev = cls()

    return dev


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
    """
    def __init__(self, x=None, y=None, x_init=None, x_spacing=None,
                 x_comp=None, y_init=None, y_spacing=None, y_comp=None,
                 name=None):
        
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
        Return current position of X and Y axes.
        """
        return {'x': self.x.wm(), 'y': self.y.wm()}

    def reset(self, wait=False):
        """
        Return to the defined initial position (x_init, y_init). Should be 
        called during experiment setup prior to using other class methods to
        initialize the position. 
        """
        self.x.mv(self.x_init, wait=wait)
        self.y.mv(self.y_init, wait=wait)

    def next(self, nspaces=1, wait=False):
        """
        Move forward (in X) by specified integer number of targets.
        """
        self._xgrid.advance(nspaces, 1, wait=wait)
        if self.y_comp:
            self._y_comp_axis.advance(nspaces, 1, wait=wait)

    def back(self, nspaces=1, wait=False):
        """
        Move backward (in X) by specified integer number of targets.
        """
        self._xgrid.advance(nspaces, -1, wait=wait)
        if self.y_comp:
            self._y_comp_axis.advance(nspaces, -1, wait=wait)

    def up(self, nspaces=1, wait=False):
        """
        Move to higher target position by specified integer number of targets
        (stage moves down).
        """
        self._ygrid.advance(nspaces, 1, wait=wait)
        if self.x_comp:
            self._x_comp_axis.advance(nspaces, 1, wait=wait)

    def down(self, nspaces=1, wait=False):
        """
        Move to lower target position by specified integer number of targets
        (stage moves up).
        """
        self._ygrid.advance(nspaces, -1, wait=wait)
        if self.x_comp:
            self._x_comp_axis.advance(nspaces, -1, wait=wait)

    def move(self, nxspaces, nyspaces, wait=False):
        """
        Move to a specific target position given by (xspaces, yspaces)
        from the defined initial position. Includes compensation if defined.
        """
        xpos = self.x_init + self.x_spacing*nxspaces + self.x_comp*nyspaces
        ypos = self.y_init + self.y_spacing*nyspaces + self.y_comp*nxspaces

        self.x.mv(xpos, wait=wait)
        self.y.mv(ypos, wait=wait)


#class XYTargetGrid():
#    """
#    Class methods for managing a target grid oriented normal to the beam, with
#    regular X-Y spacing between targets.
#    """
#    def __init__(self, x_pv=None, y_pv=None, x_init=None, x_spacing=None,
#                 y_init=None, y_spacing=None, sim=False):
#        assert isinstance(x_pv, str), "Must specify a x pv"
#        assert isinstance(y_pv, str), "Must specify a y pv"
#        assert isinstance(x_init, float), "Must specify a float x_init value"
#        assert isinstance(y_init, float), "Must specify a float y_init value"
#        assert isinstance(x_spacing, float), \
#            "Must specify a float x_spacing value"
#        assert isinstance(y_spacing, float), \
#            "Must specify a float y_spacing value"
#
#        self.x_init = x_init
#        self.y_init = y_init
#        self.x_spacing = x_spacing
#        self.y_spacing = y_spacing
#
#        xcls = _GetMotorClass(x_pv, sim=sim) 
#        self.x = xcls(x_pv)
#        self._xgrid = GridAxis(self.x, self.x_spacing)
#        ycls = _GetMotorClass(y_pv, sim=sim) 
#        self.y = ycls(y_pv)
#        self._ygrid = GridAxis(self.y, self.y_spacing)
#
#    def reset(self, wait=False):
#        """
#        Return to the defined initial position (x_init, y_init). Should be 
#        called during experiment setup prior to using other class methods to
#        initialize the position. 
#        """
#        self.x.mv(x_init, wait=wait)
#        self.y.mv(y_init, wait=wait)
#
#    def next(self, n_targets=1, wait=False):
#        """Move forward (in X) by specified integer number of targets."""
#        self._xgrid.advance(n_targets, 1, wait=wait)
#
#    def back(self, n_targets=1, wait=False):
#        """Move backward (in X) by specified integer number of targets."""
#        self._xgrid.advance(n_targets, -1, wait=wait)
#
#    def up(self, n_targets=1, wait=False):
#        """Move up by specified integer number of targets (stage moves down)."""
#        self._ygrid.advance(n_targets, 1, wait=wait)
#
#    def down(self, n_targets=1, wait=False):
#        """Move down by specified integer number of targets (stage moves up)."""
#        self._ygrid.advance(n_targets, -1, wait=wait)
#
#
#def XYZStackXYTargetGrid(name, x_pv=None, y_pv=None, z_pv=None, x_init=None,
#                         x_spacing=None, y_init=None, y_spacing=None,
#                         sim=False):
#
#    stackcls = StageStack(name, x_pv=x_pv, y_pv=y_pv, z_pv=z_pv)
#    cls = type(name+'XYZStackXYTargetGrid', (stackcls, XYTargetGrid,), {})
#    dev = cls(x_pv=None, y_pv=None, z_pv=None, x_init=None,
#                         x_spacing=None, y_init=None, y_spacing=None,
#                         sim=False)
#
#    return dev
