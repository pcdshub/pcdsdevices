"""
Module for digitizers such as the Wave8.
"""

import logging

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.variety import set_metadata

logger = logging.getLogger(__name__)


class Wave8V2Channel(Device):
    """
    Class for a single LCLS-II Wave8 channel.
    """

    waveform = Cpt(EpicsSignalRO, ':ArrayData', kind='normal')
    

class Wave8V2SystemRegs(Device):
    """
    Class for Wave8 system registers.
    """

    trigger_enable = Cpt(EpicsSignal, ':TrigEn_RBV', write_pv=':TrigEn',
                         kind='configure')
    trigger_source = Cpt(EpicsSignal, ':TrigSrcSel_RBV',
                         write_pv=':TrigSrcSel', kind='configure')
    trigger_delay = Cpt(EpicsSignal, ':TrigDelay_RBV', write_pv=':TrigDelay',
                        kind='configure')
    timing_mini_tpg = Cpt(EpicsSignal, ':timingUseMiniTpg_RBV',
                          write_pv=':timingUseMiniTpg', kind='configure')

    a0p3v3_en = Cpt(EpicsSignal, ':A0p3V3En_RBV', write_pv=':A0p3V3En',
                    kind='configure')
    a1p3v3_en = Cpt(EpicsSignal, ':A1p3V3En_RBV', write_pv=':A1p3V3En',
                    kind='configure')
    ap1v8_en = Cpt(EpicsSignal, ':Ap1V8En_RBV', write_pv=':Ap1V8En',
                   kind='config')
    ap5v0_en = Cpt(EpicsSignal, ':Ap5V0En_RBV', write_pv=':Ap5V0En',
                   kind='config')
    ap5v5_en = Cpt(EpicsSignal, ':Ap5V5En_RBV', write_pv=':Ap5V5En',
                   kind='config')
    avcc_en0 = Cpt(EpicsSignal, ':AvccEn0_RBV', write_pv=':AvccEn0',
                   kind='config')
    avcc_en1 = Cpt(EpicsSignal, ':AvccEn1_RBV', write_pv=':AvccEn1',
                   kind='config')

    adc_ctrl1 = Cpt(EpicsSignal, ':AdcCtrl1_RBV', write_pv=':AdcCtrl1',
                    kind='config')
    adc_ctrl2 = Cpt(EpicsSignal, ':AdcCtrl2_RBV', write_pv=':AdcCtrl2',
                    kind='config')

    adc_reset = Cpt(EpicsSignal, ':AdcReset_RBV', write_pv=':AdcReset',
                    kind='config')

    fpga_tmp_critlatch = Cpt(EpicsSignal, ':FpgaTmpCritLatch_RBV',
                             write_pv=':FpgaTmpCritLatch', kind='config')

    temp_ana_raw0 = Cpt(EpicsSignalRO, ':TempAnaRaw0', kind='config')
    temp_ana_raw1 = Cpt(EpicsSignalRO, ':TempAnaRaw1', kind='config')
    temp_dig_raw0 = Cpt(EpicsSignalRO, ':TempDigRaw0', kind='config')
    temp_dig_raw1 = Cpt(EpicsSignalRO, ':TempDigRaw1', kind='config')

