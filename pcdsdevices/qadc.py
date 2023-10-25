from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal

from .interface import BaseInterface
from .variety import set_metadata


class QadcCommon(BaseInterface, Device):
    """
    Common class for Abaco FMC digitizers. Used in Qadc and Qadc134.
    """

    ch0 = Cpt(EpicsSignal, ":CH0", kind="normal")
    ch1 = Cpt(EpicsSignal, ":CH1", kind="normal")
    ch2 = Cpt(EpicsSignal, ":CH2", kind="normal")
    ch3 = Cpt(EpicsSignal, ":CH3", kind="normal")
    config = Cpt(EpicsSignal, ":CONFIG", kind="config")
    start = Cpt(EpicsSignal, ":START", kind="normal")


class QadcLcls1Timing(BaseInterface, Device):
    """
    LCLS-I timing interface for FMC134 QADCs.
    """
    trig_event = Cpt(
        EpicsSignal, ":TRIG_EVENT_RBV", write_pv=":TRIG_EVENT", kind="config"
    )


class QadcLcls2Timing(BaseInterface, Device):
    """
    LCLS-II timing interface for FMC134 QADCs.
    """
    trig_rate_mode = Cpt(EpicsSignal, ":TRIG_RATEMODE", kind="config")
    trig_fixed_rate = Cpt(EpicsSignal, ":TRIG_FIXEDRATE", kind="config")
    trig_ac_rate = Cpt(EpicsSignal, ":TRIG_ACRATE", kind="config")
    trig_ts_mask = Cpt(EpicsSignal, ":TRIG_TSMASK", kind="config")
    trig_seq_num = Cpt(EpicsSignal, ":TRIG_SEQNUM", kind="config")
    trig_seq_bit = Cpt(EpicsSignal, ":TRIG_SEQBIT", kind="config")
    trig_partition = Cpt(EpicsSignal, ":TRIG_PARTITION", kind="config")


class Qadc134Common(QadcCommon):
    """
    Common class for FMC134 digitizers.
    """
    trig_delay = Cpt(
        EpicsSignal, ":TRIG_DELAY_RBV", write_pv=":TRIG_DELAY", kind="config"
    )
    full_en = Cpt(EpicsSignal, ":FULL_EN_RBV", write_pv=":FULL_EN", kind="config")
    hi_thresh = Cpt(EpicsSignal, ":HI_THRESH_RBV", write_pv=":HI_THRESH", kind="config")
    hi_thresh_raw = Cpt(
        EpicsSignal, ":HI_THRESH_RAW_RBV", write_pv=":HI_THRESH_RAW", kind="config"
    )
    ichan = Cpt(EpicsSignal, ":ICHAN_RBV", write_pv=":ICHAN", kind="config")
    interleave = Cpt(
        EpicsSignal, ":INTERLEAVE_RBV", write_pv=":INTERLEAVE", kind="config"
    )
    length = Cpt(EpicsSignal, ":LENGTH_RBV", write_pv=":LENGTH", kind="config")
    lo_thresh = Cpt(EpicsSignal, ":LO_THRESH_RBV", write_pv=":LO_THRESH", kind="config")
    lo_thresh_raw = Cpt(
        EpicsSignal, ":LO_THRESH_RAW_RBV", write_pv=":LO_THRESH_RAW", kind="config"
    )
    prescale = Cpt(EpicsSignal, ":PRESCALE_RBV", write_pv=":PRESCALE", kind="config")
    rows_after = Cpt(
        EpicsSignal, ":ROWS_AFTER_RBV", write_pv=":ROWS_AFTER", kind="config"
    )
    rows_before = Cpt(
        EpicsSignal, ":ROWS_BEFORE_RBV", write_pv=":ROWS_BEFORE", kind="config"
    )
    sparse_en = Cpt(EpicsSignal, ":SPARSE_EN_RBV", write_pv=":SPARSE_EN", kind="config")
    clear_config = Cpt(EpicsSignal, ":CLEAR_CONFIG", kind="config")
    set_metadata(clear_config, dict(variety='command-proc', value=1))
    out0 = Cpt(EpicsSignal, ":OUT0", kind="normal")
    out1 = Cpt(EpicsSignal, ":OUT1", kind="normal")
    rawdata0 = Cpt(EpicsSignal, ":RAWDATA0", kind="normal")
    rawdata1 = Cpt(EpicsSignal, ":RAWDATA1", kind="normal")
    sparse0 = Cpt(EpicsSignal, ":SPARSE0", kind="normal")
    sparse1 = Cpt(EpicsSignal, ":SPARSE1", kind="normal")


class Qadc134(Qadc134Common, QadcLcls1Timing):
    """
    Class for LCLS-I FMC134 digitizers. Implements LCLS-I timing interface.
    """


class Qadc134Lcls2(Qadc134Common, QadcLcls2Timing):
    """
    Class for LCLS-2 FMC134 digitizers. Implements LCLS-2 timing interface.
    """


class Qadc(QadcCommon):
    """
    Class for an older Abaco FMC PCIe digitzer, used in the LCLS-I hutches.
    """

    gain0_i = Cpt(EpicsSignal, ":GAIN0_I", kind="config")
    gain0_ni = Cpt(EpicsSignal, ":GAIN0_NI", kind="config")
    gain1_i = Cpt(EpicsSignal, ":GAIN1_I", kind="config")
    gain1_ni = Cpt(EpicsSignal, ":GAIN1_NI", kind="config")
    gain2_i = Cpt(EpicsSignal, ":GAIN2_I", kind="config")
    gain2_ni = Cpt(EpicsSignal, ":GAIN2_NI", kind="config")
    gain3_i = Cpt(EpicsSignal, ":GAIN3_I", kind="config")
    gain3_ni = Cpt(EpicsSignal, ":GAIN3_NI", kind="config")
    ichan = Cpt(EpicsSignal, ":ICHAN", kind="config")
    interleave = Cpt(EpicsSignal, ":INTERLEAVE", kind="config")
    length = Cpt(EpicsSignal, ":LENGTH", kind="config")
    off0_i = Cpt(EpicsSignal, ":OFF0_I", kind="config")
    off0_ni = Cpt(EpicsSignal, ":OFF0_NI", kind="config")
    off1_i = Cpt(EpicsSignal, ":OFF1_I", kind="config")
    off1_ni = Cpt(EpicsSignal, ":OFF1_NI", kind="config")
    off2_i = Cpt(EpicsSignal, ":OFF2_I", kind="config")
    off2_ni = Cpt(EpicsSignal, ":OFF2_NI", kind="config")
    off3_i = Cpt(EpicsSignal, ":OFF3_I", kind="config")
    off3_ni = Cpt(EpicsSignal, ":OFF3_NI", kind="config")
    out = Cpt(EpicsSignal, ":OUT", kind="normal")
    rawdata = Cpt(EpicsSignal, ":RAWDATA", kind="normal")
    train = Cpt(EpicsSignal, ":TRAIN", kind="config")
    trig_delay = Cpt(EpicsSignal, ":TRIG_DELAY", kind="config")
    trig_event = Cpt(EpicsSignal, ":TRIG_EVENT", kind="config")
