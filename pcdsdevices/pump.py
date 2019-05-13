"""
Standard classes for LCLS Gauges
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Component as Cpt

logger = logging.getLogger(__name__)

class TurboPump(Device):
    """
    Vacuum Pump
    """
    # 
    atspeed = Cpt(EpicsSignal, ':ATSPEED_DI', kind='normal')
    start = Cpt(EpicsSignal, ':START_SW', kind='normal')

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)


class EbaraPump(Device):
    """
    Ebara Turbo Pump
    """
    # 
    start = Cpt(EpicsSignal, ':MPSTART_SW', kind='normal')

    def run(self):
        """Start the Turbo Pump"""
        self.start.put(1)

    def stop(self):
        """Start the Turbo Pump"""
        self.start.put(0)

class IonPump(Device):
    """
    Ion Pump (Gamma controller)
    """
    # 
    pressure = Cpt(EpicsSignalRO, ':PMON', kind='normal')
    current = Cpt(EpicsSignalRO, ':IMON', kind='normal')
    voltage = Cpt(EpicsSignalRO, ':VMON', kind='normal')
    status_code = Cpt(EpicsSignalRO, ':STATUSCODE', kind='normal')
    status = Cpt(EpicsSignalRO, ':STATUS', kind='normal')
    #check if this work as its an enum
    state = Cpt(EpicsSignal, ':STATEMON', write_pv=':STATEDES', kind='normal')
    #state_rbk = Cpt(EpicsSignal, ':STATEMON', kind='normal')
    #state_cmd = Cpt(EpicsSignal, ':STATEDES', kind='normal')

    pumpsize = Cpt(EpicsSignal, ':PUMPSIZEDES', write_pv=':PUMPSIZE', kind='omitted')
    controllername = Cpt(EpicsSignal, ':VPCNAME', kind='omitted')
    hvstrapping = Cpt(EpicsSignal, ':VDESRBCK', kind='omitted')
    supplysize = Cpt(EpicsSignalRO, ':SUPPLYSIZE', kind='omitted')
    egu = Cpt(EpicsSignalRO, ':PMON.EGU', kind='omitted')

    aomode = Cpt(EpicsSignal, ':AOMODEDES', write_pv=':AOMODE', kind='config')
    calfactor = Cpt(EpicsSignal, ':CALFACTOREDES', write_pv=':CALFACTOR', kind='config')

    def on(self):
        self.state.put(1)

    def off(self):
        self.state.put(0)

    def __repr__(self):
        print('Pump is %s'%self.state)
        if self.state>0:
            print('Pressure: %g'%self.pressure)
            print('Current: %g'%self.current)
            print('Voltage: %g'%self.voltage)
