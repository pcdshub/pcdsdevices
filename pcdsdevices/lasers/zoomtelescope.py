import logging

from ophyd import Device, EpicsSignal, EpicsSignalRO, Component as Cpt

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

    zt.req_zoom.put(1.5)     # set the zoom factor to 1.5

    zt.tweak_val.put(0.05)   # set tweak parameter to 0.05

    zt.tweak_plus.put(1)     # tweak the zoom by +zt.tweak_val

    zt.tweak_minus.put(1)    # tweak the zoom by +zt.tweak_val
    """

    # Calibration parameters
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

    min_zoom = Cpt(EpicsSignalRO, ':CAL:MIN_ZOOM', kind='config')
    max_zoom = Cpt(EpicsSignalRO, ':CAL:MAX_ZOOM', kind='config')

    # Control parameters
    req_zoom = Cpt(EpicsSignal, ':REQ_ZOOM', kind='normal')

    tweak_plus = Cpt(EpicsSignal, ':TWEAK_ZOOM_PLUS.PROC', kind='normal')
    tweak_minus = Cpt(EpicsSignal, ':TWEAK_ZOOM_MINUS.PROC', kind='normal')
    tweak_val = Cpt(EpicsSignal, ':TWEAK', kind='normal')

    permission = Cpt(EpicsSignalRO, ':PERMISSION_STATUS', kind='normal')
