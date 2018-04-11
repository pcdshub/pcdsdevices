from ophyd.device import Device, Component as Cpt
from ophyd.signal import EpicsSignalRO


class BeamStats(Device):
    ev = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO541')
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID')

    _default_read_attrs = ['ev', 'mj', 'rate']
