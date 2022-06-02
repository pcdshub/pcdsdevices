"""
Module for the Instrumentation Technologies Low-Jitter Continuous Wave Reference Clock Transfer System used in the LCLS-II timing system.
"""

import logging
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from pcdsdevices.interface import BaseInterface

logger = logging.getLogger(__name__)


class rfof_rx(BaseInterface, Device):
    """
    Class for reading back the RFoF receiver PVs.
    """
    rx_pc1 = Cpt(EpicsSignalRO, ':RX_PC1', kind='normal', doc='Rx internal lock (uV)')
    rx_pd1_i = Cpt(EpicsSignalRO, ':RX_PD1_I', kind='normal', doc='Compenstated link photodiode current (uA)')
    rx_pd2_i = Cpt(EpicsSignalRO, ':RX_PD2_I', kind='normal', doc='Low-noise link photodiode current (uA)')
    rx_rfout = Cpt(EpicsSignalRO, ':RX_RFOUT', kind='normal', doc='Output RF power (dBm)')
    rx_pd1_rf = Cpt(EpicsSignalRO, ':RX_PD1_RF', kind='normal', doc='Compensated link photodiode RF power (dBm)')
    rx_pd2_rf = Cpt(EpicsSignalRO, ':RX_PD2_RF', kind='normal', doc='Low-noise link photodiode RF Power (dBm)')
    rx_orf_s = Cpt(EpicsSignalRO, ':RX_ORF_S', kind='normal', doc='Output RF power setpoint (dBm)')
    rx_att_v = Cpt(EpicsSignalRO, ':RX_ATT_V', kind='normal', doc='Variable attenuator voltage (V)')
    rx_ps_v = Cpt(EpicsSignalRO, ':RX_PS_V', kind='normal', doc='Phase shifter voltage (V)')
    rx_stp_t = Cpt(EpicsSignalRO, ':RX_STP_T', kind='normal', doc='Modules temperature setpoint (C)')
    rx_t = Cpt(EpicsSignalRO, ':RX_T', kind='normal', doc='Rx board temperature (C)')
    rx_opt_t = Cpt(EpicsSignalRO, ':RX_OPT_T', kind='normal', doc='Optical assembly temperature (C)')
    rx_spl_t = Cpt(EpicsSignalRO, ':RX_SPL_T', kind='normal', doc='Rx spool temperature (C)')
    rx_ext_h = Cpt(EpicsSignalRO, ':RX_EXT_H', kind='normal', doc='External relative humidity (%)')
    rx_exth_t = Cpt(EpicsSignalRO, ':RX_EXTH_T', kind='normal', doc='External temperature (humidity sensor) (C)')
    rx_ext_p = Cpt(EpicsSignalRO, ':RX_EXT_P', kind='normal', doc='External pressure (mbar)')
    rx_extp_t = Cpt(EpicsSignalRO, ':RX_EXTP_T', kind='normal', doc='External temperature (pressure sensor) (C)')
    rx_int_h = Cpt(EpicsSignalRO, ':RX_INT_H', kind='normal', doc='Internal relative humidity (%)')
    rx_inth_t = Cpt(EpicsSignalRO, ':RX_INTH_T', kind='normal', doc='Internal temperature (humidity sensor) (C)')
    rx_int_p = Cpt(EpicsSignalRO, ':RX_INT_P', kind='normal', doc='Internal pressure (mbar)')
    rx_intp_t = Cpt(EpicsSignalRO, ':RX_INTP_T', kind='normal', doc='Internal temperature (pressure sensor) (C)')


