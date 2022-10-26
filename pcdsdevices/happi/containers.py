"""
Define subclasses of Device for specific hardware.
"""
import re
import warnings
from copy import copy, deepcopy

import lightpath.happi.containers as lp_containers
from happi.item import EntryInfo, HappiItem, OphydItem


class LCLSItem(OphydItem):
    name = EntryInfo(('Shorthand Python-valid name for the Python instance. '
                      'Must be between 3 and 80 characters.'),
                     optional=False,
                     enforce=re.compile(r'[a-z][a-z\_0-9]{2,78}$'))
    beamline = EntryInfo('Section of beamline the device belongs',
                         optional=False, enforce=str)
    location_group = EntryInfo('LUCID grouping parameter for location',
                               optional=False, enforce=str)
    functional_group = EntryInfo('LUCID grouping parameter for function',
                                 optional=False, enforce=str)
    z = EntryInfo('Beamline position of the device',
                  enforce=float, default=-1.0)
    stand = EntryInfo('Acronym for stand, must be three alphanumeric '
                      'characters like an LCLSI stand (e.g. DG3) or follow '
                      'the LCLSII stand naming convention (e.g. L0S04).',
                      enforce=re.compile(r'[A-Z0-9]{3}$|[A-Z][0-9]S[0-9]{2}$'))
    lightpath = EntryInfo("If the device should be included in the "
                          "LCLS Lightpath", enforce=bool, default=False)
    input_branches = EntryInfo(('List of branches the device can receive '
                                'beam from.'),
                               optional=True, enforce=list)
    output_branches = EntryInfo(('List of branches the device can deliver '
                                'beam to.'),
                                optional=True, enforce=list)
    ioc_engineer = EntryInfo(('Engineer for the IOC. Used to build IOC '
                             'configs.'),
                             optional=True, enforce=str)
    ioc_location = EntryInfo('Location of the IOC. Used to build IOC configs.',
                             optional=True, enforce=str)
    ioc_hutch = EntryInfo(('Hutch the IOC will be used in. Used to build IOC '
                           'configs.'), optional=True, enforce=str)
    ioc_release = EntryInfo(('Full path to IOC release directory. Used to '
                            'build IOC configs.'),
                            optional=True, enforce=str)
    ioc_arch = EntryInfo(('The IOC host architecture. Used to build IOC '
                         'configs.'), optional=True, enforce=str)
    ioc_name = EntryInfo('The name of the device IOC. Used to build the IOC.',
                         optional=True, enforce=str)
    ioc_type = EntryInfo(('The type of device IOC. Useful when multiple '
                          'device classes can occupy the same controller. Can '
                          'be used to tell higher level code how to interpret '
                          'the ioc data.'), optional=True, enforce=str)


class LCLSLightpathItem(lp_containers.LightpathItem, LCLSItem):
    """
    LCLS version of a LightpathItem.  Since some containers serve both
    lightpath and non-lightpath devices, make branches and kwargs optional

    The default for branches will be None, and omitted from the kwargs
    dictionary if its option matches said default of None.
    """
    input_branches = copy(lp_containers.LightpathItem.input_branches)
    input_branches.optional = True
    input_branches.include_default_as_kwarg = False
    output_branches = copy(lp_containers.LightpathItem.output_branches)
    output_branches.optional = True
    output_branches.include_default_as_kwarg = False


