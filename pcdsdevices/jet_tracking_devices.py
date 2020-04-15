import epics
import pandas as pd
from ophyd.areadetector.plugins import ImagePlugin, ROIPlugin, StatsPlugin
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignal
from pcdsdevices.areadetector.detectors import PCDSAreaDetector
from pcdsdevices.epics_motor import IMS


class _TableMixin:
    _table_attrs = ('value', 'units', 'desc')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._descriptions = None

    def _update_descriptions(self):
        adesc = {}
        for name, signal in self._signals.items():
            pvname = getattr(signal, 'pvname', None)
            adesc[name] = (epics.caget(pvname + '.DESC')
                           if pvname else '')
        self._descriptions = adesc

    @property
    def table(self):
        """
        Return table of Device settings
        """
        if self._descriptions is None:
            self._update_descriptions()

        atable = {}
        for name, signal in sorted(self._signals.items()):
            try:
                value = signal.read()[signal.name]['value']
            except Exception:
                value = None

            try:
                units = signal.describe()[signal.name].get('units', '')
            except Exception:
                units = None

            atable[name] = {
                'value': value,
                'units': units,
                'desc': self._descriptions.get(name),
            }

        return pd.DataFrame(atable).T.loc[:, self._table_attrs]


class Injector(Device, _TableMixin):
    '''An Injector which consists of 3 coarse control motors and 3 fine control motors

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the name of the device and
           the PVs of all the injector components

       Attributes
       ----------
       coarseX : EpicsSignal
           The coarse control motor in the X direction
       coarseY : EpicsSignal
           The coarse control motor in the Y direction
       coarseZ : EpicsSignal
           The coarse control motor in the Z direction
       fineX : EpicsSignal
           The fine control motor in the X direction
       fineY : EpicsSignal
           The fine control motor in the Y direction
       fineZ : EpicsSignal
           The fine control motor in the Z direction
    '''
    coarseX = FCpt(IMS, '{self._coarseX}')
    coarseY = FCpt(IMS, '{self._coarseY}')
    coarseZ = FCpt(IMS, '{self._coarseZ}')

    fineX = FCpt(IMS, '{self._fineX}')
    fineY = FCpt(IMS, '{self._fineY}')
    fineZ = FCpt(IMS, '{self._fineZ}')

    def __init__(self, name,
                 coarseX, coarseY, coarseZ,
                 fineX, fineY, fineZ, **kwargs):

        self._coarseX = coarseX
        self._coarseY = coarseY
        self._coarseZ = coarseZ

        self._fineX = fineX
        self._fineY = fineY
        self._fineZ = fineZ

        super().__init__(name=name, **kwargs)


class Selector(Device, _TableMixin):
    '''A Selector for the sample delivery system

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the name of the device and
           the PVs of all the selector components

       Attributes
       ----------
       remote_control : EpicsSignal
           Remote control enabled
       status : EpicsSignal
           Connection status for selector
       flow : EpicsSignal
           Flow
       flowstate : EpicsSignal
           State of the flow
       flowtype : EpicsSignal
           Type of the flow
       FM_rb : EpicsSignal

       FM_reset : EpicsSignal

       FM : EpicsSignal

       names_button : EpicsSignal

       couple_button : EpicsSignal

       names1 : EpicsSignal

       names2 : EpicsSignal

       shaker1 : EpicsSignal
           Shaker 1
       shaker2 : EpicsSignal
           Shaker 2
       shaker3 : EpicsSignal
           Shaker 3
       shaker4 : EpicsSignal
           Shaker 4
       '''

    # also appears on pressure controller screen?
    remote_control = FCpt(EpicsSignal, '{self._remote_control}')
    status = FCpt(EpicsSignal, '{self._status}')

    flow = FCpt(EpicsSignal, '{self._flow}')
    flowstate = FCpt(EpicsSignal, '{self._flowstate}')
    flowtype = FCpt(EpicsSignal, '{self._flowtype}')

    FM_rb = FCpt(EpicsSignal, '{self._FM_rb}')
    FM_reset = FCpt(EpicsSignal, '{self._FM_reset}')
    FM = FCpt(EpicsSignal, '{self._FM}')

    names_button = FCpt(EpicsSignal, '{self._names_button}')
    couple_button = FCpt(EpicsSignal, '{self._couple_button}')
    names1 = FCpt(EpicsSignal, '{self._names1}')
    names2 = FCpt(EpicsSignal, '{self._names2}')

    shaker1 = FCpt(EpicsSignal, '{self._shaker1}')
    shaker2 = FCpt(EpicsSignal, '{self._shaker2}')
    shaker3 = FCpt(EpicsSignal, '{self._shaker3}')
    shaker4 = FCpt(EpicsSignal, '{self._shaker4}')

    def __init__(self, name,
                 remote_control, status,
                 flow, flowstate, flowtype,
                 FM_rb, FM_reset, FM,
                 names_button, couple_button, names1, names2,
                 shaker1, shaker2, shaker3, shaker4, **kwargs):

        self._status = status
        self._remote_control = remote_control

        self._flow = flow
        self._flowstate = flowstate
        self._flowtype = flowtype

        self._FM_rb = FM_rb
        self._FM_reset = FM_reset
        self._FM = FM

        self._names_button = names_button
        self._couple_button = couple_button
        self._names1 = names1
        self._names2 = names2

        self._shaker1 = shaker1
        self._shaker2 = shaker2
        self._shaker3 = shaker3
        self._shaker4 = shaker4

        super().__init__(name=name, **kwargs)


