import time
import numpy as np
import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO

from .interface import BaseInterface
from .pv_positioner import PVPositionerDone
from .signal import AvgSignal


logger = logging.getLogger(__name__)


class BeamStats(BaseInterface, Device):
    mj = Cpt(EpicsSignalRO, 'GDET:FEE1:241:ENRC', kind='hinted')
    ev = Cpt(EpicsSignalRO, 'BLD:SYS0:500:PHOTONENERGY', kind='normal')
    rate = Cpt(EpicsSignalRO, 'EVNT:SYS0:1:LCLSBEAMRATE', kind='normal')
    owner = Cpt(EpicsSignalRO, 'ECS:SYS0:0:BEAM_OWNER_ID', kind='omitted')

    # Bunch charge
    bunch_charge = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO470', kind='normal')
    # estimated FEL Pulse Duration (FWHM)
    bunch_length = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO820', kind='normal')
    # Peak current after BC2 (A)
    peak_current = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO195', kind='normal')
    # Last Eloss sxray energy
    eloss_energy = Cpt(EpicsSignalRO, 'PHYS:SYS0:1:ELOSSENERGY', kind='normal')
    # Vernier energy?  FBCK:FB04:LG01:DL2VERNIER

    mj_avg = Cpt(AvgSignal, 'mj', averages=120, kind='normal')
    mj_buffersize = Cpt(AttributeSignal, 'mj_avg.averages', kind='config')

    tab_component_names = True

    def __init__(self, prefix='', name='beam_stats', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)


class SxrGmd(Device):
    mj = Cpt(EpicsSignalRO, 'SXR:GMD:BLD:milliJoulesPerPulse', kind='hinted')

    def __init__(self, prefix='', name='sxr_gmd', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)


class BeamEnergyRequest(PVPositionerDone):
    """
    Positioner to request beam color changes from ACR in eV.

    It is up to ACR how to and whether to fulfill these requests. This is often
    fulfilled by moving the Vernier but can also be a more involved process.

    Motion is immedately considered "done", but will not execute unless the
    requested position delta is larger than the tolerance. The default
    tolerance here is 30 eV, but this can be changed on a per-instance basis
    by passing ``atol`` into the initializer, or on a per-subclass basis by
    overriding the default.

    Parameters
    ----------
    prefix: str
        PV prefix for the request setpoint. This should always be a hutch name.

    name: str, required keyword
        Name to use for this device in log messages, data streams, etc.

    skip_small_moves: bool, optional
        Defaults to True, which ignores move requests that are smaller than the
        atol factor. If False, we'll perform every requested move.
        This can be very useful for synchronized energy scans where the ACR
        side of the process can be very slow, but does not necessarily need to
        happen at every step. Rather than design complicated scan patterns, we
        can skip the small moves here and move the monochromater and beam
        request devices in parallel.

    atol: int, optional
        Absolute tolerance that determines when the move is done and when to
        skip moves using the skip_small_moves parameter.
    """

    # Default vernier tolerance
    atol = 5

    setpoint = Cpt(EpicsSignal, ':USER:MCC:EPHOT', kind='hinted')

    def __init__(self, prefix, *, name, skip_small_moves=True, atol=None,
                 **kwargs):
        if atol is not None:
            self.atol = atol
        super().__init__(prefix, name=name, skip_small_moves=skip_small_moves,
                         **kwargs)


class LclsEvent(Device):
    def __init__(self, prefix='', name='lcls_event', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)

        # Abort Active Status
        # [ 0] Disable [ 1] Enable
        self.bykik_abort = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTACT',
                               kind='normal')
        # Abort Period in  beam shots
        self.bykik_period = Cpt(EpicsSignal, 'IOC:IN20:EV01:BYKIK_ABTPRD',
                                kind='normal')

        def bykik_status(self):
            """
            Returns status of bykik abort
            """
            status = self.bykik_abort.get()
            if status == 0:
                return 'Disable'
            else:
                return 'Enable'

        def bykik_disable(self):
            """
            Disables bykik abort
            """
            return self.bykik_abort.put(0)

        def bykik_enable(self):
            """
            Enables bykik abort
            """
            return self.bykik_abort.put(1)

        def bykik_get_period(self):
            """
            Gets the number of events between bykik aborts
            """
            return self.bykik_period.get()

        def bykik_set_period(self, period):
            """
            Sets the number of events between bykik aborts
            """
            return self.bykik_period.put(period)