class LegacyItem(HappiItem):
    """
    Formally, happi.device.Device

    Extracted from happi so that happi can drop support for LCLS-specific
    deprecated containers.

    This should be removed when we clean up our database
    """
    prefix = EntryInfo('A base PV for all related records',
                       optional=False, enforce=str)
    beamline = EntryInfo('Section of beamline the device belongs',
                         optional=False, enforce=str)
    location_group = EntryInfo('Grouping parameter for device location',
                               optional=False, enforce=str)
    functional_group = EntryInfo('Grouping parameter for device function',
                                 optional=False, enforce=str)
    z = EntryInfo('Beamline position of the device',
                  enforce=float, default=-1.0)
    stand = EntryInfo('Acronym for stand, must be three alphanumeric '
                      'characters like an LCLSI stand (e.g. DG3) or follow '
                      'the LCLSII stand naming convention (e.g. L0S04).',
                      enforce=re.compile(r'[A-Z0-9]{3}$|[A-Z][0-9]S[0-9]{2}$'))
    detailed_screen = EntryInfo('The absolute path to the main control screen',
                                enforce=str)
    embedded_screen = EntryInfo('The absolute path to the '
                                'embedded control screen',
                                enforce=str)
    engineering_screen = EntryInfo('The absolute path to '
                                   'the engineering control screen',
                                   enforce=str)
    system = EntryInfo('The system the device is involved with, i.e '
                       'Vacuum, Timing e.t.c',
                       enforce=str)
    macros = EntryInfo("The EDM macro string asscociated with the "
                       "with the device. By using a jinja2 template, "
                       "this can reference other EntryInfo keywords.",
                       enforce=str)
    lightpath = EntryInfo("If the device should be included in the "
                          "LCLS Lightpath", enforce=bool, default=False)
    documentation = EntryInfo("Relevant documentation for the Device",
                              enforce=str)
    parent = EntryInfo('If the device is a component of another, '
                       'enter the name', enforce=str)
    args = copy(HappiItem.args)
    args.default = ['{{prefix}}']
    kwargs = copy(HappiItem.kwargs)
    kwargs.default = {'name': '{{name}}'}

    def __repr__(self):
        return '{} (name={}, prefix={}, z={})'.format(
                                    self.__class__.__name__,
                                    self.name,
                                    self.prefix,
                                    self.z)

    @property
    def screen(self):
        warnings.warn("The 'screen' keyword is no longer used in Happi as it "
                      "lacks specificity. Use one of detailed_screen, "
                      "embedded_screen, or engineering screen instead",
                      DeprecationWarning)
        return self.detailed_screen


class Vacuum(LCLSItem, LegacyItem):
    """
    Parent class for devices in the vacuum system.
    """
    system = copy(LegacyItem.system)
    system.default = 'vacuum'


class Diagnostic(LCLSItem, LegacyItem):
    """
    Parent class for devices that are used as diagnostics.
    """
    system = copy(LegacyItem.system)
    system.default = 'diagnostic'
    data = EntryInfo('PV that gives us the diagnostic readback in EPICS.',
                     enforce=str)


class BeamControl(LCLSItem, LegacyItem):
    """
    Parent class for devices that control any beam parameter.
    """
    system = copy(LegacyItem.system)
    system.default = 'beam control'


# Basic classes that inherit from above
class GateValve(Vacuum):
    """
    Standard isolation valves. Generally, these close when there is a
    problem and beam is not allowed. Devices made with this class will be set
    as part of the vacuum system.

    Attributes
    ----------
    prefix : str
        The prefix pv should be the record one level below the state and
        control PVs. For example, if the open command pv is
        "HXX:MXT:VGC:01:OPN_SW", the base pv is "HXX:MXT:VGC:01". A regex will
        be used to check that "VGC" is found in the base PV.

    veto : bool
        Set this to `True` if the gate valve is a veto device.
    """
    prefix = copy(Vacuum.prefix)
    prefix.enforce = re.compile(r'.*VGC.*')
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.GateValve'


class Slits(BeamControl):
    """
    Mechanical devices to control beam profile. This class refers specifically
    to slits that use the JAWS record. These devices will be assigned the beam
    control system by default.

    Attributes
    ----------
    prefix : str
        The prefix PV should be the JAWS record one level below the center and
        width PVs. Note that this is NOT the motor record. For example, if the
        x center PV is "XCS:SB2:DS:JAWS:ACTUAL_XCENTER", then the base PV
        should be "XCS:SB2:DS:JAWS". A regex will be used to check that "JAWS"
        is found in the base PV.
    """
    prefix = copy(BeamControl.prefix)
    prefix.enforce = re.compile(r'.*JAWS.*')
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.Slits'