class CoolerShaker(Device, _TableMixin):
    '''A Cooler/Shaker for the sample delivery system

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the PVs of all the cooler/shaker components
       name : str
           The device name

       Attributes
       ----------
       temperature1 : EpicsSignal
           Temperature of 1
       SP1 : EpicsSignal
           Set point of 1
       set_SP1 : EpicsSignal
           Set the set point for 1
       current1 : EpicsSignal
           Current for 1
       temperature2 : EpicsSignal
           Temperature of 2
       SP2 : EpicsSignal
           Set point of 2
       set_SP2 : EpicsSignal
           Set the set point of 2
       current2 : EpicsSignal
           Current of 2
       reboot : EpicsSignal
           Reboot the cooler/shaker
       '''

    temperature1 = FCpt(EpicsSignal, '{self._temperature1}')
    SP1 = FCpt(EpicsSignal, '{self._SP1}')
    set_SP1 = FCpt(EpicsSignal, '{self._set_SP1}')
    current1 = FCpt(EpicsSignal, '{self._current1}')

    temperature2 = FCpt(EpicsSignal, '{self._temperature2}')
    SP2 = FCpt(EpicsSignal, '{self._SP2}')
    set_SP2 = FCpt(EpicsSignal, '{self._set_SP2}')
    current2 = FCpt(EpicsSignal, '{self._current2}')

    reboot = FCpt(EpicsSignal, '{self._reboot}')

    def __init__(self, name,
                 temperature1, SP1, set_SP1, current1,
                 temperature2, SP2, set_SP2, current2,
                 reboot, **kwargs):

        self._temperature1 = temperature1
        self._SP1 = SP1
        self._set_SP1 = set_SP1
        self._current1 = current1

        self._temperature2 = temperature2
        self._SP2 = SP2
        self._set_SP2 = set_SP2
        self._current2 = current2

        self._reboot = reboot

        super().__init__(name=name, **kwargs)


class HPLC(Device, _TableMixin):
    '''An HPLC for the sample delivery system

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the PVs of all the HPLC components
       name : str
           The device name

       Attributes
       ----------
       status : EpicsSignal
           Status of the HPLC
       run : EpicsSignal
           Run the HPLC
       flowrate : EpicsSignal
           Flow rate of the HPLC
       set_flowrate : EpicsSignal
           Set the flow rate of the HPLC
       flowrate_SP : EpicsSignal
           Set point for the flow rate
       pressure : EpicsSignal
           Pressure in the HPLC
       pressure_units : EpicsSignal
           Units for the pressure
       set_max_pressure : EpicsSignal
           Set the maximum pressure
       max_pressure : EpicsSignal
           Maximum pressure
       clear_error : EpicsSignal
           Clear errors
       '''

    status = FCpt(EpicsSignal, '{self._status}')
    run = FCpt(EpicsSignal, '{self._run}')

    flowrate = FCpt(EpicsSignal, '{self._flowrate}')
    set_flowrate = FCpt(EpicsSignal, '{self._set_flowrate}')
    flowrate_SP = FCpt(EpicsSignal, '{self._flowrate_SP}')

    pressure = FCpt(EpicsSignal, '{self._pressure}')
    pressure_units = FCpt(EpicsSignal, '{self._pressure_units}')
    set_max_pressure = FCpt(EpicsSignal, '{self._set_max_pressure}')
    max_pressure = FCpt(EpicsSignal, '{self._max_pressure}')

    clear_error = FCpt(EpicsSignal, '{self._clear_error}')

    def __init__(self, name,
                 status, run,
                 flowrate, set_flowrate, flowrate_SP,
                 pressure, pressure_units, set_max_pressure, max_pressure,
                 clear_error, **kwargs):

        self._status = status
        self._run = run

        self._flowrate = flowrate
        self._set_flowrate = set_flowrate
        self._flowrate_SP = flowrate_SP

        self._pressure = pressure
        self._pressure_units = pressure_units
        self._set_max_pressure = set_max_pressure
        self._max_pressure = max_pressure

        self._clear_error = clear_error

        super().__init__(name=name, **kwargs)


