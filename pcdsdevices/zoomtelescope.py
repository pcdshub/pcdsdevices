import logging

from ophyd import Device, EpicsSignal, EpicsSignalRO, Component as Cpt
from ophyd.status import DeviceStatus, SubscriptionStatus
from ophyd.utils.epics_pvs import raise_if_disconnected

logger = logging.getLogger(__name__)

class ZoomTelescope(Device):
    """
    Zoom telescope

    Device for the zoom telescope used in the MODS TILEs.

    Parameters
    ----------
    prefix : str
        Base prefix of the zoom telescope 

    name : str
        Name of zoom telescope object

    Examples
    --------

    zt = ZoomTelescope('LAS:ZOOM:01', name='LAS Zoom 1')

    zt.zoom = 1.5 # set the zoom to 1.5x magnification

    zt.tweak_val = 0.05 # set tweak parameter to 0.05

    zt.tweak_plus()     # tweak the zoom by +zt.tweak_val

    zt.tweak_minus()     # tweak the zoom by +zt.tweak_val
    """

    ### Calibration parameters
    # Not sure about putting these calibration parameters in here, since they 
    # should never really be required during normal operation, but will leave 
    # them in for debugging during commissioning.
    _l2_p0 = Cpt(EpicsSignalRO, ':CAL:L2:P0', kind='omitted')
    _l2_p1 = Cpt(EpicsSignalRO, ':CAL:L2:P1', kind='omitted')

    _l3_p0 = Cpt(EpicsSignalRO, ':CAL:L3:P0', kind='omitted')
    _l3_p1 = Cpt(EpicsSignalRO, ':CAL:L3:P1', kind='omitted')
    _l3_p2 = Cpt(EpicsSignalRO, ':CAL:L3:P2', kind='omitted')
    _l3_p3 = Cpt(EpicsSignalRO, ':CAL:L3:P3', kind='omitted')
    _l3_p4 = Cpt(EpicsSignalRO, ':CAL:L3:P4', kind='omitted')
    _l3_p5 = Cpt(EpicsSignalRO, ':CAL:L3:P5', kind='omitted')

    _min_zoom = Cpt(EpicsSignalRO, ':CAL:MIN_ZOOM', kind='config')
    _max_zoom = Cpt(EpicsSignalRO, ':CAL:MAX_ZOOM', kind='config')

    ### Control parameters
    _req_zoom = Cpt(EpicsSignal, ':REQ_ZOOM', kind='normal')

    _tweak_plus = Cpt(EpicsSignal, ':TWEAK_ZOOM_PLUS.PROC', kind='normal')
    _tweak_minus = Cpt(EpicsSignal, ':TWEAK_ZOOM_MINUS.PROC', kind='normal')
    _tweak_val = Cpt(EpicsSignal, ':TWEAK', kind='normal')

    _permission = Cpt(EpicsSignalRO, ':PERMISSION_STATUS', kind='normal')

    @property
    def tweak_val(self):  
        """The amount to tweak the magnification when calling tweak_plus or
        tweak_minus."""
        tweak = self._tweak_val.get()
        return tweak

    @tweak_val.setter
    def tweak_val(self, val):
        self._tweak_val.put(val)

    def tweak_plus(self):
        """Adjust the magnification by +tweak_val."""
        self._tweak_plus.put(1)

    def tweak_minus(self):
        """Adjust the magnification by -tweak_val."""
        self._tweak_minus.put(1)

    @property
    def zoom(self):
        """Get/Set the zoom level of the zoom telescope."""
        return self._req_zoom.get()

    @zoom.setter
    def zoom(self, val):
        minz = self._min_zoom.get()
        maxz = self._max_zoom.get()

        if val <= maxz and val >= minz:
            self._req_zoom.put(val)
        else:
            m = "Please select a zoom between {} and {}!".format(minz, maxz)
            raise Exception(m)