class Wave8V2RawBuffers(Device):
    """
    Class for LCLS-II Wave8 raw buffer registers.
    """

    buffer0_enable = Cpt(EpicsSignal, ':BuffEn0_RBV', write_pv=':BuffEn0',
                         kind='configure')
    buffer1_enable = Cpt(EpicsSignal, ':BuffEn1_RBV', write_pv=':BuffEn1',
                         kind='configure')
    buffer2_enable = Cpt(EpicsSignal, ':BuffEn2_RBV', write_pv=':BuffEn2',
                         kind='configure')
    buffer3_enable = Cpt(EpicsSignal, ':BuffEn3_RBV', write_pv=':BuffEn3',
                         kind='configure')
    buffer4_enable = Cpt(EpicsSignal, ':BuffEn4_RBV', write_pv=':BuffEn4',
                         kind='configure')
    buffer5_enable = Cpt(EpicsSignal, ':BuffEn5_RBV', write_pv=':BuffEn5',
                         kind='configure')
    buffer6_enable = Cpt(EpicsSignal, ':BuffEn6_RBV', write_pv=':BuffEn6',
                         kind='configure')
    buffer7_enable = Cpt(EpicsSignal, ':BuffEn7_RBV', write_pv=':BuffEn7',
                         kind='configure')

    overflow_cnt_buffer0 = Cpt(EpicsSignal, ':OvflCntBuff0_RBV',
                               write_pv=':OvflCntBuff0', kind='configure')
    # Currently excluded from EDM screen.
    #overflow_cnt_buffer1 = Cpt(EpicsSignal, ':OvflCntBuff1_RBV',
    #                           write_pv=':OvflCntBuff1', kind='configure')
    #overflow_cnt_buffer2 = Cpt(EpicsSignal, ':OvflCntBuff2_RBV',
    #                           write_pv=':OvflCntBuff2', kind='configure')
    #overflow_cnt_buffer3 = Cpt(EpicsSignal, ':OvflCntBuff3_RBV',
    #                           write_pv=':OvflCntBuff3', kind='configure')
    #overflow_cnt_buffer4 = Cpt(EpicsSignal, ':OvflCntBuff4_RBV',
    #                           write_pv=':OvflCntBuff4', kind='configure')
    #overflow_cnt_buffer5 = Cpt(EpicsSignal, ':OvflCntBuff5_RBV',
    #                           write_pv=':OvflCntBuff5', kind='configure')
    #overflow_cnt_buffer6 = Cpt(EpicsSignal, ':OvflCntBuff6_RBV',
    #                           write_pv=':OvflCntBuff6', kind='configure')
    overflow_cnt_buffer7 = Cpt(EpicsSignal, ':OvflCntBuff7_RBV',
                               write_pv=':OvflCntBuff7', kind='configure')

    buffer_length = Cpt(EpicsSignal, ':BuffLen_RBV', write_pv=':BuffLen',
                        kind='configure')

    trigger_prescale = Cpt(EpicsSignal, ':TriggerPrescale_RBV',
                           write_pv=':TriggerPrescale', kind='configure')

    counter_reset = Cpt(EpicsSignal, ':CntRst_RBV', write_pv=':CntRst',
                        kind='configure')

    fifo_pause_threshold = Cpt(EpicsSignal, ':FifoPauseThreshold_RBV',
                              write_pv=':FifoPauseThreshold', kind='configure')

    fifo_pause_count = Cpt(EpicsSignalRO, ':FifoPauseCnt', kind='config')

    trigger_count = Cpt(EpicsSignalRO, ':TrigCnt', kind='config')


class Wave8V2Sfp(Device):
    """
    Class for LCLS-II Wave8 SFP connection (PGP, EVR).
    """
    # There are other diagnostic PVs for these, but excluding for now.
    sfp_type = Cpt(EpicsSignalRO, ':Type_RBV', kind='config')
    sfp_connector = Cpt(EpicsSignalRO, ':Connector_RBV', kind='config')
    rx_watts = Cpt(EpicsSignalRO, ':RxWatts_RBV', kind='config')
    rx_power = Cpt(EpicsSignalRO, ':RxPower_RBV', kind='config')
    tx_power = Cpt(EpicsSignalRO, ':TxPower_RBV', kind='config')