class PIM(Diagnostic):
    """
    Beam profile monitors. All of these are cameras pointing at YAG screens.
    These devices have a data attribute in addition to the standard entries to
    link up the device with its camera output. These devices will be assigned
    the diagnostic system by default.

    Attributes
    ----------
    prefix : str
        The base PV should be the motor states PV that shows whether the
        monitor is out, in at yag, or in at diode. Note that this is NOT the
        motor record. For example, if the command PV to pull the PIM out is
        "XPP:SB3:PIM:OUT:GO", then the base PV is "XPP:SB3:PIM". A regex will
        be used to check that "PIM" is found in the base PV.

    data : str
        The data PV should be the AreaDetector base. For example, if the image
        data is broadcast on "XCS:SB1:P6740:IMAGE1:ArrayData", the data base
        should be "XCS:SB1:P6740".
    """
    prefix = copy(Diagnostic.prefix)
    prefix.enforce = re.compile(r'.*PIM.*')
    prefix_det = EntryInfo("Prefix for associated camera", enforce=str)
    device_class = copy(Diagnostic.device_class)
    device_class.default = 'pcdsdevices.device_types.PIM'
    kwargs = deepcopy(Diagnostic.kwargs)
    kwargs.default['prefix_det'] = "{{prefix_det}}"


class IPM(Diagnostic):
    """
    Beam intensity monitors. These are often used as a sanity check for beam
    presence, though they can also be used to track shot to shot intensity and
    estimate beam position. These devices have a data attribute in addition to
    the standard entries to link the device with its scalar output. These
    devices will be assigned the diagnostic system by default.

    Attributes
    ----------
    prefix : str
        The base PV should be the prefix one level up from the diode and target
        state PVs. Note that this is NOT the motor record, it is neither the
        diode nor the target state PV, and it may not even be a valid PV name.
        For example, if the command PV to set the target position to a state is
        "XPP:SB3:IPM:TARGET:GO" and the command PV to move the diode to a state
        is "XPP:SB3:IPM:DIODE:GO", then the base PV is the shared prefix
        "XPP:SB3:IPM". A regex will be used to check that "IPM" is found in the
        base PV.

    data : str
        The data PV should be the IPM PV that most reliably predicts beam
        prescence. This will, in general, be the sum of the channels.

    z : float
        If the diode and target have subtly different recorded z-positions, use
        the diode position for the purposes of this database.
    """
    prefix = copy(Diagnostic.prefix)
    prefix.enforce = re.compile(r'.*IPM.*')
    device_class = copy(Diagnostic.device_class)
    device_class.default = 'pcdsdevices.device_types.IPM'


class Attenuator(BeamControl):
    """
    Beam attenuators, used to get a lower intensity beam downstream to protect
    the sample or to protect hardware components. These devices will be
    assigned the beam control system by default.

    Attributes
    ----------
    prefix : str
        For attunators, the base PV should be the base record from the
        attentuation calculation and control IOC, one level up from the
        calculated tranmission ratio. For example, if the transmission PV is
        "XPP:ATT:COM:R_CUR", the base PV is "XPP:ATT". A regex will be used
        to check that "ATT" is found in the base PV

    n_filters : int
        Number of Attenuator blades
    """
    prefix = copy(BeamControl.prefix)
    prefix.enforce = re.compile(r'.*ATT.*')
    device_class = copy(BeamControl.device_class)
    device_class.default = 'pcdsdevices.device_types.Attenuator'
    n_filters = EntryInfo("Number of filters on the Attenuator",
                          enforce=int, optional=False)
    kwargs = deepcopy(BeamControl.kwargs)
    kwargs.default['n_filters'] = "{{n_filters}}"


