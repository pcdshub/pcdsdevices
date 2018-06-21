from ophyd.device import Device, Component as Cpt
from ophyd.signal import EpicsSignalRO, AttributeSignal

from .signal import AvgSignal


class BeamStats(Device):
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC')
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID')

    mj_avg = Cpt(AvgSignal, 'mj', averages=120)
    mj_buffersize = Cpt(AttributeSignal, 'mj_avg.averages')

    _default_read_attrs = ['mj', 'mj_avg', 'ev', 'rate']
    _default_configuration_attrs = ['mj_buffersize']

    def __init__(self, prefix='', name='beam_stats', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)

    @property
    def hints(self):
        return {'fields': [self.mj.name]}


class SxrGmd(Device):
    mj = Cpt(EpicsSignalRO, 'SXR:GMD:BLD:milliJoulesPerPulse')

    def __init__(self, prefix='', name='sxr_gmd', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)

    @property
    def hints(self):
        return {'fields': [self.mj.name]}