class Wave8V2ADCRegs(Device):
    """
    Class for accessing LCLS-II Wave8 ADC registers.
    """

    adc_reg_x0006 = Cpt(EpicsSignal, ':AdcReg_0x0006_RBV',
                        write_pv=':AdcReg_0x0006', kind='config')
    adc_reg_x0007 = Cpt(EpicsSignal, ':AdcReg_0x0007_RBV',
                        write_pv=':AdcReg_0x0007', kind='config')
    adc_reg_x0008 = Cpt(EpicsSignal, ':AdcReg_0x0008_RBV',
                        write_pv=':AdcReg_0x0008', kind='config')
    # No x0009, x000A
    adc_reg_x000B = Cpt(EpicsSignal, ':AdcReg_0x000B_RBV',
                        write_pv=':AdcReg_0x000B', kind='config')
    adc_reg_x000C = Cpt(EpicsSignal, ':AdcReg_0x000C_RBV',
                        write_pv=':AdcReg_0x000C', kind='config')
    adc_reg_x000D = Cpt(EpicsSignal, ':AdcReg_0x000D_RBV',
                        write_pv=':AdcReg_0x000D', kind='config')
    # No x000E
    adc_reg_x000F = Cpt(EpicsSignal, ':AdcReg_0x000F_RBV',
                        write_pv=':AdcReg_0x000F', kind='config')
    adc_reg_x0010 = Cpt(EpicsSignal, ':AdcReg_0x0010_RBV',
                        write_pv=':AdcReg_0x0010', kind='config')
    adc_reg_x0011 = Cpt(EpicsSignal, ':AdcReg_0x0011_RBV',
                        write_pv=':AdcReg_0x0011', kind='config')
    adc_reg_x0012 = Cpt(EpicsSignal, ':AdcReg_0x0012_RBV',
                        write_pv=':AdcReg_0x0012', kind='config')
    adc_reg_x0013 = Cpt(EpicsSignal, ':AdcReg_0x0013_RBV',
                        write_pv=':AdcReg_0x0013', kind='config')
    adc_reg_x0014 = Cpt(EpicsSignal, ':AdcReg_0x0014_RBV',
                        write_pv=':AdcReg_0x0014', kind='config')
    adc_reg_x0015 = Cpt(EpicsSignal, ':AdcReg_0x0015_RBV',
                        write_pv=':AdcReg_0x0015', kind='config')
    adc_reg_x0016 = Cpt(EpicsSignal, ':AdcReg_0x0016_RBV',
                        write_pv=':AdcReg_0x0016', kind='config')
    adc_reg_x0017 = Cpt(EpicsSignal, ':AdcReg_0x0017_RBV',
                        write_pv=':AdcReg_0x0017', kind='config')
    adc_reg_x0018 = Cpt(EpicsSignal, ':AdcReg_0x0018_RBV',
                        write_pv=':AdcReg_0x0018', kind='config')
    # No x0019 through x001E 
    adc_reg_x001F = Cpt(EpicsSignal, ':AdcReg_0x001F_RBV',
                        write_pv=':AdcReg_0x001F', kind='config')
    adc_reg_x0020 = Cpt(EpicsSignal, ':AdcReg_0x0020_RBV',
                        write_pv=':AdcReg_0x0020', kind='config')


class Wave8V2ADCSamples(Device):
    """
    Class for the LCLS-II Wave8 ADC sample readout registers.
    """

    sample0 = Cpt(EpicsSignal, 'Sample[0]', kind='config')
    sample1 = Cpt(EpicsSignal, 'Sample[1]', kind='config')
    sample2 = Cpt(EpicsSignal, 'Sample[2]', kind='config')
    sample3 = Cpt(EpicsSignal, 'Sample[3]', kind='config')
    sample4 = Cpt(EpicsSignal, 'Sample[4]', kind='config')
    sample5 = Cpt(EpicsSignal, 'Sample[5]', kind='config')
    sample6 = Cpt(EpicsSignal, 'Sample[6]', kind='config')
    sample7 = Cpt(EpicsSignal, 'Sample[7]', kind='config')