class Stopper(LCLSItem, LegacyItem):
    """
    Large devices that prevent beam when it could cause damage to hardware.

    Attributes
    ----------
    prefix : str
        The base PV should be the combined mps status PV e.g.
        "STPR:XRT1:1:S5IN_MPS".
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.Stopper'


class OffsetMirror(BeamControl):
    """
    A device that steers beam in the x direction by changing a pitch motor.
    These are used for beam delivery and alignment. These have additional
    entires for destinations and in/out state. Mirrors will have their system
    set to beam control by default.

    Attributes
    ----------
    prefix : str
        The base PV should be a states PV that tells us which destination the
        mirror is pointing to. These states will be fairly rough and should not
        be relied on for alignment purposes, except for a guarantee that if a
        state is not active, then the beam is definitely not pointing to that
        state.
        If the mirror is purely for alignment and not for steering, or it
        doesn't make sense for the pitch to have states, this can be the pitch
        control motor record base instead.

    prefix_xy : str, optional
        Name of the X and Y motors if different than the standard prefix

    xgantry_prefix : str, optional
        Prefix of the X Gantry PVs if different than the standard prefix
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.OffsetMirror'
    prefix_xy = EntryInfo("Prefix for X and Y motors", enforce=str)
    xgantry_prefix = EntryInfo("Prefix for the X Gantry", enforce=str)

    # Lightpath relevant settings.  Ranges for various mirror settings
    pitch_ranges = EntryInfo("valid pitch ranges for each destination",
                             optional=True, enforce=list,
                             include_default_as_kwarg=False)
    x_ranges = EntryInfo("valid x positions, determining insertion",
                         optional=True, enforce=list,
                         include_default_as_kwarg=False)
    y_ranges = EntryInfo("valid y positions, determining coating",
                         optional=True, enforce=list,
                         include_default_as_kwarg=False)


class PulsePicker(BeamControl):
    """
    A device that syncs with the timing system to control when beam arrives in
    the hutch. These have an additional states entry to define their in/out
    states pv. Pulse pickers will be assigned the beam control system by
    default.

    Attributes
    ----------
    prefix : str
        The base PV should be the motor record base that the pulsepicker IOC
        is built on top of e.g. "XCS:SB2:MMS:09".

    states : str
        The additional state should be the states PV associated with the
        pulsepicker in/out. An example of one such PV is "XCS:SB2:PP:Y".
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.PulsePicker'


class LODCM(BeamControl):
    """
    This LODCM class doesn't refer to the full LODCM, but rather one of the two
    crystals. This makes 4 LODCM objects in total, 2 for each LODCM. These have
    an additional states entry to define a list of all the miscellaneous states
    pvs associated with the LODCMs. LODCMs will be assigned the beam control
    system by default.

    We're simplifying here, assuming the LODCM is aligned and that the states
    are accurate. We'll probably only look at the H1N state for lightpath
    purposes, but it's good to collect all the available information.

    Attributes
    ----------
    prefix : str
        The base PV should be the state PV associated with the h1n or h2n
        state, depending on which crystal we're referring to e.g.
        "XPP:LODCM:H1N".

    mono_line : str
        Name of the mono line
    """
    device_class = copy(BeamControl.device_class)
    device_class.default = 'pcdsdevices.device_types.LODCM'
    mono_line = EntryInfo("Name of the MONO beamline",
                          enforce=str, optional=False)
    kwargs = deepcopy(BeamControl.kwargs)
    kwargs.default.update({'mono_line': '{{mono_line}}',
                           'main_line': '{{beamline}}'})


class MovableStand(LegacyItem):
    """
    This class stores information about stands that move, like XPP's hand-crank
    that moves SB2 and SB3 from the PINK to XPP lines and back. There is no
    need to instantiate one of these for static stands.

    Attributes
    ----------
    prefix : str
        If there is a single PV with the stand's location, this should be the
        base PV. In general, these devices will actually have multiple PVs
        with binary outputs that have yes/no on the stand being in each
        position. In these cases we pick the common prefix of these PVs.

    stand : list
        List of stands affected by table movement.
    """
    stand = copy(LegacyItem.stand)
    stand.enforce = list
    system = copy(LegacyItem.system)
    system.default = 'changeover'


class Motor(LCLSItem, LegacyItem):
    """
    A Generic EpicsMotor
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.Motor'
    system = copy(LegacyItem.system)
    system.default = 'motion'


class AreaDetector(LegacyItem):
    """
    A Generic EpicsCamera
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.PCDSDetector'
    system = copy(LegacyItem.system)
    system.default = 'camera'


class Acromag(LegacyItem):
    """
    A Generic class for Acromag
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.Acromag'
    system = copy(LegacyItem.system)
    system.default = 'acromag'


class Trigger(LegacyItem):
    """
    A Generic class for Controls Triggers
    """
    device_class = copy(LegacyItem.device_class)
    device_class.default = 'pcdsdevices.device_types.Trigger'
    system = copy(LegacyItem.system)
    system.default = 'timing'


