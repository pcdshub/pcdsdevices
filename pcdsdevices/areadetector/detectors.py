"""
PCDS detectors and overrides for ophyd detectors.

All components at the detector level such as plugins or image processing
functions needed by all instances of a detector are added here.
"""
import logging
import shutil
import subprocess
import time
import warnings

from ophyd import Device
from ophyd.areadetector import cam
from ophyd.areadetector.base import (ADComponent, EpicsSignalWithRBV,
                                     NDDerivedSignal)
from ophyd.areadetector.detectors import DetectorBase
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.device import Component as Cpt
from ophyd.ophydobj import OphydObject
from ophyd.signal import AttributeSignal, EpicsSignal, EpicsSignalRO
from pcdsutils.ext_scripts import get_hutch_name

from pcdsdevices.variety import set_metadata

from .plugins import (ColorConvPlugin, HDF5FileStore, HDF5Plugin, ImagePlugin,
                      JPEGPlugin, NetCDFPlugin, NexusPlugin, OverlayPlugin,
                      ProcessPlugin, ROIPlugin, StatsPlugin, TIFFPlugin,
                      TransformPlugin)

logger = logging.getLogger(__name__)


__all__ = ['PCDSAreaDetectorBase',
           'PCDSAreaDetectorEmbedded',
           'PCDSAreaDetector']


class PCDSAreaDetectorBase(DetectorBase):
    """Standard area detector with no plugins."""
    cam = ADComponent(cam.CamBase, '')

    def get_plugin_graph_edges(self, *, use_names=True, include_cam=False):
        """
        Get a list of (source, destination) ports for all plugin chains.

        Parameters
        ----------
        use_names : bool, optional
            By default, the ophyd names for each plugin are used. Set this to
            False to instead get the AreaDetector port names.
        include_cam : bool, optional
            Include plugins with 'CAM' as the source.  As it is easy to assume
            that a camera without an explicit source is CAM, by default this
            method does not include it in the list.
        """

        cam_port = self.cam.port_name.get()
        graph, port_map = self.get_asyn_digraph()
        port_edges = [(src, dest) for src, dest in graph.edges
                      if src != cam_port or include_cam]
        if use_names:
            port_edges = [(port_map[src].name, port_map[dest].name)
                          for src, dest in port_edges]
        return port_edges

    def screen(self, main: bool=False) -> None:
        """
        Open camViewer screen for camera.

        Parameters
        ----------
        main : bool, optional
            Set to True to bring up 'main' edm config screen.
            Defaults to False, which opens python viewer.
        """
        if not shutil.which('camViewer'):
            logger.error('no camViewer available')
            return

        arglist = ['camViewer', '-H', str(get_hutch_name()).lower(),
                    '-c', self.name]
        if main:
            arglist.append('-m')

        logger.info('starting camviewer')
        subprocess.run(arglist, check=False)


