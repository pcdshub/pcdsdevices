"""
Module for the RFoF systems used in the LCLS-II timing system.
"""


import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO

from pcdsdevices.interface import BaseInterface

logger = logging.getLogger(__name__)

# Cycle RFOF classes


class CycleRfofRx(BaseInterface, Device):

    """Class for reading back the Cycle RFoF receiver PVs."""

    rf_temperature = Cpt(EpicsSignalRO, ":RFTEMPERATURE", kind="normal")
    rf_power = Cpt(EpicsSignalRO, ":RFPOWER", kind="normal")
    optical_power = Cpt(EpicsSignalRO, ":OPTICALPOWER", kind="normal")


class CycleRfofTx(CycleRfofRx):

    """Class for reading back the Cycle RFoF transmitter PVs."""

    # Transmitter adds a single control PV
    enable_laser = Cpt(EpicsSignal, ":ENABLELASER", kind="normal")


# Instrumentation Technologies Low-Jitter Continuous Wave RCT Classes


class ItechRfofRx(BaseInterface, Device):

    """Itech RFoF receiver PVs."""

    internal_lock = Cpt(
        EpicsSignalRO,
        ":RX_PC1",
        kind="normal",
        doc="Rx internal lock (uV)"
    )
    comp_link_pd_current = Cpt(
        EpicsSignalRO,
        ":RX_PD1_I",
        kind="normal",
        doc="Compenstated link photodiode current (uA)"
    )
    low_noise_pd_current = Cpt(
        EpicsSignalRO,
        ":RX_PD2_I",
        kind="normal",
        doc="Low-noise link photodiode current (uA)"
    )
    output_rf_power = Cpt(
        EpicsSignalRO,
        ":RX_RFOUT",
        kind="normal",
        doc="Output RF power (dBm)"
    )
    comp_link_pd_rf_power = Cpt(
        EpicsSignalRO,
        ":RX_PD1_RF",
        kind="normal",
        doc=(
            "Compensated link photodiode"
            "RF power (dBm)"
        )
    )
    low_noise_pd_rf_power = Cpt(
        EpicsSignalRO,
        ":RX_PD2_RF",
        kind="normal",
        doc="Low-noise link photodiode RF Power (dBm)"
    )
    output_rf_power_sp = Cpt(
        EpicsSignalRO,
        ":RX_ORF_S",
        kind="normal",
        doc="Output RF power setpoint (dBm)"
    )
    attenuator_v = Cpt(
        EpicsSignalRO,
        ":RX_ATT_V",
        kind="normal",
        doc="Variable attenuator voltage (V)"
    )
    phase_shifter_v = Cpt(
        EpicsSignalRO,
        ":RX_PS_V",
        kind="normal",
        doc="Phase shifter voltage (V)"
    )
    module_temp_sp = Cpt(
        EpicsSignalRO,
        ":RX_STP_T",
        kind="normal",
        doc="Modules temperature setpoint (C)"
    )
    board_temp = Cpt(
        EpicsSignalRO,
        ":RX_T",
        kind="normal",
        doc="Rx board temperature (C)"
    )
    opt_assembly_temp = Cpt(
        EpicsSignalRO,
        ":RX_OPT_T",
        kind="normal",
        doc="Optical assembly temperature (C)"
    )
    spool_temp = Cpt(
        EpicsSignalRO,
        ":RX_SPL_T",
        kind="normal",
        doc="Rx spool temperature (C)"
    )
    ext_relative_hum = Cpt(
        EpicsSignalRO,
        ":RX_EXT_H",
        kind="normal",
        doc="External relative humidity (%)"
    )
    ext_temp_hum_sens = Cpt(
        EpicsSignalRO,
        ":RX_EXTH_T",
        kind="normal",
        doc="External temperature (humidity sensor) (C)"
    )
    ext_press = Cpt(
        EpicsSignalRO,
        ":RX_EXT_P",
        kind="normal",
        doc="External pressure (mbar)"
    )
    ext_temp_press_sens = Cpt(
        EpicsSignalRO,
        ":RX_EXTP_T",
        kind="normal",
        doc="External temperature (pressure sensor) (C)"
    )
    int_relative_hum = Cpt(
        EpicsSignalRO,
        ":RX_INT_H",
        kind="normal",
        doc="Internal relative humidity (%)"
    )
    int_temp_hum_sens = Cpt(
        EpicsSignalRO,
        ":RX_INTH_T",
        kind="normal",
        doc="Internal temperature (humidity sensor) (C)"
    )
    int_press = Cpt(
        EpicsSignalRO,
        ":RX_INT_P",
        kind="normal",
        doc="Internal pressure (mbar)"
    )
    int_temp_press_sens = Cpt(
        EpicsSignalRO,
        ":RX_INTP_T",
        kind="normal",
        doc="Internal temperature (pressure sensor) (C)"
    )


