#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Plugins.
"""

import logging
import ophyd.plugins
from ophyd import GenerateDatumInterface
from .base import ADBase

logger = logging.getLogger(__name__)


class PluginBase(ophyd.plugins.PluginBase, ADBase):
    pass


class ImagePlugin(ophyd.plugins.ImagePlugin, PluginBase):
    pass


class StatsPlugin(ophyd.plugins.StatsPlugin, PluginBase):
    pass


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
    pass


class HDF5Plugin(ophyd.plugins.HDF5Plugin, FilePlugin):
    pass


class MagickPlugin(ophyd.plugins.MagickPlugin, FilePlugin):
    pass