class Wave8V2ADCDelayLanes(Device):
    """
    Class for the LCLS-II Wave8 ADC delay lanes.
    """
    lane0 = Cpt(EpicsSignal, 'Lane0_RBV', write_pv='Lane0', kind='config')
    lane1 = Cpt(EpicsSignal, 'Lane1_RBV', write_pv='Lane1', kind='config')
    lane2 = Cpt(EpicsSignal, 'Lane2_RBV', write_pv='Lane2', kind='config')
    lane3 = Cpt(EpicsSignal, 'Lane3_RBV', write_pv='Lane3', kind='config')
    lane4 = Cpt(EpicsSignal, 'Lane4_RBV', write_pv='Lane4', kind='config')
    lane5 = Cpt(EpicsSignal, 'Lane5_RBV', write_pv='Lane5', kind='config')
    lane6 = Cpt(EpicsSignal, 'Lane6_RBV', write_pv='Lane6', kind='config')
    lane7 = Cpt(EpicsSignal, 'Lane7_RBV', write_pv='Lane7', kind='config')


class Wave8V2ADCSampleReadout(Device):
    """
    Class for the LCLS-II Wave8 ADC sample readout registers.
    """

    convert = Cpt(EpicsSingal, ':Convert_RBV', write_pv=':Convert',
                  kind='config')

    dmode = Cpt(EpicsSingal, ':DMode_RBV', write_pv=':DMode', kind='config')

    invert = Cpt(EpicsSingal, ':Invert_RBV', write_pv=':Invert', kind='config')

    adcA_samples = Cpt(Wave8V2ADCSamples, ':AdcA')
    adcB_samples = Cpt(Wave8V2ADCSamples, ':AdcB')

    adcA_delay_lanes = Cpt(Wave8V2ADCDelayLanes, ':DelayAdcA')
    adcB_delay_lanes = Cpt(Wave8V2ADCDelayLanes, ':DelayAdcB')


class Wave8V2AxiVersion(Device):
    """
    Class for LCLS-II Wave8 AxiVersion registers.
    """

    build_stamp = Cpt(EpicsSignalRO, ':BuildStamp', kind='config')

    fpga_reload = Cpt(EpicsSignal, ':FpgaReload', kind='config')
    set_metadata(fpga_reload, dict(variety='command-proc', value=1))
    
    fpga_version = Cpt(EpicsSignalRO, ':FpgaVersion', kind='config')
    
    scratch_pad = Cpt(EpicsSignal, ':ScratchPad_RBV', write_pv=':ScratchPad',
                      kind='config')

    user_reset = Cpt(EpicsSignal, ':UserReset_RBV', write_pv=':UserReset',
                      kind='config')

    uptime = Cpt(EpicsSignalRO, ':UpTime', kind='config')


class Wave8V2EventBuilder(Device):
    """
    Class for controlling the LCLS-II Wave8 event builder registers.
    """
    cnt_rst = Cpt(EpicsSignal, ':CntRst', kind='normal')
    set_metadata(cnt_rst, dict(variety='command-proc', value=1))

    hard_rst = Cpt(EpicsSignal, ':HardRst', kind='normal')
    set_metadata(hard_rst, dict(variety='command-proc', value=1))

    soft_rst = Cpt(EpicsSignal, ':SoftRst', kind='normal')
    set_metadata(soft_rst, dict(variety='command-proc', value=1))
 
    timer_rst = Cpt(EpicsSignal, ':TimerRst', kind='normal')
    set_metadata(timer_rst, dict(variety='command-proc', value=1))

    blowoff_ext = Cpt(EpicsSignalRO, ':BlowoffExt', kind='config')
    blowoff = Cpt(EpicsSignal, ':Blowoff_RBV', write_pv=':Blowoff',
                  kind='config')
    bypass = Cpt(EpicsSignal, ':Bypass_RBV', write_pv=':Bypass',
                 kind='config')

    # DataCnt1 through DataCnt9 are the raw waveforms; captured elsewhere. 
    datacnt0 = Cpt(EpicsSignalRO, ':DataCnt0', kind='config')
    datacnt10 = Cpt(EpicsSignalRO, ':DataCnt10', kind='config')

    # NullCnt1 through NullCnt9 are not needed here. 
    nullcnt0 = Cpt(EpicsSignalRO, ':NullCnt0', kind='config')
    nullcnt10 = Cpt(EpicsSignalRO, ':NullCnt10', kind='config')

    # TimeoutDropCnt1 through TimeoutDropCnt9 are not needed here. 
    timeout_dropcnt0 = Cpt(EpicsSignalRO, ':NullCnt0', kind='config')
    timeout_dropcnt10 = Cpt(EpicsSignalRO, ':NullCnt10', kind='config')

    timeout = Cpt(EpicsSignal, ':Timeout_RBV', write_pv=':Timeout',
                  kind='config')

    num_slaves_g = Cpt(EpicsSignalRO, ':NUM_SLAVES_G', kind='config')
    trans_tdest_g = Cpt(EpicsSignalRO, ':TRANS_TDEST_G', kind='config')

    state = Cpt(EpicsSignalRO, ':State', kind='config')

    transaction_cnt = Cpt(EpicsSignalRO, ':TransactionCnt', kind='config')


