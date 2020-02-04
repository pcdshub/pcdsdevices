"""
PCDS detectors and overrides for ophyd detectors.

All components at the detector level such as plugins or image processing
functions needed by all instances of a detector are added here.
"""
import logging
import warnings

from ophyd.areadetector import cam
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.detectors import DetectorBase
from ophyd.device import Component as Cpt
from .plugins import (ColorConvPlugin, HDF5Plugin, ImagePlugin, JPEGPlugin,
                      NetCDFPlugin, OverlayPlugin, ProcessPlugin, ROIPlugin,
                      StatsPlugin, TIFFPlugin, TransformPlugin, NexusPlugin)

logger = logging.getLogger(__name__)


__all__ = ['PCDSAreaDetectorBase',
           'PCDSAreaDetector']


class PCDSAreaDetectorBase(DetectorBase):
    """
    Standard area detector with no plugins.
    """
    cam = ADComponent(cam.CamBase, '')


class PCDSAreaDetector(PCDSAreaDetectorBase):
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

    Note
    ----
    Subclasses should replace 'cam' with that of the respective detector, such
    as `ophyd.areadetector.cam.PilatusDetectorCam` for the Pilatus detector.
    """
    image1 = Cpt(ImagePlugin, 'IMAGE1:', read_attrs=['array_data'],
                 doc='Image plugin for general usage')
    image1_roi = Cpt(ROIPlugin, 'IMAGE1:ROI:')
    image1_cc = Cpt(ColorConvPlugin, 'IMAGE1:CC:')
    image1_proc = Cpt(ProcessPlugin, 'IMAGE1:Proc:')
    image1_over = Cpt(OverlayPlugin, 'IMAGE1:Over:')
    image2 = Cpt(ImagePlugin, 'IMAGE2:', read_attrs=['array_data'],
                 doc='Image plugin used for the camera viewer')
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
    stats1 = Cpt(StatsPlugin, 'Stats1:', read_attrs=['centroid', 'mean_value',
                                                     'sigma_x', 'sigma_y'])
    stats2 = Cpt(StatsPlugin, 'Stats2:', read_attrs=['centroid', 'mean_value',
                                                     'sigma_x', 'sigma_y'])
    stats3 = Cpt(StatsPlugin, 'Stats3:', read_attrs=['centroid', 'mean_value',
                                                     'sigma_x', 'sigma_y'])
    stats4 = Cpt(StatsPlugin, 'Stats4:', read_attrs=['centroid', 'mean_value',
                                                     'sigma_x', 'sigma_y'])
    stats5 = Cpt(StatsPlugin, 'Stats5:', read_attrs=['centroid', 'mean_value',
                                                     'sigma_x', 'sigma_y'])
    tiff1 = Cpt(TIFFPlugin, 'TIFF1:')
    trans1 = Cpt(TransformPlugin, 'Trans1:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image2.stage_sigs['enable'] = 1
        self.stats2.stage_sigs['enable'] = 1
        self.stats2.stage_sigs['compute_statistics'] = 'Yes'
        self.stats2.stage_sigs['compute_centroid'] = 'Yes'

    def get_plugin_graph_edges(self, *, use_names=True, include_cam=False):
        '''Get a list of (source, destination) ports for all plugin chains

        Parameters
        ----------
        use_names : bool, optional
            By default, the ophyd names for each plugin are used. Set this to
            False to instead get the AreaDetector port names.
        include_cam : bool, optional
            Include plugins with 'CAM' as the source.  As it is easy to assume
            that a camera without an explicit source is CAM, by default this
            method does not include it in the list.
        '''
        cam_port = self.cam.port_name.get()
        graph, port_map = self.get_asyn_digraph()
        port_edges = [(src, dest) for src, dest in graph.edges
                      if src != cam_port or include_cam]
        if use_names:
            port_edges = [(port_map[src].name, port_map[dest].name)
                          for src, dest in port_edges]
        return port_edges

    @property
    def image(self):
        'Deprecated - alias for `image2`'
        warnings.warn('PCDSAreaDetector.image is deprecated; use {}.image2 '
                      'instead'.format(self.name))
        return self.image2

    @property
    def stats(self):
        'Deprecated - alias for `stats2`'
        warnings.warn('PCDSAreaDetector.image is deprecated; use {}.stats2 '
                      'instead'.format(self.name))
        return self.stats2