class Elliptec(LCLSItem):
    """
    A Generic class for Elliptec Motors
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.device_types.EllBase'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'Elliptec'
    kwargs = deepcopy(LegacyItem.kwargs)
    kwargs.default['port'] = "0"
    kwargs.default['channel'] = "{{ioc_channel}}"
    ioc_serial = EntryInfo(('Serial number of the stage controller. Used to '
                            'build IOC configs.'),
                           optional=True, enforce=str)
    ioc_model = EntryInfo(('Model number of the stage. Used to build IOC '
                           'configs.'),
                          optional=True, enforce=str)
    ioc_channel = EntryInfo(('Channel number of the stage. Used to build IOC '
                             'configs, and passed to python object.'),
                            optional=False, enforce=str)
    ioc_base = EntryInfo(('Elliptec controller PV base. This is not '
                          'necessarily the same as the desired axis '
                          'base PV. Use the "ioc_alias" entry to modify '
                          'if a different axis PV is desired.'),
                         optional=True, enforce=str)
    ioc_alias = EntryInfo('Optional alias to give the axis.', optional=True,
                          enforce=str, default=None)


class Qmini(LCLSItem):
    """
    A Generic class for Qseries spectrometers
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.device_types.QminiSpectrometer'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'Qmini'
    ioc_serial = EntryInfo(('Serial number of the spectrometer. Used to '
                            'build IOC configs.'),
                           optional=True, enforce=str)
    ioc_use_evr = EntryInfo(('Option to use an EVR or not. Options are "yes"'
                             ' and "no". Default is no.'), optional=True,
                            default='no', enforce=str)
    ioc_evr_channel = EntryInfo('The EVR channel the IOC will use, if any.',
                                optional=True, default='1', enforce=str)


class SmarActMotor(LCLSItem):
    """
    Container for individual SmarAct motors (open or closed loop).
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.epics_motor.SmarAct'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'SmarAct'
    ioc_ip = EntryInfo(('Netconfig entry name for motor controller. Used to '
                        'build IOC configs.'),
                       optional=True, enforce=str)
    ioc_base = EntryInfo(('Base PV of the SmarAct controller. Used to build '
                          'IOC configs.'), optional=True, enforce=str)
    ioc_channel = EntryInfo(('Controller channel that the axis is on. Ranges '
                             'from 1 to 18.'), optional=True, enforce=str)
    ioc_alias = EntryInfo('Optional PV alias to give this axis.',
                          optional=True, enforce=str)


class SmarActTipTiltMotor(LCLSItem):
    """
    Container for SmarAct tip-tilt motor pairs.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.epics_motor.SmarActTipTilt'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'SmarAct'
    kwargs = deepcopy(LegacyItem.kwargs)
    args = deepcopy(LegacyItem.args)
    args = []  # No args for me, thank you
    kwargs.default['tip_pv'] = "{{ioc_tip_suffix}}"
    kwargs.default['tilt_pv'] = "{{ioc_tilt_suffix}}"
    ioc_ip = EntryInfo(('Netconfig entry name for motor controller. Used to '
                        'build IOC configs.'), optional=True, enforce=str)
    ioc_tip_channel = EntryInfo(('Controller channel that the tip axis is on. '
                                 'Ranges from 1 to 18.'), optional=True,
                                enforce=str)
    ioc_tilt_channel = EntryInfo(('Controller channel that the tilt axis is '
                                  'on. Ranges from 1 to 18.'), optional=True,
                                 enforce=str)
    ioc_base = EntryInfo(('Base PV of the SmarAct controller. Used to build '
                          'IOC configs.'), optional=True, enforce=str)
    ioc_alias = EntryInfo(('Base alias PV of the two stages. Used to build '
                          'IOC configs.'), optional=True, enforce=str)
    ioc_tip_suffix = EntryInfo('PV suffix to give the tip axis alias.',
                               default='_TIP1', optional=True, enforce=str)
    ioc_tilt_suffix = EntryInfo('PV suffix to give the tilt axis alias.',
                                default='_TILT1', optional=True, enforce=str)