class ItechRfofTx(BaseInterface, Device):

    """Itech RFoF transmitter PVs."""

    low_drift_opt_link_lock = Cpt(
        EpicsSignalRO,
        ":TX_PC1",
        kind="normal",
        doc="Low-drift optical link loop lock (uV)"
    )
    las_and_mod_loop_lock = Cpt(
        EpicsSignalRO,
        ":TX_PC2",
        kind="normal",
        doc="Laser and modulator loop lock (uV)"
    )
    pd1_current_return = Cpt(
        EpicsSignalRO,
        ":TX_PD1_I",
        kind="normal",
        doc="PD1 current - returned optical signal (uA)"
    )
    pd2_current_transmit = Cpt(
        EpicsSignalRO,
        ":TX_PD2_I",
        kind="normal",
        doc=(
            "PD2 current - "
            "transmitted optical signal (uA)"
        )
    )
    las_diode_sp = Cpt(
        EpicsSignalRO,
        ":TX_LD_S",
        kind="normal",
        doc="Laser diode setpoint (uA)"
    )
    las_temp = Cpt(
        EpicsSignalRO,
        ":TX_LAS_T",
        kind="normal",
        doc="Laser temperature (C)"
    )
    comp_spool_temp = Cpt(
        EpicsSignalRO,
        ":TX_SPL_T",
        kind="normal",
        doc="Compensation spool temperature (C)"
    )
    comp_spool_temp_sp = Cpt(
        EpicsSignalRO,
        ":TX_SPL_S",
        kind="normal",
        doc="Compensation spool temperature setpoint (C)"
    )
    input_rf_power = Cpt(
        EpicsSignalRO,
        ":TX_RFIN",
        kind="normal",
        doc="Input RF power (dBm)"
    )
    pd1_rf_power_return = Cpt(
        EpicsSignalRO,
        ":TX_PD1_RF",
        kind="normal",
        doc=(
            "PD1 RF power - returned "
            "optical signal (dBm)"
            )
    )
    pd2_rf_power_transmit = Cpt(
        EpicsSignalRO,
        ":TX_PD2_RF",
        kind="normal",
        doc=(
            "PD2 RF power - transmitted "
            "optical signal (dBm)"
        )
    )
    las_opt_power = Cpt(
        EpicsSignalRO,
        ":TX_LAS_P",
        kind="normal",
        doc="Laser optical power (mW)"
    )
    rf_output_mzm_power = Cpt(
        EpicsSignalRO,
        ":TX_RFO",
        kind="normal",
        doc="RF output power to MZM (dBm)"
    )
    las_current = Cpt(
        EpicsSignalRO,
        ":TX_LAS_I",
        kind="normal",
        doc="Laser current (mA)"
    )
    elect_phase_shift_v = Cpt(
        EpicsSignalRO,
        ":TX_PS_V",
        kind="normal",
        doc="Electrical phase shifter voltage (V)"
    )
    attenuator_setpoint_v = Cpt(
        EpicsSignalRO,
        ":TX_ATTS_V",
        kind="normal",
        doc=(
            "Variable RF attenuator "
            "controller setpoint voltage (V)"
        )
    )
    attenuator_v = Cpt(
        EpicsSignalRO,
        ":TX_ATT_V",
        kind="normal",
        doc="Variable RF attenuator voltage (V)"
    )
    input_phase_shift_v = Cpt(
        EpicsSignalRO,
        ":TX_PSI_V",
        kind="normal",
        doc="Input phase shifter voltage (V)"
    )
    mzm_bias_v = Cpt(
        EpicsSignalRO,
        ":TX_MZM_V",
        kind="normal",
        doc="MZ modulator bias voltage (V)"
    )
    voa_control_sp = Cpt(
        EpicsSignalRO,
        ":TX_VOA_S",
        kind="normal",
        doc="VOA controller setpoint (mA)"
    )
    voa_v = Cpt(
        EpicsSignalRO,
        ":TX_VOA_V",
        kind="normal",
        doc="VOA voltage (V)"
    )
    int_mod_temp_sp = Cpt(
        EpicsSignalRO,
        ":TX_STP_T",
        kind="normal",
        doc="Temperature setpoint for internal modules (C)"
    )
    board_temp = Cpt(
        EpicsSignalRO,
        ":TX_T",
        kind="normal",
        doc="Tx board temperature (C)"
    )
    opt_assembly_temp = Cpt(
        EpicsSignalRO,
        ":TX_OPT_T",
        kind="normal",
        doc="Optical assembly temperature (C)"
    )
    ext_rel_hum = Cpt(
        EpicsSignalRO,
        ":TX_EXT_H",
        kind="normal",
        doc="External relative humidity (%)"
    )
    ext_temp_hum_sens = Cpt(
        EpicsSignalRO,
        ":TX_EXTH_T",
        kind="normal",
        doc="External temperature (humidity sensor) (C)"
    )
    ext_press = Cpt(
        EpicsSignalRO,
        ":TX_EXT_P",
        kind="normal",
        doc="External pressure (mbar)"
    )
    ext_temp_press_sens = Cpt(
        EpicsSignalRO,
        ":TX_EXTP_T",
        kind="normal",
        doc="External temperature (pressure sensor) (C)"
    )
    int_rel_hum = Cpt(
        EpicsSignalRO,
        ":TX_INT_H",
        kind="normal",
        doc="Interal relative humidity (%)"
    )
    int_temp_hum_sens = Cpt(
        EpicsSignalRO,
        ":TX_INTH_T",
        kind="normal",
        doc="Internal temperature (humidity sensor) (C)"
    )
    int_press = Cpt(
        EpicsSignalRO,
        ":TX_INT_P",
        kind="normal",
        doc="Internal pressure (mbar)"
    )
    int_temp_press_sens = Cpt(
        EpicsSignalRO,
        ":TX_INTP_T",
        kind="normal",
        doc="Internal temperature (pressure sensor) (C)"
    )