class rfof_tx(BaseInterface, Device):
    """
    Class for reading back the RFoF transmitter PVs.
    """
    # Transmitter adds a single control PV
    tx_pc1 = Cpt(EpicsSignalRO, ':TX_PC1', kind='normal', doc='Low-drift optical link loop lock (uV)')
    tx_pc2 = Cpt(EpicsSignalRO, ':TX_PC2', kind='normal', doc='Laser and modulator loop lock (uV)')
    tx_pd1_i = Cpt(EpicsSignalRO, ':TX_PD1_I', kind='normal', doc='PD1 current - returned optical signal (uA)')
    tx_pd2_i = Cpt(EpicsSignalRO, ':TX_PD2_I', kind='normal', doc='PD2 current - transmitted optical signal (uA)')
    tx_ld_s = Cpt(EpicsSignalRO, ':TX_LD_S', kind='normal', doc='Laser diode setpoint (uA)')
    tx_las_t = Cpt(EpicsSignalRO, ':TX_LAS_T', kind='normal', doc='Laser temperature (C)')
    tx_spl_t = Cpt(EpicsSignalRO, ':TX_SPL_T', kind='normal', doc='Compensation spool temperature (C)')
    tx_spl_s = Cpt(EpicsSignalRO, ':TX_SPL_S', kind='normal', doc='Compensation spool temperature setpoint (C)')
    tx_rfin = Cpt(EpicsSignalRO, ':TX_RFIN', kind='normal', doc='Input RF power (dBm)')
    tx_pd1_rf = Cpt(EpicsSignalRO, ':TX_PD1_RF', kind='normal', doc='PD1 RF power - returned optical signal (dBm)')
    tx_pd2_rf = Cpt(EpicsSignalRO, ':TX_PD2_RF', kind='normal', doc='PD2 RF power - transmitted optical signal (dBm)')
    tx_las_p = Cpt(EpicsSignalRO, ':TX_LAS_P', kind='normal', doc='Laser optical power (mW)')
    tx_rfo = Cpt(EpicsSignalRO, ':TX_RFO', kind='normal', doc='RF output power to MZM (dBm)')
    tx_las_i = Cpt(EpicsSignalRO, ':TX_LAS_I', kind='normal', doc='Laser current (mA)')
    tx_ps_v = Cpt(EpicsSignalRO, ':TX_PS_V', kind='normal', doc='Electrical phase shifter voltage (V)')
    tx_att_s = Cpt(EpicsSignalRO, ':TX_ATTS_V', kind='normal', doc='Variable RF attenuator controller setpoint voltage (V)')
    tx_att_v = Cpt(EpicsSignalRO, ':TX_ATT_V', kind='normal', doc='Variable RF attenuator voltage (V)')
    tx_psi_v = Cpt(EpicsSignalRO, ':TX_PSI_V', kind='normal', doc='Input phase shifter voltage (V)')
    tx_mzm_v = Cpt(EpicsSignalRO, ':TX_MZM_V', kind='normal', doc='MZ modulator bias voltage (V)')
    tx_voa_s = Cpt(EpicsSignalRO, ':TX_VOA_S', kind='normal', doc='VOA controller setpoint (mA)')
    tx_voa_v = Cpt(EpicsSignalRO, ':TX_VOA_V', kind='normal', doc='VOA voltage (V)')
    tx_stp_t = Cpt(EpicsSignalRO, ':TX_STP_T', kind='normal', doc='Temperature setpoint for internal modules (C)')
    tx_t = Cpt(EpicsSignalRO, ':TX_T', kind='normal', doc='Tx board temperature (C)')
    tx_opt_t = Cpt(EpicsSignalRO, ':TX_OPT_T', kind='normal', doc='Optical assembly temperature (C)')
    tx_ext_h = Cpt(EpicsSignalRO, ':TX_EXT_H', kind='normal', doc='External relative humidity (%)')
    tx_exth_t = Cpt(EpicsSignalRO, ':TX_EXTH_T', kind='normal', doc='External temperature (humidity sensor) (C)')
    tx_ext_p = Cpt(EpicsSignalRO, ':TX_EXT_P', kind='normal', doc='External pressure (mbar)')
    tx_extp_t = Cpt(EpicsSignalRO, ':TX_EXTP_T', kind='normal', doc='External temperature (pressure sensor) (C)')
    tx_int_h = Cpt(EpicsSignalRO, ':TX_INT_H', kind='normal', doc='Interal relative humidity (%)')
    tx_inth_t = Cpt(EpicsSignalRO, ':TX_INTH_T', kind='normal', doc='Internal temperature (humidity sensor) (C)')
    tx_int_p = Cpt(EpicsSignalRO, ':TX_INT_P', kind='normal', doc='Internal pressure (mbar)')
    tx_intp_t = Cpt(EpicsSignalRO, ':TX_INTP_T', kind='normal', doc='Internal temperature (pressure sensor) (C)')

class rfof_status(BaseInterface, Device):
    """
    Class for general status PVs, both readback and caput able PVs
    """

    #States
    locked = Cpt(EpicsSignalRO, ':LOCKED', kind='normal', doc='Binary showing if device is locked')
    semi_locked = Cpt(EpicsSignalRO, ':SEMI_LOCKED', kind='normal', doc='Binary showing if device is semi-locked')
    unlocked = Cpt(EpicsSignalRO, ':UNLOCKED', kind='normal', doc='Binary showing if device is unlocked')
    start = Cpt(EpicsSignalRO, ':START', kind='normal', doc='Binary showing if device is starting')
    shutdown = Cpt(EpicsSignalRO, ':SHUTDOWN', kind='normal', doc='Binary showing if device is shutdown')
    init = Cpt(EpicsSignalRO, ':INIT', kind='normal', doc='Binary showing if device is initiating')
    warming_up = Cpt(EpicsSignalRO, ':WARMING_UP', kind='normal', doc='Binary showing if device is warming up')
    tuning = Cpt(EpicsSignalRO, ':TUNING', kind='normal', doc='Binary showing if device is tuning')
    ready = Cpt(EpicsSignalRO, ':READY', kind='normal', doc='Binary showing if device is ready')

    #Misc
    opt_link = Cpt(EpicsSignal, ':GET_OPT', write_pv=':SET_OPT', kind='normal', doc='View and set optical length (m)')
    power = Cpt(EpicsSignal, ':STATE', write_pv=':SET_POWER', kind='normal', doc='View and set power state of the device')

