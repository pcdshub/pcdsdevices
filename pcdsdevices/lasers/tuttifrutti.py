"""
Classes for the Tuttifrutti diagnostic stack designed for the MODS TILEs.
"""

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.device import create_device_from_components

from pcdsdevices.areadetector.detectors import PCDSAreaDetectorTyphos
from pcdsdevices.lasers.qmini import QminiSpectrometer
from pcdsdevices.lasers.ek9000 import El3174AiCh
from pcdsdevices.lasers.elliptec import Ell6


def TuttiFrutti(prefix, name, nf=False, ff=False, spec=False, pm=False,
                diode=False, em=False, qc=False, pd=False, wfs=False,
                ell=False, misc=[]):
    """
    Factory function for Tuttifrutti diagnostic stack device. Returns a class
    based on the diagnostics installed.

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

    wfs : bool <False> (Not Implemented)
        Flag indicating if a wavefront sensor is installed.

    ell : bool <False>
        Flag indicating if a 2-position filter slider is installed is
        installed.

    misc : dict of ophyd.FormattedComponent <empty>
        Dictionary of FCpt for providing miscellaneous Ophyd Component objects
        to the TuttiFrutti. Used for non-standard devices or when you need to
        hack in a component that hasn't made it into a released TuttiFrutti
        object yet (can you say "Commissioning"?). The dictionary key is the
        desired name of the component.

        Note: you must use the full base PV in the FCpt when instantiating it
        (see example), even if the base PV is the same as the TuttiFrutti. We
        are using FCpt here to get around possible PV naming incompatibilities
        (I'm looking at you, EK9000...).

    Examples
    --------
    # Create an object for a basic tuttifrutti containing NF/FF cameras,
    # a spectrometer, and a filter slider.

    ttf = TutttFruttiBase('LAS:TTF:01', nf=True, ff=True, spec=True, ell=True)

    # Create a TuttiFrutti as above, while including a non-standard component.

    from ophyd import FormattedComponent as FCpt

    from fruit import Banana
    banana = FCpt(Banana, 'IOC:LAS:BANANA', kind='normal') # Use full base PV

    dmisc = {'banana' : banana}

    ttf = TutttFruttiBase('LAS:TTF:01', nf=True, ff=True, spec=True, ell=True,
                           misc=[dmisc])
    """
    cpts = {}
    if nf:
        cpt = Cpt(PCDSAreaDetectorTyphos, '_NF:', kind='normal')
        cpts['nf_camera'] = cpt
    if nf:
        cpt = Cpt(PCDSAreaDetectorTyphos, '_FF:', kind='normal')
        cpts['ff_camera'] = cpt
    if spec:
        cpt = Cpt(QminiSpectrometer, '_SP', kind='normal')
        cpts['spectrometer'] = cpt
    if pm:
        cpt = Cpt(El3174AiCh, '_PM', kind='normal')
        cpts['power_meter'] = cpt
    if diode:
        raise(NotImplemented, "Diode is not yet implemented")
    if em:
        raise(NotImplemented, "Energy meter is not yet implemented")
    if qc:
        raise(NotImplemented, "Quad cell is not yet implemented")
    if pd:
        raise(NotImplemented, "Pulse duration is not yet implemented")
    if wfs:
        raise(NotImplemented, "Wavefront sensor is not yet implemented")
    if ell:
        cpt = Cpt(Ell6, '_SL', kind='normal')
        cpts['slider'] = cpt
    # This feels kind of hacky, but also kind of cool.
    if misc:
        for cptname, cpt in misc.items():
            cpts[cptname] = cpt
    cls_name = prefix.replace(':', '_') + '_TuttiFrutti'
    cls = create_device_from_components(cls_name, base_class=Device,
                                        class_kwargs=None, **cpts)

    dev = cls(prefix, name=name)

    return dev