class ItechRfofStatus(BaseInterface, Device):

    """Itech RFOF Status PVs"""

    # States
    locked = Cpt(
        EpicsSignalRO,
        ":LOCKED",
        kind="normal",
        doc="Binary showing if device is locked"
    )
    semi_locked = Cpt(
        EpicsSignalRO,
        ":SEMI_LOCKED",
        kind="normal",
        doc="Binary showing if device is semi-locked"
    )
    unlocked = Cpt(
        EpicsSignalRO,
        ":UNLOCKED",
        kind="normal",
        doc="Binary showing if device is unlocked"
    )
    start = Cpt(
        EpicsSignalRO,
        ":START",
        kind="normal",
        doc="Binary showing if device is starting"
    )
    shutdown = Cpt(
        EpicsSignalRO,
        ":SHUTDOWN",
        kind="normal",
        doc="Binary showing if device is shutdown"
    )
    init = Cpt(
        EpicsSignalRO,
        ":INIT",
        kind="normal",
        doc="Binary showing if device is initiating"
    )
    warming_up = Cpt(
        EpicsSignalRO,
        ":WARMING_UP",
        kind="normal",
        doc="Binary showing if device is warming up"
    )
    tuning = Cpt(
        EpicsSignalRO,
        ":TUNING",
        kind="normal",
        doc="Binary showing if device is tuning"
    )
    ready = Cpt(
        EpicsSignalRO,
        ":READY",
        kind="normal",
        doc="Binary showing if device is ready"
    )

    # Misc
    opt_link_length = Cpt(
        EpicsSignal,
        ":OPT_RBV",
        write_pv=":OPT",
        kind="normal",
        doc="View and set optical length (m)"
    )
    power = Cpt(
        EpicsSignal,
        ":STATE",
        write_pv=":SET_POWER",
        kind="normal",
        doc="View and set power state of the device"
    )
    fan_speed = Cpt(
        EpicsSignal,
        ":FAN_SPD_RBV",
        write_pv=":FAN_SPD",
        kind="normal",
        doc="Get and set fan speed"
    )


