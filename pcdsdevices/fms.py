"""
CXI:SETRA:01:PERIODS_RBV 60 monitor
CXI:SETRA:01:DELAY_TIME_RBV 60 monitor
CXI:SETRA:01:SAMPLE_TIME_RBV 60 monitor
CXI:SETRA:01:HOLD_TIME_RBV 60 monitor
CXI:SETRA:01:SAMPLE_MODE_RBV 60 monitor
CXI:SETRA:01:MASS_MODE_RBV 60 monitor
CXI:SETRA:01:RECIPE_MODE_RBV 60 monitor
CXI:SETRA:01:RECORD_REQ 60 monitor
CXI:SETRA:01:RH 60 monitor
CXI:SETRA:01:BP 60 monitor
CXI:SETRA:01:TEMP 60 monitor
CXI:SETRA:01:DATE 60 monitor
CXI:SETRA:01:TIME 60 monitor
CXI:SETRA:01:TVOC 60 monitor
CXI:SETRA:01:CO2 60 monitor
CXI:SETRA:01:FLOW_RATE 60 monitor
CXI:SETRA:01:SAMPLE_DURATION 60 monitor
CXI:SETRA:01:CH0_SIZE 60 monitor
CXI:SETRA:01:CH0_MASS 60 monitor
CXI:SETRA:01:CH1_SIZE 60 monitor
CXI:SETRA:01:CH1_MASS 60 monitor
CXI:SETRA:01:CH2_SIZE 60 monitor
CXI:SETRA:01:CH2_MASS 60 monitor
CXI:SETRA:01:CH3_SIZE 60 monitor
CXI:SETRA:01:CH3_MASS 60 monitor
CXI:SETRA:01:CH4_SIZE 60 monitor
CXI:SETRA:01:CH4_MASS 60 monitor
CXI:SETRA:01:CH5_SIZE 60 monitor
CXI:SETRA:01:CH5_MASS 60 monitor
"""


from ophyd import Component as Cpt, Device, EpicsSignalRO
from ophyd import FormattedComponent as FCpt, EpicsSignalRO, Device

class Setra5000(Device):
    Timestamp = Cpt(EpicsSignalRO, ':TIME', kind='hinted')
    Date = Cpt(EpicsSignalRO, ':DATE', kind='hinted')

    SampleState = Cpt(EpicsSignalRO, ':SAMP_STATE', kind='hinted')
    SampleDuration = Cpt(EpicsSignalRO, ':SAMPLE_TIME_RBV', kind='hinted')
    SampleMode = Cpt(EpicsSignalRO, ':SAMPLE_MODE_RBV', kind='hinted')
    MassMode = Cpt(EpicsSignalRO, ':MASS_MODE_RBV', kind='hinted')
    
    Temperature = Cpt(EpicsSignalRO, ':TEMP', kind='hinted')
    RH = Cpt(EpicsSignalRO, ':RH', kind='hinted')
    BarometricPressure = Cpt(EpicsSignalRO, ':BP', kind='hinted')
    FlowRate = Cpt(EpicsSignalRO, ':FLOW_RATE', kind='hinted')
    CO2 = Cpt(EpicsSignalRO, ':CO2', kind='hinted')
    TVOC = Cpt(EpicsSignalRO, ':TVOC', kind='hinted')    

    '''
    ch0_size = Cpt(EpicsSignalRO, ':CH0_SIZE', kind='normal')
    ch0_mass = Cpt(EpicsSignalRO, ':CH0_MASS', kind='normal')
    ch1_size = Cpt(EpicsSignalRO, ':CH1_SIZE', kind='normal')
    ch1_mass = Cpt(EpicsSignalRO, ':CH1_MASS', kind='normal')
    ch2_size = Cpt(EpicsSignalRO, ':CH2_SIZE', kind='normal')
    ch2_mass = Cpt(EpicsSignalRO, ':CH2_MASS', kind='normal')
    ch3_size = Cpt(EpicsSignalRO, ':CH3_SIZE', kind='normal')
    ch3_mass = Cpt(EpicsSignalRO, ':CH3_MASS', kind='normal')
    ch4_size = Cpt(EpicsSignalRO, ':CH4_SIZE', kind='normal')
    ch4_mass = Cpt(EpicsSignalRO, ':CH4_MASS', kind='normal')
    ch5_size = Cpt(EpicsSignalRO, ':CH5_SIZE', kind='normal')
    ch5_mass = Cpt(EpicsSignalRO, ':CH5_MASS', kind='normal')
    Total_Mass = Cpt(EpicsSignalRO, ':TOT_MASS', kind='normal')
    '''

    # kind, doc are important keywords for later
    # kind=hinted, normal, config, omitted



 #Power Distribution Units: Temperature, Humidity, and Load Feed