class Wave8V2EvrV2(Device):
    """
    Class for LCLS-II Wave8 EVR V2 (TPR) registers.
    """

    count = Cpt(EpicsSignalRO, ':Count', kind='config') 

    delay = Cpt(EpicsSignal, ':Delay_RBV', write_pv=':Delay', kind='config')
    dest_sel = Cpt(EpicsSignal, ':DestSel_RBV', write_pv=':DestSel',
                   kind='config')
    dest_type = Cpt(EpicsSignal, ':DestType_RBV', write_pv=':DestType',
                    kind='config')
    enable_reg = Cpt(EpicsSignal, ':EnableReg_RBV', write_pv=':EnableReg',
                     kind='config')
    enable_trig = Cpt(EpicsSignal, ':EnableTrig_RBV', write_pv=':EnableTrig',
                      kind='config')
    event_code = Cpt(EpicsSignal, ':EventCode_RBV', write_pv=':EventCode',
                     kind='config')
    polarity = Cpt(EpicsSignal, ':Polarity_RBV', write_pv=':Polarity',
                   kind='config')
    rate_type = Cpt(EpicsSignal, ':RateType_RBV', write_pv=':RateType',
                    kind='config')
    source = Cpt(EpicsSignal, ':Source_RBV', write_pv=':Source',
                    kind='config')


class Wave8V2Integrators(Device):
    """
    Class for controlling the LCLS-II Wave8 integrators.
    """
    # Including PVs based on EDM GUI. 
    integral_size = Cpt(EpicsSignal, ':IntegralSize_RBV',
                        write_pv=':IntegralSize', kind='config')
    baseline_size = Cpt(EpicsSignal, ':BaselineSize_RBV',
                        write_pv=':BaselineSize', kind='config')
    trig_delay = Cpt(EpicsSignal, ':TrigDelay_RBV',
                     write_pv=':TrigDelay', kind='config')
    quadrant_sel = Cpt(EpicsSignal, ':QuadrantSel_RBV',
                       write_pv=':QuadrantSel', kind='config')

    corr_coeff_raw0 = Cpt(EpicsSignal, ':CorrCoefficientRaw0_RBV',
                          write_pv=':CorrCoefficientRaw0', kind='config')
    corr_coeff_raw1 = Cpt(EpicsSignal, ':CorrCoefficientRaw1_RBV',
                          write_pv=':CorrCoefficientRaw1', kind='config')
    corr_coeff_raw2 = Cpt(EpicsSignal, ':CorrCoefficientRaw2_RBV',
                          write_pv=':CorrCoefficientRaw2', kind='config')

    cnt_rst = Cpt(EpicsSignal, ':CntRst_RBV', write_pv=':CntRst',
                  kind='config')

    proc_fifo_pause_thresh = Cpt(EpicsSignal, ':ProcFifoPauseThreshold',
                                 kind='config')

    int_fifo_pause_thresh = Cpt(EpicsSignal, ':IntFifoPauseThreshold_RBV',
                          write_pv=':IntFifoPauseThreshold', kind='config')

    intensity_raw = Cpt(EpicsSignalRO, ':IntensityRaw', kind='config')
    pos_x_raw = Cpt(EpicsSignalRO, ':PositionXRaw', kind='config')
    pos_y_raw = Cpt(EpicsSignalRO, ':PositionYRaw', kind='config')

    adc_integral0 = Cpt(EpicsSignalRO, ':AdcIntegral0', kind='config')
    adc_integral7 = Cpt(EpicsSignalRO, ':AdcIntegral7', kind='config')

    baseline0 = Cpt(EpicsSignalRO, ':Baseline0', kind='config')
    baseline7 = Cpt(EpicsSignalRO, ':Baseline7', kind='config')

    proc_fifo_pause_cnt = Cpt(EpicsSignalRO, ':ProcFifoPauseCnt',
                              kind='config')

    int_fifo_pause_cnt = Cpt(EpicsSignalRO, ':IntFifoPauseCnt',
                             kind='config')

    trig_cnt = Cpt(EpicsSignalRO, ':TrigCnt', kind='config')


