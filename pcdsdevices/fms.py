"""
Module to define classes for the Facility Monitoring System (FMS),
CURRENTLY including Setra5000, levitons, and LCPs
"""
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .analog_signals import FDQ
from .utils import reorder_components


class Setra5000(Device):
    time_stamp = Cpt(EpicsSignalRO, ':TIME', kind='hinted')
    date = Cpt(EpicsSignalRO, ':DATE', kind='hinted')

    sample_state = Cpt(EpicsSignalRO, ':SAMP_STATE', kind='hinted')
    sample_duration = Cpt(EpicsSignalRO, ':SAMPLE_TIME_RBV', kind='hinted')
    sample_mode = Cpt(EpicsSignalRO, ':SAMPLE_MODE_RBV', kind='hinted')
    mass_mode = Cpt(EpicsSignalRO, ':MASS_MODE_RBV', kind='hinted')

    temperature = Cpt(EpicsSignalRO, ':TEMP', kind='hinted')
    rh = Cpt(EpicsSignalRO, ':RH', kind='hinted')
    barometric_pressure = Cpt(EpicsSignalRO, ':BP', kind='hinted')
    flow_rate = Cpt(EpicsSignalRO, ':FLOW_RATE', kind='hinted')
    CO2 = Cpt(EpicsSignalRO, ':CO2', kind='hinted')
    TVOC = Cpt(EpicsSignalRO, ':TVOC', kind='hinted')
    # kind, doc are important keywords for later
    # kind=hinted, normal, config, omitted
    # Power Distribution Units: Temperature, Humidity, and Load Feed