class rfof_errors(BaseInterface, Device):
    eth_con_err = Cpt(EpicsSignalRO, ':ETH_CON_ERR', kind='normal', doc='Tx/Rx Ethernet connection failure')
    pwr_supply_v_err = Cpt(EpicsSignalRO, ':PWR_SUPPLY_V_ERR', kind='normal', doc='Power supply voltages are out of range')
    env_cond_err = Cpt(EpicsSignalRO, ':ENV_COND_ERR', kind='normal', doc='Environmental conditions are out of range')
    int_mod_err = Cpt(EpicsSignalRO, ':INT_MOD_ERR', kind='normal', doc='Internal modules temperatures are out of range')
    rf_pwr_err = Cpt(EpicsSignalRO, ':RF_PWR_ERR', kind='normal', doc='RF power is out of range')
    opt_pwr_err = Cpt(EpicsSignalRO, ':OPT_PWR_ERR', kind='normal', doc='Optical power is too low')
    las_pwr_err = Cpt(EpicsSignalRO, ':LAS_PWR_ERR', kind='normal', doc='Laser is switched off')
    phase_err = Cpt(EpicsSignalRO, ':PHASE_ERR', kind='normal', doc='Phase loops are not locked')
    fan_spd_err = Cpt(EpicsSignalRO, ':FAN_SPD_ERR', kind='normal', doc='Fan revolutions are too low')
    pwr_supply_i_err = Cpt(EpicsSignalRO, ':PWR_SUPPLY_I_ERR', kind='normal', doc='Power supply currents are too high')
    tx_eth_err = Cpt(EpicsSignalRO, ':TX_ETH_SYNC_ERR', kind='normal', doc='Tx: Ethernet sync between units lost for more than 10 min')
    rx_eth_err = Cpt(EpicsSignalRO, ':RX_ETH_SYNC_ERR', kind='normal', doc='Rx: Ethernet sync between units lost for more than 10 min')
    tx_input_err = Cpt(EpicsSignalRO, ':TX_RF_INPUT_ERR', kind='normal', doc='RF input is out of range for more than 60s')
    rx_output_err = Cpt(EpicsSignalRO, ':RX_RF_OUTPUT_ERR', kind='normal', doc='RF output is out of range for more than 10 min')
    tx_temp_sens_err = Cpt(EpicsSignalRO, ':TX_TEMP_SENS_ERR', kind='normal', doc='Tx: Temperature sensors are not working properly; TEC protection activated')
    rx_temp_sens_err = Cpt(EpicsSignalRO, ':RX_TEMP_SENS_ERR', kind='normal', doc='Rx: Temperature sensors are not working properly; TEC protection activated')
    tx_rf_idn_err = Cpt(EpicsSignalRO, ':TX_RF_IDN_ERR', kind='normal', doc='Tx: RF control identification failed')
    tx_rf_sens_err = Cpt(EpicsSignalRO, ':TX_RF_SENS_ERR', kind='normal', doc='Tx: RF control sensor failure')
    tx_arm_idn_err = Cpt(EpicsSignalRO, ':TX_ARM_IDN_ERR', kind='normal', doc='Tx: Arm control identification failed')
    tx_arm_sens_err = Cpt(EpicsSignalRO, ':TX_ARM_SENS_ERR', kind='normal', doc='Tx: Arm control sensor failure')
    unlock_err = Cpt(EpicsSignalRO, ':UNLOCK_ERR', kind='normal', doc='System is unlocked for more than 15 min')
    rx_rf_idn_err = Cpt(EpicsSignalRO, ':RX_RF_IDN_ERR', kind='normal', doc='Rx: RF control identification failed')
    rx_rf_sens_err = Cpt(EpicsSignalRO, ':RX_RF_SENS_ERR', kind='normal', doc='Rx: RF control sensor failure')
    rx_arm_idn_err = Cpt(EpicsSignalRO, ':RX_ARM_IDN_ERR', kind='normal', doc='Rx: Arm control identification failed')
    rx_arm_sens_err = Cpt(EpicsSignalRO, ':RX_ARM_SENS_ERR', kind='normal', doc='Rx: Arm control sensor failure')