class Wave8V2PgpMon(Device):
    """
    Class for monitoring the PGP status of the LCLS-II Wave8.
    """

    count_reset = Cpt(EpicsSignal, ':CountReset', kind='config')

    rx_eb_overflow_cnt = Cpt(EpicsSignalRO, ':RxStatus:EbOverflowCnt',
                             kind='config')

    rx_frame_cnt = Cpt(EpicsSignalRO, ':RxStatus:FrameCnt', kind='config')

    rx_link_down_cnt = Cpt(EpicsSignalRO, ':RxStatus:LinkDownCnt',
                           kind='config')
    rx_link_error_cnt = Cpt(EpicsSignalRO, ':RxStatus:LinkErrorCnt',
                            kind='config')
    rx_link_ready_cnt = Cpt(EpicsSignalRO, ':RxStatus:LinkReadyCnt',
                            kind='config')
    rx_link_ready = Cpt(EpicsSignalRO, ':RxStatus:LinkReady',
                        kind='config')

    rx_phys_active_cnt = Cpt(EpicsSignalRO, ':RxStatus:PhysActiveCnt',
                             kind='config')
    rx_phys_active = Cpt(EpicsSignalRO, ':RxStatus:PhysActive',
                         kind='config')

    rx_rem_overflow_cnt0 = Cpt(EpicsSignalRO, ':RxStatus:RemOverflowCnt0',
                               kind='config')
    rx_rem_overflow_cnt1 = Cpt(EpicsSignalRO, ':RxStatus:RemOverflowCnt1',
                               kind='config')
    rx_rem_overflow_cnt2 = Cpt(EpicsSignalRO, ':RxStatus:RemOverflowCnt2',
                               kind='config')
    rx_rem_overflow_cnt3 = Cpt(EpicsSignalRO, ':RxStatus:RemOverflowCnt3',
                               kind='config')

    rx_rem_link_ready_cnt = Cpt(EpicsSignalRO, ':RxStatus:RemRxLinkReadyCnt',
                                kind='config')
    rx_rem_link_ready = Cpt(EpicsSignalRO, ':RxStatus:RemRxLinkReady',
                            kind='config')

    tx_frame_cnt = Cpt(EpicsSignalRO, ':TxStatus:FrameCnt', kind='config')

    tx_link_ready_cnt = Cpt(EpicsSignalRO, ':TxStatus:LinkReadyCnt',
                            kind='config')
    tx_link_ready = Cpt(EpicsSignalRO, ':TxStatus:LinkReady',
                        kind='config')

    tx_loc_overflow_cnt0 = Cpt(EpicsSignalRO, ':RxStatus:LocOverflowCnt0',
                            kind='config')
    tx_loc_overflow_cnt1 = Cpt(EpicsSignalRO, ':RxStatus:LocOverflowCnt1',
                            kind='config')
    tx_loc_overflow_cnt2 = Cpt(EpicsSignalRO, ':RxStatus:LocOverflowCnt2',
                            kind='config')
    tx_loc_overflow_cnt3 = Cpt(EpicsSignalRO, ':RxStatus:LocOverflowCnt3',
                               kind='config')

    tx_phys_active_cnt = Cpt(EpicsSignalRO, ':TxStatus:PhysActiveCnt',
                             kind='config')
    tx_phys_active = Cpt(EpicsSignalRO, ':TxStatus:PhysActive',
                         kind='config')


