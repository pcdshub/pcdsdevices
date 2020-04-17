from ophyd.areadetector.plugins import ImagePlugin, ROIPlugin, StatsPlugin
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from .areadetector.detectors import PCDSAreaDetector
from .component import UnrelatedComponent as UCpt
from .epics_motor import IMS


class Injector(Device):
    """
    Injector Positioner.

    Consists of 3 coarse control motors and 3 fine control motors.

    Parameters
    ----------
    pvs : str dict
       A dictionary containing the name of the device and
       the PVs of all the injector components.

    Attributes
    ----------
    coarseX : EpicsSignal
        The coarse control motor in the X direction.

    coarseY : EpicsSignal
        The coarse control motor in the Y direction.

    coarseZ : EpicsSignal
        The coarse control motor in the Z direction.

    fineX : EpicsSignal
        The fine control motor in the X direction.

    fineY : EpicsSignal
        The fine control motor in the Y direction.

    fineZ : EpicsSignal
        The fine control motor in the Z direction.
    """

    coarseX = UCpt(IMS)
    coarseY = UCpt(IMS)
    coarseZ = UCpt(IMS)
    fineX = UCpt(IMS)
    fineY = UCpt(IMS)
    fineZ = UCpt(IMS)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class Selector(Device):
    """
    A Selector for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the name of the device and
        the PVs of all the selector components.

    Attributes
    ----------
    remote_control : EpicsSignal
        Remote control enabled.

    status : EpicsSignal
        Connection status for selector.

    flow : EpicsSignal
        Flow.

    flowstate : EpicsSignal
        State of the flow.

    flowtype : EpicsSignal
        Type of the flow.

    FM_rb : EpicsSignal

    FM_reset : EpicsSignal

    FM : EpicsSignal

    names_button : EpicsSignal

    couple_button : EpicsSignal

    names1 : EpicsSignal

    names2 : EpicsSignal

    shaker1 : EpicsSignal
        Shaker 1.

    shaker2 : EpicsSignal
        Shaker 2.

    shaker3 : EpicsSignal
        Shaker 3.

    shaker4 : EpicsSignal
        Shaker 4.
    """

    # also appears on pressure controller screen?
    remote_control = UCpt(EpicsSignal)
    status = UCpt(EpicsSignal)

    flow = UCpt(EpicsSignal)
    flowstate = UCpt(EpicsSignal)
    flowtype = UCpt(EpicsSignal)

    FM_rb = UCpt(EpicsSignal)
    FM_reset = UCpt(EpicsSignal)
    FM = UCpt(EpicsSignal)

    names_button = UCpt(EpicsSignal)
    couple_button = UCpt(EpicsSignal)
    names1 = UCpt(EpicsSignal)
    names2 = UCpt(EpicsSignal)

    shaker1 = UCpt(EpicsSignal)
    shaker2 = UCpt(EpicsSignal)
    shaker3 = UCpt(EpicsSignal)
    shaker4 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class CoolerShaker(Device):
    """
    A Cooler/Shaker for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the cooler/shaker components.
    name : str
        The device name.

    Attributes
    ----------
    temperature1 : EpicsSignal
        Temperature of 1.

    SP1 : EpicsSignal
        Set point of 1.

    set_SP1 : EpicsSignal
        Set the set point for 1.

    current1 : EpicsSignal
        Current for 1.

    temperature2 : EpicsSignal
        Temperature of 2.

    SP2 : EpicsSignal
        Set point of 2.

    set_SP2 : EpicsSignal
        Set the set point of 2.

    current2 : EpicsSignal
        Current of 2.

    reboot : EpicsSignal
        Reboot the cooler/shaker.
    """

    temperature1 = UCpt(EpicsSignal)
    SP1 = UCpt(EpicsSignal)
    set_SP1 = UCpt(EpicsSignal)
    current1 = UCpt(EpicsSignal)

    temperature2 = UCpt(EpicsSignal)
    SP2 = UCpt(EpicsSignal)
    set_SP2 = UCpt(EpicsSignal)
    current2 = UCpt(EpicsSignal)

    reboot = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class HPLC(Device):
    """
    An HPLC for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the HPLC components.

    name : str
        The device name.

    Attributes
    ----------
    status : EpicsSignal
        Status of the HPLC.

    run : EpicsSignal
        Run the HPLC.

    flowrate : EpicsSignal
        Flow rate of the HPLC.

    set_flowrate : EpicsSignal
        Set the flow rate of the HPLC.

    flowrate_SP : EpicsSignal
        Set point for the flow rate.

    pressure : EpicsSignal
        Pressure in the HPLC.

    pressure_units : EpicsSignal
        Units for the pressure.

    set_max_pressure : EpicsSignal
        Set the maximum pressure.

    max_pressure : EpicsSignal
        Maximum pressure.

    clear_error : EpicsSignal
        Clear errors.
    """

    status = UCpt(EpicsSignal)
    run = UCpt(EpicsSignal)

    flowrate = UCpt(EpicsSignal)
    set_flowrate = UCpt(EpicsSignal)
    flowrate_SP = UCpt(EpicsSignal)

    pressure = UCpt(EpicsSignal)
    pressure_units = UCpt(EpicsSignal)
    set_max_pressure = UCpt(EpicsSignal)
    max_pressure = UCpt(EpicsSignal)

    clear_error = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(name=name, **kwargs)


