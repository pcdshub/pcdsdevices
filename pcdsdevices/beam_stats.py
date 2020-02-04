from ophyd.device import Device, Component as Cpt
from ophyd.signal import EpicsSignalRO, AttributeSignal

from .signal import AvgSignal
from .interface import BaseInterface


class BeamStats(Device, BaseInterface):
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC', kind='hinted')
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY', kind='normal')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE', kind='normal')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID', kind='omitted')

    mj_avg = Cpt(AvgSignal, 'mj', averages=120, kind='normal')
    mj_buffersize = Cpt(AttributeSignal, 'mj_avg.averages', kind='config')

    tab_component_names = True

    def __init__(self, prefix='', name='beam_stats', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)


class SxrGmd(Device):
    mj = Cpt(EpicsSignalRO, 'SXR:GMD:BLD:milliJoulesPerPulse', kind='hinted')

    def __init__(self, prefix='', name='sxr_gmd', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)