#PDU_Temp1: Will be for racks with 2 PDUs, with total of 3 sensors for monitoring purposes
class PDU_Temp1(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

#PDU_Temp2: Will be for portable racks or Racks that have a single PDU, with a total of 2 sensors for monitoring
class PDU_Temp2(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

#PDU_Temp3: Will be for PDUs that are linked, 1=Master, 2=Child

class PDU_Temp3(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetTempValue', kind='hinted')
       
    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Temp4(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor7 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[6]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor8 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[7]}:Sensor:2:GetTempValue', kind='hinted')
    
    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

"""
class PDU_Temp4(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)
"""
#PDU_Temp1(elevations = [15, 15, 32])

class PDU_Humidity1(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

#PDU_Temp2: Will be for portable racks or Racks that have a single PDU, with a total of 2 sensors for monitoring
class PDU_Humidity2(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Humidity3(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Humidity4(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor7 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[6]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor8 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[7]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Load1(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Load2(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    #Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetInfeedLoadValue', kind='hinted')
    #Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Load3(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

class PDU_Load4(Device):
    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:GetInfeedLoadValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations = [], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

#LCP FEE ALCOVE TEMP

class LCP1(Device):
   Temperature_F = Cpt(EpicsSignalRO, ':Temperature_CALC', kind='hinted')
   Power_Vsupply_V = Cpt(EpicsSignalRO, ':24Vsupply_CALC', kind='hinted')
   AirFan1Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan1Rpm_CALC', kind='hinted')
   AirFan2Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan2Rpm_CALC', kind='hinted')
   AirFan3Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan3Rpm_CALC', kind='hinted')
   AirFan4Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan4Rpm_CALC', kind='hinted')
   AirFan5Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan5Rpm_CALC', kind='hinted')
   AirFan6Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan6Rpm_CALC', kind='hinted')
   WaterTempIn_F = Cpt(EpicsSignalRO, ':WaterTempIn_CALC', kind='hinted')
   WaterTempOut_F = Cpt(EpicsSignalRO, ':WaterTempOut_CALC', kind='hinted')
   WaterFlowRate_gpm = Cpt(EpicsSignalRO, ':WaterFlowRate_CALC', kind='hinted')
   AirTempInTop_F = Cpt(EpicsSignalRO, ':AirTempInTop_CALC', kind='hinted')
   AirTempInMid_F = Cpt(EpicsSignalRO, ':AirTempInMid_CALC', kind='hinted')
   AirTempInBot_F = Cpt(EpicsSignalRO, ':AirTempInBot_CALC', kind='hinted')
   AirTempOutTop_F = Cpt(EpicsSignalRO, ':AirTempOutTop_CALC', kind='hinted')
   AirTempOutMid_F = Cpt(EpicsSignalRO, ':AirTempOutMid_CALC', kind='hinted')
   AirTempOutBot_F = Cpt(EpicsSignalRO, ':AirTempOutBot_CALC', kind='hinted')
  
class LCP2(Device):
   Temperature_F = Cpt(EpicsSignalRO, ':Temperature_CALC', kind='hinted')
   Power_Vsupply_V = Cpt(EpicsSignalRO, ':24Vsupply_CALC', kind='hinted')
   AirFan1Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan1Rpm_CALC', kind='hinted')
   AirFan2Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan2Rpm_CALC', kind='hinted')
   AirFan3Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan3Rpm_CALC', kind='hinted')
   AirFan4Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan4Rpm_CALC', kind='hinted')
   AirFan5Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan5Rpm_CALC', kind='hinted')
   AirFan6Rpm_Percent = Cpt(EpicsSignalRO, ':AirFan6Rpm_CALC', kind='hinted')
   WaterTempIn_F = Cpt(EpicsSignalRO, ':WaterTempIn_CALC', kind='hinted')
   WaterTempOut_F = Cpt(EpicsSignalRO, ':WaterTempOut_CALC', kind='hinted')
   WaterFlowRate_gpm = Cpt(EpicsSignalRO, ':WaterFlowRate_CALC', kind='hinted')
   AirTempInTop_F = Cpt(EpicsSignalRO, ':AirTempInTop_CALC', kind='hinted')
   AirTempInMid_F = Cpt(EpicsSignalRO, ':AirTempInMid_CALC', kind='hinted')
   AirTempInBot_F = Cpt(EpicsSignalRO, ':AirTempInBot_CALC', kind='hinted')
   AirTempOutTop_F = Cpt(EpicsSignalRO, ':AirTempOutTop_CALC', kind='hinted')
   AirTempOutMid_F = Cpt(EpicsSignalRO, ':AirTempOutMid_CALC', kind='hinted')
   AirTempOutBot_F = Cpt(EpicsSignalRO, ':AirTempOutBot_CALC', kind='hinted')
   FrontDoorAccess = Cpt(EpicsSignalRO, ':FrontDoorAccess_CALC', kind='hinted')
   RearDoorAccess = Cpt(EpicsSignalRO, ':RearDoorAccess_CALC', kind='hinted')