class PCDSHDF5BlueskyTriggerable(SingleTrigger, PCDSAreaDetectorBase):
    """
    Saves an HDF5 file in a bluesky plan.

    This class takes care of all the standard setup for saving the files
    using the HDF5 plugin for our area detector setups at LCLS during
    bluesky scans, including configuration of the stage signals
    and various site-specific settings.

    You can decide how many images we'll take at each point by setting
    the `num_images_per_point` attribute.

    There are two modes provided: "always aquire" and "aquire at points"
    with key differences in the behavior. You can select which one
    to use using the ``always_acquire`` keyword argument, which
    defaults to True.

    With always_aquire=True (default):
    - Viewers will remain updated throughout the scan, even between
      scan points.
    - The camera will be set to ``acquire`` at ``stage``, if needed, which
      begins taking images. This happens early in the scan.
    - At each point, the ``capture`` feature of the HDF5 plugin will be
      toggled on until we've saved an image count equal to the
      `num_images_per_point` attribute. The counting is handled by the
      plugin.
    - If the camera or server lags during the aquisition, the scan will
      patiently wait for the correct number of images to be saved.
    - There is no guarantee that the images are sequential, there can be
      gaps, but each image that does get saved will be trigger-synchronized.
      (And therefore, beam-synchronized with beam-synchronized triggers).
    - Each point in the scan will have its own associate hdf5 file.
    - If the camera needed to be set to ``acquire`` at ``stage``,
      it will revert to ``stop`` at ``unstage``.

    With always_acquire=False:
    - Viewers will only be updated at the specific scan points.
    - The HDF5 plugin will be set to ``capture`` at stage, and the camera
      will be configured to take a fixed number of images per acquisition
      cycle.
    - At each point, the ``acquire`` bit will be turned on, which causes
      `num_images_per_point` images to be acquired.
    - If the camera or server lags during the acquisition, it will be
      unable to complete it cleanly.
    - There is a guarantee that the images are sequential.
    - All the points in the scan will be grouped into one larger hdf5 file.

    This class can be also be used interactively via the ``save_images``
    function.

    Parameters
    ----------
    prefix : ``str``
        The PV prefix that leads us to this camera's PVs.
    write_path : ``str``
        The directory to drop our hdf5 files into.
    always_acquire : ``bool``, optional
        Determines which mode we use to collect images as described above.
    name : ``str``, keyword-only
        A name to associate with the camera for bluesky.
    """
    hdf51 = ADComponent(
        HDF5FileStore,
        'HDF51:',
        write_path_template='/dev/null',
        kind='normal',
        doc='Save output as an HDF5 file'
    )
    def __init__(
        self,
        *args,
        write_path: str,
        always_acquire: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.hutch_name = get_hutch_name()
        self.always_acquire = always_acquire
        self.num_images_per_point = 1
        self.hdf51.write_path_template = write_path
        self.hdf51.stage_sigs['file_template'] = '%s%s_%03d.h5'
        self.hdf51.stage_sigs['file_write_mode'] = 'Stream'
        del self.hdf51.stage_sigs["capture"]
        if always_acquire:
            # This mode is "acquire always, capture on trigger"
            # Override the default to Continuous, always go
            self.stage_sigs['cam.acquire'] = 1
            self.stage_sigs['cam.image_mode'] = 2
            # Make sure we toggle capture for trigger
            self._acquisition_signal = self.hdf51.capture
        else:
            # This mode is "acquire on trigger, capture always"
            # Confirm default of Multiple, start off
            # Redundantly set these here for code clarity
            self.stage_sigs['cam.acquire'] = 0
            self.stage_sigs['cam.image_mode'] = 1
            # If we include capture in stage, it must be last
            self.hdf51.stage_sigs["capture"] = 1
            # Ensure we use the cam acquire as the trigger
            self._acquisition_signal = self.cam.acquire

    def stage(self) -> list[OphydObject]:
        """
        Bluesky interface for setting up the plan.

        This will unpack all of our stage_sigs like normal, but also
        add a small delay to avoid a race condition in the IOC.
        """
        rval = super().stage()
        # It takes a moment for the IOC to be ready sometimes
        time.sleep(0.1)
        return rval

    @property
    def num_images_per_point(self) -> int:
        """
        The number of images to save at each point in the scan.
        """
        if self.always_acquire:
            return self.cam.stage_sigs['num_images']
        return self.hdf51.stage_sigs['num_capture']

    @num_images_per_point.setter
    def num_images_per_point(self, num_images: int):
        if self.always_acquire:
            self.hdf51.stage_sigs['num_capture'] = num_images
            self.cam.stage_sigs['num_images'] = 1
        else:
            self.hdf51.stage_sigs['num_capture'] = 0
            self.cam.stage_sigs['num_images'] = num_images

    def save_images(self) -> None:
        """
        Save images interactively as if we were currently at a scan point.
        """
        self.stage()
        self.trigger().wait()
        self.unstage()


class PCDSAreaDetectorEmbedded(PCDSAreaDetectorBase):
    """
    Minimal area detector including only the most-used PCDS plugins.

    The plugins included are:
        IMAGE2: reduced rate image, used for camera viewer.
        Stats2: reduced rate stats.
        HDF51: hdf5 files.
    """

    image2 = Cpt(ImagePlugin, 'IMAGE2:', kind='normal',
                 doc='Image plugin used for the camera viewer')
    stats2 = Cpt(StatsPlugin, 'Stats2:', kind='normal',
                 doc='Stats plugin used for alignments')
    hdf51 = Cpt(HDF5Plugin, 'HDF51:', kind='normal',
                doc='HDF5 plugin used to create HDF5 files')

    def get_full_area_detector(self):
        if isinstance(self, PCDSAreaDetector):
            return self
        return PCDSAreaDetector(self.prefix, name=self.name + '_full')


class PCDSAreaDetector(PCDSAreaDetectorEmbedded):
    """
    Standard area detector including all (*) standard PCDS plugins.

    Notable plugins:
        IMAGE2: reduced rate image, used for camera viewer
        Stats2: reduced rate stats

    (*) Currently excludes all PVAccess plugins:
        IMAGE1:Pva
        IMAGE2:Pva:
        THUMBNAIL:Pva

    Default port chains
    -------------------
    The default configuration of ports is as follows::

        CAM -> CC1
        CAM -> CC2
        CAM -> HDF51
        CAM -> IMAGE1:CC
        CAM -> IMAGE1:Proc
        CAM -> IMAGE1:ROI
        CAM -> IMAGE2:CC
        CAM -> IMAGE2:Over
        CAM -> IMAGE2:Proc
        CAM -> IMAGE2:ROI -> IMAGE2
        CAM -> JPEG1
        CAM -> NetCDF1
        CAM -> Over1
        CAM -> Proc1
        CAM -> ROI1 -> IMAGE1
        CAM -> ROI1 -> Stats1
        CAM -> ROI2
        CAM -> ROI3
        CAM -> ROI4
        CAM -> Stats2
        CAM -> Stats3
        CAM -> Stats4
        CAM -> Stats5
        CAM -> THUMBNAIL:CC
        CAM -> THUMBNAIL:Over
        CAM -> THUMBNAIL:Proc
        CAM -> THUMBNAIL:ROI -> THUMBNAIL
        CAM -> TIFF1
        CAM -> Trans1

    Notes
    -----
    Subclasses should replace :attr:`cam` with that of the respective detector,
    such as `PilatusDetectorCam` for the Pilatus
    detector.
    """

    image1 = Cpt(ImagePlugin, 'IMAGE1:')
    image1_roi = Cpt(ROIPlugin, 'IMAGE1:ROI:')
    image1_cc = Cpt(ColorConvPlugin, 'IMAGE1:CC:')
    image1_proc = Cpt(ProcessPlugin, 'IMAGE1:Proc:')
    image1_over = Cpt(OverlayPlugin, 'IMAGE1:Over:')
    # image2 in parent
    image2_roi = Cpt(ROIPlugin, 'IMAGE2:ROI:')
    image2_cc = Cpt(ColorConvPlugin, 'IMAGE2:CC:')
    image2_proc = Cpt(ProcessPlugin, 'IMAGE2:Proc:')
    image2_over = Cpt(OverlayPlugin, 'IMAGE2:Over:')
    thumbnail = Cpt(ImagePlugin, 'THUMBNAIL:')
    thumbnail_roi = Cpt(ROIPlugin, 'THUMBNAIL:ROI:')
    thumbnail_cc = Cpt(ColorConvPlugin, 'THUMBNAIL:CC:')
    thumbnail_proc = Cpt(ProcessPlugin, 'THUMBNAIL:Proc:')
    thumbnail_over = Cpt(OverlayPlugin, 'THUMBNAIL:Over:')
    cc1 = Cpt(ColorConvPlugin, 'CC1:')
    cc2 = Cpt(ColorConvPlugin, 'CC2:')
    hdf51 = Cpt(HDF5Plugin, 'HDF51:')
    jpeg1 = Cpt(JPEGPlugin, 'JPEG1:')
    netcdf1 = Cpt(NetCDFPlugin, 'NetCDF1:')
    nexus1 = Cpt(NexusPlugin, 'Nexus1:')
    over1 = Cpt(OverlayPlugin, 'Over1:')
    proc1 = Cpt(ProcessPlugin, 'Proc1:')
    roi1 = Cpt(ROIPlugin, 'ROI1:')
    roi2 = Cpt(ROIPlugin, 'ROI2:')
    roi3 = Cpt(ROIPlugin, 'ROI3:')
    roi4 = Cpt(ROIPlugin, 'ROI4:')
    stats1 = Cpt(StatsPlugin, 'Stats1:')
    # stats2 in parent
    stats3 = Cpt(StatsPlugin, 'Stats3:')
    stats4 = Cpt(StatsPlugin, 'Stats4:')
    stats5 = Cpt(StatsPlugin, 'Stats5:')
    tiff1 = Cpt(TIFFPlugin, 'TIFF1:')
    trans1 = Cpt(TransformPlugin, 'Trans1:')


class PCDSAreaDetectorTyphos(Device):
    """
    A 'bare' PCDS areadetector class specifically for Typhos screens.
    Implements only the most commonly used PVs for areadetector IOCS.
    Includes a simple image viewer.
    """

    # Status and specifications
    manufacturer = Cpt(EpicsSignalRO, 'Manufacturer_RBV', kind='config')
    camera_model = Cpt(EpicsSignalRO, 'Model_RBV', kind='normal')
    sensor_size_x = Cpt(EpicsSignalRO, 'MaxSizeX_RBV', kind='config')
    sensor_size_y = Cpt(EpicsSignalRO, 'MaxSizeY_RBV', kind='config')
    data_type = Cpt(EpicsSignalWithRBV, 'DataType', kind='config')

    # Acquisition settings
    exposure = Cpt(EpicsSignalWithRBV, 'AcquireTime', kind='config')
    gain = Cpt(EpicsSignalWithRBV, 'Gain', kind='config')
    num_images = Cpt(EpicsSignalWithRBV, 'NumImages', kind='config')
    image_mode = Cpt(EpicsSignalWithRBV, 'ImageMode', kind='config')
    trigger_mode = Cpt(EpicsSignalWithRBV, 'TriggerMode', kind='config')
    acquisition_period = Cpt(EpicsSignalWithRBV, 'AcquirePeriod', kind='config')

    # Image collection settings
    acquire = Cpt(EpicsSignal, 'Acquire', kind='normal')
    acquire_rbv = Cpt(EpicsSignalRO, 'DetectorState_RBV', kind='normal')
    image_counter = Cpt(EpicsSignalRO, 'NumImagesCounter_RBV', kind='normal')

    # TJ: removing from the class for now. May be useful later.
    # Image data
#    ndimensions = Cpt(EpicsSignalRO, 'IMAGE2:NDimensions_RBV', kind='omitted')
#    width = Cpt(EpicsSignalRO, 'IMAGE2:ArraySize0_RBV', kind='omitted')
#    height = Cpt(EpicsSignalRO, 'IMAGE2:ArraySize1_RBV', kind='omitted')
#    depth = Cpt(EpicsSignalRO, 'IMAGE2:ArraySize2_RBV', kind='omitted')
#    array_data = Cpt(EpicsSignal, 'IMAGE2:ArrayData', kind='omitted')
#    cam_image = Cpt(NDDerivedSignal, derived_from='array_data',
#                    shape=('height',
#                           'width',
#                           'depth'),
#                    num_dimensions='ndimensions',
#                    kind='normal')

    def open_viewer(self):
        """
        Launch the python camera viewer for this camera.
        """
        arglist = ['/reg/g/pcds/pyps/apps/camviewer/latest/run_viewer.sh',
                   '--instrument',
                   '{}.format(get_hutch_name())',
                   '--oneline',
                   'GE:16,{0}:IMAGE1;{0},,{0}'.format(self.prefix[0:-1])]

        self.log.info('Opening python viewer for camera...')
        subprocess.run(arglist, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)

    # Make viewer available in Typhos screen
    cam_viewer = Cpt(AttributeSignal, attr='_open_screen', kind='normal')
    set_metadata(cam_viewer, dict(variety='command-proc', value=1))

    @property
    def _open_screen(self):
        return 0

    @_open_screen.setter
    def _open_screen(self, value):
        self.open_viewer()

    def screen(self):
        """ Lean on open_viewer method """
        self.open_viewer()


class PCDSAreaDetectorTyphosTrigger(PCDSAreaDetectorTyphos):
    """
    Expanded typhos-optimized areadetector class for cameras with triggers.
    """

    event_code = Cpt(EpicsSignalWithRBV, 'CamEventCode', kind='config',
                     doc='Code to determine beam synchronization rate.')
    event_rate = Cpt(EpicsSignalRO, 'CamRepRate_RBV', kind='config',
                     doc='Current rate of the incoming triggers. '
                         'Determined by event_code and the '
                         'accelerator state.')


class PCDSAreaDetectorTyphosBeamStats(PCDSAreaDetectorTyphosTrigger):
    """
    Adds in some PVs related to beam statistics, as well as a cross hair.
    Primarily intended for use in the laser control system.
    """

    # Stats2 PVs
    stats_enable = Cpt(EpicsSignalWithRBV, 'Stats2:EnableCallbacks',
                       kind='config')
    centroid_x = Cpt(EpicsSignalRO, 'Stats2:CentroidX_RBV', kind='normal')
    centroid_y = Cpt(EpicsSignalRO, 'Stats2:CentroidY_RBV', kind='normal')
    sigma_x = Cpt(EpicsSignalRO, 'Stats2:SigmaX_RBV', kind='normal')
    sigma_y = Cpt(EpicsSignalRO, 'Stats2:SigmaY_RBV', kind='normal')
    centroid_threshold = Cpt(EpicsSignalWithRBV, 'Stats2:CentroidThreshold',
                             kind='config')
    centroid_enable = Cpt(EpicsSignal, 'Stats2:ComputeCentroid', kind='config')

    # Cross PVs
    target_x = Cpt(EpicsSignalWithRBV, 'Cross4:MinX', kind='normal')
    target_y = Cpt(EpicsSignalWithRBV, 'Cross4:MinY', kind='normal')


class BaslerBase(Device):
    """
    Base class with Basler specific PVs. Intended to be sub-classed, not used
    stand-alone.
    """
    reset = Cpt(EpicsSignal, 'RESET.PROC', kind='config', doc='Reset the camera')
    set_metadata(reset, dict(variety='command-proc', value=1))
    packet_size = Cpt(EpicsSignal, 'GevSCPSPacketSiz_RBV',
                      write_pv='GevSCPSPacketSiz', kind='config',
                      doc='Set Ethernet Packet Size (typ. 9000)')
    enet_bw = Cpt(EpicsSignalRO, 'GevSCDCT_RBV', kind='config',
                  doc='Current Ethernet bandwidth')


# Typical "hutch" Basler class
class Basler(PCDSAreaDetectorTyphosTrigger, BaslerBase):
    """
    Class for Basler cameras.
    See Also
    --------
    :class:`LasBasler`
        Basler camera with additional laser-specific entries.
    """
    pass


class LasBasler(PCDSAreaDetectorTyphosBeamStats, BaslerBase):
    """
    Class for the Basler cameras used in the laser control system.
    """
    pass