class PressureController(Device, _TableMixin):
    '''An Pressure Controller for the sample delivery system

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the PVs of all the pressure controller components
       name : str
           The device name

       Attributes
       ----------
       status : EpicsSignal
           Connection status of pressure controller
       pressure1 : EpicsSignal
           Pressure of 1
       enabled1 : EpicsSignal
           Is 1 enabled
       limit1 : EpicsSignal
           High pressure limit of 1
       SP1 : EpicsSignal
           Pressure set point of 1
       pressure2 : EpicsSignal
           Pressure of 2
       enabled2 : EpicsSignal
           Is 2 enabled
       limit2 : EpicsSignal
           High pressure limit of 2
       SP2 : EpicsSignal
           Pressure set point of 2
       '''

    status = FCpt(EpicsSignal, '{self._status}')

    pressure1 = FCpt(EpicsSignal, '{self._pressure1}')
    enabled1 = FCpt(EpicsSignal, '{self._enabled1}')
    limit1 = FCpt(EpicsSignal, '{self._limit1}')
    SP1 = FCpt(EpicsSignal, '{self._SP1}')

    pressure2 = FCpt(EpicsSignal, '{self._pressure2}')
    enabled2 = FCpt(EpicsSignal, '{self._enabled2}')
    limit2 = FCpt(EpicsSignal, '{self._limit2}')
    SP2 = FCpt(EpicsSignal, '{self._SP2}')

    def __init__(self, name,
                 status,
                 pressure1, enabled1, limit1, SP1,
                 pressure2, enabled2, limit2, SP2, **kwargs):

        self._status = status

        self._pressure1 = pressure1
        self._enabled1 = enabled1
        self._limit1 = limit1
        self._SP1 = SP1

        self._pressure2 = pressure2
        self._enabled2 = enabled2
        self._limit2 = limit2
        self._SP2 = SP2

        super().__init__(name=name, **kwargs)


