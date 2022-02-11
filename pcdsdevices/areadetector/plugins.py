"""
PCDS plugins and Overrides for AreaDetector Plugins.
"""
import datetime
import logging
import time

import numpy as np
import ophyd
from ophyd import Component as C
from ophyd import EpicsSignal
from ophyd.areadetector.base import ADBase
from ophyd.areadetector.filestore_mixins import FileStoreHDF5IterativeWrite
from ophyd.areadetector.plugins import HDF5Plugin_V31
from ophyd.device import GenerateDatumInterface
from ophyd.ophydobj import OphydObject
from ophyd.utils import set_and_wait
from pcdsutils.ext_scripts import get_current_experiment, get_run_number

logger = logging.getLogger(__name__)


class PluginBase(ophyd.plugins.PluginBase, ADBase):
    """
    Overridden PluginBase to make it work when the root device is not a CamBase
    class.
    """
    enable = C(EpicsSignal, 'EnableCallbacks_RBV.RVAL', write_pv="EnableCallbacks", string=False)

    @property
    def source_plugin(self):
        # The PluginBase object that is the asyn source for this plugin.
        source_port = self.nd_array_port.get()
        if source_port == 'CAM' or not hasattr(
                self.root, 'get_plugin_by_asyn_port'):
            return None
        source_plugin = self.root.get_plugin_by_asyn_port(source_port)
        return source_plugin

    @property
    def _asyn_pipeline_configuration_names(self):
        # This broke any instantiated plugin b/c _asyn_pipeline is a list that
        # can have None.
        return [_.configuration_names.name for _ in self._asyn_pipeline if
                hasattr(_, 'configuration_names')]

    @property
    def _asyn_pipeline(self):
        parent = None
        # Add a check to make sure root has this attr, otherwise return None
        if hasattr(self.root, 'get_plugin_by_asyn_port') and self.root != self:
            parent = self.root.get_plugin_by_asyn_port(self.nd_array_port.get())
            if hasattr(parent, '_asyn_pipeline'):
                return parent._asyn_pipeline + (self, )
        return (parent, self)

    def describe_configuration(self):
        # Use the overridden describe_configuration defined above
        ret = ADBase.describe_configuration(self)
        source_plugin = self.source_plugin
        if source_plugin is not None and source_plugin is not self:
            ret.update(source_plugin.describe_configuration())
        return ret

    def read_configuration(self):
        ret = ADBase.read_configuration(self)
        if self.source_plugin is not self:
            ret.update(self.source_plugin.read_configuration())
        return ret

    def stage(self):
        # Ensure the plugin is enabled. We do not disable it on unstage
        if self.enable not in self.stage_sigs and 'enable' not in self.stage_sigs:
            if not self.enable.connected:
                self.enable.get()
            set_and_wait(self.enable, 1, atol=0)
        ADBase.stage(self)

    @property
    def array_pixels(self):
        """The total number of pixels, calculated from array_size."""
        array_size = list(self.array_size.get())
        dimensions = int(self.ndimensions.get())

        if dimensions == 0:
            return 0

        pixels = array_size[0]
        for dim in array_size[1:dimensions]:
            if dim:
                pixels *= dim

        return int(pixels)


class ImagePlugin(ophyd.plugins.ImagePlugin, PluginBase):
    @property
    def image(self):
        """Overriden image method to add in some corrections."""
        array_size = [int(val) for val in self.array_size.get()]
        if array_size == [0, 0, 0]:
            raise RuntimeError('Invalid image; ensure array_callbacks are on')

        if array_size[-1] == 0:
            array_size = array_size[:-1]

        pixel_count = self.array_pixels
        image = self.array_data.get(count=pixel_count)
        return np.array(image).reshape(array_size)


class StatsPlugin(ophyd.plugins.StatsPlugin, PluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs['compute_statistics'] = 'Yes'
        self.stage_sigs['compute_centroid'] = 'Yes'


class ColorConvPlugin(ophyd.plugins.ColorConvPlugin, PluginBase):
    pass


class ProcessPlugin(ophyd.plugins.ProcessPlugin, PluginBase):
    pass


class Overlay(ophyd.plugins.Overlay, ADBase):
    pass


class OverlayPlugin(ophyd.plugins.OverlayPlugin, PluginBase):
    pass


class ROIPlugin(ophyd.plugins.ROIPlugin, PluginBase):
    pass


class TransformPlugin(ophyd.plugins.TransformPlugin, PluginBase):
    pass


class FilePlugin(ophyd.plugins.FilePlugin, PluginBase, GenerateDatumInterface):
    pass


class NetCDFPlugin(ophyd.plugins.NetCDFPlugin, FilePlugin):
    pass


class TIFFPlugin(ophyd.plugins.TIFFPlugin, FilePlugin):
    pass


class JPEGPlugin(ophyd.plugins.JPEGPlugin, FilePlugin):
    pass


class NexusPlugin(ophyd.plugins.NexusPlugin, FilePlugin):
    # Skip plugin_type checks on this plugin, as old versions of AD did not
    # reflect this correctly
    _plugin_type = None


class HDF5Plugin(ophyd.plugins.HDF5Plugin, FilePlugin):
    pass


class MagickPlugin(ophyd.plugins.MagickPlugin, FilePlugin):
    pass


class HDF5FileStore(FileStoreHDF5IterativeWrite, HDF5Plugin_V31):
    """
    HDF5 Plugin to use for interactive/in-scan saving at LCLS.

    Includes some mangling of the filename selection to keep
    the names human-readable because we don't actually use
    filestore/databroker at LCLS.
    """
    def make_filename(self) -> str:
        """Select a filename that makes SLAC scientists happy"""
        try:
            run_number = get_run_number(
                hutch=self.parent.hutch_name,
                live=False,
                timeout=5,
            )
            experiment = get_current_experiment(
                self.parent.hutch_name,
                live=False,
                timeout=5,
            )
            filename = f'{experiment}_run{run_number}_{time.time():.0f}'
        except Exception:
            filename = f'{self.name}_{time.time():.0f}'
        formatter = datetime.datetime.now().strftime
        return (
            filename,
            formatter(self.read_path_template),
            formatter(self.write_path_template),
        )

    def unstage(self) -> list[OphydObject]:
        """
        At cleanup, let the user know which file has been created last.
        """
        super().unstage()
        print(f'Created file {self.full_file_name.get()}')