class PressureController(Device):
    """
    An Pressure Controller for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the pressure
        controller components.

    name : str
        The device name.

    Attributes
    ----------
    status : EpicsSignal
        Connection status of pressure controller.

    pressure1 : EpicsSignal
        Pressure of 1.

    enabled1 : EpicsSignal
        Is 1 enabled.

    limit1 : EpicsSignal
        High pressure limit of 1.

    SP1 : EpicsSignal
        Pressure set point of 1.

    pressure2 : EpicsSignal
        Pressure of 2.

    enabled2 : EpicsSignal
        Is 2 enabled.

    limit2 : EpicsSignal
        High pressure limit of 2.

    SP2 : EpicsSignal
        Pressure set point of 2.
    """

    status = UCpt(EpicsSignal)

    pressure1 = UCpt(EpicsSignal)
    enabled1 = UCpt(EpicsSignal)
    limit1 = UCpt(EpicsSignal)
    SP1 = UCpt(EpicsSignal)

    pressure2 = UCpt(EpicsSignal)
    enabled2 = UCpt(EpicsSignal)
    limit2 = UCpt(EpicsSignal)
    SP2 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class FlowIntegrator(Device):
    """
    An Flow Integrator for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the flow integrator components.

    name : str
        The device name.


    Attributes
    ----------
    integrator_source: EpicsSignal

    flow_source : EpicsSignal

    names : EpicsSignal
        Names of.

    start1 : EpicsSignal
        Starting volume of 1.

    used1 : EpicsSignal
        Flow of 1.

    time1 : EpicsSignal
        Estimated depletion time of 1.

    start2 : EpicsSignal
        Starting volume of 2.

    used2 : EpicsSignal
        Flow of 2.

    time2 : EpicsSignal
        Estimated depletion time of 2.

    start3 : EpicsSignal
        Starting volume of 3.

    used3 : EpicsSignal
        Flow of 3.

    time3 : EpicsSignal
        Estimated depletion time of 3.

    start4 : EpicsSignal
        Starting volume of 4.

    used4 : EpicsSignal
        Flow of 4.

    time4 : EpicsSignal
        Estimated depletion time of 4.

    start5 : EpicsSignal
        Starting volume of 5.

    used5 : EpicsSignal
        Flow of 5.

    time5 : EpicsSignal
        Estimated depletion time of 5.

    start6 : EpicsSignal
        Starting volume of 6.

    used6 : EpicsSignal
        Flow of 6.

    time6 : EpicsSignal
        Estimated depletion time of 6.

    start7 : EpicsSignal
        Starting volume of 7.

    used7 : EpicsSignal
        Flow of 7.

    time7 : EpicsSignal
        Estimated depletion time of 7.

    start8 : EpicsSignal
        Starting volume of 8.

    used8 : EpicsSignal
        Flow of 8.

    time8 : EpicsSignal
        Estimated depletion time of 8.

    start9 : EpicsSignal
        Starting volume of 9.

    used9 : EpicsSignal
        Flow of 9.

    time9 : EpicsSignal
        Estimated depletion time of 9.

    start10 : EpicsSignal
        Starting volume of 10.

    used10 : EpicsSignal
        Flow of 10.

    time10 : EpicsSignal
        Estimated depletion time of 10.

    """

    integrator_source = UCpt(EpicsSignal)
    flow_source = UCpt(EpicsSignal)
    names = UCpt(EpicsSignal)

    start1 = UCpt(EpicsSignal)
    used1 = UCpt(EpicsSignal)
    time1 = UCpt(EpicsSignal)

    start2 = UCpt(EpicsSignal)
    used2 = UCpt(EpicsSignal)
    time2 = UCpt(EpicsSignal)

    start3 = UCpt(EpicsSignal)
    used3 = UCpt(EpicsSignal)
    time3 = UCpt(EpicsSignal)

    start4 = UCpt(EpicsSignal)
    used4 = UCpt(EpicsSignal)
    time4 = UCpt(EpicsSignal)

    start5 = UCpt(EpicsSignal)
    used5 = UCpt(EpicsSignal)
    time5 = UCpt(EpicsSignal)

    start6 = UCpt(EpicsSignal)
    used6 = UCpt(EpicsSignal)
    time6 = UCpt(EpicsSignal)

    start7 = UCpt(EpicsSignal)
    used7 = UCpt(EpicsSignal)
    time7 = UCpt(EpicsSignal)

    start8 = UCpt(EpicsSignal)
    used8 = UCpt(EpicsSignal)
    time8 = UCpt(EpicsSignal)

    start9 = UCpt(EpicsSignal)
    used9 = UCpt(EpicsSignal)
    time9 = UCpt(EpicsSignal)

    start10 = UCpt(EpicsSignal)
    used10 = UCpt(EpicsSignal)
    time10 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class SDS(Device):
    """
    Sample delivery system.

    Parameters
    ----------
    devices : dict
        A dictionary of dictionaries containing the devices to be made and
        their PV names. The dictionary key is a string, one of the following:
        {'selector', 'cooler_shaker', 'hplc', 'pressure_controller',
        'flow_integrator'}
        The values of the dictionary, are also dictionaries. These are passed
        to the new device, allowing parameters such as PV names to be
        specified.

    Attributes
    ----------
    SDS_devices : list
        List containing all the devices that are in the sample delivery system.
    """

    selector = UCpt(Selector)
    cooler_shaker = UCpt(CoolerShaker)
    hplc = UCpt(HPLC)
    pressure_controller = UCpt(PressureController)
    flow_integrator = UCpt(FlowIntegrator)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class Offaxis(PCDSAreaDetector):
    """
    Area detector for Offaxis camera in CXI.

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins.

    prefix : str
        Prefix for the PV name of the camera.

    name : str
        Name of the camera.

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image.

    ROI_stats : StatsPlugin
        Stats on ROI of original rate image.
    """

    ROI = UCpt(ROIPlugin)
    ROI_stats = UCpt(StatsPlugin)
    ROI_image = UCpt(ImagePlugin)

    # TODO: Figure out good default ROI_port
    def __init__(self, prefix, *, name, ROI_port=0, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Questar(PCDSAreaDetector):
    """
    Area detector for Inline Questar Camera in CXI.

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins.

    prefix : str
        Prefix for the PV name of the camera.

    name : str
        Name of the camera.

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image.

    ROI_stats : StatsPlugin
        Stats on ROI of original rate image.
    """

    ROI = UCpt(ROIPlugin)
    ROI_stats = UCpt(StatsPlugin)
    ROI_image = UCpt(ImagePlugin)

    def __init__(self, prefix, *, name, ROI_port=0, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Parameters(Device):
    """Contains EPICS PVs used for jet tracking."""
    cam_x = Cpt(EpicsSignal, ':CAM_X',
                doc='x-coordinate of camera position in mm')
    cam_y = Cpt(EpicsSignal, ':CAM_Y',
                doc='y-coordinate of camera position in mm')
    pxsize = Cpt(EpicsSignal, ':PXSIZE',
                 doc='size of pixel in mm')
    cam_roll = Cpt(EpicsSignal, ':CAM_ROLL',
                   doc='rotation of camera about z axis in radians')
    beam_x = Cpt(EpicsSignal, ':BEAM_X',
                 doc='x-coordinate of x-ray beam in mm (usually 0)')
    beam_y = Cpt(EpicsSignal, ':BEAM_Y',
                 doc='y-coordinate of x-ray beam in mm (usually 0)')
    beam_x_px = Cpt(EpicsSignal, ':BEAM_X_PX',
                    doc='x-coordinate of x-ray beam in camera image in pixels')
    beam_y_px = Cpt(EpicsSignal, ':BEAM_Y_PX',
                    doc='y-coordinate of x-ray beam in camera image in pixels')
    nozzle_x = Cpt(EpicsSignal, ':NOZZLE_X',
                   doc='x-coordinate of nozzle in mm')
    nozzle_y = Cpt(EpicsSignal, ':NOZZLE_Y',
                   doc='y-coordinate of nozzle in mm')
    nozzle_xwidth = Cpt(EpicsSignal, ':NOZZLE_XWIDTH',
                        doc='width of nozzle in mm')
    jet_x = Cpt(EpicsSignal, ':JET_X',
                doc='distance from sample jet to x-ray beam in mm')
    jet_roll = Cpt(EpicsSignal, ':JET_ROLL',
                   doc='rotation of sample jet about z axis in radians')
    state = Cpt(EpicsSignal, ':STATE',
                doc='dictionary of strings')
    jet_counter = Cpt(EpicsSignal, ':JET_Counter',
                      doc='Jet counter')
    jet_reprate = Cpt(EpicsSignal, ':JET_RepRate',
                      doc='Jet repetition rate')
    nozzle_counter = Cpt(EpicsSignal, ':NOZZLE_Counter',
                         doc='Nozzle counter')
    nozzle_reprate = Cpt(EpicsSignal, ':NOZZLE_RepRate',
                         doc='Nozzle repetition rate')
    mean = Cpt(EpicsSignal, ':ROI_mean',
               doc='mean of calibration ROI image with jet')
    std = Cpt(EpicsSignal, ':ROI_std',
              doc='standard devation of calibration ROI image with jet')
    radius = Cpt(EpicsSignal, ':RADIUS',
                 doc='radius of calibration diffraction ring')
    intensity = Cpt(EpicsSignal, ':INTENSITY',
                    doc='intensity of calibration diffraction ring')
    thresh_hi = Cpt(EpicsSignal, ':THRESH_hi',
                    doc='upper threshold for CSPAD ring intensity')
    thresh_lo = Cpt(EpicsSignal, ':THRESH_lo',
                    doc='lower threshold for CSPAD ring intensity')
    thresh_w8 = Cpt(EpicsSignal, ':THRESH_w8',
                    doc='threshold for wave8')
    thresh_cam = Cpt(EpicsSignal, ':THRESH_cam',
                     doc='threshold for camera-based jet tracking')
    bypass_cam = Cpt(EpicsSignal, ':BYPASS_cam',
                     doc='bypass camera during jet tracking')
    frames_cam = Cpt(EpicsSignal, ':FRAMES_cam',
                     doc='number of frames for integration for camera')
    frames_cspad = Cpt(EpicsSignal, ':FRAMES_cspad',
                       doc='number of frames for integration for cspad')


class OffaxisParams(Device):
    """Contains EPICS PVs used with Offaxis camera for jet tracking."""
    cam_z = Cpt(EpicsSignal, ':CAM_Z',
                doc='z-coordinate of camera position in mm')
    cam_y = Cpt(EpicsSignal, ':CAM_Y',
                doc='y-coordinate of camera position in mm')
    pxsize = Cpt(EpicsSignal, ':PXSIZE',
                 doc='size of pixel in mm')
    cam_pitch = Cpt(EpicsSignal, ':CAM_PITCH',
                    doc='rotation of camera about x axis in radians')
    beam_z = Cpt(EpicsSignal, ':BEAM_Z',
                 doc='z-coordinate of x-ray beam in mm (usually 0)')
    beam_y = Cpt(EpicsSignal, ':BEAM_Y',
                 doc='y-coordinate of x-ray beam in mm (usually 0)')
    beam_z_px = Cpt(EpicsSignal, ':BEAM_Z_PX',
                    doc='z-coordinate of x-ray beam in camera image in pixels')
    beam_y_px = Cpt(EpicsSignal, ':BEAM_Y_PX',
                    doc='y-coordinate of x-ray beam in camera image in pixels')
    nozzle_z = Cpt(EpicsSignal, ':NOZZLE_Z',
                   doc='z-coordinate of nozzle in mm')
    nozzle_y = Cpt(EpicsSignal, ':NOZZLE_Y',
                   doc='y-coordinate of nozzle in mm')
    nozzle_zwidth = Cpt(EpicsSignal, ':NOZZLE_ZWIDTH',
                        doc='width of nozzle in mm')
    jet_z = Cpt(EpicsSignal, ':JET_Z',
                doc='distance from sample jet to x-ray beam in mm')
    jet_pitch = Cpt(EpicsSignal, ':JET_PITCH',
                    doc='rotation of sample jet about z axis in radians')
    state = Cpt(EpicsSignal, ':STATE',
                doc='dictionary of strings')
    jet_counter = Cpt(EpicsSignal, ':JET_Counter',
                      doc='Jet counter')
    jet_reprate = Cpt(EpicsSignal, ':JET_RepRate',
                      doc='Jet repetition rate')
    nozzle_counter = Cpt(EpicsSignal, ':NOZZLE_Counter',
                         doc='Nozzle counter')
    nozzle_reprate = Cpt(EpicsSignal, ':NOZZLE_RepRate',
                         doc='Nozzle repetition rate')
    mean = Cpt(EpicsSignal, ':ROI_mean',
               doc='mean of calibration ROI image with jet')
    std = Cpt(EpicsSignal, ':ROI_std',
              doc='standard devation of calibration ROI image with jet')
    radius = Cpt(EpicsSignal, ':RADIUS',
                 doc='radius of calibration diffraction ring')
    intensity = Cpt(EpicsSignal, ':INTENSITY',
                    doc='intensity of calibration diffraction ring')
    thresh_hi = Cpt(EpicsSignal, ':THRESH_hi',
                    doc='upper threshold for CSPAD ring intensity')
    thresh_lo = Cpt(EpicsSignal, ':THRESH_lo',
                    doc='lower threshold for CSPAD ring intensity')
    thresh_w8 = Cpt(EpicsSignal, ':THRESH_w8',
                    doc='threshold for wave8')
    thresh_cam = Cpt(EpicsSignal, ':THRESH_cam',
                     doc='threshold for camera-based jet tracking')
    bypass_cam = Cpt(EpicsSignal, ':BYPASS_cam',
                     doc='bypass camera during jet tracking')
    frames_cam = Cpt(EpicsSignal, ':FRAMES_cam',
                     doc='number of frames for integration for camera')
    frames_cspad = Cpt(EpicsSignal, ':FRAMES_cspad',
                       doc='number of frames for integration for cspad')


class Control(Device):
    """Contains EPICS PVs used for jet tracking control."""
    re_state = Cpt(EpicsSignal, ':RE:STATE')
    beam_state = Cpt(EpicsSignal, ':BEAM:STATE')
    injector_state = Cpt(EpicsSignal, ':INJECTOR:STATE')
    beam_trans = Cpt(EpicsSignal, ':BEAM:TRANS')
    beam_pulse_energy = Cpt(EpicsSignal, ':BEAM:PULSE_ENERGY')
    beam_e_thresh = Cpt(EpicsSignal, ':BEAM:E_THRESH')
    xstep_size = Cpt(EpicsSignal, ':INJECTOR:XSTEP_SIZE')
    xscan_min = Cpt(EpicsSignal, ':INJECTOR:XSCAN_MIN')
    xscan_max = Cpt(EpicsSignal, ':INJECTOR:XSCAN_MAX')
    bounce_width = Cpt(EpicsSignal, ':INJECTOR:BOUNCE_WIDTH')
    xmin = Cpt(EpicsSignal, ':INJECTOR:XMIN')
    xmax = Cpt(EpicsSignal, ':INJECTOR:XMAX')


class Diffract(Device):
    """
    Contains EPICS PVs used for shared memory X-ray Diffraction detector
    used in jet tracking.
    """
    total_counter = Cpt(EpicsSignal, ':TOTAL_Counter',
                        doc='Total counter')
    total_reprate = Cpt(EpicsSignal, ':TOTAL_RepRate',
                        doc='Diffraction total intensity calc rate')
    ring_counter = Cpt(EpicsSignal, ':RING_Counter',
                       doc='Diffraction ring intensity event counter')
    ring_reprate = Cpt(EpicsSignal, ':RING_RepRate',
                       doc='Diffraction ring intensity event counter')
    psd_counter = Cpt(EpicsSignal, ':PSD_Counter',
                      doc='Diffraction periodogram event counter')
    psd_reprate = Cpt(EpicsSignal, ':PSD_RepRate',
                      doc='Diffraction periodogram event counter')
    stats_counter = Cpt(EpicsSignal, ':STATS_Counter',
                        doc='Diffraction stats event counter')
    stats_reprate = Cpt(EpicsSignal, ':STATS_RepRate',
                        doc='Diffraction stats event counter')
    streak_counter = Cpt(EpicsSignal, ':STREAK_Counter',
                         doc='Diffraction streak event counter')
    streak_reprate = Cpt(EpicsSignal, ':STREAK_RepRate',
                         doc='Diffraction streak event counter')
    cspad_sum = Cpt(EpicsSignal, ':TOTAL_ADU',
                    doc='Total detector ADU')
    streak_fraction = Cpt(EpicsSignal, ':STREAK_FRACTION',
                          doc='Fraction of events with diffraction streak')
    stats_mean = Cpt(EpicsSignal, ':STATS_MEAN',
                     doc='Mean Diffraction Statistic')
    stats_std = Cpt(EpicsSignal, ':STATS_STD',
                    doc='Std Diffraction Statistic')
    stats_min = Cpt(EpicsSignal, ':STATS_MIN',
                    doc='Min Diffraction Statistic')
    stats_max = Cpt(EpicsSignal, ':STATS_MAX',
                    doc='Max Diffraction Statistic')
    psd_frequency = Cpt(EpicsSignal, ':PSD_FREQUENCY',
                        doc='Diffraction periodogram fundamental frequency')
    psd_amplitude = Cpt(EpicsSignal, ':PSD_AMPLITUDE',
                        doc='Diffraction periodogram Frequency analysis'
                            'amplitude')
    psd_rate = Cpt(EpicsSignal, ':PSD_RATE',
                   doc='Event frequency for periodogram')
    psd_events = Cpt(EpicsSignal, ':PSD_EVENTS',
                     doc='Diffraction periodogram')
    psd_resolution = Cpt(EpicsSignal, ':PSD_RESOLUTION',
                         doc='Resultion to smooth over for periodogra')
    psd_freq_min = Cpt(EpicsSignal, ':PSD_FREQ_MIN',
                       doc='Minimum frequency for periodogram calcs')
    psd_amp_wf = Cpt(EpicsSignal, ':PSD_AMP_WF',
                     doc='Diffraction periodogram Frequency analysis waveform'
                         'array')
    psd_freq_wf = Cpt(EpicsSignal, ':PSD_FREQ_WF',
                      doc='Diffraction periodogram frequency waveform')
    psd_amp_array = Cpt(EpicsSignal, ':PSD_AMP_ARRAY',
                        doc='Diffraction periodogram Frequency analysis'
                            'amplitude array')
    state = Cpt(EpicsSignal, ':STATE',
                doc='State of diffraction analysis')


# classes used for jet tracking testing
class JTInput(Device):
    nframe = Cpt(EpicsSignal, ':NFRAME', doc='number of frames passed')
    i0 = Cpt(EpicsSignal, ':i0', doc='Wave8')
    evtcode = Cpt(EpicsSignal, ':EVTCODE', doc='event code')
    mtr = Cpt(EpicsSignal, ':MTR', doc='motor position')
    mtr_prec = Cpt(EpicsSignal, ':MTR_PREC', doc='motor precision')


class JTOutput(Device):
    nframe = Cpt(EpicsSignal, ':NFRAME', doc='number of frames used')
    det = Cpt(EpicsSignal, ':DET', doc='detector intensity')
    i0 = Cpt(EpicsSignal, ':I0', doc='Wave8')
    mtr = Cpt(EpicsSignal, ':MTR', doc='motor position')


class JTFake(Device):
    stopper = Cpt(EpicsSignal, ':STOPPER', doc='fake stopper')
    pulse_picker = Cpt(EpicsSignal, ':PP', doc='fake pulse picker')