class Linac(Device):
    """
    Contains methods to view and change parameters from the
    lcls event/timing system screen
    """
    def __init__(self, prefix='', name='linac', **kwargs):
        super().__init__(prefix=prefix, name=name, **kwargs)

        # Photon eV HXR (units: eV)
        self.photon_ev_hxr = Cpt(EpicsSignalRO, 'SIOC:SYS0:ML00:AO627',
                                 kind='normal')
        # BeTpv
        #  Actual Ratio
        self.actual_ratio = Cpt(EpicsSignalRO, 'SATT:FEE1:320:RACT',
                                kind='normal')
        # BeMilspv
        # Sum All
        self.sum_all = Cpt(EpicsSignalRO, 'SATT:FEE1:320:TACT',
                           kind='normal')

        # LCLSBEAM Event Rate (units: Hz)
        self.beam_event_rate = Cpt(EpicsSignalRO,
                                   'EVNT:SYS0:1:LCLSBEAMRATE',
                                   kind='normal')
        # Request BYKIK Burst Mode
        # [ 0] No [ 1] Yes
        self.is_bykik_burst_mode_en = Cpt(EpicsSignalRO,
                                          'IOC:BSY0:MP01:REQBYKIKBRST',
                                          kind='normal')
        # Request Pockels Cell Burst Mode
        # [ 0] No [ 1] Yes
        self.is_pockels_cell_burst_mode_en = Cpt(EpicsSignalRO,
                                                 'IOC:BSY0:MP01:REQPCBRST',
                                                 kind='normal')
        # Maximum Pulses to Inhibit
        self.max_pulses_to_inhibit = Cpt(EpicsSignal,
                                         'PATT:SYS0:1:MPSBURSTCNTMAX',
                                         kind='normal')
        # MPSBURST Control
        self.mps_burst_control = Cpt(EpicsSignal,
                                     'PATT:SYS0:1:MPSBURSTCTRL',
                                     kind='normal')
        # Actual Count
        self.burst_count = Cpt(EpicsSignalRO, 'PATT:SYS0:1:MPSBURSTCNT',
                               kind='norml')
        # aximum Pulses to Inhibit
        self.test_burst_count = Cpt(EpicsSignal,
                                    'PATT:SYS0:1:TESTBURSTCNTMAX',
                                    kind='normal')
        # Rate to Inhibit Pulses
        self.rate_to_inhibit_pulses = Cpt(EpicsSignal,
                                          'PATT:SYS0:1:MPSBURSTRATE',
                                          kind='normal')
        # Rate to Inhibit Pulses
        self.test_burst_rate = Cpt(EpicsSignal,
                                   'PATT:SYS0:1:TESTBURSTRATE',
                                   kind='normal')
        # Set Pattern Check Parameters
        self.test_burst = Cpt(EpicsSignal, 'PATT:SYS0:1:TESTBURST.N',
                              kind='normal')
        # undulator k value - not the correct PV i think
        self.undulator_k = Cpt(EpicsSignal, 'USEG:UND1:150:KACT',
                               kind='normal')
        # MPSBURST Control
        # [ 0] Off [ 1] Burst - why declared twice?
        self.burst_delivered = Cpt(EpicsSignalRO, 'PATT:SYS0:1:MPSBURSTCTRL',
                                   kind='normal')

        self.dict_rate_to_enum = {0.5: 5, 1: 4, 5: 3, 10: 2, 30: 1,
                                  120: 0, 0: 0}

        self.freqs = {'Full': 0, 'full': 0, '30Hz': 1, '10Hz': 2,
                      '5Hz': 3, '1Hz': 4, '0.5Hz': 5}

    def get_BeL(self):
        return self.sum_all.get() / 1e3 * 25.4e-3

    def get_BeT(self):
        return self.actual_ratio.get()

    def get_fee_att_t(self):
        return self.actual_ratio.get()

    def get_xray_eV(self):
        return self.photon_ev_hxr.get()

    def is_burst_enabled(self):
        """
        Checks if the burst is enabled
        """
        is_burst_en = (self.is_bykik_burst_mode_en.get() == 1 or
                       self.is_pockels_cell_burst_mode_en.get() == 1)
        return True if is_burst_en else False

    def is_legal_rate(self, rate):
        return rate in self.dict_rate_to_enum

    def set_num_burst(self, num):
        if num == "forever":
            num = -1
        self.max_pulses_to_inhibit.put(int(num))

    def get_num_bursts(self):
        return self.burst_count.get()

    def get_burst(self, num=None, wait=False):
        if num is not None:
            self.set_num_burst(num)
            time.sleep(0.03)
            # make sure the PV is written before executing
            self.start_burst()

    def get_shot(self):
        self.set_num_burst(1)
        time.sleep(0.03)
        # make sure PV is written before executing
        # return self.mps_burst_control.put(1)
        self.start_burst()

    def start_burst(self):
        return self.mps_burst_control.put(1)

    def stop_burst(self):
        self.mps_burst_control.put(0)
        self.set_num_burst(1)

    def stop(self):
        self.stop_burst()

    def burst_forever(self):
        self.set_num_burst(-1)
        time.sleep(0.1)
        self.start_burst()

    def set_test_nburst(self, num):
        if num == "forever":
            num = -1
        self.test_burst_count.put(int(num))

    def set_fburst(self, f='Full'):
        f.replace(' ', '')
        # remove spaces
        if not (f in self.freqs):
            logger.error('Frequency should be one of: %s',
                         list(self.dict_rate_to_enum.keys()))
            return
        self.rate_to_inhibit_pulses.put(self.freqs[f])

    def set_burst_rate(self, rate):
        if not (rate in self.dict_rate_to_enum):
            logger.error('Rate should be one of: %s',
                         list(self.dict_rate_to_enum.keys()))
            return
        self.test_burst.put(0)
        self.test_burst_rate.put(self.dict_rate_to_enum[rate])

    def get_fburst(self):
        rate = self.rate_to_inhibit_pulses.get()
        if rate == 0:
            return self.get_ebeam_rate()
        elif rate == 1:
            return 30.0
        elif rate == 2:
            return 10.0
        elif rate == 3:
            return 5.0
        elif rate == 4:
            return 1.0
        elif rate == 5:
            return 0.5
        else:
            return 0.0

    def get_test_burst(self):
        rate = self.test_burst_rate.get()
        if rate == 0:
            return self.get_ebeam_rate()
        elif rate == 1:
            return 30.0
        elif rate == 2:
            return 10.0
        elif rate == 3:
            return 5.0
        elif rate == 4:
            return 1.0
        elif rate == 5:
            return 0.5
        else:
            return 0.0

    def get_ebeam_rate(self):
        return self.beam_event_rate.get()

    def get_xray_beam_rate(self):
        if self.is_bykik_burst_mode_en():
            return self.get_fburst()
        else:
            return self.get_ebeam_rate()

    def wait_burst(self, timeout=1.0):
        self.burst_delivered.wait_for_value(1, float(timeout))
        time.sleep(0.2)
        # This is commented out in the old code too
        # while(self.mps_burst_control.get() != 0):
        #     time.sleep(0.02)
        #     logger.info('Wait...')

    def wait_for_shot(self, verbose=False, timeout=None):
        """
        Waits for the burst to be over to make sure the PV is
        written, otherwise a sequence get_shot(); wait_for_shot() may fail
        """
        time.sleep(0.03)
        t0 = time.time()
        self.burst_delivered.wait_for_value(0, timeout)
        if verbose:
            logger.info("waited %.3f secs for shots" % (time.time() - t0))

    def GeV_to_keV(self, electron_in_GeV):
        und_period = 3
        # in cm
        und_K = self.undulator_k_k.get()
        return 0.95 * electron_in_GeV ** 2 / (1 + und_K ** 2 / 2) / und_period

    def KeV_to_GeV(self, exray_in_keV):
        und_period = 3
        # in cm
        und_K = self.undulator_k.get()
        return np.sqrt((1 + und_K ** 2 / 2) * und_period * exray_in_keV / 0.95)