class Wave8V2TrigEventBuffer(Device):
    """
    Class for LCLS-II Wave8 trigger event buffer.
    """

    

class Wave8V2(Device):
    """
    Complete top-level class for the LCLS-II Wave8. Put _all_ the things in. 
    """

    run_start = Cpt(EpicsSignal, ':SeqStartRun.PROC', kind='normal')
    set_metadata(run_start, dict(variety='command-proc', value=1))

    run_stop = Cpt(EpicsSignal, ':SeqStopRun.PROC', kind='normal')
    set_metadata(run_stop, dict(variety='command-proc', value=1))
    
    ch0 = Cpt(Wave8V2Channel, ':CH0')
    ch1 = Cpt(Wave8V2Channel, ':CH1')
    ch2 = Cpt(Wave8V2Channel, ':CH2')
    ch3 = Cpt(Wave8V2Channel, ':CH3')
    ch4 = Cpt(Wave8V2Channel, ':CH4')
    ch5 = Cpt(Wave8V2Channel, ':CH5')
    ch6 = Cpt(Wave8V2Channel, ':CH6')
    ch7 = Cpt(Wave8V2Channel, ':CH7')

    sys_regs = Cpt(Wave8V2SystemRegs, ':Top:SystemRegs')

    raw_buffers = Cpt(Wave8V2RawBuffers, ':Top:RawBuffers')

    sfp0 = Cpt(Wave8V2Sfp, ':Sfp0') # Typ. DAQ fiber
    sfp1 = Cpt(Wave8V2Sfp, ':Sfp1') # Typ. Controls fiber
    sfp2 = Cpt(Wave8V2Sfp, ':Sfp2') # Typ. LCLS-II timing
    sfp3 = Cpt(Wave8V2Sfp, ':Sfp3') # Typ. LCLS-I timing

    adc_config0 = Cpt(Wave8V2ADCRegs, ':AdcConfig0')
    adc_config1 = Cpt(Wave8V2ADCRegs, ':AdcConfig1')
    adc_config2 = Cpt(Wave8V2ADCRegs, ':AdcConfig2')
    adc_config3 = Cpt(Wave8V2ADCRegs, ':AdcConfig3')
    
    adc_sample_readout0 = Cpt(Wave8V2ADCSampleReadout, ':AdcReadout0')
    adc_sample_readout1 = Cpt(Wave8V2ADCSampleReadout, ':AdcReadout1')
    adc_sample_readout2 = Cpt(Wave8V2ADCSampleReadout, ':AdcReadout2')
    adc_sample_readout3 = Cpt(Wave8V2ADCSampleReadout, ':AdcReadout3')

    axi_version = Cpt(Wave8V2AxiVersion, ':AxiVersion')

    event_builder = Cpt(Wave8V2EventBuilder, ':EventBuilder')

    evr_v2 = Cpt(Wave8V2EvrV2, ':EvrV2')
    
    integrators = Cpt(Wave8V2Integrators, ':Integrators')

    pgp_mon0 = Cpt(Wave8V2PgpMon, ':PgpMon0')
    pgp_mon1 = Cpt(Wave8V2PgpMon, ':PgpMon1')