class BaslerCamera(LCLSItem):
    """
    Container for Basler cameras.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.areadetector.detectors.Basler'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'BaslerGigE'
    ioc_ip = EntryInfo(('IP address (not netconfig name) of the camera. Used '
                        'to build IOC configs.'), optional=True, enforce=str)
    ioc_cam_model = EntryInfo(('Model number of the camera, e.g. '
                               '"Basler_acA2500-20gm". Used to build IOC '
                               'config files.'), optional=True, enforce=str)
    ioc_use_evr = EntryInfo(('Option to use an EVR or not. Options are "yes"'
                             ' and "no". Default is no.'), optional=True,
                            default='no', enforce=str)
    ioc_evr_channel = EntryInfo('The EVR channel the IOC will use, if any.',
                                optional=True, default='1', enforce=str)
    ioc_net_if = EntryInfo(('Network interface name. Typically ETH0, ETH1, '
                           'ENO1 or ENO2.'), optional=True, default='ETH0',
                           enforce=str)
    ioc_net_if_num = EntryInfo('Network interface number. Typically 1.',
                               optional=True, default='1', enforce=str)
    ioc_http_port = EntryInfo('Unique HTTP port. Needed for MJPG plugin.',
                              optional=True, default='7801', enforce=str)


class LasBasler(BaslerCamera):
    """
    Container for MODS system Basler cameras.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.areadetector.detectors.LasBasler'


class ThorlabsWfs(LCLSItem):
    """
    Container for Thorlabs WFS sensors.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.device_types.ThorlabsWfs40'
    # This device uses a weird version of gcc. Also needs special environment
    # to compile; this can be set using a script in the IOC parent directory.
    ioc_arch = copy(LCLSItem.ioc_arch)
    ioc_arch.default = 'rhel7-gcc494-x86_64'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'ThorLabsWfs40'
    ioc_model = EntryInfo('Thorlabs camera model number.', optional=True,
                          default='WFS-40', enforce=str)
    ioc_id_num = EntryInfo('Unique ID number of the camera', optional=True,
                           enforce=str)
    ioc_lenslet_pitch = EntryInfo('Pitch of WFS lenslets.', optional=True,
                                  default='150', enforce=str)
    ioc_use_evr = EntryInfo(('Option to use an EVR or not. Options are "yes"'
                             ' and "no". Default is no.'), optional=True,
                            default='no', enforce=str)
    ioc_evr_channel = EntryInfo('The EVR channel the IOC will use, if any.',
                                optional=True, default='1', enforce=str)


class ThorlabsPM101PowerMeter(LCLSItem):
    """
    Container for the Thorlabs PM101A power meter, digitized with an EL3174.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.device_types.El3174AiCh'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'EK9000'
    ioc_ip = EntryInfo(('Netconfig name of the EK9000 the power meter is '
                        'connected to. Used to build IOC configs.'),
                       optional=True, enforce=str)
    ioc_card_num = EntryInfo(('Card number of the EL3174 the power meter is '
                              'connected to.'), optional=True, enforce=str)
    ioc_chan_num = EntryInfo(('Channel number of the EL3174 the power meter '
                              'is connected to.'), optional=True, enforce=str)
    ioc_base = EntryInfo('Base PV of the EK9000 IOC', optional=True,
                         enforce=str)
    ioc_alias = EntryInfo('Optional PV alias to give this power meter.',
                          optional=True, enforce=str)


class EnvironmentalMonitor(LCLSItem):
    """
    Container for MODS environmental monitor units.

    These units follow a standard deployment and naming configuration. It is
    assumed that the sensors will be connected to the first card, an EL3174,
    on the EK9000 with the pressure, humidity and temperature sensors connected
    to channels1, 2 and 3 respectively.
    """
    device_class = copy(LCLSItem.device_class)
    device_class.default = 'pcdsdevices.device_types.EnvironmentalMonitor'
    ioc_type = copy(LCLSItem.ioc_type)
    ioc_type.default = 'EK9000'
    ioc_ip = EntryInfo(('Netconfig name of the EK9000 the sensors are '
                        'connected to. Used to build IOC configs.'),
                       optional=True, enforce=str)
    ioc_base = EntryInfo('Base PV of the EK9000 IOC', optional=True,
                         enforce=str)
