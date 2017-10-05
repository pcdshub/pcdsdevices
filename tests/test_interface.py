############
# Standard #
############

###############
# Third Party #
###############
from ophyd import Device

##########
# Module #
##########
import pcdsdevices
from pcdsdevices.interface import MPSInterface, BranchingInterface, LightInterface

class BasicDevice(Device, metaclass=LightInterface):

    @property
    def z(self):
        """
        Z position along the beamline
        """
        return None

    @property
    def beamline(self):
        """
        Specific beamline the device is on
        """
        return None


    @property
    def transmission(self):
        """
        Approximate transmission of X-rays through device
        """
        return None


    @property
    def inserted(self):
        """
        Report if the device is inserted into the beam
        """
        return None


    @property
    def removed(self):
        """
        Report if the device is inserted into the beam
        """
        return None


    def remove(self, timeout=None, finished_cb=None):
        """
        Remove the device from the beampath
        """
        pass


    def subscribe(cb, event_type=None, run=False, **kwargs):
        """
        Subscribe a callback function to run when the device changes state
        """
        pass


class BasicBranching(Device, metaclass=BranchingInterface):
    @property
    def z(self):
        """
        Z position along the beamline
        """
        return None

    @property
    def beamline(self):
        """
        Specific beamline the device is on
        """
        return None


    @property
    def transmission(self):
        """
        Approximate transmission of X-rays through device
        """
        return None


    @property
    def inserted(self):
        """
        Report if the device is inserted into the beam
        """
        return None


    @property
    def removed(self):
        """
        Report if the device is inserted into the beam
        """
        return None


    def remove(self, timeout=None, finished_cb=None):
        """
        Remove the device from the beampath
        """
        pass


    def subscribe(cb, event_type=None, run=False, **kwargs):
        """
        Subscribe a callback function to run when the device changes state
        """
        pass

    @property
    def branching(self):
        return None

    @property
    def destination(self):
        return None


class MPS(Device, metaclass=MPSInterface):
    """
    Basic MPS implementation
    """
    @property
    def faulted(self):
        return None

    @property
    def bypassed(self):
        return None

    @property
    def veto_capable(self):
        return None


def test_basic_interface():
    device = BasicDevice("base")
    #Check that our class is a LightInterface type 
    assert type(BasicDevice) == LightInterface
    #Check that the device is a pcdsdevice
    assert isinstance(device, Device)


def test_branching_interface():
    device = BasicBranching("base")
    #Check that our class is a LightInterface type 
    assert type(BasicBranching) == BranchingInterface
    #Check that the device is a pcdsdevice
    assert isinstance(device, Device)


def test_mps_interface():
    device = MPS("base")
    #Check that our class is a LightInterface type 
    assert type(MPS) == MPSInterface
    #Check that the device is an ophyd device
    #It can not be a pcdsdevices because this uses LightInterface
    assert isinstance(device, Device)

def test_device_metadata():
    d = pcdsdevices.device.Device('Tst:Device', beamline='TST', z=10.0)
    assert d.beamline == 'TST'
    assert d.z == 10.0