class ItechRfofErrors(BaseInterface, Device):

    """Itech RFOF Error PVs"""

    eth_con_err = Cpt(
        EpicsSignalRO,
        ":ETH_CON_ERR",
        kind="normal",
        doc="Tx/Rx Ethernet connection failure"
    )
    pwr_supply_v_err = Cpt(
        EpicsSignalRO,
        ":PWR_SUPPLY_V_ERR",
        kind="normal",
        doc="Power supply voltages are out of range"
    )
    env_cond_err = Cpt(
        EpicsSignalRO,
        ":ENV_COND_ERR",
        kind="normal",
        doc="Environmental conditions are out of range"
    )
    int_mod_err = Cpt(
        EpicsSignalRO,
        ":INT_MOD_ERR",
        kind="normal",
        doc="Internal modules temperatures are out of range"
    )
    rf_pwr_err = Cpt(
        EpicsSignalRO,
        ":RF_PWR_ERR",
        kind="normal",
        doc="RF power is out of range"
    )
    opt_pwr_err = Cpt(
        EpicsSignalRO,
        ":OPT_PWR_ERR",
        kind="normal",
        doc="Optical power is too low"
    )
    las_pwr_err = Cpt(
        EpicsSignalRO,
        ":LAS_PWR_ERR",
        kind="normal",
        doc="Laser is switched off"
    )
    phase_err = Cpt(
        EpicsSignalRO,
        ":PHASE_ERR",
        kind="normal",
        doc="Phase loops are not locked"
    )
    fan_spd_err = Cpt(
        EpicsSignalRO,
        ":FAN_SPD_ERR",
        kind="normal",
        doc="Fan revolutions are too low"
    )
    pwr_supply_i_err = Cpt(
        EpicsSignalRO,
        ":PWR_SUPPLY_I_ERR",
        kind="normal",
        doc="Power supply currents are too high"
    )
    tx_eth_err = Cpt(
        EpicsSignalRO,
        ":TX_ETH_SYNC_ERR",
        kind="normal",
        doc=(
            "Tx: Ethernet sync between units "
            "lost for more than 10 min"
        )
    )
    rx_eth_err = Cpt(
        EpicsSignalRO,
        ":RX_ETH_SYNC_ERR",
        kind="normal",
        doc=(
            "Rx: Ethernet sync between units "
            "lost for more than 10 min"
        )
    )
    tx_input_err = Cpt(
        EpicsSignalRO,
        ":TX_RF_INPUT_ERR",
        kind="normal",
        doc="RF input is out of range for more than 60s"
    )
    rx_output_err = Cpt(
        EpicsSignalRO,
        ":RX_RF_OUTPUT_ERR",
        kind="normal",
        doc="RF output is out of range for more than 10 min"
    )
    tx_temp_sens_err = Cpt(
        EpicsSignalRO,
        ":TX_TEMP_SENS_ERR",
        kind="normal",
        doc=(
            "Tx: Temperature sensors are not working properly; "
            "TEC protection activated"
        )
    )
    rx_temp_sens_err = Cpt(
        EpicsSignalRO,
        ":RX_TEMP_SENS_ERR",
        kind="normal",
        doc=(
            "Rx: Temperature sensors are not working properly; "
            "TEC protection activated"
        )
    )
    tx_rf_idn_err = Cpt(
        EpicsSignalRO,
        ":TX_RF_IDN_ERR",
        kind="normal",
        doc="Tx: RF control identification failed"
    )
    tx_rf_sens_err = Cpt(
        EpicsSignalRO,
        ":TX_RF_SENS_ERR",
        kind="normal",
        doc="Tx: RF control sensor failure"
    )
    tx_arm_idn_err = Cpt(
        EpicsSignalRO,
        ":TX_ARM_IDN_ERR",
        kind="normal",
        doc="Tx: Arm control identification failed"
    )
    tx_arm_sens_err = Cpt(
        EpicsSignalRO,
        ":TX_ARM_SENS_ERR",
        kind="normal",
        doc="Tx: Arm control sensor failure"
    )
    unlock_err = Cpt(
        EpicsSignalRO,
        ":UNLOCK_ERR",
        kind="normal",
        doc="System is unlocked for more than 15 min"
    )
    rx_rf_idn_err = Cpt(
        EpicsSignalRO,
        ":RX_RF_IDN_ERR",
        kind="normal",
        doc="Rx: RF control identification failed"
    )
    rx_rf_sens_err = Cpt(
        EpicsSignalRO,
        ":RX_RF_SENS_ERR",
        kind="normal",
        doc="Rx: RF control sensor failure"
    )
    rx_arm_idn_err = Cpt(
        EpicsSignalRO,
        ":RX_ARM_IDN_ERR",
        kind="normal",
        doc="Rx: Arm control identification failed"
    )
    rx_arm_sens_err = Cpt(
        EpicsSignalRO,
        ":RX_ARM_SENS_ERR",
        kind="normal",
        doc="Rx: Arm control sensor failure"
    )


class ItechRfofAll(BaseInterface, Device):

    """
    Class for including all subclasses
    For example, for receiver PVs, use object would use object.receiver.<pv>
    """

    transmitter = Cpt(ItechRfofTx, "")
    receiver = Cpt(ItechRfofRx, "")
    errors = Cpt(ItechRfofErrors, "")
    status = Cpt(ItechRfofStatus, "")
