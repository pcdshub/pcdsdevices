'''
Module to define classes for the Facility Monitoring System (FMS), CURRENTLY including Setra5000, levitons, and LCPs
'''
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO
from ophyd import FormattedComponent as FCpt


class Setra5000(Device):
    Time_Stamp = Cpt(EpicsSignalRO, ':TIME', kind='hinted')
    Date = Cpt(EpicsSignalRO, ':DATE', kind='hinted')

    Sample_State = Cpt(EpicsSignalRO, ':SAMP_STATE', kind='hinted')
    Sample_Duration = Cpt(EpicsSignalRO, ':SAMPLE_TIME_RBV', kind='hinted')
    Sample_Mode = Cpt(EpicsSignalRO, ':SAMPLE_MODE_RBV', kind='hinted')
    Mass_Mode = Cpt(EpicsSignalRO, ':MASS_MODE_RBV', kind='hinted')

    Temperature = Cpt(EpicsSignalRO, ':TEMP', kind='hinted')
    RH = Cpt(EpicsSignalRO, ':RH', kind='hinted')
    Barometric_Pressure = Cpt(EpicsSignalRO, ':BP', kind='hinted')
    Flow_Rate = Cpt(EpicsSignalRO, ':FLOW_RATE', kind='hinted')
    CO2 = Cpt(EpicsSignalRO, ':CO2', kind='hinted')
    TVOC = Cpt(EpicsSignalRO, ':TVOC', kind='hinted')
    # kind, doc are important keywords for later
    # kind=hinted, normal, config, omitted
    # Power Distribution Units: Temperature, Humidity, and Load Feed


class PDU_Temp4(Device):

    """ For racks with 2 PDUs, with total of 4 sensors for monitoring purposes """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Temp2(Device):

    """ Will be for portable racks or Racks that have a single PDU, with a total of 2 sensors for monitoring"""

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Temp6(Device):

    """ Will be for PDUs that are linked, 1=Master, 2=Child (4 sensors) plus a single PDU (2 sensors), 6 total sensors """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Temp8(Device):

    """ Will be for PDUs that are linked, 1=Master, 2=Child (4 Sensors) plus 2 single PDUs (4 Sensors), 8 sensors total """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetTempValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor7 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[6]}:Sensor:2:GetTempValue', kind='hinted')
    Sensor8 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[7]}:Sensor:2:GetTempValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Humidity4(Device):

    """ For racks with 2 PDUs, with total of 4 sensors for monitoring purposes """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Humidity2(Device):

    """ Will be for portable racks or Racks that have a single PDU, with a total of 2 sensors for monitoring """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Humidity6(Device):

    """ Will be for PDUs that are linked, 1=Master, 2=Child (4 sensors) plus a single PDU (2 sensors), 6 total sensors """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Humidity8(Device):

    """ Will be for PDUs that are linked, 1=Master, 2=Child (4 Sensors) plus 2 single PDUs (4 Sensors), 8 sensors total """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor5 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[4]}:Sensor:1:GetHumidValue', kind='hinted')
    Sensor6 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[5]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor7 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[6]}:Sensor:2:GetHumidValue', kind='hinted')
    Sensor8 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[7]}:Sensor:2:GetHumidValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Load1(Device):

    """ For racks with 1 PDU """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Load2(Device):

    """ For racks with 2 PDUs """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    # Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:Sensor:1:GetInfeedLoadValue', kind='hinted')
    # Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:Sensor:2:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Load3(Device):

    """ For racks with 3 PDUs """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)


class PDU_Load4(Device):

    """ For racks with 4 PDUs """

    Sensor1 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[0]}:GetInfeedLoadValue', kind='hinted')
    Sensor2 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[1]}:GetInfeedLoadValue', kind='hinted')
    Sensor3 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[2]}:GetInfeedLoadValue', kind='hinted')
    Sensor4 = FCpt(EpicsSignalRO, '{self.prefix}:{self.elevation[3]}:GetInfeedLoadValue', kind='hinted')

    def __init__(self, *args, elevations=[], **kwargs):
        self.elevation = elevations
        super().__init__(*args, **kwargs)

# FEE ALCOVE LCPs


class LCP1(Device):

    """ For LCPs with CMC-III PU, with Door Module off """

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

    """ For LCPs with CMC-III PU, with Door Module working """

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