class PDU_Temp4(Device):
    """ For racks with 2 PDUs, with total of 4 sensors for monitoring purposes """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetTempValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Temp2(Device):
    """
    Will be for portable racks or Racks that have a single PDU,
    with a total of 2 sensors for monitoring
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}Sensor:1:GetTempValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}Sensor:2:GetTempValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Temp6(Device):
    """
    Will be for PDUs that are linked, 1=Master, 2=Child (4 sensors)
    plus a single PDU (2 sensors), 6 total sensors
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor5 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[4]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor6 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[5]}:Sensor:2:GetTempValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Temp8(Device):
    """
    Will be for PDUs that are linked, 1=Master, 2=Child (4 Sensors)
    plus 2 single PDUs (4 Sensors), 8 sensors total
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor5 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[4]}:Sensor:1:GetTempValue',
                   kind='hinted')
    sensor6 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[5]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor7 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[6]}:Sensor:2:GetTempValue',
                   kind='hinted')
    sensor8 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[7]}:Sensor:2:GetTempValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Humidity4(Device):
    """ For racks with 2 PDUs, with total of 4 sensors for monitoring purposes """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetHumidValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Humidity2(Device):
    """
    Will be for portable racks or Racks that have a single PDU,
    with a total of 2 sensors for monitoring
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}Sensor:2:GetHumidValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Humidity6(Device):
    """
    Will be for PDUs that are linked, 1=Master, 2=Child (4 sensors)
    plus a single PDU (2 sensors), 6 total sensors
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor5 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[4]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor6 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[5]}:Sensor:2:GetHumidValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Humidity8(Device):
    """
    Will be for PDUs that are linked, 1=Master, 2=Child (4 Sensors)
    plus 2 single PDUs (4 Sensors), 8 sensors total
    """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor5 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[4]}:Sensor:1:GetHumidValue',
                   kind='hinted')
    sensor6 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[5]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    sensor7 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[6]}:Sensor:2:GetHumidValue',
                   kind='hinted')
    Sensor8 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[7]}:Sensor:2:GetHumidValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Load1(Device):
    """ For racks with 1 PDU """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}GetInfeedLoadValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Load2(Device):
    """ For racks with 2 PDUs """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:GetInfeedLoadValue',
                   kind='hinted')
    # sensor3 = FCpt(EpicsSignalRO,
    #                '{prefix}:{elevation[2]}:Sensor:1:GetInfeedLoadValue',
    #                kind='hinted')
    # sensor4 = FCpt(EpicsSignalRO,
    #                '{prefix}:{elevation[3]}:Sensor:2:GetInfeedLoadValue',
    #                kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Load3(Device):
    """ For racks with 3 PDUs """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:GetInfeedLoadValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)


class PDU_Load4(Device):
    """ For racks with 4 PDUs """

    sensor1 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[0]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor2 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[1]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor3 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[2]}:GetInfeedLoadValue',
                   kind='hinted')
    sensor4 = FCpt(EpicsSignalRO,
                   '{prefix}:{elevation[3]}:GetInfeedLoadValue',
                   kind='hinted')

    def __init__(self, *args, elevations=None, **kwargs):
        self.elevation = elevations or []
        super().__init__(*args, **kwargs)

# FEE ALCOVE LCPs


class LCP1(Device):
    """ For LCPs with CMC-III PU, with Door Module off """

    temperature_f = Cpt(EpicsSignalRO, ':Temperature_CALC', kind='hinted')
    power_v_supply_v = Cpt(EpicsSignalRO, ':24Vsupply_CALC', kind='hinted')
    air_fan_1_rpm_percent = Cpt(EpicsSignalRO, ':AirFan1Rpm_CALC', kind='hinted')
    air_fan_2_rpm_percent = Cpt(EpicsSignalRO, ':AirFan2Rpm_CALC', kind='hinted')
    air_fan_3_rpm_percent = Cpt(EpicsSignalRO, ':AirFan3Rpm_CALC', kind='hinted')
    air_fan_4_rpm_percent = Cpt(EpicsSignalRO, ':AirFan4Rpm_CALC', kind='hinted')
    air_fan_5_rpm_percent = Cpt(EpicsSignalRO, ':AirFan5Rpm_CALC', kind='hinted')
    air_fan_6_rpm_percent = Cpt(EpicsSignalRO, ':AirFan6Rpm_CALC', kind='hinted')
    water_temp_in_f = Cpt(EpicsSignalRO, ':WaterTempIn_CALC', kind='hinted')
    water_temp_out_f = Cpt(EpicsSignalRO, ':WaterTempOut_CALC', kind='hinted')
    water_flow_rate_gpm = Cpt(EpicsSignalRO, ':WaterFlowRate_CALC', kind='hinted')
    air_temp_in_top_f = Cpt(EpicsSignalRO, ':AirTempInTop_CALC', kind='hinted')
    air_temp_in_mid_f = Cpt(EpicsSignalRO, ':AirTempInMid_CALC', kind='hinted')
    air_temp_in_bot_f = Cpt(EpicsSignalRO, ':AirTempInBot_CALC', kind='hinted')
    air_temp_out_top_f = Cpt(EpicsSignalRO, ':AirTempOutTop_CALC', kind='hinted')
    air_temp_out_mid_f = Cpt(EpicsSignalRO, ':AirTempOutMid_CALC', kind='hinted')
    air_temp_out_bot_f = Cpt(EpicsSignalRO, ':AirTempOutBot_CALC', kind='hinted')


class LCP2(Device):

    """ For LCPs with CMC-III PU, with Door Module working """

    temperature_f = Cpt(EpicsSignalRO, ':Temperature_CALC', kind='hinted')
    power_v_supply_v = Cpt(EpicsSignalRO, ':24Vsupply_CALC', kind='hinted')
    air_fan_1_rpm_percent = Cpt(EpicsSignalRO, ':AirFan1Rpm_CALC', kind='hinted')
    air_fan_2_rpm_percent = Cpt(EpicsSignalRO, ':AirFan2Rpm_CALC', kind='hinted')
    air_fan_3_rpm_percent = Cpt(EpicsSignalRO, ':AirFan3Rpm_CALC', kind='hinted')
    air_fan_4_rpm_percent = Cpt(EpicsSignalRO, ':AirFan4Rpm_CALC', kind='hinted')
    air_fan_5_rpm_percent = Cpt(EpicsSignalRO, ':AirFan5Rpm_CALC', kind='hinted')
    air_fan_6_rpm_percent = Cpt(EpicsSignalRO, ':AirFan6Rpm_CALC', kind='hinted')
    water_temp_in_f = Cpt(EpicsSignalRO, ':WaterTempIn_CALC', kind='hinted')
    water_temp_out_f = Cpt(EpicsSignalRO, ':WaterTempOut_CALC', kind='hinted')
    water_flow_rate_gpm = Cpt(EpicsSignalRO, ':WaterFlowRate_CALC', kind='hinted')
    air_temp_in_top_f = Cpt(EpicsSignalRO, ':AirTempInTop_CALC', kind='hinted')
    air_temp_in_mid_f = Cpt(EpicsSignalRO, ':AirTempInMid_CALC', kind='hinted')
    air_temp_in_bot_f = Cpt(EpicsSignalRO, ':AirTempInBot_CALC', kind='hinted')
    air_temp_out_top_f = Cpt(EpicsSignalRO, ':AirTempOutTop_CALC', kind='hinted')
    air_temp_out_mid_f = Cpt(EpicsSignalRO, ':AirTempOutMid_CALC', kind='hinted')
    air_temp_out_bot_f = Cpt(EpicsSignalRO, ':AirTempOutBot_CALC', kind='hinted')
    front_door_access = Cpt(EpicsSignalRO, ':FrontDoorAccess_CALC', kind='hinted')
    rear_door_access = Cpt(EpicsSignalRO, ':RearDoorAccess_CALC', kind='hinted')


class SRCController(Device):
    """
    A Raritan SRC 800 controller. One unit required to connect
    to all Raritan sensors.
    """
    src_model = Cpt(EpicsSignalRO, ':SRC800:MODEL_RBV', doc="Raritan 8 port Smart Sensor Controller")
    serial_number = Cpt(EpicsSignalRO, ':SRC800:SERIAL_RBV', doc="Controller Serial Number")
    number_sensors = Cpt(EpicsSignalRO, ':SRC800:MAX_SENSOR_NUM', doc="Number of sensors on controller")


class RaritanSensor(Device):
    """
    Raritan Sensor meta data.
    """
    sensor_name = Cpt(EpicsSignalRO, ':NAME_RBV')
    chain_position = Cpt(EpicsSignalRO, ':POSITION_RBV')
    sensor_serial = Cpt(EpicsSignalRO, ':SERIAL_RBV')
    state = Cpt(EpicsSignalRO, ':STATE_RBV')


@reorder_components(
    start_with=[
        'sensor_name', 'leak_detection'
    ]
)
class Floor(RaritanSensor):
    """
    Raritan Water/Leak Rope SmartSensor DX2-WSC-35-KIT
    """
    leak_detection = Cpt(EpicsSignalRO, ':SEVR_RBV', doc="Detects fluid leak, 0 dry, 2 wet")


class PCWFlow(Device):
    """
    Two Keyence flow meters intalled one on PCW supply
    and one PCW outlet.
    """
    pcw_flow_supply = Cpt(FDQ, ':PCW:SUP', doc="FDQ Measurment of PCW flow supply")
    pcw_flow_return = Cpt(FDQ, ':PCW:RET', doc="FDQ Measurement of PCW flow return")


class PCWTemp(Device):
    """
    3 Wire RTDs surface mount on cooling hoses
    or pipes.
    """
    pcw_temp = Cpt(EpicsSignalRO, ":PCW:TEMP_RBV")


@reorder_components(
    start_with=[
        'sensor_name', 'temp'
    ]
)
class AmbTemp(RaritanSensor):
    """Ambient temperature sensor Raritan DX2-T1"""
    temp = Cpt(EpicsSignalRO, ":SVAL_RBV")


class Rack(Device):
    """
    Racks equipped with a Raritan DX2-T1H1 sensor.
    Reads out humidity and temperature.
    """

    temp = Cpt(EpicsSignalRO, ":TEMP:SVAL_RBV")
    humidity = Cpt(EpicsSignalRO, ":HMD:SVAL_RBV")
    th1_sensor_data = Cpt(RaritanSensor, ":TEMP")