#cat wave8Reg.db | grep record | cut -d' ' -f3 | sed -e 's/"$(P)$(R)/:/g' | sed -e 's/"/", kind="config")/g' | uniq
:Timing:ClkSel, kind='config')
:Timing:ClkSel_RBV, kind='config')
:Timing:C_RxReset, kind='config')
:Timing:eofCount, kind='config')
:Timing:FidCount, kind='config')
:TimingFrameRx:RxClkCount, kind='config')
:TimingFrameRx:RxRstCount, kind='config')
:Timing:ModeSelEn, kind='config')
:Timing:ModeSelEn_RBV, kind='config')
:Timing:ModeSel, kind='config')
:Timing:ModeSel_RBV, kind='config')
:Timing:RxDown, kind='config')
:Timing:RxDown_RBV, kind='config')
:Timing:RxLinkUp, kind='config')
:Timing:RxPllReset, kind='config')
:Timing:RxPllReset_RBV, kind='config')
:Timing:sofCount, kind='config')
:Timing:timingRxUserRst, kind='config')
:Timing:timingTxUserRst, kind='config')
:Timing:UseMiniTpg, kind='config')
:Timing:UseMiniTpg_RBV, kind='config')
:TrEvent:FifoOverflow, kind='config')
:TrEvent:FifoPause, kind='config')
:TrEvent:FifoReset, kind='config')
:TrEvent:FifoWrCnt, kind='config')
:TrEvent:L0Count, kind='config')
:TrEvent:L1AcceptCount, kind='config')
:TrEvent:L1RejectCount, kind='config')
:TrEvent:MasterEnable, kind='config')
:TrEvent:MasterEnable_RBV, kind='config')
:TrEvent:NotPauseToTrig, kind='config')
:TrEvent:Partition, kind='config')
:TrEvent:Partition_RBV, kind='config')
:TrEvent:PauseThreshold, kind='config')
:TrEvent:PauseThreshold_RBV, kind='config')
:TrEvent:PauseToTrig, kind='config')
:TrEvent:ResetCounters, kind='config')
:TrEvent:TransitionCount, kind='config')
:TrEvent:TriggerCount, kind='config')
:TrEvent:TriggerDelay, kind='config')
:TrEvent:TriggerDelay_RBV, kind='config')
:TrEvent:XpmMessageCount, kind='config')
:TrEvent:XpmMsg:PartitionDelay0, kind='config')
:TrEvent:XpmMsg:PartitionDelay1, kind='config')
:TrEvent:XpmMsg:PartitionDelay2, kind='config')
:TrEvent:XpmMsg:PartitionDelay3, kind='config')
:TrEvent:XpmMsg:PartitionDelay4, kind='config')
:TrEvent:XpmMsg:PartitionDelay5, kind='config')
:TrEvent:XpmMsg:PartitionDelay6, kind='config')
:TrEvent:XpmMsg:PartitionDelay7, kind='config')
:TrEvent:XpmMsg:RxId, kind='config')
:TrEvent:XpmMsg:TxId, kind='config')
:TrEvent:XpmMsg:TxId_RBV, kind='config')
:TrEvent:XpmOverflow, kind='config')
:TrEvent:XpmPause, kind='config')
:XpmMini:Config_L0Select_DestSel, kind='config')
:XpmMini:Config_L0Select_DestSel_RBV, kind='config')
:XpmMini:Config_L0Select_Enabled, kind='config')
:XpmMini:Config_L0Select_Enabled_RBV, kind='config')
:XpmMini:Config_L0Select_RateSel, kind='config')
:XpmMini:Config_L0Select_RateSel_RBV, kind='config')
:XpmMini:HwEnable, kind='config')
:XpmMini:HwEnable_RBV, kind='config')
:XpmMini:Link, kind='config')
:XpmMini:Link_RBV, kind='config')
