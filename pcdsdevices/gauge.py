"""
Standard classes for LCLS Gauges
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Device, Component as Cpt

logger = logging.getLogger(__name__)

class BaseGauge(Device):
    """
    Vacuum gauge

    A base class for a device with two limits switches controlled via an
    external command PV. This fully encompasses the controls `Stopper`
    installations as well as un-interlocked `GateValves`

    Parameters
    ----------
    prefix : ``str``
        Full Gauge base PV

    name : ``str``
        Alias for the gauge
    """
    # 
    pressure = Cpt(EpicsSignalRO, ':PMON', kind='normal')
    status = Cpt(EpicsSignalRO, ':STATUSMON', kind='normal')
    pressure_status = Cpt(EpicsSignalRO, ':PSTATMON', kind='normal')
    pressure_status_enable = Cpt(EpicsSignal, ':PSTATMSP', kind='normal')

    def __repr__(self):
        print('Gauge is %s'%self.status)
        if self.status>0:
            print('Pressure: %g'%self.pressure)

class GaugePirani(BaseGauge):
    """
    Class for Pirani gauge
    """
    pass

class GaugeColdCathode(BaseGauge):
    """
    Class for Cold Cathode Gauge
    """
    enable = Cpt(EpicsSignalRO, ':ENB_DO_SW', kind='normal')
    #this should be combined.
    tripSetpointRB = Cpt(EpicsSignal, ':PSTATSPDES', kind='normal')
    tripSetpoint = Cpt(EpicsSignalRO, ':PSTATSPRBCK', kind='normal')

class GaugeSet(Device):
    """
    Class for a gauge set with a Pirani and Cold Cathode Gauge
    argument is the base PV for the cold cathode gauge
    """
    gpi = Cpt(GaugePirani, self.prefix.replace('GCC','GPI'))
    gcc = Cpt(GaugeColdCathode)
    
    def pressure(self):
        if self.gcc.status > 0:
            return self.gcc.pmon
        else:
            return self.gpi.pmon