class FlowIntegrator(Device, _TableMixin):
    '''An FlowIntegrator for the sample delivery system

       Parameters
       ----------
       pvs : str dict
           A dictionary containing the PVs of all the flow integrator components
       name : str
           The device name

       Attributes
       ----------
       integrator_source: EpicsSignal

       flow_source : EpicsSignal

       names : EpicsSignal
           Names of
       start1 : EpicsSignal
           Starting volume of 1
       used1 : EpicsSignal
           Flow of 1
       time1 : EpicsSignal
           Estimated depletion time of 1
       start2 : EpicsSignal
           Starting volume of 2
       used2 : EpicsSignal
           Flow of 2
       time2 : EpicsSignal
           Estimated depletion time of 2
       start3 : EpicsSignal
           Starting volume of 3
       used3 : EpicsSignal
           Flow of 3
       time3 : EpicsSignal
           Estimated depletion time of 3
       start4 : EpicsSignal
           Starting volume of 4
       used4 : EpicsSignal
           Flow of 4
       time4 : EpicsSignal
           Estimated depletion time of 4
       start5 : EpicsSignal
           Starting volume of 5
       used5 : EpicsSignal
           Flow of 5
       time5 : EpicsSignal
           Estimated depletion time of 5
       start6 : EpicsSignal
           Starting volume of 6
       used6 : EpicsSignal
           Flow of 6
       time6 : EpicsSignal
           Estimated depletion time of 6
       start7 : EpicsSignal
           Starting volume of 7
       used7 : EpicsSignal
           Flow of 7
       time7 : EpicsSignal
           Estimated depletion time of 7
       start8 : EpicsSignal
           Starting volume of 8
       used8 : EpicsSignal
           Flow of 8
       time8 : EpicsSignal
           Estimated depletion time of 8
       start9 : EpicsSignal
           Starting volume of 9
       used9 : EpicsSignal
           Flow of 9
       time9 : EpicsSignal
           Estimated depletion time of 9
       start10 : EpicsSignal
           Starting volume of 10
       used10 : EpicsSignal
           Flow of 10
       time10 : EpicsSignal
           Estimated depletion time of 10
       '''

    integrator_source = FCpt(EpicsSignal, '{self._integrator_source}')
    flow_source = FCpt(EpicsSignal, '{self._flow_source}')
    names = FCpt(EpicsSignal, '{self._names}')

    start1 = FCpt(EpicsSignal, '{self._start1}')
    used1 = FCpt(EpicsSignal, '{self._used1}')
    time1 = FCpt(EpicsSignal, '{self._time1}')

    start2 = FCpt(EpicsSignal, '{self._start2}')
    used2 = FCpt(EpicsSignal, '{self._used2}')
    time2 = FCpt(EpicsSignal, '{self._time2}')

    start3 = FCpt(EpicsSignal, '{self._start3}')
    used3 = FCpt(EpicsSignal, '{self._used3}')
    time3 = FCpt(EpicsSignal, '{self._time3}')

    start4 = FCpt(EpicsSignal, '{self._start4}')
    used4 = FCpt(EpicsSignal, '{self._used4}')
    time4 = FCpt(EpicsSignal, '{self._time4}')

    start5 = FCpt(EpicsSignal, '{self._start5}')
    used5 = FCpt(EpicsSignal, '{self._used5}')
    time5 = FCpt(EpicsSignal, '{self._time5}')

    start6 = FCpt(EpicsSignal, '{self._start6}')
    used6 = FCpt(EpicsSignal, '{self._used6}')
    time6 = FCpt(EpicsSignal, '{self._time6}')

    start7 = FCpt(EpicsSignal, '{self._start7}')
    used7 = FCpt(EpicsSignal, '{self._used7}')
    time7 = FCpt(EpicsSignal, '{self._time7}')

    start8 = FCpt(EpicsSignal, '{self._start8}')
    used8 = FCpt(EpicsSignal, '{self._used8}')
    time8 = FCpt(EpicsSignal, '{self._time8}')

    start9 = FCpt(EpicsSignal, '{self._start9}')
    used9 = FCpt(EpicsSignal, '{self._used9}')
    time9 = FCpt(EpicsSignal, '{self._time9}')

    start10 = FCpt(EpicsSignal, '{self._start10}')
    used10 = FCpt(EpicsSignal, '{self._used10}')
    time10 = FCpt(EpicsSignal, '{self._time10}')

    def __init__(self, name,
                 integrator_source, flow_source, names,
                 start1, used1, time1,
                 start2, used2, time2,
                 start3, used3, time3,
                 start4, used4, time4,
                 start5, used5, time5,
                 start6, used6, time6,
                 start7, used7, time7,
                 start8, used8, time8,
                 start9, used9, time9,
                 start10, used10, time10, **kwargs):

        self._integrator_source = integrator_source
        self._flow_source = flow_source
        self._names = names

        self._start1 = start1
        self._used1 = used1
        self._time1 = time1

        self._start2 = start2
        self._used2 = used2
        self._time2 = time2

        self._start3 = start3
        self._used3 = used3
        self._time3 = time3

        self._start4 = start4
        self._used4 = used4
        self._time4 = time4

        self._start5 = start5
        self._used5 = used5
        self._time5 = time5

        self._start6 = start6
        self._used6 = used6
        self._time6 = time6

        self._start7 = start7
        self._used7 = used7
        self._time7 = time7

        self._start8 = start8
        self._used8 = used8
        self._time8 = time8

        self._start9 = start9
        self._used9 = used9
        self._time9 = time9

        self._start10 = start10
        self._used10 = used10
        self._time10 = time10

        super().__init__(name=name, **kwargs)


