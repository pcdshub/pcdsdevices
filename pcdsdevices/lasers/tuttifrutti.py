"""
Classes for the Tuttifrutti diagnostic stack designed for the MODS TILEs.
"""

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.device import create_device_from_components

from pcdsdevices.areadetector.detectors import LasBasler
from pcdsdevices.lasers.ek9000 import El3174AiCh
from pcdsdevices.lasers.elliptec import Ell6
from pcdsdevices.lasers.qmini import QminiSpectrometer
from pcdsdevices.lasers.thorlabsWFS import ThorlabsWfs40


def TuttiFruttiCls(prefix, name, nf=False, ff=False, spec=False, pm=False,
                   diode=False, em=False, qc=False, pd=False, wfs=False,
                   ell=False, ellch=1, misc=[]):
    """
    Generate a TuttiFrutti class. See TuttiFrutti function for more details.
    """
    cpts = {}
    if nf:
        cpt = Cpt(LasBasler, '_NF1:', kind='normal')
        cpts['nf_camera'] = cpt
    if nf:
        cpt = Cpt(LasBasler, '_FF1:', kind='normal')
        cpts['ff_camera'] = cpt
    if spec:
        cpt = Cpt(QminiSpectrometer, '_SP1', kind='normal')
        cpts['spectrometer'] = cpt
    if pm:
        cpt = Cpt(El3174AiCh, '_PM1', kind='normal')
        cpts['power_meter'] = cpt
    if diode:
        raise NotImplementedError("Diode is not yet implemented")
    if em:
        raise NotImplementedError("Energy meter is not yet implemented")
    if qc:
        raise NotImplementedError("Quad cell is not yet implemented")
    if pd:
        raise NotImplementedError("Pulse duration is not yet implemented")
    if wfs:
        cpt = Cpt(ThorlabsWfs40, '_WF1:', kind='normal')
        cpts['wfs'] = cpt
    if ell:
        cpt = Cpt(Ell6, '_SL1:ELL', channel=ellch, kind='normal')
        cpts['slider'] = cpt
    if misc:  # This feels kind of hacky, but also kind of cool.
        for cptname, cpt in misc.items():
            cpts[cptname] = cpt
    cls_name = prefix.replace(':', '_') + '_TuttiFrutti'
    cls = create_device_from_components(cls_name, base_class=Device,
                                        class_kwargs=None, **cpts)

    return cls


def TuttiFrutti(prefix, name, nf=False, ff=False, spec=False, pm=False,
                diode=False, em=False, qc=False, pd=False, wfs=False,
                ell=False, ellch=1, misc=[]):
    """
    Factory function for Tuttifrutti diagnostic stack device. Returns a device
    based on the specified components.

    Sufficient for basic control and generation of Typhos screens.

    Parameters
    ----------
    prefix : str
        The PV base of the tuttifrutti diagnostic stack. All consituent
        diagnostics have regimented PV suffixes based on this prefix.

    name: str
        The name of the TuttiFrutti device.

    nf : bool <False>
        Flag indicating if a near-field camera is installed.

    ff : bool <False>
        Flag indicating if a far-field camera is installed.

    spec : bool <False>
        Flag indicating if a spectrometer is installed.

    pm : bool <False>
        Flag indicating if a power meter is installed.

    diode : bool <False> (Not Implemented)
        Flag indicating if a diode is installed.

    em : bool <False> (Not Implemented)
        Flag indicating if an energy meter is installed.

    qc : bool <False> (Not Implemented)
        Flag indicating if a quad cell detector is installed.

    pd : bool <False> (Not Implemented)
        Flag indicating if a pulse duration diagnostic is installed.

    wfs : bool <False>
        Flag indicating if a wavefront sensor is installed.

    ell : bool <False>
        Flag indicating if a 2-position filter slider is installed is
        installed.

    ellch : int <0x1>
        The integer channel that the slider is assigned to on the controller.
        Typically between 0x1 and 0x3, up to 0xF.

    misc : dict of ophyd.Component or ophyd.FormattedComponent <empty>
        Dictionary of Cpt and/or FCpt for providing miscellaneous Ophyd
        Component objects to the TuttiFrutti. Used for non-standard devices or
        when you need to hack in a component that hasn't made it into a
        released version of TuttiFrutti object yet (can you say
        "Commissioning"?). The dictionary key is the desired name of the
        attribute name for the component.

        Note: you must use the full base PV in the FCpt when instantiating it
        (see example), even if the base PV is the same as the TuttiFrutti. We
        can use FCpt here to temporarily get around possible PV naming
        incompatibilities with the L2SI laser PV naming convention (I'm looking
        at you, EK9000...).

    Examples
    --------
    # Create an object for a basic tuttifrutti containing NF/FF cameras,
    # a spectrometer, and a filter slider.

    ttf = TuttiFrutti('LAS:TTF:01', nf=True, ff=True, spec=True, ell=True)

    # Create a TuttiFrutti as above, while including a non-standard component.

    from ophyd import Component as Cpt
    from ophyd import FormattedComponent as FCpt

    from fruit import Apple, Orange
    apple = Cpt(Apple, ':APPLE', kind='normal') # Use TuttiFrutti base PV
    orange = FCpt(Orange, 'IOC:LAS:ORANGE', kind='normal') # Use full base PV

    dmisc = {'apple': apple, 'orange' : orange}

    ttf = TuttiFrutti('LAS:TTF:01', nf=True, ff=True, spec=True, ell=True,
                           misc=dmisc)
    """
    cls = TuttiFruttiCls(prefix, name, nf=nf, ff=ff, spec=spec, pm=pm,
                         diode=diode, em=em, qc=qc, pd=pd, wfs=wfs, ell=ell,
                         ellch=ellch, misc=misc)
    dev = cls(prefix, name=name)

    return dev