class SDS:
    '''
    Sample delivery system

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
        List containing all the devices that are in the sample delivery system
   '''

    device_types = {
        'selector': Selector,
        'cooler_shaker': CoolerShaker,
        'hplc': HPLC,
        'pressure_controller': PressureController,
        'flow_integrator': FlowIntegrator,
    }

    def __init__(self, devices):
        self.SDS_devices = [
            self.device_types[dev](**kwargs)
            for dev, kwargs in devices.items()
            if dev in self.device_types
        ]

        invalid_devices = [dev for dev in devices
                           if dev not in self.device_types]
        for device in invalid_devices:
            print(f'WARNING: {device} is not a valid device type')


class Offaxis(PCDSAreaDetector):
    '''Area detector for Offaxis camera in CXI

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins
    prefix : str
        Prefix for the PV name of the camera
    name : str
        Name of the camera

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image
    ROI_stats : StatsPlugin
        Stats on ROI of original rate image
    '''

    ROI = FCpt(ROIPlugin, '{self.prefix}:{self._ROI_port}:')
    ROI_stats = FCpt(StatsPlugin, '{self.prefix}:{self._ROI_stats_port}:')
    ROI_image = FCpt(ImagePlugin, '{self.prefix}:{self._ROI_image_port}:')

    def __init__(self, ROI_port,
                 ROI_stats_port,
                 ROI_image_port,
                 prefix, *args, **kwargs):
        self._ROI_port = ROI_port
        self._ROI_stats_port = ROI_stats_port
        self._ROI_image_port = ROI_image_port

        super().__init__(prefix, *args, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Questar(PCDSAreaDetector):
    '''
    Area detector for Inline Questar Camera in CXI

    Parameters
    ----------
    port_names : str dict
        A dictionary containing the access port names for the plugins
    prefix : str
        Prefix for the PV name of the camera
    name : str
        Name of the camera

    Attributes
    ----------
    ROI : ROIPlugin
        ROI on original rate image
    ROI_stats : StatsPlugin
        Stats on ROI of original rate image
    '''

    ROI = FCpt(ROIPlugin, '{self.prefix}:{self._ROI_port}:')
    ROI_stats = FCpt(StatsPlugin, '{self.prefix}:{self._ROI_stats_port}:')
    ROI_image = FCpt(ImagePlugin, '{self.prefix}:{self._ROI_image_port}:')

    def __init__(self, ROI_port,
                 ROI_stats_port,
                 ROI_image_port,
                 prefix, *args, **kwargs):
        self._ROI_port = ROI_port
        self._ROI_stats_port = ROI_stats_port
        self._ROI_image_port = ROI_image_port

        super().__init__(prefix, *args, **kwargs)

        self.ROI_stats.nd_array_port.put(ROI_port)
        self.ROI_image.nd_array_port.put(ROI_port)
        self.ROI.enable.put('Enabled')
        self.ROI_stats.enable.put('Enabled')
        self.ROI_image.enable.put('Enabled')


class Parameters(Device, _TableMixin):
    '''
    Contains EPICS PVs used for jet tracking
    '''
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


class OffaxisParams(Device, _TableMixin):
    '''
    Contains EPICS PVs used with Offaxis camera for jet tracking
    '''
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


class Control(Device, _TableMixin):
    '''
    Contains EPICS PVs used for jet tracking control
    '''

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


class Diffract(Device, _TableMixin):
    '''
    Contains EPICS PVs used for shared memory X-ray Diffraction detector
    used in jet tracking.
    '''
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
                        doc='Diffraction periodogram Frequency analysis amplitude')
    psd_rate = Cpt(EpicsSignal, ':PSD_RATE',
                   doc='Event frequency for periodogram')
    psd_events = Cpt(EpicsSignal, ':PSD_EVENTS',
                     doc='Diffraction periodogram')
    psd_resolution = Cpt(EpicsSignal, ':PSD_RESOLUTION',
                         doc='Resultion to smooth over for periodogra')
    psd_freq_min = Cpt(EpicsSignal, ':PSD_FREQ_MIN',
                       doc='Minimum frequency for periodogram calcs')
    psd_amp_wf = Cpt(EpicsSignal, ':PSD_AMP_WF',
                     doc='Diffraction periodogram Frequency analysis waveform array')
    psd_freq_wf = Cpt(EpicsSignal, ':PSD_FREQ_WF',
                      doc='Diffraction periodogram frequency waveform')
    psd_amp_array = Cpt(EpicsSignal, ':PSD_AMP_ARRAY',
                        doc='Diffraction periodogram Frequency analysis amplitude array')
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
